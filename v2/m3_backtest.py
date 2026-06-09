#!/usr/bin/env python3
"""
M3 weight selection — backtest the Conjunto blend.
Trains the M2 net-ensemble and the GBT on the train split, then sweeps the blend
weight w (λ = w·net + (1-w)·gbt) and reports held-out RPS for each. Picks the w
that minimizes RPS — the data decides, not taste. w=1 is pure M2; w=0 is pure GBT.

Run:  .venv/bin/python v2/m3_backtest.py
"""
import sys, os, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from feature_engine import build_training_data
from neural_poisson import EnsembleNeuralPoisson, GBTPoissonModel
from backtest import wdl, rps, MIN_DATE, CUTOFF

N_ENSEMBLE = 5  # smaller for the sweep; production uses 50


def main():
    df = pd.read_csv(os.path.join(os.path.dirname(__file__), '..', 'results.csv'))
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    X, y, elo, tv, frame = build_training_data(df, min_date=MIN_DATE, return_frame=True)
    feat = list(X.columns)
    frame['date'] = pd.to_datetime(frame['date'])
    train = frame[frame['date'] < CUTOFF]
    test = frame[frame['date'] >= CUTOFF].reset_index(drop=True)
    print(f"train {len(train):,} | test {len(test):,}")

    print(f"Training net-ensemble (N={N_ENSEMBLE}) + GBT on train split...")
    net = EnsembleNeuralPoisson(feat, n_models=N_ENSEMBLE)
    net.fit(train[feat], train['goals_scored'], epochs=300, batch_size=64, verbose=0)
    gbt = GBTPoissonModel(feat)
    gbt.fit(train[feat], train['goals_scored'])

    lam_net = net.predict_lambda(test[feat])
    lam_gbt = gbt.predict_lambda(test[feat])

    # pair the two team-rows per match (by reset index)
    pairs = {}
    for i, r in test.iterrows():
        pairs.setdefault((r['date'], frozenset((r['team'], r['opponent']))), []).append(i)
    pair_idx = [sorted(v, key=lambda k: test.loc[k, 'team']) for v in pairs.values() if len(v) == 2]

    def mean_rps(lam):
        out = []
        for i, j in pair_idx:
            g1, g2 = test.loc[i, 'goals_scored'], test.loc[j, 'goals_scored']
            o = 0 if g1 > g2 else (1 if g1 == g2 else 2)
            out.append(rps(wdl(lam[i], lam[j]), o))
        return float(np.mean(out))

    print(f"\n  {'w_net':>6}  {'RPS':>8}")
    best = (None, 9.9)
    for w in [0.0, 0.25, 0.4, 0.5, 0.6, 0.75, 1.0]:
        r = mean_rps(w * lam_net + (1 - w) * lam_gbt)
        tag = "  ← pure GBT" if w == 0 else ("  ← pure net (M2)" if w == 1 else "")
        print(f"  {w:6.2f}  {r:8.4f}{tag}")
        if r < best[1]:
            best = (w, r)
    print(f"\n  BEST w_net = {best[0]}  (held-out RPS {best[1]:.4f}) over {len(pair_idx)} matches")


if __name__ == '__main__':
    main()
