#!/usr/bin/env python3
"""
backtest_m3.py — leave-one-tournament-out RPS gate for the suspension downweight (B6).

The honest test: does applying the downweight improve MATCH-OUTCOME (W/D/L)
prediction out-of-sample? For each edition T we apply the b_susp learned from the
OTHER editions (LOTO, from m3_posterior.json) — so the effect size never sees the
matches it is scored on. Baseline λ (team/opp/stage/home Poisson GLM) is identical
in both arms; the ONLY difference is multiplying a team's λ by exp(b_susp·w) when a
key player of weight w is suspended. So ΔRPS is driven purely by the ~treated matches.

Gate: ship the feature only if adjusted RPS beats baseline AND the difference is
distinguishable from noise (bootstrap CI on ΔRPS + Diebold-Mariano test). A null
result is a valid, honest outcome — keep the machinery, leave the effect dormant.

  python v2/m3/backtest_m3.py

Reuses v2/backtest.py (wdl, rps) and v2/dm_test.py (dm_test).
"""
import os
import sys
import json
import numpy as np
import pandas as pd
from sklearn.linear_model import PoissonRegressor
from sklearn.model_selection import GridSearchCV

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..'))   # v2/ for backtest, dm_test
from backtest import wdl, rps          # noqa: E402
from dm_test import dm_test            # noqa: E402
CORPUS = os.path.join(HERE, 'corpus')


def baseline_lambda(df):
    """Fit a treatment-free Poisson GLM (team attack / opp defence / stage / home)
    and return λ̂ for every row. Same baseline for both arms of the gate."""
    atk = pd.get_dummies(df['team_id'], prefix='atk')
    dfn = pd.get_dummies(df['opponent_id'], prefix='def')
    from rules import stage_of
    stg = pd.get_dummies(df['stage'].map(stage_of), prefix='stg')
    X = pd.concat([atk.reset_index(drop=True), dfn.reset_index(drop=True),
                   stg.reset_index(drop=True), df[['is_home']].reset_index(drop=True)],
                  axis=1).astype(float)
    y = df['goals_for'].values
    gs = GridSearchCV(PoissonRegressor(max_iter=4000),
                      {'alpha': np.logspace(-2, 2.5, 12)},
                      scoring='neg_mean_poisson_deviance', cv=5)
    gs.fit(X, y)
    model = PoissonRegressor(alpha=gs.best_params_['alpha'], max_iter=6000).fit(X, y)
    return model.predict(X), gs.best_params_['alpha']


def main():
    df = pd.read_csv(os.path.join(CORPUS, 'modeling_rows.csv')).reset_index(drop=True)
    post = json.load(open(os.path.join(CORPUS, 'm3_posterior.json')))
    loto = post['loto_b_susp']  # {'{lid}_{season}': b_susp trained leaving it out}

    lam_base, alpha = baseline_lambda(df)
    df['lam_base'] = lam_base
    # downweight factor per row, using the OUT-OF-SAMPLE b_susp for that edition
    df['b'] = df.apply(lambda r: loto.get(f"{int(r['league_id'])}_{int(r['season'])}", 0.0), axis=1)
    df['lam_adj'] = df['lam_base'] * np.exp(df['b'] * df['susp_weight'])

    # pair rows by fixture (home + away), compute per-match RPS for both arms
    loss_base, loss_adj, n_diff = [], [], 0
    for fid, g in df.groupby('fixture_id'):
        h = g[g['is_home'] == 1]
        a = g[g['is_home'] == 0]
        if len(h) != 1 or len(a) != 1:
            continue
        h = h.iloc[0]; a = a.iloc[0]
        gf, ga = h['goals_for'], h['goals_against']
        o = 0 if gf > ga else (1 if gf == ga else 2)
        rb = rps(wdl(h['lam_base'], a['lam_base']), o)
        ra = rps(wdl(h['lam_adj'], a['lam_adj']), o)
        loss_base.append(rb); loss_adj.append(ra)
        if abs(h['lam_base'] - h['lam_adj']) > 1e-9 or abs(a['lam_base'] - a['lam_adj']) > 1e-9:
            n_diff += 1
    loss_base = np.array(loss_base); loss_adj = np.array(loss_adj)

    mean_base, mean_adj = loss_base.mean(), loss_adj.mean()
    d_rps = mean_base - mean_adj           # >0 ⇒ adjusted better
    dm, p, dbar, n = dm_test(loss_base, loss_adj)

    # bootstrap CI on ΔRPS (resample matches)
    rng = np.random.default_rng(20260626)
    diffs = loss_base - loss_adj
    boot = [diffs[rng.integers(0, n, n)].mean() for _ in range(2000)]
    lo, hi = np.percentile(boot, [2.5, 97.5])

    significant = (lo > 0) and (p < 0.05)
    verdict = 'SHIP' if significant else 'DO NOT SHIP (keep machinery dormant)'

    out = {
        'matches': int(n), 'matches_affected': int(n_diff),
        'rps_baseline': round(float(mean_base), 5),
        'rps_adjusted': round(float(mean_adj), 5),
        'delta_rps': round(float(d_rps), 6),
        'delta_rps_ci95': [round(float(lo), 6), round(float(hi), 6)],
        'dm_stat': round(float(dm), 3), 'dm_p': round(float(p), 4),
        'baseline_alpha': float(alpha),
        'verdict': verdict,
    }
    with open(os.path.join(CORPUS, 'm3_gate.json'), 'w') as fh:
        json.dump(out, fh, indent=1)

    print('B6 — LOTO RPS gate\n')
    print(f"  matches: {n} | affected by downweight: {n_diff}")
    print(f"  RPS baseline: {mean_base:.5f}")
    print(f"  RPS adjusted: {mean_adj:.5f}")
    print(f"  ΔRPS (base-adj, >0=better): {d_rps:+.6f}  95% CI [{lo:+.6f}, {hi:+.6f}]")
    print(f"  Diebold-Mariano: stat={dm:+.3f}  p={p:.4f}")
    print(f"\n  VERDICT: {verdict}")
    print(f"  wrote {os.path.join(CORPUS, 'm3_gate.json')}")


if __name__ == '__main__':
    main()
