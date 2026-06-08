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
import json, math, os, datetime, csv

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
PRED = os.path.join(ROOT, 'output', 'predictions.json')
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


def load_or_init_results(matches):
    """Live results: read web/data/results_live.csv; create a blank template if missing
    (preserves your edits on re-runs). Returns {match_id: (home_score, away_score)}."""
    os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
    if not os.path.exists(RESULTS):
        with open(RESULTS, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(['id', 'home', 'away', 'home_score', 'away_score'])
            for m in matches:
                w.writerow([m['id'], m['home'], m['away'], '', ''])
        return {}
    res = {}
    with open(RESULTS, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            hs, a_s = (row.get('home_score') or '').strip(), (row.get('away_score') or '').strip()
            if hs != '' and a_s != '':
                res[row['id']] = (int(hs), int(a_s))
    return res


def apply_results(matches, res):
    """Flip matched fixtures to finalizado with their result (outcome derived)."""
    for m in matches:
        sc = res.get(m['id'])
        if not sc:
            continue
        hs, a_s = sc
        outcome = 'home' if hs > a_s else ('away' if a_s > hs else 'draw')
        m['status'] = 'finalizado'
        m['result'] = {'home': hs, 'away': a_s, 'outcome': outcome}


def load_or_init_market(matches):
    """Market odds (decimal 1X2): web/data/market_odds.csv. Blank template if missing;
    preserves edits on re-run. Returns {match_id: (odd_home, odd_draw, odd_away)}."""
    os.makedirs(os.path.dirname(MARKET), exist_ok=True)
    if not os.path.exists(MARKET):
        with open(MARKET, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(['id', 'home', 'away', 'odd_1', 'odd_X', 'odd_2'])
            for m in matches:
                w.writerow([m['id'], m['home'], m['away'], '', '', ''])
        return {}
    odds = {}
    with open(MARKET, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
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


def main():
    import csv
    pred = json.load(open(PRED))
    mp = pred['match_predictions']
    elo = pred['elo_ratings']
    groups = pred['groups']
    team_group = {t: g for g, teams in groups.items() for t in teams}

    # Index M2 predictions by unordered team pair.
    mp_by_pair = {frozenset((v['team_a'], v['team_b'])): v for v in mp.values()}

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
        group = team_group.get(home)
        if group is None or team_group.get(away) != group:
            missing.append((home, away, 'group mismatch'))
            continue
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
            'predictions': {'M1': m1, 'M2': m2, 'M3': None, 'Mercado': None},
        })

    results = load_or_init_results(matches)
    apply_results(matches, results)
    market = load_or_init_market(matches)
    apply_market(matches, market)

    groups_data, knockout_data = build_standings(pred)

    out = {
        'meta': {
            'generated': datetime.date.today().isoformat(),
            'source': 'results.csv (fixtures) + output/predictions.json (v1: M2 neural, M1 from Elo)',
            'models': ['M1', 'M2', 'M3', 'Mercado'],
            'stub': ['M3', 'Mercado'],
            'count': len(matches),
            'note': 'Group stage only (72); knockouts added as the bracket resolves. '
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
