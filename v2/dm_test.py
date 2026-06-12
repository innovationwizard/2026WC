#!/usr/bin/env python3
"""
Diebold–Mariano test on the held-out per-match RPS series.
Is the accuracy gap between M1 (Elo) / M2 (net) / M3 (conjunto) statistically real?

Forecasts are 1-step and non-overlapping (each match predicted independently), so the
long-run variance reduces to the sample variance (h=1). Harvey–Leybourne–Newbold (1997)
small-sample correction + t(n-1) p-values. Where one model nests the other (the net uses
Elo as a feature; M3's family contains M2 at w=1), DM is conservative — a rejection is a
robust lower bound (Clark–West would be more powerful).

Run:  .venv/bin/python v2/dm_test.py
"""
import sys, os, math, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
from scipy import stats
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from feature_engine import build_training_data
from neural_poisson import EnsembleNeuralPoisson, GBTPoissonModel, EloBaselineModel
from backtest import wdl, rps, MIN_DATE, CUTOFF

N_ENSEMBLE = 5
W_NET = 0.5


def dm_test(loss_a, loss_b, h=1):
    """DM on d = loss_a - loss_b (negative mean ⇒ A more accurate)."""
    d = np.asarray(loss_a) - np.asarray(loss_b)
    n = len(d)
    dbar = d.mean()
    dc = d - dbar
    lrv = np.mean(dc ** 2)
    for k in range(1, h):
        lrv += 2 * np.mean(dc[k:] * dc[:-k])
    dm = dbar / math.sqrt(lrv / n)
    hln = math.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)   # small-sample correction
    dm *= hln
    p = 2 * stats.t.cdf(-abs(dm), df=n - 1)
    return dm, p, dbar, n


def main():
    df = pd.read_csv(os.path.join(os.path.dirname(__file__), '..', 'results.csv'))
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    X, y, elo, tv, frame = build_training_data(df, min_date=MIN_DATE, return_frame=True)
    feat = list(X.columns)
    frame['date'] = pd.to_datetime(frame['date'])
    train = frame[frame['date'] < CUTOFF]
    test = frame[frame['date'] >= CUTOFF].reset_index(drop=True)

    net = EnsembleNeuralPoisson(feat, n_models=N_ENSEMBLE)
    net.fit(train[feat], train['goals_scored'], epochs=300, batch_size=64, verbose=0)
    gbt = GBTPoissonModel(feat)
    gbt.fit(train[feat], train['goals_scored'])
    lam_net = net.predict_lambda(test[feat])
    lam_gbt = gbt.predict_lambda(test[feat])
    lam_m3 = W_NET * lam_net + (1 - W_NET) * lam_gbt
    elob = EloBaselineModel()

    pairs = {}
    for i, r in test.iterrows():
        pairs.setdefault((r['date'], frozenset((r['team'], r['opponent']))), []).append(i)
    pair_idx = [sorted(v, key=lambda k: test.loc[k, 'team']) for v in pairs.values() if len(v) == 2]
    pair_idx.sort(key=lambda ij: test.loc[ij[0], 'date'])   # chronological

    L = {'M1': [], 'M2': [], 'M3': []}
    for i, j in pair_idx:
        g1, g2 = test.loc[i, 'goals_scored'], test.loc[j, 'goals_scored']
        o = 0 if g1 > g2 else (1 if g1 == g2 else 2)
        l1, l2 = elob.predict_match(test.loc[i, 'elo'], test.loc[j, 'elo'])
        L['M1'].append(rps(wdl(l1, l2), o))
        L['M2'].append(rps(wdl(lam_net[i], lam_net[j]), o))
        L['M3'].append(rps(wdl(lam_m3[i], lam_m3[j]), o))
    L = {k: np.array(v) for k, v in L.items()}

    n = len(L['M1'])
    print(f"\nn = {n} held-out matches (chronological)")
    print(f"mean RPS:  M1 {L['M1'].mean():.4f}   M2 {L['M2'].mean():.4f}   M3 {L['M3'].mean():.4f}")
    print(f"\n{'pair':<12}{'mean ΔRPS':>11}{'DM':>9}{'p (2-sided)':>14}   verdict")
    for a, b in [('M2', 'M1'), ('M3', 'M1'), ('M3', 'M2')]:
        dm, p, dbar, _ = dm_test(L[a], L[b])
        winner = a if dbar < 0 else b
        sig = 'significant' if p < 0.05 else ('marginal' if p < 0.10 else 'n.s.')
        print(f"{a} vs {b:<6}{dbar:>+11.5f}{dm:>+9.2f}{p:>14.4g}   {winner} better · {sig}")


if __name__ == '__main__':
    main()
