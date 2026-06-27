#!/usr/bin/env python3
"""
parse_corpus.py — turn the raw API-Football cache into clean tabular corpus files

(Re-gate after 2026: see RE-RUN recipe in M3_BUILD_PROGRESS.md.)
(Batch B2). Reads ONLY from cache (zero API calls). Writes to v2/m3/corpus/.

Tables (one row per the natural unit):
  matches.csv       B2.1  one row per fixture
  cards.csv         B2.2  one row per card event
  squads.csv        B2.3  one row per (fixture, team, player) with start/bench role
  player_match.csv  B2.4  one row per (fixture, team, player) with stats (null->0)

  python v2/m3/parse_corpus.py        # build all four tables + print DoD checks
"""
import os
import sys
import csv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from af_client import get  # noqa: E402  (cached reads only)
from af_backfill import TOURNAMENTS, finished_fixtures  # noqa: E402

CORPUS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'corpus')


def _z(v):
    """Coalesce API null -> 0 (API returns null for a zero stat)."""
    return 0 if v is None else v


def _iter_fixtures():
    """Yield (label, lid, season, fixture_dict) for every finished finals match."""
    for label, lid, season in TOURNAMENTS:
        for f in finished_fixtures(lid, season):
            yield label, lid, season, f


def _events(fid):
    return get(f'/fixtures/events?fixture={fid}').get('response') or []


def _lineups(fid):
    return get(f'/fixtures/lineups?fixture={fid}').get('response') or []


def _players(fid):
    return get(f'/fixtures/players?fixture={fid}').get('response') or []


def _write(name, header, rows):
    os.makedirs(CORPUS, exist_ok=True)
    path = os.path.join(CORPUS, name)
    with open(path, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=header)
        w.writeheader()
        w.writerows(rows)
    return path, len(rows)


# ---------------- B2.1 matches ----------------
def parse_matches():
    hdr = ['fixture_id', 'league_id', 'season', 'tournament', 'round', 'date',
           'home_id', 'home', 'away_id', 'away', 'goals_home', 'goals_away', 'status']
    rows = []
    for label, lid, season, f in _iter_fixtures():
        fx, tm, gl = f['fixture'], f['teams'], f['goals']
        rows.append({
            'fixture_id': fx['id'], 'league_id': lid, 'season': season,
            'tournament': label, 'round': f['league'].get('round'),
            'date': fx['date'],
            'home_id': tm['home']['id'], 'home': tm['home']['name'],
            'away_id': tm['away']['id'], 'away': tm['away']['name'],
            'goals_home': gl['home'], 'goals_away': gl['away'],
            'status': fx['status']['short'],
        })
    return _write('matches.csv', hdr, rows)


# ---------------- B2.2 cards ----------------
def parse_cards():
    hdr = ['fixture_id', 'date', 'minute', 'team_id', 'team',
           'player_id', 'player', 'color', 'comments']
    rows = []
    for label, lid, season, f in _iter_fixtures():
        fid = f['fixture']['id']
        date = f['fixture']['date']
        for e in _events(fid):
            if e.get('type') != 'Card':
                continue
            rows.append({
                'fixture_id': fid, 'date': date,
                'minute': (e.get('time') or {}).get('elapsed'),
                'team_id': (e.get('team') or {}).get('id'),
                'team': (e.get('team') or {}).get('name'),
                'player_id': (e.get('player') or {}).get('id'),
                'player': (e.get('player') or {}).get('name'),
                'color': e.get('detail'),          # 'Yellow Card' | 'Red Card'
                'comments': e.get('comments'),
            })
    return _write('cards.csv', hdr, rows)


# ---------------- B2.3 squads ----------------
def parse_squads():
    hdr = ['fixture_id', 'team_id', 'team', 'player_id', 'player', 'role', 'position']
    rows = []
    for label, lid, season, f in _iter_fixtures():
        fid = f['fixture']['id']
        for side in _lineups(fid):
            team = side.get('team', {})
            for role, key in (('start', 'startXI'), ('bench', 'substitutes')):
                for entry in (side.get(key) or []):
                    p = entry.get('player', {})
                    rows.append({
                        'fixture_id': fid,
                        'team_id': team.get('id'), 'team': team.get('name'),
                        'player_id': p.get('id'), 'player': p.get('name'),
                        'role': role, 'position': p.get('pos'),
                    })
    return _write('squads.csv', hdr, rows)


# ---------------- B2.4 player_match ----------------
def parse_player_match():
    hdr = ['fixture_id', 'team_id', 'team', 'player_id', 'player',
           'minutes', 'position', 'substitute', 'rating',
           'goals', 'assists', 'shots', 'shots_on', 'yellow', 'red']
    rows = []
    for label, lid, season, f in _iter_fixtures():
        fid = f['fixture']['id']
        for side in _players(fid):
            team = side.get('team', {})
            for pl in (side.get('players') or []):
                p = pl.get('player', {})
                st = (pl.get('statistics') or [{}])[0]
                games = st.get('games') or {}
                goals = st.get('goals') or {}
                shots = st.get('shots') or {}
                cards = st.get('cards') or {}
                rows.append({
                    'fixture_id': fid,
                    'team_id': team.get('id'), 'team': team.get('name'),
                    'player_id': p.get('id'), 'player': p.get('name'),
                    'minutes': _z(games.get('minutes')),
                    'position': games.get('position'),
                    'substitute': games.get('substitute'),
                    'rating': games.get('rating'),
                    'goals': _z(goals.get('total')),
                    'assists': _z(goals.get('assists')),
                    'shots': _z(shots.get('total')),
                    'shots_on': _z(shots.get('on')),
                    'yellow': _z(cards.get('yellow')),
                    'red': _z(cards.get('red')),
                })
    return _write('player_match.csv', hdr, rows)


# ---------------- B2.6 integrity pass ----------------
def integrity():
    """B2.6 — reconcile the four tables; flag every exception (none dropped silently).
    Writes corpus/_integrity_report.json."""
    import json
    import pandas as pd
    m = pd.read_csv(os.path.join(CORPUS, 'matches.csv'))
    c = pd.read_csv(os.path.join(CORPUS, 'cards.csv'))
    sq = pd.read_csv(os.path.join(CORPUS, 'squads.csv'))
    pm = pd.read_csv(os.path.join(CORPUS, 'player_match.csv'))

    fids = set(m['fixture_id'])
    flags = []

    def check(name, cond, detail):
        flags.append({'check': name, 'pass': bool(cond), 'detail': detail})

    # orphans: any detail row referencing an unknown fixture
    for nm, df in (('cards', c), ('squads', sq), ('player_match', pm)):
        orphan = sorted(set(df['fixture_id']) - fids)
        check(f'{nm}_no_orphan_fixtures', not orphan, f'orphans: {orphan[:10]}')

    # every match present in player_match and squads, exactly 2 teams each
    pm_teams = pm.groupby('fixture_id')['team_id'].nunique()
    sq_teams = sq.groupby('fixture_id')['team_id'].nunique()
    check('player_match_2_teams_per_fixture',
          (pm_teams == 2).all() and len(pm_teams) == len(fids),
          f'fixtures w/o 2 teams: {pm_teams[pm_teams != 2].index.tolist()[:10]}; '
          f'coverage {len(pm_teams)}/{len(fids)}')
    check('squads_2_teams_per_fixture',
          (sq_teams == 2).all() and len(sq_teams) == len(fids),
          f'fixtures w/o 2 teams: {sq_teams[sq_teams != 2].index.tolist()[:10]}; '
          f'coverage {len(sq_teams)}/{len(fids)}')

    # squads vs player_match per-(fixture,player) reconciliation (explain the gap)
    sq_key = set(zip(sq['fixture_id'], sq['player_id']))
    pm_key = set(zip(pm['fixture_id'], pm['player_id']))
    in_sq_not_pm = sq_key - pm_key
    in_pm_not_sq = pm_key - sq_key
    check('squad_vs_playermatch_gap_small',
          len(in_sq_not_pm) + len(in_pm_not_sq) < 50,
          f'in squad not player_match: {len(in_sq_not_pm)}; '
          f'in player_match not squad: {len(in_pm_not_sq)}')

    # value-domain checks
    check('cards_color_domain', set(c['color'].dropna()) <= {'Yellow Card', 'Red Card'},
          f"colors: {sorted(set(c['color'].dropna()))}")
    check('minutes_in_range', pm['minutes'].between(0, 120).all(),
          f"min={pm['minutes'].min()} max={pm['minutes'].max()}")
    check('no_null_numeric',
          int(pm[['minutes', 'goals', 'assists', 'shots', 'shots_on', 'yellow', 'red']].isna().sum().sum()) == 0,
          'numeric coalesce')
    check('scores_present', not m[['goals_home', 'goals_away']].isna().any().any(),
          'all finished matches have scores')

    report = {'flags': flags,
              'failed': [f for f in flags if not f['pass']],
              'totals': {'matches': len(m), 'cards': len(c),
                         'squads': len(sq), 'player_match': len(pm)}}
    with open(os.path.join(CORPUS, '_integrity_report.json'), 'w') as fh:
        json.dump(report, fh, indent=1)

    print('\n  B2.6 integrity:')
    for f in flags:
        print(f"    [{'PASS' if f['pass'] else 'FAIL'}] {f['check']}: {f['detail']}")
    print(f"  RESULT: {'ALL GREEN ✓' if not report['failed'] else 'FAILURES ⚠'}")
    return report


if __name__ == '__main__':
    print('B2 — parse raw cache -> clean corpus\n')
    for fn in (parse_matches, parse_cards, parse_squads, parse_player_match):
        path, n = fn()
        print(f"  wrote {os.path.basename(path):<18} {n:>6} rows")
    print('\n  DoD spot-checks:')
    import pandas as pd
    m = pd.read_csv(os.path.join(CORPUS, 'matches.csv'))
    print(f"    matches: {len(m)} rows | finished scores null? "
          f"{m[['goals_home','goals_away']].isna().any().any()}")
    c = pd.read_csv(os.path.join(CORPUS, 'cards.csv'))
    print(f"    cards: {len(c)} | colors: {dict(c['color'].value_counts())}")
    sq = pd.read_csv(os.path.join(CORPUS, 'squads.csv'))
    print(f"    squads: {len(sq)} | avg players/fixture-team: "
          f"{len(sq)/ (sq[['fixture_id','team_id']].drop_duplicates().shape[0]):.1f}")
    pm = pd.read_csv(os.path.join(CORPUS, 'player_match.csv'))
    nums = ['minutes', 'goals', 'assists', 'shots', 'shots_on', 'yellow', 'red']
    print(f"    player_match: {len(pm)} | nulls in numeric cols: "
          f"{int(pm[nums].isna().sum().sum())} | max minutes: {pm['minutes'].max()}")
    integrity()
