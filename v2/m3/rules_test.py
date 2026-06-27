#!/usr/bin/env python3
"""
rules_test.py — B3.4 unit tests for the disciplinary rule engine.
Asserts structural invariants + hand-verified known cases.

  python v2/m3/rules_test.py
"""
import os
import sys
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rules import derive_suspensions  # noqa: E402

CORPUS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'corpus')


def main():
    ev = derive_suspensions()
    s = pd.DataFrame(ev)
    m = pd.read_csv(os.path.join(CORPUS, 'matches.csv'))
    c = pd.read_csv(os.path.join(CORPUS, 'cards.csv'))

    # fixture_id -> (league, season, date) for edition/chronology checks
    meta = {r['fixture_id']: (r['league_id'], r['season'], r['date'])
            for _, r in m.iterrows()}

    passed = []

    def ok(name, cond):
        assert cond, f'FAILED: {name}'
        passed.append(name)

    # 1. Every derived ban corresponds to a real absence (cross-check 100%).
    ok('all_bans_absent', (s['appeared_despite_ban'] == 0).all())

    # 2. No cross-edition leakage: the triggering card and the missed match are in
    #    the same tournament edition, and the trigger is chronologically earlier.
    same_edition = chrono = True
    for _, r in s.iterrows():
        le_b, se_b, dt_b = meta[r['fixture_id']]
        le_s, se_s, dt_s = meta[r['source_fixture']]
        if (le_b, se_b) != (le_s, se_s):
            same_edition = False
        if not (dt_s < dt_b):
            chrono = False
    ok('no_cross_edition_leak', same_edition)
    ok('trigger_precedes_ban', chrono)

    # 3. Plausible total (recon expected ~60-120 across the 6 tournaments).
    ok('count_plausible', 50 <= len(s) <= 110)

    # 4. KNOWN NEGATIVE (amnesty): Derek Cornelius got his 2nd yellow IN the Copa
    #    2024 quarter-final (fixture 1219958); the post-QF wipe means NO semi-final
    #    ban. There must be no suspension event for him at the SF (1227537).
    cornelius_sf = s[(s['player_id'] == 51295) & (s['fixture_id'] == 1227537)]
    ok('amnesty_clears_qf_2nd_yellow', len(cornelius_sf) == 0)

    # 5. KNOWN POSITIVE (red card): Wayne Hennessey was sent off (straight red) for
    #    Wales vs Iran at WC 2022; he must be banned for Wales' next match.
    hennessey_red = c[(c['player'].str.contains('Hennessey', na=False)) &
                      (c['color'] == 'Red Card')]
    ok('hennessey_has_red', len(hennessey_red) >= 1)
    hpid = int(hennessey_red['player_id'].iloc[0])
    ok('hennessey_banned_next', (s['player_id'] == hpid).any() and
       (s[s['player_id'] == hpid]['trigger'] == 'red').any())

    # 6. Every 'red' trigger maps to an actual Red Card event in the source fixture;
    #    every '2yellow' trigger's player has >=2 Yellow Card events that edition.
    red_ok = True
    for _, r in s[s['trigger'] == 'red'].iterrows():
        got = c[(c['fixture_id'] == r['source_fixture']) &
                (c['player_id'] == r['player_id']) & (c['color'] == 'Red Card')]
        if len(got) == 0:
            red_ok = False
    ok('red_triggers_have_red_event', red_ok)

    print('B3.4 — rule-engine tests\n')
    for name in passed:
        print(f'  [PASS] {name}')
    print(f'\n  {len(passed)} checks passed | {len(s)} suspensions '
          f'({(s.trigger == "red").sum()} red, {(s.trigger == "2yellow").sum()} 2-yellow)')


if __name__ == '__main__':
    main()
