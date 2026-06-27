#!/usr/bin/env python3
"""
rules.py — disciplinary rule engine (Batch B3). Derives card suspensions
DETERMINISTICALLY from the corpus (matches + cards + appearances). This is the
PRIMARY suspension signal (API-Football has no historical injury/suspension label);
it is more bulletproof than any editorial label because the rules are public and
the cards are observed.

Rules (verified 2026-06-26 against tournament regulations — sources in comments):
  - Two yellow cards in SEPARATE matches → 1-match ban.
  - A red card (straight, OR a 2nd yellow in the same match) → 1-match ban.
  - Yellow-card accumulation is WIPED at edition-specific stage boundaries.

Per-edition wipe stages (the rule has CHANGED across editions — do not assume):
  - WC 2018/2022, Euro 2020/2024, Copa 2021/2024: wipe AFTER the quarter-finals only.
    (Yellows carry from the group stage through the knockouts into the QF.)
  - WC 2026 (LIVE target, used in B7): FIFA changed it — wipe AFTER the group stage
    AND after the QF. Encoded here for the live path; not used by the historical fit.

DATA FINDING (B1.3, verified): a same-match 2nd-yellow sending-off appears in the
events feed as [Yellow Card, Yellow Card, Red Card] — BOTH yellows AND the red.
So a match in which a player sees a Red Card contributes 0 to cross-match yellow
accumulation (the yellows are consumed by the dismissal); the red itself is the ban.

  python v2/m3/rules.py        # derive suspensions + cross-check + write corpus/suspensions.csv

Sources:
  WC 2022 carry-through + QF wipe: NBC Sports "clean slate rule"; Yahoo Sports WC rules.
  WC 2026 group-stage wipe (new): FIFA rule change, Apr 2026 (Archysport/Wego/Fox).
  Euro 2024 QF wipe: Goal.com, 90min, Yahoo. Copa 2024 QF wipe: AllFootball, MSN.
"""
import os
import sys
import csv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
CORPUS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'corpus')

# Stage ordering for reset logic.
STAGE_ORDER = {'group': 0, 'r16': 1, 'qf': 2, 'sf': 3, '3p': 4, 'final': 4}

# Wipe stages by edition (league_id, season). Default = historical {'qf'}.
RESET_AFTER = {
    (1, 2018): {'qf'}, (1, 2022): {'qf'},
    (4, 2020): {'qf'}, (4, 2024): {'qf'},
    (9, 2021): {'qf'}, (9, 2024): {'qf'},
    (1, 2026): {'group', 'qf'},   # WC 2026 — new rule, for the live path (B7)
}
DEFAULT_RESET = {'qf'}


def stage_of(round_label):
    """Map a round label to a canonical stage. Order matters: several labels
    (Quarter-finals, Semi-finals, 3rd Place Final, 8th Finals) contain 'final'."""
    r = (round_label or '').lower()
    if 'group' in r:
        return 'group'
    if 'quarter' in r:
        return 'qf'
    if 'semi' in r:
        return 'sf'
    if '3rd place' in r or 'third place' in r:
        return '3p'
    if 'round of 16' in r or '8th final' in r or 'eighth' in r:
        return 'r16'
    if 'final' in r:
        return 'final'
    return 'group'  # safe default (qualifiers already filtered out upstream)


def _crosses_reset(prev_stage, stage, reset_after):
    """True if a wipe boundary lies between the previous and current stage."""
    if prev_stage is None:
        return False
    po, so = STAGE_ORDER[prev_stage], STAGE_ORDER[stage]
    return any(po <= STAGE_ORDER[rs] < so for rs in reset_after)


def _load():
    import pandas as pd
    m = pd.read_csv(os.path.join(CORPUS, 'matches.csv'))
    c = pd.read_csv(os.path.join(CORPUS, 'cards.csv'))
    pm = pd.read_csv(os.path.join(CORPUS, 'player_match.csv'))
    return m, c, pm


def derive_suspensions():
    """B3.2 — return a list of suspension events: (player banned for a specific
    fixture, the trigger, provenance). B3.3 cross-check is computed here too."""
    import pandas as pd
    m, c, pm = _load()
    m['stage'] = m['round'].map(stage_of)

    # (team, league_id, season) -> ordered [(fixture_id, date, stage)]
    # Keyed PER EDITION: card accumulation must NOT leak across tournaments
    # (a yellow in WC 2018 cannot ban a player in Euro 2020).
    team_fix = {}
    for _, r in m.iterrows():
        for side in ('home', 'away'):
            key = (r[f'{side}_id'], r['league_id'], r['season'])
            team_fix.setdefault(key, []).append((r['fixture_id'], r['date'], r['stage']))
    for k in team_fix:
        team_fix[k].sort(key=lambda x: x[1])  # by date

    # (fixture_id, player_id) -> list of card colors
    cards_by = {}
    for _, r in c.iterrows():
        cards_by.setdefault((r['fixture_id'], r['player_id']), []).append(r['color'])

    # players per team, and the set of (fixture,player) appearances
    appeared = set(zip(pm['fixture_id'], pm['player_id']))
    team_players = {}
    pm_named = pm[['team_id', 'player_id', 'player']].drop_duplicates()
    for _, r in pm_named.iterrows():
        team_players.setdefault(r['team_id'], {})[r['player_id']] = r['player']

    events = []
    for (team, lid, season), fixtures in team_fix.items():
        reset_after = RESET_AFTER.get((lid, season), DEFAULT_RESET)
        for pid, pname in team_players.get(team, {}).items():
            acc = 0
            prev_stage = None
            pending = None          # (trigger, source_fixture) banned for next fixture
            for (fid, date, stage) in fixtures:
                if _crosses_reset(prev_stage, stage, reset_after):
                    acc = 0
                    # The yellow amnesty also wipes a yellow-accumulation ban that
                    # completed just before the boundary (e.g. a 2nd yellow in the QF
                    # does NOT carry into the SF). A RED-card ban is served regardless.
                    if pending is not None and pending[0] == '2yellow':
                        pending = None
                if pending is not None:
                    trig, src = pending
                    events.append({
                        'player_id': pid, 'player': pname,
                        'team_id': team, 'fixture_id': fid, 'date': date,
                        'stage': stage, 'trigger': trig, 'source_fixture': src,
                        'appeared_despite_ban': int((fid, pid) in appeared),
                    })
                    pending = None
                    prev_stage = stage
                    continue  # banned: no cards to process this match
                cols = cards_by.get((fid, pid), [])
                if (fid, pid) in appeared or cols:
                    red = 'Red Card' in cols
                    if red:
                        pending = ('red', fid)
                        acc = 0  # yellows in a red match are consumed by the dismissal
                    elif 'Yellow Card' in cols:
                        acc += 1   # at most 1 carries per non-red match
                        if acc >= 2:
                            pending = ('2yellow', fid)
                            acc -= 2
                prev_stage = stage
    return events


def main():
    events = derive_suspensions()
    os.makedirs(CORPUS, exist_ok=True)
    hdr = ['player_id', 'player', 'team_id', 'fixture_id', 'date', 'stage',
           'trigger', 'source_fixture', 'appeared_despite_ban']
    with open(os.path.join(CORPUS, 'suspensions.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=hdr)
        w.writeheader()
        w.writerows(events)

    n = len(events)
    by_trig = {}
    absent = 0
    for e in events:
        by_trig[e['trigger']] = by_trig.get(e['trigger'], 0) + 1
        absent += (e['appeared_despite_ban'] == 0)
    print('B3.2/B3.3 — derived suspensions\n')
    print(f"  suspension events: {n}")
    print(f"  by trigger: {by_trig}")
    print(f"  B3.3 cross-check: {absent}/{n} banned players were ABSENT as expected "
          f"({100*absent/n:.0f}% agreement)")
    disagree = [e for e in events if e['appeared_despite_ban'] == 1]
    if disagree:
        print(f"  ⚠ {len(disagree)} appeared despite a derived ban (flagged, not dropped):")
        for e in disagree[:10]:
            print(f"     {e['player']} (team {e['team_id']}) fixture {e['fixture_id']} "
                  f"trigger={e['trigger']}")
    print(f"\n  wrote {os.path.join(CORPUS, 'suspensions.csv')}")


if __name__ == '__main__':
    main()
