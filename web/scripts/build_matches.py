#!/usr/bin/env python3
"""
build_matches.py — emit web/static/data/matches.json (the Context-page data contract).

Sources (read-only):
  - <repo>/results.csv               → the 72 WC2026 group-stage fixtures (+ venue)
  - <repo>/output/predictions.json   → M2 (neural) match predictions + Elo ratings + groups

Produces M1 (Azar/Elo foil) and M2 (Red Neuronal) per match; M3 (Conjunto) and
Mercado are null stubs until those models exist. Knockout matches are not yet in
results.csv (teams unknown) so this MVP emits the 72 group matches only.

Run:  .venv/bin/python web/scripts/build_matches.py
Contract: web/static/data/README.md
"""
import json, math, os, sys, datetime, csv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import knockout as ko

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
KO_FIXTURES = os.path.join(ROOT, 'web', 'data', 'knockout_fixtures.csv')
FROZEN_PREDS = os.path.join(ROOT, 'web', 'data', 'frozen_predictions.json')    # A0 snapshot (immutable benchmark)
KICKOFF_PREDS = os.path.join(ROOT, 'web', 'data', 'kickoff_predictions.json')   # accumulating per-match kickoff freeze

# Knockout stage code → Spanish display label (matches the group-stage 'grupos' style).
STAGE_ES = {'r32': 'dieciseisavos', 'r16': 'octavos', 'qf': 'cuartos',
            'sf': 'semifinal', 'third': 'tercer puesto', 'final': 'final'}
# M2 source: prefer the v2 ensemble model; fall back to the locked baseline if absent.
_V2_PRED = os.path.join(ROOT, 'v2', 'output', 'predictions.json')
PRED = _V2_PRED if os.path.exists(_V2_PRED) else os.path.join(ROOT, 'output', 'predictions.json')
CSV  = os.path.join(ROOT, 'results.csv')
OUT  = os.path.join(ROOT, 'web', 'static', 'data', 'matches.json')
RESULTS = os.path.join(ROOT, 'web', 'data', 'results_live.csv')  # live scores you edit (NOT the locked results.csv)
MARKET  = os.path.join(ROOT, 'web', 'data', 'market_odds.csv')   # decimal 1X2 odds you enter per match (Mercado line)

# NOTE: team display (Spanish full/short names + flags) is GUI-only and lives in
# web/src/lib/teams.js. This data file carries only canonical (CSV) team names.

GLOBAL_AVG_GOALS = 1.35  # mirrors neural_poisson.EloBaselineModel


def pois_mode(lam):
    """Poisson mode = floor(λ) — the modal goal count (NOT rounded λ)."""
    return int(math.floor(lam))


def poisson_pmf(k, lam):
    return math.exp(-lam) * lam ** k / math.factorial(k)


def wdl_from_lambdas(lh, la, maxg=12):
    """P(home win), P(draw), P(away win) from independent Poisson(λ)."""
    ph = pd = pa = 0.0
    home_pmf = [poisson_pmf(i, lh) for i in range(maxg + 1)]
    away_pmf = [poisson_pmf(j, la) for j in range(maxg + 1)]
    for i in range(maxg + 1):
        for j in range(maxg + 1):
            p = home_pmf[i] * away_pmf[j]
            if i > j: ph += p
            elif i == j: pd += p
            else: pa += p
    return ph, pd, pa


def elo_lambdas(elo_a, elo_b):
    """Replicates neural_poisson.EloBaselineModel.predict_match (M1)."""
    diff = elo_a - elo_b
    exp_a = 1.0 / (1.0 + 10 ** (-diff / 400.0))
    la = GLOBAL_AVG_GOALS * (0.5 + exp_a)
    lb = GLOBAL_AVG_GOALS * (0.5 + (1 - exp_a))
    la = min(max(la, 0.3), 4.0)
    lb = min(max(lb, 0.3), 4.0)
    return la, lb


def pick_from_probs(ph, pdr, pa):
    return ('home', 'draw', 'away')[max(range(3), key=lambda i: (ph, pdr, pa)[i])]


def scoreline_model(lh, la, ph, pdr, pa):
    return {
        'home': pois_mode(lh), 'away': pois_mode(la),
        'pick': pick_from_probs(ph, pdr, pa),
        'probs': {'home': round(ph, 3), 'draw': round(pdr, 3), 'away': round(pa, 3)},
        'lambda': {'home': round(lh, 2), 'away': round(la, 2)},
    }


def conformal_set(probs, tau):
    """M3 conformal outcome set: the outcomes whose prob ≥ τ (the rest are ruled out
    at the calibrated coverage). Never empty — falls back to the single most-likely."""
    order = ['home', 'draw', 'away']
    s = [o for o in order if probs[o] >= tau]
    if not s:
        s = [max(order, key=lambda o: probs[o])]
    return s


def build_standings(pred):
    """Team-level data for the Grupos (standings) and Llaves (stage odds) views."""
    tp = pred['team_probabilities']
    elo = pred['elo_ratings']
    vals = pred.get('squad_values', {})
    groups = pred['groups']
    gp = pred.get('group_predictions', {})

    out_groups = []
    for g in sorted(groups):
        teams = []
        for t in groups[g]:
            p = tp.get(t, {})
            teams.append({
                'team': t,
                'elo': round(elo.get(t, 1500)),
                'value': vals.get(t),  # None if missing — Dirty George: no phantom €0M
                'advance': round(p.get('group_advance', 0), 4),
                'champion': round(p.get('champion', 0), 4),
                'winner': round(gp.get(g, {}).get('winner_probs', {}).get(t, 0), 4),
                'runner': round(gp.get(g, {}).get('runner_probs', {}).get(t, 0), 4),
            })
        teams.sort(key=lambda x: x['advance'], reverse=True)
        out_groups.append({'group': g, 'teams': teams})

    team_group = {t: g for g, ts in groups.items() for t in ts}
    knockout = []
    for t, p in tp.items():
        knockout.append({
            'team': t, 'group': team_group.get(t),
            'r16': round(p.get('r16', 0), 4),
            'qf': round(p.get('quarterfinal', 0), 4),
            'sf': round(p.get('semifinal', 0), 4),
            'final': round(p.get('finalist', 0), 4),
            'champion': round(p.get('champion', 0), 4),
        })
    knockout.sort(key=lambda x: x['champion'], reverse=True)
    return out_groups, knockout


def _upsert_rows(path, matches, base_fields):
    """Ensure web/data/<file> has a row for every match (group + knockout), preserving
    existing edits and any extra columns (e.g. 'advances'). Appends blank rows for new
    fixtures so record.py can address knockout ids. Returns (rows, fieldnames)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    rows, fields = [], list(base_fields)
    if os.path.exists(path):
        with open(path, newline='', encoding='utf-8') as f:
            rd = csv.DictReader(f)
            fields = list(rd.fieldnames or base_fields)
            rows = list(rd)
    have = {r['id'] for r in rows}
    changed = not os.path.exists(path)
    for m in matches:
        if m['id'] not in have:
            row = {k: '' for k in fields}
            row.update({'id': m['id'], 'home': m['home'], 'away': m['away']})
            rows.append(row); have.add(m['id']); changed = True
    if changed:
        with open(path, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader(); w.writerows(rows)
    return rows, fields


def load_or_init_results(matches):
    """Live results (web/data/results_live.csv), upserting a row per fixture. Returns
    {match_id: (home_score, away_score, advances|None)} — 'advances' is knockout-only."""
    rows, _ = _upsert_rows(RESULTS, matches, ['id', 'home', 'away', 'home_score', 'away_score'])
    res = {}
    for row in rows:
        hs, a_s = (row.get('home_score') or '').strip(), (row.get('away_score') or '').strip()
        if hs != '' and a_s != '':
            res[row['id']] = (int(hs), int(a_s), (row.get('advances') or '').strip() or None)
    return res


def apply_results(matches, res):
    """Flip matched fixtures to finalizado with their 90-minute result (outcome derived).
    For knockout ties, also carry `advances` — the side that progressed (ET/penalties)."""
    for m in matches:
        sc = res.get(m['id'])
        if not sc:
            continue
        hs, a_s, advances = sc
        outcome = 'home' if hs > a_s else ('away' if a_s > hs else 'draw')
        m['status'] = 'finalizado'
        m['result'] = {'home': hs, 'away': a_s, 'outcome': outcome}
        if m['stage'] != 'grupos':
            m['result']['advances'] = advances


def load_or_init_market(matches):
    """Market odds (decimal 1X2): web/data/market_odds.csv, upserting a row per fixture.
    Returns {match_id: (odd_home, odd_draw, odd_away)}."""
    rows, _ = _upsert_rows(MARKET, matches, ['id', 'home', 'away', 'odd_1', 'odd_X', 'odd_2'])
    odds = {}
    for row in rows:
        try:
            o1, ox, o2 = float(row['odd_1']), float(row['odd_X']), float(row['odd_2'])
        except (ValueError, KeyError, TypeError):
            continue  # blank/invalid row → skip (no silent bad data)
        if o1 > 0 and ox > 0 and o2 > 0:
            odds[row['id']] = (o1, ox, o2)
    return odds


def apply_market(matches, odds):
    """Decimal odds → vig-free implied 1X2 probabilities → Mercado prediction (pick + probs; no scoreline)."""
    for m in matches:
        o = odds.get(m['id'])
        if not o:
            continue
        raw = [1.0 / o[0], 1.0 / o[1], 1.0 / o[2]]   # implied probs (with overround)
        s = sum(raw)                                  # overround
        probs = {'home': round(raw[0] / s, 3), 'draw': round(raw[1] / s, 3), 'away': round(raw[2] / s, 3)}
        pick = ('home', 'draw', 'away')[max(range(3), key=lambda i: raw[i])]
        m['predictions']['Mercado'] = {'pick': pick, 'probs': probs}


def _scoreline_for_pair(home, away, by_pair, tau=None):
    """Build a scoreline-model prediction (oriented home/away) from a by-pair entry, or
    None if the pair isn't in the prediction set. Adds the conformal set when tau given (M3)."""
    pm = by_pair.get(frozenset((home, away)))
    if pm is None:
        return None
    if pm['team_a'] == home:
        lh, la = pm['lambda_a'], pm['lambda_b']
        ph, pd, pa = pm['prob_win_a'], pm['prob_draw'], pm['prob_win_b']
    else:
        lh, la = pm['lambda_b'], pm['lambda_a']
        ph, pd, pa = pm['prob_win_b'], pm['prob_draw'], pm['prob_win_a']
    sm = scoreline_model(lh, la, ph, pd, pa)
    if tau is not None:
        sm['set'] = conformal_set(sm['probs'], tau)
        sm['coverage'] = 0.80
    return sm


def build_ko_matches(elo, mp_by_pair, m3_by_pair, tau_show):
    """Emit knockout match entries from the discovered bracket (knockout_fixtures.csv).
    M1 (Elo foil) is always computed; M2/M3 come from predictions.json keyed by team pair
    when present (added by v2/main.py on its next run), else null — the same graceful stub
    the group stage uses. Predictions are the 90-minute 1X2 (knockout draws are decided by
    ET/penalties, tracked separately in result.advances)."""
    if not os.path.exists(KO_FIXTURES):
        return []
    out = []
    with open(KO_FIXTURES, newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            home, away = r['home'], r['away']
            eh, ea = elo.get(home, 1500.0), elo.get(away, 1500.0)
            lh1, la1 = elo_lambdas(eh, ea)
            ph1, pd1, pa1 = wdl_from_lambdas(lh1, la1)
            m1 = scoreline_model(lh1, la1, ph1, pd1, pa1)
            out.append({
                'id': r['id'],
                'date': r['date'] or None,
                'time': r['time'] or None,
                'stage': STAGE_ES.get(r['stage'], r['stage']),
                'group': None,
                'home': home, 'away': away,
                'venue': {'city': None, 'country': None, 'neutral': True},
                'status': 'por_jugarse',
                'result': None,
                'predictions': {
                    'M1': m1,
                    'M2': _scoreline_for_pair(home, away, mp_by_pair),
                    'M3': _scoreline_for_pair(home, away, m3_by_pair, tau=tau_show),
                    'Mercado': None,
                },
            })
    return out


def main():
    import csv
    pred = json.load(open(PRED))
    mp = pred['match_predictions']
    elo = pred['elo_ratings']
    groups = pred['groups']
    team_group = {t: g for g, teams in groups.items() for t in teams}

    # Index M2 predictions by unordered team pair.
    mp_by_pair = {frozenset((v['team_a'], v['team_b'])): v for v in mp.values()}
    # M3 (Conjunto) predictions + the validated conformal threshold (90% coverage).
    m3p = pred.get('m3_match_predictions', {})
    m3_by_pair = {frozenset((v['team_a'], v['team_b'])): v for v in m3p.values()}
    # Default display coverage = 80%: informative sets (most matches a single pick or a
    # 2-way; genuine toss-ups show all three). Higher coverage (wider sets) is Act 3's slider.
    tau_show = pred.get('conformal_tau', {}).get('0.80', 0.236)

    # Read the 72 WC2026 fixtures from results.csv (content-based, not by row position).
    fixtures = []
    with open(CSV, newline='') as f:
        for row in csv.DictReader(f):
            if row['tournament'] != 'FIFA World Cup':
                continue
            if not row['date'].startswith('2026'):
                continue
            fixtures.append(row)
    fixtures.sort(key=lambda r: r['date'])

    matches, missing = [], []
    per_group_n = {}
    for r in fixtures:
        home, away = r['home_team'], r['away_team']
        gh, ga = team_group.get(home), team_group.get(away)
        # Knockout rows now live in results.csv too (fed in by sync_results_to_corpus.py so
        # Elo/form update). A cross-group WC row is a knockout — skip it here silently; the
        # KO matches are emitted separately from knockout_fixtures.csv. Only a genuinely
        # unknown team (in no group) is a real data error worth flagging.
        if gh is None or ga is None:
            missing.append((home, away, 'unknown team (not in any group)'))
            continue
        if gh != ga:
            continue  # knockout fixture — handled by build_ko_matches
        group = gh
        per_group_n[group] = per_group_n.get(group, 0) + 1
        mid = f"g{group}-{per_group_n[group]:02d}"

        # M1 — Elo foil (computed from ratings)
        eh, ea = elo.get(home, 1500.0), elo.get(away, 1500.0)
        lh1, la1 = elo_lambdas(eh, ea)
        ph1, pd1, pa1 = wdl_from_lambdas(lh1, la1)
        m1 = scoreline_model(lh1, la1, ph1, pd1, pa1)

        # M2 — neural (oriented to home/away)
        pm = mp_by_pair.get(frozenset((home, away)))
        if pm is None:
            missing.append((home, away, 'no M2 prediction'))
            m2 = None
        else:
            if pm['team_a'] == home:
                lh2, la2 = pm['lambda_a'], pm['lambda_b']
                ph2, pd2, pa2 = pm['prob_win_a'], pm['prob_draw'], pm['prob_win_b']
            else:  # team_a == away → swap
                lh2, la2 = pm['lambda_b'], pm['lambda_a']
                ph2, pd2, pa2 = pm['prob_win_b'], pm['prob_draw'], pm['prob_win_a']
            m2 = scoreline_model(lh2, la2, ph2, pd2, pa2)

        # M3 — Conjunto (net+GBT blend) + conformal outcome set
        pm3 = m3_by_pair.get(frozenset((home, away)))
        if pm3 is None:
            m3 = None
        else:
            if pm3['team_a'] == home:
                lh3, la3 = pm3['lambda_a'], pm3['lambda_b']
                ph3, pd3, pa3 = pm3['prob_win_a'], pm3['prob_draw'], pm3['prob_win_b']
            else:  # team_a == away → swap
                lh3, la3 = pm3['lambda_b'], pm3['lambda_a']
                ph3, pd3, pa3 = pm3['prob_win_b'], pm3['prob_draw'], pm3['prob_win_a']
            m3 = scoreline_model(lh3, la3, ph3, pd3, pa3)
            m3['set'] = conformal_set(m3['probs'], tau_show)   # 80%-coverage plausible outcomes
            m3['coverage'] = 0.80

        matches.append({
            'id': mid,
            'date': r['date'],
            'time': None,                       # kickoff time not in CSV (add later)
            'stage': 'grupos',
            'group': group,
            'home': home, 'away': away,
            'venue': {'city': r['city'] or None, 'country': r['country'] or None,
                      'neutral': str(r['neutral']).upper() == 'TRUE'},
            'status': 'por_jugarse',
            'result': None,
            'predictions': {'M1': m1, 'M2': m2, 'M3': m3, 'Mercado': None},
        })

    # Knockout matches (R32→Final) from the discovered bracket — appended so results,
    # odds, and predictions apply uniformly with the group stage.
    n_group = len(matches)
    matches += build_ko_matches(elo, mp_by_pair, m3_by_pair, tau_show)
    n_ko = len(matches) - n_group

    results = load_or_init_results(matches)
    apply_results(matches, results)
    market = load_or_init_market(matches)
    apply_market(matches, market)

    # ── Freeze-at-kickoff (evaluation integrity) ───────────────────────────────
    # A model's prediction for a match is FROZEN at kickoff and never recomputed: once
    # a match is played, grading its (updated) prediction on the very results that
    # updated the model would be in-sample/lookahead-leaky. So: refresh the kickoff
    # snapshot ONLY for not-yet-played matches, then override every played match's
    # M1/M2/M3 with its frozen kickoff value. The updated model thus earns a clean
    # out-of-sample record going forward. (Mercado is inherently a pre-match line — not
    # frozen here.) kickoff_predictions.json accumulates; seeded from the A0 snapshot.
    ko = {'matches': {}}
    if os.path.exists(KICKOFF_PREDS):
        ko = json.load(open(KICKOFF_PREDS, encoding='utf-8'))
    kmap = ko.setdefault('matches', {})
    for m in matches:
        if m['status'] != 'finalizado':   # still pending → its kickoff estimate is the latest live one
            kmap[m['id']] = {k: m['predictions'][k] for k in ('M1', 'M2', 'M3')}
    with open(KICKOFF_PREDS, 'w', encoding='utf-8') as f:
        json.dump(ko, f, ensure_ascii=False, indent=2)
    for m in matches:                      # override with the frozen kickoff prediction where we have one
        k = kmap.get(m['id'])
        if k:
            for line in ('M1', 'M2', 'M3'):
                if k.get(line) is not None:
                    m['predictions'][line] = k[line]

    # Frozen PRE-TOURNAMENT M3 (immutable A0 snapshot) as the scoreboard benchmark line
    # 'M3_frozen' — measures whether tournament-updating the model helps, out-of-sample.
    if os.path.exists(FROZEN_PREDS):
        frozen = json.load(open(FROZEN_PREDS, encoding='utf-8')).get('matches', {})
        for m in matches:
            m['predictions']['M3_frozen'] = (frozen.get(m['id']) or {}).get('M3')

    groups_data, knockout_data = build_standings(pred)

    out = {
        'meta': {
            'generated': datetime.date.today().isoformat(),
            'source': f'results.csv (fixtures) + {os.path.relpath(PRED, ROOT)} (M1 Elo, M2 neural-ensemble, M3 conjunto+conformal)',
            'models': ['M1', 'M2', 'M3', 'Mercado'],
            'stub': ['Mercado'],
            'count': len(matches),
            'count_group': n_group,
            'count_knockout': n_ko,
            'note': f'{n_group} group + {n_ko} knockout matches (knockouts read from the '
                    'authoritative feeds as the bracket resolves). Knockout predictions are '
                    'the 90-min 1X2; result.advances carries who progressed (ET/penalties). '
                    'Team display (Spanish/flags) is GUI-only in web/src/lib/teams.js.',
        },
        'matches': matches,
        'groups': groups_data,
        'knockout': knockout_data,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"wrote {OUT}")
    n_fin = sum(1 for m in matches if m['status'] == 'finalizado')
    print(f"matches: {len(matches)} | finalizado: {n_fin} | missing/flagged: {missing if missing else 'none'}")


if __name__ == '__main__':
    main()
