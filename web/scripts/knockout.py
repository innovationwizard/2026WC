#!/usr/bin/env python3
"""
knockout.py — shared knockout-bracket logic for the 2026 World Cup pipeline.

Single source of truth (Python side) for:
  • the official FIFA slot map (P73–P104) — mirrors web/src/lib/bracket.js,
  • group standings + the 8 best-third qualifiers, computed from played group matches,
  • assigning a REAL discovered knockout fixture (team A vs team B, from the data
    sources) to its bracket slot id — by matching teams to slot feeds, NOT by
    recomputing the FIFA combination matrix (the sources already did the draw).

Design (matches the project ETL rules):
  • Knockout matchups are READ from the authoritative feeds (autofetch), never guessed.
  • A fixture is assigned to a slot only when the match is unambiguous; otherwise it
    is FLAGGED (returned in `unassigned`) — the parser does not silently mis-place data.
  • Stage codes: r32 / r16 / qf / sf / third / final. Spanish labels for display live
    in the frontend; this module emits canonical (CSV) team names + stage codes only.
"""

# ── Official slot map (mirror of web/src/lib/bracket.js) ────────────────────────
# Feed: {'pos': 1|2, 'group': 'A'} (group winner/runner) or {'third': ['A', ...]}.
def w(g): return {'pos': 1, 'group': g}
def r(g): return {'pos': 2, 'group': g}
def t(*gs): return {'third': list(gs)}

# R32 ties (P73–P88) with date/time, mirroring bracket.js.
R32 = [
    {'id': 'P73', 'date': '2026-06-28', 'time': '13:00', 'a': r('A'), 'b': r('B')},
    {'id': 'P74', 'date': '2026-06-29', 'time': '14:30', 'a': w('E'), 'b': t('A', 'B', 'C', 'D', 'F')},
    {'id': 'P75', 'date': '2026-06-29', 'time': '19:00', 'a': w('F'), 'b': r('C')},
    {'id': 'P76', 'date': '2026-06-29', 'time': '11:00', 'a': w('C'), 'b': r('F')},
    {'id': 'P77', 'date': '2026-06-30', 'time': '15:00', 'a': w('I'), 'b': t('C', 'D', 'F', 'G', 'H')},
    {'id': 'P78', 'date': '2026-06-30', 'time': '11:00', 'a': r('E'), 'b': r('I')},
    {'id': 'P79', 'date': '2026-06-30', 'time': '19:00', 'a': w('A'), 'b': t('C', 'E', 'F', 'H', 'I')},
    {'id': 'P80', 'date': '2026-07-01', 'time': '10:00', 'a': w('L'), 'b': t('E', 'H', 'I', 'J', 'K')},
    {'id': 'P81', 'date': '2026-07-01', 'time': '18:00', 'a': w('D'), 'b': t('B', 'E', 'F', 'I', 'J')},
    {'id': 'P82', 'date': '2026-07-01', 'time': '14:00', 'a': w('G'), 'b': t('A', 'E', 'H', 'I', 'J')},
    {'id': 'P83', 'date': '2026-07-02', 'time': '17:00', 'a': r('K'), 'b': r('L')},
    {'id': 'P84', 'date': '2026-07-02', 'time': '13:00', 'a': w('H'), 'b': r('J')},
    {'id': 'P85', 'date': '2026-07-02', 'time': '21:00', 'a': w('B'), 'b': t('E', 'F', 'G', 'I', 'J')},
    {'id': 'P86', 'date': '2026-07-03', 'time': '16:00', 'a': w('J'), 'b': r('H')},
    {'id': 'P87', 'date': '2026-07-03', 'time': '19:30', 'a': w('K'), 'b': t('D', 'E', 'I', 'J', 'L')},
    {'id': 'P88', 'date': '2026-07-03', 'time': '12:00', 'a': r('D'), 'b': r('G')},
]

# Later rounds reference the winner (W##) of earlier slots.
ROUNDS = {
    'r16': [
        {'id': 'P89', 'date': '2026-07-04', 'time': '15:00', 'a': 'P74', 'b': 'P77'},
        {'id': 'P90', 'date': '2026-07-04', 'time': '11:00', 'a': 'P73', 'b': 'P75'},
        {'id': 'P94', 'date': '2026-07-06', 'time': '18:00', 'a': 'P81', 'b': 'P82'},
        {'id': 'P93', 'date': '2026-07-06', 'time': '13:00', 'a': 'P83', 'b': 'P84'},
        {'id': 'P91', 'date': '2026-07-05', 'time': '14:00', 'a': 'P76', 'b': 'P78'},
        {'id': 'P92', 'date': '2026-07-05', 'time': '18:00', 'a': 'P79', 'b': 'P80'},
        {'id': 'P95', 'date': '2026-07-07', 'time': '10:00', 'a': 'P86', 'b': 'P88'},
        {'id': 'P96', 'date': '2026-07-07', 'time': '14:00', 'a': 'P85', 'b': 'P87'},
    ],
    'qf': [
        {'id': 'P97', 'date': '2026-07-09', 'time': '14:00', 'a': 'P89', 'b': 'P90'},
        {'id': 'P98', 'date': '2026-07-10', 'time': '13:00', 'a': 'P93', 'b': 'P94'},
        {'id': 'P99', 'date': '2026-07-11', 'time': '15:00', 'a': 'P91', 'b': 'P92'},
        {'id': 'P100', 'date': '2026-07-11', 'time': '19:00', 'a': 'P95', 'b': 'P96'},
    ],
    'sf': [
        {'id': 'P101', 'date': '2026-07-14', 'time': '13:00', 'a': 'P97', 'b': 'P98'},
        {'id': 'P102', 'date': '2026-07-15', 'time': '13:00', 'a': 'P99', 'b': 'P100'},
    ],
    'third': {'id': 'P103', 'date': '2026-07-18', 'time': '15:00', 'a': 'P101', 'b': 'P102'},
    'final': {'id': 'P104', 'date': '2026-07-19', 'time': '13:00', 'a': 'P101', 'b': 'P102'},
}

# slot id → stage code (for emitting match entries / display grouping)
SLOT_STAGE = {tie['id']: 'r32' for tie in R32}
SLOT_STAGE.update({tie['id']: 'r16' for tie in ROUNDS['r16']})
SLOT_STAGE.update({tie['id']: 'qf' for tie in ROUNDS['qf']})
SLOT_STAGE.update({tie['id']: 'sf' for tie in ROUNDS['sf']})
SLOT_STAGE[ROUNDS['third']['id']] = 'third'
SLOT_STAGE[ROUNDS['final']['id']] = 'final'

# How the data sources label each round → our stage code. Lower-cased, punctuation-loose.
ROUND_LABEL_TO_STAGE = {
    'round of 32': 'r32',
    'round of 16': 'r16',
    'quarter-finals': 'qf', 'quarterfinals': 'qf', 'quarter finals': 'qf',
    'semi-finals': 'sf', 'semifinals': 'sf', 'semi finals': 'sf',
    '3rd place final': 'third', 'third place final': 'third', '3rd place': 'third',
    'play-off for third place': 'third',
    'final': 'final',
}


def stage_from_round_label(label):
    """Map a source round label (e.g. 'Round of 32') to a stage code, or None."""
    if not label:
        return None
    key = ' '.join(str(label).lower().replace('-', ' ').split())
    # exact, then prefix (sources sometimes append a leg/' - 1' suffix)
    if key in ROUND_LABEL_TO_STAGE:
        return ROUND_LABEL_TO_STAGE[key]
    for lbl, st in ROUND_LABEL_TO_STAGE.items():
        if key.startswith(lbl):
            return st
    return None


# ── Group standings + best-third qualifiers ────────────────────────────────────
def group_standings(group_matches):
    """From finalized group matches (each: home, away, group, result{home,away}),
    return {group: [team_1st, team_2nd, team_3rd, team_4th]} for COMPLETE groups only.
    FIFA order: points, goal difference, goals for (head-to-head not needed once all
    play the same schedule and we only need a stable, complete-group ordering)."""
    by_group = {}
    for m in group_matches:
        g = m.get('group')
        if not g:
            continue
        by_group.setdefault(g, []).append(m)

    standings = {}
    for g, gm in by_group.items():
        rows = {}
        complete = True
        for m in gm:
            for team in (m['home'], m['away']):
                rows.setdefault(team, {'team': team, 'pts': 0, 'gf': 0, 'ga': 0})
            res = m.get('result')
            if m.get('status') != 'finalizado' or not res:
                complete = False
                continue
            hg, ag = res['home'], res['away']
            rows[m['home']]['gf'] += hg; rows[m['home']]['ga'] += ag
            rows[m['away']]['gf'] += ag; rows[m['away']]['ga'] += hg
            if hg > ag: rows[m['home']]['pts'] += 3
            elif ag > hg: rows[m['away']]['pts'] += 3
            else: rows[m['home']]['pts'] += 1; rows[m['away']]['pts'] += 1
        if not complete:
            continue
        order = sorted(rows.values(),
                       key=lambda x: (x['pts'], x['gf'] - x['ga'], x['gf'], x['team']),
                       reverse=True)
        standings[g] = [x['team'] for x in order]
    return standings


def best_thirds(standings):
    """Rank the third-placed teams of complete groups; the top 8 qualify.
    Returns {'qualified_groups': set(groups whose 3rd advances), 'third_of': {group: team}}.
    Only meaningful once enough groups are complete; returns the best-available ranking."""
    thirds = []
    third_of = {}
    for g, order in standings.items():
        if len(order) >= 3:
            team = order[2]
            third_of[g] = team
            thirds.append((g, team))
    # We need the per-(group,team) stats to rank; recompute from standings position is
    # insufficient, so callers pass full rows via rank_thirds when available. Here we
    # only know identities; ranking by stats happens in qualified_third_groups().
    return {'third_of': third_of, 'groups_with_third': [g for g, _ in thirds]}


def qualified_third_groups(group_matches):
    """The set of groups whose third-placed team is among the 8 best thirds.
    Computed from full stats. Returns (set_of_groups, {group: third_team})."""
    standings = group_standings(group_matches)
    # Build third-place rows with stats.
    rows_by_group = {}
    for m in group_matches:
        g = m.get('group')
        if not g:
            continue
        rows_by_group.setdefault(g, {})
        for team in (m['home'], m['away']):
            rows_by_group[g].setdefault(team, {'team': team, 'pts': 0, 'gf': 0, 'ga': 0})
        res = m.get('result')
        if m.get('status') != 'finalizado' or not res:
            continue
        hg, ag = res['home'], res['away']
        rows_by_group[g][m['home']]['gf'] += hg; rows_by_group[g][m['home']]['ga'] += ag
        rows_by_group[g][m['away']]['gf'] += ag; rows_by_group[g][m['away']]['ga'] += hg
        if hg > ag: rows_by_group[g][m['home']]['pts'] += 3
        elif ag > hg: rows_by_group[g][m['away']]['pts'] += 3
        else: rows_by_group[g][m['home']]['pts'] += 1; rows_by_group[g][m['away']]['pts'] += 1

    third_rows = []
    third_of = {}
    for g, order in standings.items():
        if len(order) >= 3:
            team = order[2]
            third_of[g] = team
            stat = rows_by_group[g][team]
            third_rows.append((g, team, stat['pts'], stat['gf'] - stat['ga'], stat['gf']))
    third_rows.sort(key=lambda x: (x[2], x[3], x[4], x[1]), reverse=True)
    qualified = {g for g, *_ in third_rows[:8]}
    return qualified, third_of


# ── Assign discovered fixtures to slots ─────────────────────────────────────────
def _resolved_positions(standings):
    """{(group, pos): team} for winner(1)/runner(2) of complete groups."""
    out = {}
    for g, order in standings.items():
        if len(order) >= 1: out[(g, 1)] = order[0]
        if len(order) >= 2: out[(g, 2)] = order[1]
    return out


def assign_r32_slots(fixtures, group_matches):
    """Map each discovered R32 fixture to its slot id (P73–P88).

    fixtures: list of dicts with at least {'home', 'away'} (canonical names).
    Returns (assigned, unassigned) where assigned = {slot_id: fixture} and
    unassigned = list of fixtures that could not be placed unambiguously.

    A fixture matches a slot when, for some orientation of (X, Y) onto (feed_a, feed_b):
      • a {pos,group} feed equals the resolved winner/runner team, AND
      • the partner feed is satisfied: either the other {pos,group} team matches, or a
        {third:[groups]} feed and the other team is that group's qualified third.
    """
    standings = group_standings(group_matches)
    pos_team = _resolved_positions(standings)          # (group,pos) -> team
    # Third-place team of every complete group. We do NOT pre-compute which 8 "qualify":
    # the FIFA best-third tiebreak is subtle and the authoritative source already made the
    # draw, so we map a third-feed by the team's actual group, letting the real fixture +
    # the partner (winner/runner) feed pin the slot uniquely. (Computing qualifiers here
    # mis-ranked the 8th/9th boundary — Ghana/Iran — which is exactly why we read, not guess.)
    third_team_group = {order[2]: g for g, order in standings.items() if len(order) >= 3}

    def feed_matches(feed, team):
        if 'third' in feed:
            g = third_team_group.get(team)
            return g is not None and g in feed['third']
        return pos_team.get((feed['group'], feed['pos'])) == team

    assigned, unassigned = {}, []
    used_slots = set()
    for fx in fixtures:
        x, y = fx['home'], fx['away']
        hit = None
        for tie in R32:
            if tie['id'] in used_slots:
                continue
            fa, fb = tie['a'], tie['b']
            if (feed_matches(fa, x) and feed_matches(fb, y)) or \
               (feed_matches(fa, y) and feed_matches(fb, x)):
                hit = tie['id']
                break
        if hit:
            assigned[hit] = fx
            used_slots.add(hit)
        else:
            unassigned.append(fx)
    return assigned, unassigned


def _winner_loser(fx):
    """(advancer, eliminated) for a discovered fixture, or (None, None) if undecided.
    Prefers the explicit advancer flag; falls back to the 90-min score when decisive."""
    adv = fx.get('advancer')
    if adv:
        other = fx['away'] if adv == fx['home'] else fx['home']
        return adv, other
    ft = fx.get('ft')
    if ft and ft[0] != ft[1]:
        return (fx['home'], fx['away']) if ft[0] > ft[1] else (fx['away'], fx['home'])
    return None, None


def resolve_bracket(fixtures, group_matches):
    """Slot EVERY discovered knockout fixture (all rounds) to its bracket id.

    R32 is slotted by group winner/runner/third feeds; later rounds by advancement —
    a slot's two teams are the advancers of its two feeder slots, so a later-round
    fixture matches the slot whose expected pair equals its teams (works as soon as the
    feeders are decided, even before the later match kicks off). Returns
    (assigned: {slot_id: fixture}, unassigned: [fixtures]).
    """
    assigned, unassigned = {}, []
    by_stage = {}
    for fx in fixtures:
        by_stage.setdefault(fx.get('stage'), []).append(fx)

    # R32 — feed-based.
    r32_assigned, r32_unassigned = assign_r32_slots(by_stage.get('r32', []), group_matches)
    assigned.update(r32_assigned)
    unassigned.extend(r32_unassigned)

    adv_of, lost_of = {}, {}
    for sid, fx in assigned.items():
        a, l = _winner_loser(fx)
        if a: adv_of[sid], lost_of[sid] = a, l

    # Later rounds — advancement-based, in bracket order.
    later = [('r16', ROUNDS['r16']), ('qf', ROUNDS['qf']), ('sf', ROUNDS['sf'])]
    for stage, ties in later:
        pool = list(by_stage.get(stage, []))
        for tie in ties:
            ea, eb = adv_of.get(tie['a']), adv_of.get(tie['b'])
            if not (ea and eb):
                continue
            want = frozenset((ea, eb))
            match = next((fx for fx in pool if frozenset((fx['home'], fx['away'])) == want), None)
            if match:
                pool.remove(match)
                assigned[tie['id']] = match
                a, l = _winner_loser(match)
                if a: adv_of[tie['id']], lost_of[tie['id']] = a, l
        unassigned.extend(pool)

    # Final (winners of the two SFs) and third place (their losers).
    fin, third = ROUNDS['final'], ROUNDS['third']
    fa, fb = adv_of.get(fin['a']), adv_of.get(fin['b'])
    ta, tb = lost_of.get(third['a']), lost_of.get(third['b'])
    for tie, want_pair, pool in (
        (fin, (fa, fb), by_stage.get('final', [])),
        (third, (ta, tb), by_stage.get('third', [])),
    ):
        if want_pair[0] and want_pair[1]:
            want = frozenset(want_pair)
            match = next((fx for fx in pool if frozenset((fx['home'], fx['away'])) == want), None)
            if match:
                assigned[tie['id']] = match
            else:
                unassigned.extend([fx for fx in pool if id(fx) not in {id(v) for v in assigned.values()}])
        else:
            unassigned.extend(pool)
    return assigned, unassigned


if __name__ == '__main__':
    # Self-test: load group matches from matches.json, check standings + R32 slotting
    # against the real fixtures observed from the data sources.
    import json, os
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    data = json.load(open(os.path.join(ROOT, 'web', 'static', 'data', 'matches.json')))
    gm = [m for m in data['matches'] if m.get('group')]
    st = group_standings(gm)
    print(f"complete groups: {sorted(st)}")
    for g in sorted(st):
        print(f"  {g}: 1º {st[g][0]} | 2º {st[g][1]} | 3º {st[g][2]}")
    qual, third_of = qualified_third_groups(gm)
    print(f"\nbest-third groups (8 qualify): {sorted(qual)}")
    print(f"  thirds: {[(g, third_of[g]) for g in sorted(qual)]}")

    # Real R32 fixtures observed from API-Football (home, away):
    real_r32 = [
        {'home': 'South Africa', 'away': 'Canada'},
        {'home': 'Brazil', 'away': 'Japan'},
        {'home': 'Germany', 'away': 'Paraguay'},
        {'home': 'Netherlands', 'away': 'Morocco'},
        {'home': 'Ivory Coast', 'away': 'Norway'},
        {'home': 'France', 'away': 'Sweden'},
        {'home': 'Mexico', 'away': 'Ecuador'},
        {'home': 'England', 'away': 'Congo DR'},   # 'Congo DR' will need canonical 'DR Congo'
        {'home': 'Belgium', 'away': 'Senegal'},
    ]
    assigned, unassigned = assign_r32_slots(real_r32, gm)
    print("\nR32 slot assignment:")
    for sid in sorted(assigned, key=lambda s: int(s[1:])):
        fx = assigned[sid]
        print(f"  {sid}: {fx['home']} vs {fx['away']}")
    print(f"unassigned: {unassigned}")
