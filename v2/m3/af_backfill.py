#!/usr/bin/env python3
"""
af_backfill.py — pull the fixture lists for every in-scope tournament (Batch B1.2),
and (B1.3) the per-fixture detail: events, lineups, players.

All fetches go through af_client.get(), so they are cached to disk and cost zero
API calls on re-run. B1.3 is resumable — already-cached detail is skipped.

Scope (league id / season):
  World Cup    (1):  2018, 2022
  Euro         (4):  2020, 2024
  Copa América (9):  2021, 2024

  python v2/m3/af_backfill.py fixtures   # B1.2 — fixture lists + count check
  python v2/m3/af_backfill.py detail     # B1.3 — events/lineups/players per fixture
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from af_client import get, live_calls, last_quota  # noqa: E402

# (label, league_id, season)
TOURNAMENTS = [
    ('World Cup 2018', 1, 2018),
    ('World Cup 2022', 1, 2022),
    ('Euro 2020',      4, 2020),
    ('Euro 2024',      4, 2024),
    ('Copa America 2021', 9, 2021),
    ('Copa America 2024', 9, 2024),
]

# Known total match counts for a sanity check (warn on mismatch, never crash).
EXPECTED_TOTAL = {
    (1, 2018): 64, (1, 2022): 64,
    (4, 2020): 51, (4, 2024): 51,
    (9, 2021): 28, (9, 2024): 32,
}

FINISHED = {'FT', 'AET', 'PEN'}  # match-finished status codes

# Some seasons (e.g. Euro league=4 season=2020) bundle the QUALIFIERS into the
# same league-season as the final tournament. We only want the final tournament.
# Filter BY CONTENT (round name), not by count/position: any round whose name
# contains "qualifying" is a qualifier. No-op for already-clean tournaments.
def is_finals(f):
    return 'qualifying' not in (f.get('league', {}).get('round', '') or '').lower()


def fixtures_for(lid, season):
    """Cached list of FINAL-TOURNAMENT fixture dicts for one tournament-season
    (qualifiers filtered out)."""
    d = get(f'/fixtures?league={lid}&season={season}')
    if d.get('errors') or d.get('_http_error'):
        print(f"  [!] API problem for league={lid} season={season}: "
              f"{d.get('errors') or d.get('_http_error')}")
        return []
    return [f for f in d.get('response', []) if is_finals(f)]


def finished_fixtures(lid, season):
    """Only the played final-tournament matches (what B1.3 details and the model uses)."""
    out = []
    for f in fixtures_for(lid, season):
        if (f.get('fixture', {}).get('status', {}).get('short')) in FINISHED:
            out.append(f)
    return out


def backfill_fixtures():
    """B1.2 — fetch + cache all fixture lists; print a count-checked summary."""
    print('B1.2 — fixtures backfill\n')
    print(f"  {'tournament':<20} {'total':>6} {'finished':>9} {'expected':>9}  check")
    grand_total = grand_fin = 0
    for label, lid, season in TOURNAMENTS:
        fx = fixtures_for(lid, season)
        total = len(fx)
        fin = sum(1 for f in fx
                  if f.get('fixture', {}).get('status', {}).get('short') in FINISHED)
        exp = EXPECTED_TOTAL.get((lid, season))
        ok = '✓' if exp is not None and total == exp else ('?' if exp is None else '⚠ MISMATCH')
        print(f"  {label:<20} {total:>6} {fin:>9} {str(exp):>9}  {ok}")
        grand_total += total
        grand_fin += fin
    print(f"\n  TOTAL fixtures: {grand_total} | finished: {grand_fin}")
    print(f"  live API calls this run: {live_calls()} | quota: {last_quota()}")
    return grand_total, grand_fin


def backfill_detail(pause=0.0):
    """B1.3 — for every finished fixture, cache events + lineups + players.
    Resumable: af_client serves cached calls without an API hit."""
    print('B1.3 — per-fixture detail backfill (events/lineups/players)\n')
    manifest = {}
    n_fix = 0
    for label, lid, season in TOURNAMENTS:
        fins = finished_fixtures(lid, season)
        print(f"  {label}: {len(fins)} finished fixtures")
        for f in fins:
            fid = f['fixture']['id']
            n_fix += 1
            got = {}
            for kind in ('events', 'lineups', 'players'):
                d = get(f'/fixtures/{kind}?fixture={fid}', pause=pause)
                got[kind] = (not d.get('errors') and not d.get('_http_error')
                             and d.get('response') is not None)
            manifest[fid] = got
            if live_calls() and live_calls() % 100 == 0:
                print(f"    ... {live_calls()} live calls so far | quota {last_quota()}")
    print(f"\n  detailed {n_fix} fixtures | live API calls this run: {live_calls()} "
          f"| quota: {last_quota()}")
    return manifest


def audit_ingestion():
    """B1.4 — confirm every finished fixture has valid events/lineups/players in
    cache. No silent gaps: every missing/empty/error detail is flagged. Writes
    corpus/_ingestion_audit.json."""
    import json
    print('B1.4 — ingestion audit\n')
    corpus = os.path.join(os.path.dirname(__file__), 'corpus')
    os.makedirs(corpus, exist_ok=True)

    report = {'tournaments': {}, 'flags': [], 'totals': {}}
    n_fix = n_events = n_lineup_rows = n_player_rows = 0
    for label, lid, season in TOURNAMENTS:
        fins = finished_fixtures(lid, season)
        report['tournaments'][label] = len(fins)
        for f in fins:
            fid = f['fixture']['id']
            n_fix += 1
            ev = get(f'/fixtures/events?fixture={fid}')      # cached
            lu = get(f'/fixtures/lineups?fixture={fid}')
            ps = get(f'/fixtures/players?fixture={fid}')
            # events: empty is unusual but possible (flag as info)
            ne = len(ev.get('response') or [])
            n_events += ne
            if ne == 0:
                report['flags'].append({'fixture': fid, 'label': label,
                                        'issue': 'no events', 'severity': 'info'})
            # lineups: must have 2 teams
            nl = len(lu.get('response') or [])
            n_lineup_rows += nl
            if nl < 2:
                report['flags'].append({'fixture': fid, 'label': label,
                                        'issue': f'lineups has {nl} teams (expected 2)',
                                        'severity': 'error'})
            # players: must have 2 teams w/ player lists
            pr = sum(len(s.get('players') or []) for s in (ps.get('response') or []))
            n_player_rows += pr
            if pr == 0:
                report['flags'].append({'fixture': fid, 'label': label,
                                        'issue': 'no player stats', 'severity': 'error'})
            for tag, d in (('events', ev), ('lineups', lu), ('players', ps)):
                if d.get('errors') or d.get('_http_error'):
                    report['flags'].append({'fixture': fid, 'label': label,
                                            'issue': f'{tag} API error: {d.get("errors") or d.get("_http_error")}',
                                            'severity': 'error'})
    report['totals'] = {'finished_fixtures': n_fix, 'event_rows': n_events,
                        'lineup_team_rows': n_lineup_rows, 'player_stat_rows': n_player_rows}
    errors = [x for x in report['flags'] if x['severity'] == 'error']
    infos = [x for x in report['flags'] if x['severity'] == 'info']

    out = os.path.join(corpus, '_ingestion_audit.json')
    with open(out, 'w') as fh:
        json.dump(report, fh, indent=1)

    print(f"  fixtures audited: {n_fix}")
    print(f"  event rows: {n_events} | lineup team-rows: {n_lineup_rows} | player stat-rows: {n_player_rows}")
    print(f"  ERRORS: {len(errors)} | info flags: {len(infos)}")
    for x in errors[:20]:
        print(f"    [ERROR] {x['label']} fixture {x['fixture']}: {x['issue']}")
    for x in infos[:10]:
        print(f"    [info]  {x['label']} fixture {x['fixture']}: {x['issue']}")
    print(f"\n  wrote {out}")
    print(f"  RESULT: {'CLEAN ✓' if not errors else 'ERRORS PRESENT ⚠'}")
    return report


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'fixtures'
    if cmd == 'fixtures':
        backfill_fixtures()
    elif cmd == 'detail':
        backfill_detail(pause=0.0)
    elif cmd == 'audit':
        audit_ingestion()
    else:
        print(__doc__)
