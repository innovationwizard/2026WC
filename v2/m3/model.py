#!/usr/bin/env python3
"""
model.py — empirical-Bayes / shrinkage estimate of the suspension downweight (B5).

Model (Poisson GLM, log link):
    goals_for ~ Poisson( exp( atk[team] + def[opponent] + g*home
                              + b_susp*susp_weight + b_abs*absence_weight ) )

The L2 penalty IS the partial pooling: team-attack and opponent-defence effects
shrink toward the global mean, and the treatment coefficients shrink toward 0.
The penalty strength (alpha) is chosen by cross-validated Poisson deviance — the
DATA sets how much to trust the in-sample signal (Q3: no hand-set bound). A
bootstrap over matches gives an honest CI; if the signal is noise, the estimate
shrinks to ~0 and the CI straddles 0.

The downweight applied to a team's expected goals when a key player of as-of-date
weight w is suspended is the multiplicative factor  exp(b_susp * w)  (<=1 if the
effect reduces scoring; exp() keeps it >=0 automatically — the structural cap).

  python v2/m3/model.py        # fit + bootstrap CI + leave-one-tournament-out

No new dependencies: numpy / pandas / scikit-learn only.
"""
import os
import sys
import json
import numpy as np
import pandas as pd
from sklearn.linear_model import PoissonRegressor
from sklearn.model_selection import GridSearchCV

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rules import stage_of  # noqa: E402
CORPUS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'corpus')

W_REF = 0.2          # a typical key-player weight, for an interpretable downweight
ALPHAS = np.logspace(-2, 2.5, 14)
N_BOOT = 300
TREAT = ['susp_weight', 'absence_weight']


def design(df, columns=None, with_stage=True):
    """Build the GLM design matrix. atk_* = team attack, def_* = opponent defence.
    with_stage adds knockout-round controls (group/r16/qf/sf/final) — the key
    confounder: suspensions cluster late, and late rounds score less."""
    parts = [pd.get_dummies(df['team_id'].reset_index(drop=True), prefix='atk'),
             pd.get_dummies(df['opponent_id'].reset_index(drop=True), prefix='def')]
    if with_stage:
        stg = df['stage'].map(stage_of).reset_index(drop=True)
        parts.append(pd.get_dummies(stg, prefix='stg'))
    parts.append(df[['is_home'] + TREAT].reset_index(drop=True))
    X = pd.concat(parts, axis=1).astype(float)
    if columns is not None:
        X = X.reindex(columns=columns, fill_value=0.0)
    return X


def fit_alpha(X, y):
    """Pick L2 strength by cross-validated Poisson deviance."""
    gs = GridSearchCV(PoissonRegressor(max_iter=3000),
                      {'alpha': ALPHAS}, scoring='neg_mean_poisson_deviance', cv=5)
    gs.fit(X, y)
    return gs.best_params_['alpha']


def coef(model, columns, name):
    return float(model.coef_[list(columns).index(name)])


def main():
    df = pd.read_csv(os.path.join(CORPUS, 'modeling_rows.csv'))
    y = df['goals_for'].values

    # Confounder check: b_susp WITHOUT vs WITH knockout-stage controls.
    Xns = design(df, with_stage=False)
    a_ns = fit_alpha(Xns, y)
    m_ns = PoissonRegressor(alpha=a_ns, max_iter=5000).fit(Xns, y)
    b_susp_nostage = coef(m_ns, list(Xns.columns), 'susp_weight')

    X = design(df, with_stage=True)
    cols = list(X.columns)

    alpha = fit_alpha(X, y)
    base = PoissonRegressor(alpha=alpha, max_iter=5000).fit(X, y)
    b_susp = coef(base, cols, 'susp_weight')
    b_abs = coef(base, cols, 'absence_weight')

    # bootstrap over matches for a CI on b_susp and the implied downweight
    rng = np.random.default_rng(20260626)  # fixed seed (Math.random unavailable anyway)
    n = len(df)
    boot_susp, boot_mult = [], []
    for _ in range(N_BOOT):
        idx = rng.integers(0, n, n)
        Xb = design(df.iloc[idx], columns=cols)
        m = PoissonRegressor(alpha=alpha, max_iter=3000).fit(Xb, y[idx])
        bs = coef(m, cols, 'susp_weight')
        boot_susp.append(bs)
        boot_mult.append(np.exp(bs * W_REF))
    lo, hi = np.percentile(boot_susp, [2.5, 97.5])
    mlo, mhi = np.percentile(boot_mult, [2.5, 97.5])

    # leave-one-tournament-out stability (B5.3)
    loto = {}
    for (lid, season), _ in df.groupby(['league_id', 'season']):
        sub = df[~((df['league_id'] == lid) & (df['season'] == season))]
        Xl = design(sub, columns=cols)
        m = PoissonRegressor(alpha=alpha, max_iter=5000).fit(Xl, sub['goals_for'].values)
        loto[f'{int(lid)}_{int(season)}'] = round(coef(m, cols, 'susp_weight'), 4)

    n_treated = int((df['susp_weight'] > 0).sum())
    result = {
        'alpha_cv': float(alpha),
        'b_susp': round(b_susp, 4),
        'b_susp_ci95': [round(lo, 4), round(hi, 4)],
        'downweight_at_w_ref': {'w_ref': W_REF,
                                'multiplier': round(float(np.exp(b_susp * W_REF)), 4),
                                'ci95': [round(mlo, 4), round(mhi, 4)]},
        'b_absence': round(b_abs, 4),
        'b_susp_without_stage_control': round(b_susp_nostage, 4),
        'n_treated_key_suspensions': n_treated,
        'loto_b_susp': loto,
        'ci_excludes_zero': bool(lo > 0 or hi < 0),
        'note': 'b_susp<0 means suspension reduces goals; multiplier=exp(b_susp*w).',
    }
    with open(os.path.join(CORPUS, 'm3_posterior.json'), 'w') as fh:
        json.dump(result, fh, indent=1)

    print('B5 — suspension downweight (empirical-Bayes Poisson GLM)\n')
    print(f"  CV alpha (shrinkage): {alpha:.3g}")
    print(f"  CONFOUNDER CHECK  b_susp without stage control: {b_susp_nostage:+.4f}"
          f"  ->  with stage control: {b_susp:+.4f}")
    print(f"  b_susp = {b_susp:+.4f}   95% CI [{lo:+.4f}, {hi:+.4f}]")
    print(f"  downweight at w={W_REF}: x{np.exp(b_susp*W_REF):.3f}  "
          f"CI [x{mlo:.3f}, x{mhi:.3f}]")
    print(f"  b_absence = {b_abs:+.4f}   (broader prior anchor)")
    print(f"  treated key suspensions: {n_treated}")
    print(f"  leave-one-tournament-out b_susp: {loto}")
    print(f"\n  CI excludes 0? {result['ci_excludes_zero']}  "
          f"-> {'SIGNAL' if result['ci_excludes_zero'] else 'consistent with NO effect (shrinks to ~0)'}")
    print(f"  wrote {os.path.join(CORPUS, 'm3_posterior.json')}")


if __name__ == '__main__':
    main()
