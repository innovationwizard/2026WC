#!/usr/bin/env python3
"""
Emit v2/output/eval.json — held-out validation artifacts for the narrative site.
Trains M2 (net ensemble) + GBT on the train split, evaluates on held-out (>= CUTOFF):
  • RPS for M1 (Elo) / M2 (net) / M3 (blend) — the Act-2 'measured skill' numbers
  • a calibration curve for M3 (pooled one-vs-rest) — the Act-3 'when I say 70%...' chart
Real, reproducible — no hardcoded numbers in the story.

Run:  .venv/bin/python v2/eval_export.py
"""
import sys, os, json, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from feature_engine import build_training_data
from neural_poisson import EnsembleNeuralPoisson, GBTPoissonModel, EloBaselineModel
from backtest import wdl, rps, MIN_DATE, CUTOFF

N_ENSEMBLE = 5
W_NET = 0.5


def main():
    df = pd.read_csv(os.path.join(os.path.dirname(__file__), '..', 'results.csv'))
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    X, y, elo, tv, frame = build_training_data(df, min_date=MIN_DATE, return_frame=True)
    feat = list(X.columns)
    frame['date'] = pd.to_datetime(frame['date'])
    train = frame[frame['date'] < CUTOFF]
    test = frame[frame['date'] >= CUTOFF].reset_index(drop=True)
    print(f"train {len(train):,} | test {len(test):,}")

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

    rps_acc = {'M1': [], 'M2': [], 'M3': []}
    calib = []  # (predicted prob of an outcome, did it happen) — pooled over 3 outcomes
    for i, j in pair_idx:
        g1, g2 = test.loc[i, 'goals_scored'], test.loc[j, 'goals_scored']
        o = 0 if g1 > g2 else (1 if g1 == g2 else 2)
        l1, l2 = elob.predict_match(test.loc[i, 'elo'], test.loc[j, 'elo'])
        rps_acc['M1'].append(rps(wdl(l1, l2), o))
        rps_acc['M2'].append(rps(wdl(lam_net[i], lam_net[j]), o))
        pm3 = wdl(lam_m3[i], lam_m3[j])
        rps_acc['M3'].append(rps(pm3, o))
        for oi, p in enumerate(pm3):
            calib.append((p, 1.0 if oi == o else 0.0))

    calib = np.array(calib)
    bins = np.linspace(0, 1, 11)
    curve = []
    for b in range(10):
        m = (calib[:, 0] >= bins[b]) & (calib[:, 0] < bins[b + 1])
        if m.sum() >= 20:
            curve.append({'p': round(float(calib[m, 0].mean()), 3),
                          'freq': round(float(calib[m, 1].mean()), 3),
                          'n': int(m.sum())})

    out = {
        'cutoff': CUTOFF, 'n_matches': len(pair_idx),
        'rps': {k: round(float(np.mean(v)), 4) for k, v in rps_acc.items()},
        'calibration': curve,
    }
    p = os.path.join(os.path.dirname(__file__), 'output', 'eval.json')
    with open(p, 'w') as f:
        json.dump(out, f, indent=2)
    print('wrote', p)
    print('RPS:', out['rps'], '| calibration bins:', len(curve))


if __name__ == '__main__':
    main()
