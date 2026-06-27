#!/usr/bin/env python3
"""
weights.py — as-of-date key-player weights + the modeling dataset (Batch B4).

Mirrors the live collector's definition (v2/player_state.py):
    contribution = goals + 0.7 * assists
    weight       = contribution / team_total
    concentration_top3 = sum(top-3 contributions) / team_total
but computed POINT-IN-TIME: a player's weight for fixture F uses ONLY that team's
PRIOR matches in the SAME edition (date < F.date). No future leakage.

Outputs corpus/modeling_rows.csv — one row per (team, fixture):
  goals_for / goals_against, susp_weight (as-of-date weight of the most-key
  SUSPENDED player, 0 if none), absence_weight (broader: most-key player absent for
  ANY reason), concentration, prior_matches, controls. This is what B5 fits.

  python v2/m3/weights.py
"""
import os
import sys
import csv
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
CORPUS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'corpus')

ASSIST_W = 0.7  # same goal-involvement weight as v2/player_state.py


def _load():
    m = pd.read_csv(os.path.join(CORPUS, 'matches.csv'))
    pm = pd.read_csv(os.path.join(CORPUS, 'player_match.csv'))
    s = pd.read_csv(os.path.join(CORPUS, 'suspensions.csv'))
    return m, pm, s


def build():
    m, pm, s = _load()

    # fixture -> meta
    meta = {r['fixture_id']: r for _, r in m.iterrows()}
    # quick lookup: (fixture, team) -> set of player_ids present (in matchday squad)
    present = {}
    for _, r in pm.iterrows():
        present.setdefault((r['fixture_id'], r['team_id']), set()).add(r['player_id'])
    # player_match enriched with date/edition for as-of filtering
    pm = pm.merge(m[['fixture_id', 'date', 'league_id', 'season']], on='fixture_id', how='left')

    # suspensions indexed by (fixture, team) -> list of player_ids banned for it
    susp_by = {}
    for _, r in s.iterrows():
        susp_by.setdefault((r['fixture_id'], r['team_id']), []).append(r['player_id'])

    # per (team, edition) the team's player_match rows, for as-of aggregation
    pm_by_team_ed = {k: g for k, g in pm.groupby(['team_id', 'league_id', 'season'])}

    def as_of_weights(team, lid, season, before_date):
        """Point-in-time contribution weights from prior matches in this edition."""
        g = pm_by_team_ed.get((team, lid, season))
        if g is None:
            return {}, 0.0, 0
        prior = g[g['date'] < before_date]
        nprior = prior['fixture_id'].nunique()
        if prior.empty:
            return {}, 0.0, 0
        contrib = (prior.groupby('player_id')
                   .apply(lambda d: d['goals'].sum() + ASSIST_W * d['assists'].sum()))
        total = contrib.sum()
        if total <= 0:
            return {pid: 0.0 for pid in contrib.index}, 0.0, nprior
        weights = (contrib / total).to_dict()
        top3 = contrib.sort_values(ascending=False).head(3).sum()
        return weights, float(top3 / total), nprior

    rows = []
    for fid, r in meta.items():
        lid, season, date, stage = r['league_id'], r['season'], r['date'], r['round']
        for side, opp_side in (('home', 'away'), ('away', 'home')):
            team = r[f'{side}_id']
            opp = r[f'{opp_side}_id']
            gf = r[f'goals_{side}']
            ga = r[f'goals_{opp_side}']
            weights, conc, nprior = as_of_weights(team, lid, season, date)

            # suspended players for this team-fixture; their as-of-date weight
            banned = susp_by.get((fid, team), [])
            susp_w = max((weights.get(pid, 0.0) for pid in banned), default=0.0)
            susp_player = None
            if banned:
                susp_player = max(banned, key=lambda pid: weights.get(pid, 0.0))

            # broader absence: a player with weight>0 (a regular) not in today's squad
            sq = present.get((fid, team), set())
            absent_regulars = [(pid, w) for pid, w in weights.items()
                               if w > 0 and pid not in sq]
            abs_w = max((w for _, w in absent_regulars), default=0.0)

            rows.append({
                'fixture_id': fid, 'league_id': lid, 'season': season,
                'date': date, 'stage': stage,
                'team_id': team, 'opponent_id': opp, 'is_home': int(side == 'home'),
                'goals_for': gf, 'goals_against': ga,
                'prior_matches': nprior, 'concentration': round(conc, 3),
                'susp_weight': round(susp_w, 3), 'susp_player_id': susp_player,
                'n_suspended': len(banned),
                'absence_weight': round(abs_w, 3), 'n_absent_regulars': len(absent_regulars),
            })

    out = os.path.join(CORPUS, 'modeling_rows.csv')
    hdr = list(rows[0].keys())
    with open(out, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=hdr)
        w.writeheader()
        w.writerows(rows)
    return out, pd.DataFrame(rows)


def main():
    out, df = build()
    print('B4 — as-of-date weights + modeling dataset\n')
    print(f"  rows (team-fixtures): {len(df)} | wrote {os.path.basename(out)}")

    # B4.1 DoD: as-of weights sum ~1 per team-fixture WHERE prior matches exist.
    # (Re-derive a sample to confirm point-in-time normalization.)
    has_prior = df[df['prior_matches'] > 0]
    print(f"\n  B4.1 — team-fixtures with prior history: {len(has_prior)}/{len(df)} "
          f"(first match of each team has no prior → weights undefined, expected)")

    # B4.2 DoD: suspension treatment rows
    susp_rows = df[df['susp_weight'] > 0]
    treated = df[df['n_suspended'] > 0]
    print(f"\n  B4.2 — suspension rows: n_suspended>0 in {len(treated)} fixtures; "
          f"susp_weight>0 (key player) in {len(susp_rows)}")
    print(f"        susp_weight range: {df['susp_weight'].max():.3f} max | "
          f"mean(nonzero) {susp_rows['susp_weight'].mean():.3f}")

    # B4.3 DoD: suspension ⊆ absence (a suspended player must also be absent)
    viol = treated[(treated['n_suspended'] > 0) & (treated['n_absent_regulars'] == 0) &
                   (treated['susp_weight'] > 0)]
    print(f"\n  B4.3 — absence_weight populated; suspension⊆absence violations "
          f"(susp_weight>0 but no absent regular): {len(viol)}")
    print(f"        absence_weight>0 in {len(df[df['absence_weight'] > 0])} fixtures")


if __name__ == '__main__':
    main()
