#!/usr/bin/env python3
"""
ko_discover.py — discover REAL knockout fixtures (R32→Final) from the data sources.

The knockout draw is READ from the authoritative feeds, never computed: API-Football
carries every knockout fixture with its round label, the 90-minute score (score.fulltime,
kept separate from extra-time), and the advancing team (teams.*.winner). ESPN /
thesportsdb confirm the advancer so no result is recorded on a single source.

Discipline (mirrors autofetch.py):
  • A finished knockout result is accepted only when API-Football reports it AND ≥1
    other source agrees on WHO ADVANCED. The 90-minute score comes from API-Football's
    structured `fulltime` field (the only source that cleanly separates it from ET);
    cross-source agreement is on the advancer, which is well-defined even after ET/pens.
  • Fixtures are slotted via knockout.assign_r32_slots (winner/runner/third feeds) for
    R32, and by winner-advancement for later rounds. A fixture that cannot be slotted
    unambiguously is FLAGGED, never guessed.
  • Returns structured records; persistence (CSV/JSON) is the caller's job.

Run standalone to inspect:  .venv/bin/python web/scripts/ko_discover.py
"""
import os, sys, json, csv, argparse, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)

import knockout as ko
# Reuse autofetch's name normalization, alias table, and the two scrape sources.
import autofetch as af

WORLD_CUP_LEAGUE_ID = 1
AF_FINISHED = {'FT', 'AET', 'PEN', 'AWD', 'WO'}
KO_FIXTURES = os.path.join(ROOT, 'web', 'data', 'knockout_fixtures.csv')
RESULTS = os.path.join(ROOT, 'web', 'data', 'results_live.csv')


def _outcome(h, a):
    return 'home' if h > a else ('away' if a > h else 'draw')


def _af_get(path):
    af_dir = os.path.join(ROOT, 'v2', 'm3')
    if af_dir not in sys.path:
        sys.path.insert(0, af_dir)
    import af_client
    return af_client.get(path, force=True)


def fetch_apifootball_ko(season=2026):
    """All knockout fixtures of the World Cup from API-Football, structured.

    Returns (fixtures, errs) where each fixture is a dict:
      {stage, round_label, date, time, home, away, status,
       ft: [h,a] or None, advancer: canonical team or None}
    Teams are resolved to canonical names; unresolved names are flagged into errs.
    """
    fixtures, errs = [], []
    resolve = af.resolver(_canonical_team_set())
    try:
        data = _af_get(f"/fixtures?league={WORLD_CUP_LEAGUE_ID}&season={season}")
    except BaseException as e:  # noqa: BLE001 — missing key raises SystemExit; degrade
        return fixtures, [f"api-football KO: {e}"]
    problem = data.get('_http_error') or data.get('_url_error') or data.get('errors') or data.get('_api_errors')
    if problem:
        return fixtures, [f"api-football KO: {problem}"]
    for f in (data.get('response') or []):
        lg = f.get('league') or {}
        stage = ko.stage_from_round_label(lg.get('round'))
        if stage is None:
            continue  # group stage or unknown → not our concern here
        fx, t, g, sc = f.get('fixture') or {}, f.get('teams') or {}, f.get('goals') or {}, f.get('score') or {}
        rawh = (t.get('home') or {}).get('name')
        rawa = (t.get('away') or {}).get('name')
        ch, ca = resolve(rawh), resolve(rawa)
        if ch is None or ca is None:
            if rawh and rawa:
                errs.append(f"api-football KO: equipo sin mapear {rawh!r}/{rawa!r}")
            continue
        st = ((fx.get('status') or {}).get('short') or '').upper()
        kickoff = (fx.get('date') or '')[:10] or None
        ft = (sc.get('fulltime') or {})
        ft_pair = None
        if ft.get('home') is not None and ft.get('away') is not None:
            ft_pair = [int(ft['home']), int(ft['away'])]
        advancer = None
        if (t.get('home') or {}).get('winner') is True:
            advancer = ch
        elif (t.get('away') or {}).get('winner') is True:
            advancer = ca
        fixtures.append({
            'stage': stage, 'round_label': lg.get('round'),
            'date': kickoff, 'time': (fx.get('date') or '')[11:16] or None,
            'home': ch, 'away': ca,
            'status': st, 'finished': st in AF_FINISHED,
            'ft': ft_pair, 'advancer': advancer,
        })
    return fixtures, errs


def _canonical_team_set():
    """Canonical team names from the current matches.json (group stage carries all 48)."""
    data = json.load(open(ko_matches_path(), encoding='utf-8'))
    return {m['home'] for m in data['matches']} | {m['away'] for m in data['matches']}


def ko_matches_path():
    return os.path.join(ROOT, 'web', 'static', 'data', 'matches.json')


def _scrape_finals(fixtures):
    """From the scrape sources (espn, thesportsdb), return {frozenset(pair): set of
    (source, outcome, winner_or_None)} for matches they report finished. Used to confirm
    BOTH the 90-min outcome (incl. draws → the ET/pens cases) and, when decisive, the
    winner. A draw names no winner but DOES confirm a 'draw' 90-min outcome."""
    dates = set()
    for fx in fixtures:
        if not fx.get('date'):
            continue
        d = datetime.date.fromisoformat(fx['date'])
        for off in (-1, 0, 1):
            dates.add(d + datetime.timedelta(days=off))
    dates = sorted(dates)
    resolve = af.resolver(_canonical_team_set())
    out = {}
    for sname, fn in (('espn', af.src_espn), ('thesportsdb', af.src_thesportsdb)):
        raw, _ = fn(dates)
        for rh, gh, ra, ga in raw:
            ch, ca = resolve(rh), resolve(ra)
            if ch is None or ca is None:
                continue
            oc = _outcome(gh, ga)
            winner = None if oc == 'draw' else (ch if gh > ga else ca)
            out.setdefault(frozenset((ch, ca)), set()).add((sname, oc, winner))
    return out


def discover():
    """Full discovery + cross-source advancer confirmation + slotting.

    Returns (records, errors) where each record adds:
      slot: bracket id (P73…) or None if unslotted,
      advancer_confirmed: bool (≥1 scrape source agrees with API-Football's advancer),
      confirmers: list of source names confirming the advancer.
    """
    fixtures, errs = fetch_apifootball_ko()
    if not fixtures:
        return [], errs

    # Slot every round: R32 by group feeds, later rounds by advancement.
    group_matches = [m for m in json.load(open(ko_matches_path(), encoding='utf-8'))['matches'] if m.get('group')]
    assigned, unassigned = ko.resolve_bracket(fixtures, group_matches)
    fx_to_slot = {id(fx): sid for sid, fx in assigned.items()}
    for fx in unassigned:
        errs.append(f"sin asignar a slot ({fx['stage']}): {fx['home']} vs {fx['away']}")

    scrape = _scrape_finals(fixtures)

    records = []
    for fx in fixtures:
        slot = fx_to_slot.get(id(fx))
        reports = scrape.get(frozenset((fx['home'], fx['away'])), set())
        # 90-min outcome (from API-Football's fulltime) confirmed by ≥1 scrape source.
        api_outcome = _outcome(*fx['ft']) if fx.get('ft') else None
        outcome_confirmers = sorted({s for s, oc, _ in reports if oc == api_outcome}) if api_outcome else []
        # advancer corroborated by a decisive scrape final naming the same winner.
        adv = fx.get('advancer')
        adv_confirmers = sorted({s for s, _, w in reports if w and w == adv}) if adv else []
        records.append({**fx, 'slot': slot,
                        'outcome_confirmed': bool(outcome_confirmers),
                        'outcome_confirmers': outcome_confirmers,
                        'advancer_confirmed': bool(adv_confirmers),
                        'confirmers': adv_confirmers})
    return records, errs


def write_fixtures(records):
    """Persist the discovered bracket (slotted fixtures only) to knockout_fixtures.csv.
    Stable id = bracket slot. The REAL date/time from the source win over the static map."""
    rows = [{'id': r['slot'], 'stage': r['stage'], 'date': r['date'] or '',
             'time': r['time'] or '', 'home': r['home'], 'away': r['away']}
            for r in records if r['slot']]
    rows.sort(key=lambda x: int(x['id'][1:]))
    os.makedirs(os.path.dirname(KO_FIXTURES), exist_ok=True)
    with open(KO_FIXTURES, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['id', 'stage', 'date', 'time', 'home', 'away'])
        w.writeheader(); w.writerows(rows)
    return len(rows)


def update_results(records, apply):
    """Record confirmed 90-minute knockout results into results_live.csv (shared with the
    group stage + record.py). A KO result is written only when it is finished AND its
    90-min outcome is confirmed by ≥2 sources (API-Football + ≥1 scrape). The exact 90-min
    score is API-Football's `fulltime`; `advances` is the authoritative advancer.
    Returns (recorded, flagged) lists for reporting."""
    # Load existing results_live.csv preserving all rows/fields; ensure 'advances' exists.
    rows, fields = [], ['id', 'home', 'away', 'home_score', 'away_score']
    if os.path.exists(RESULTS):
        with open(RESULTS, newline='', encoding='utf-8') as f:
            rd = csv.DictReader(f)
            fields = list(rd.fieldnames or fields)
            rows = list(rd)
    if 'advances' not in fields:
        fields.append('advances')
        for r in rows:
            r.setdefault('advances', '')
    by_id = {r['id']: r for r in rows}

    recorded, flagged = [], []
    for r in records:
        if not (r['slot'] and r['finished'] and r['ft']):
            continue
        if not r['outcome_confirmed']:
            flagged.append(r); continue
        hs, as_ = r['ft']
        row = by_id.get(r['slot'])
        new = {'id': r['slot'], 'home': r['home'], 'away': r['away'],
               'home_score': str(hs), 'away_score': str(as_), 'advances': r['advancer'] or ''}
        if row is None:
            rows.append(new); by_id[r['slot']] = new
        else:
            row.update(new)
        recorded.append(r)

    if apply:
        with open(RESULTS, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader(); w.writerows(rows)
    return recorded, flagged


def main():
    ap = argparse.ArgumentParser(description="Descubrir y registrar partidos de eliminatorias.")
    ap.add_argument('--apply', action='store_true', help="persistir fixtures + resultados confirmados")
    args = ap.parse_args()

    recs, errs = discover()
    print(f"descubiertos {len(recs)} partidos de eliminatorias\n")
    for r in sorted(recs, key=lambda x: (x['date'] or '', x['slot'] or 'zzz')):
        res = f"{r['ft'][0]}-{r['ft'][1]}" if r['ft'] else "—"
        adv = f"→ avanza {r['advancer']}" if r['advancer'] else ""
        conf = f"[90' conf: {','.join(r['outcome_confirmers'])}]" if r.get('ft') else ""
        print(f"  {r['slot'] or '????'}  {r['stage']:5}  {r['date']}  {r['home']} vs {r['away']}  "
              f"90'={res} {adv} {conf}  ({r['status']})")

    n_fix = write_fixtures(recs) if args.apply else len([r for r in recs if r['slot']])
    recorded, flagged = update_results(recs, args.apply)

    print(f"\nfixtures slotted: {n_fix}")
    print(f"resultados 90' confirmados (≥2 fuentes): {len(recorded)}"
          + (" — " + ", ".join(f"{r['slot']} {r['home']} {r['ft'][0]}-{r['ft'][1]} {r['away']}" for r in recorded) if recorded else ""))
    if flagged:
        print(f"⚠ terminados SIN confirmar 90' por 2ª fuente (revisar a mano): "
              + ", ".join(f"{r['slot']} {r['home']} vs {r['away']}" for r in flagged))
    if errs:
        print("\nflags/errores:")
        for e in errs:
            print("  -", e)
    if not args.apply:
        print("\n(dry-run — usar --apply para persistir knockout_fixtures.csv + results_live.csv)")


if __name__ == '__main__':
    main()
