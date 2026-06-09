#!/usr/bin/env python3
"""
Validate M3's conformal coverage. Proper-train < 2024 | calibrate on 2024 | test on 2025+.
If the LAC threshold is right, the (1-α) prediction set should cover ~(1-α) of held-out
match outcomes. Also reports average set size (smaller = more confident).

Run:  .venv/bin/python v2/m3_conformal_validate.py
"""
import sys, os, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from feature_engine import build_training_data
from neural_poisson import ConjuntoModel
from backtest import wdl, MIN_DATE
from conformal import lac_threshold, prediction_set

CAL_CUTOFF, TEST_CUTOFF = '2024-01-01', '2025-01-01'
N_ENSEMBLE = 5


def match_units(frame, lam):
    """Pair team-rows into matches → list of (probs[home,draw,away], outcome_idx)."""
    pairs = {}
    for i, r in frame.iterrows():
        pairs.setdefault((r['date'], frozenset((r['team'], r['opponent']))), []).append(i)
    units = []
    for v in pairs.values():
        if len(v) != 2:
            continue
        i, j = sorted(v, key=lambda k: frame.loc[k, 'team'])
        probs = list(wdl(lam[i], lam[j]))
        g1, g2 = frame.loc[i, 'goals_scored'], frame.loc[j, 'goals_scored']
        o = 0 if g1 > g2 else (1 if g1 == g2 else 2)
        units.append((probs, o))
    return units


def main():
    df = pd.read_csv(os.path.join(os.path.dirname(__file__), '..', 'results.csv'))
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    X, y, elo, tv, frame = build_training_data(df, min_date=MIN_DATE, return_frame=True)
    feat = list(X.columns)
    frame['date'] = pd.to_datetime(frame['date'])
    ptrain = frame[frame['date'] < CAL_CUTOFF]
    cal = frame[(frame['date'] >= CAL_CUTOFF) & (frame['date'] < TEST_CUTOFF)].reset_index(drop=True)
    test = frame[frame['date'] >= TEST_CUTOFF].reset_index(drop=True)
    print(f"proper-train {len(ptrain):,} | calibration {len(cal):,} | test {len(test):,} rows")

    print(f"Training Conjunto (N={N_ENSEMBLE}, w=0.5) on proper-train...")
    model = ConjuntoModel(feat, n_models=N_ENSEMBLE, w_net=0.5)
    model.fit(ptrain[feat], ptrain['goals_scored'], epochs=300, batch_size=64, verbose=0)

    cal_units = match_units(cal, model.predict_lambda(cal[feat]))
    test_units = match_units(test, model.predict_lambda(test[feat]))
    cal_probs = np.array([u[0] for u in cal_units])
    cal_true = np.array([u[1] for u in cal_units])
    print(f"calibration matches {len(cal_units)} | test matches {len(test_units)}\n")

    print(f"  {'target':>7} {'coverage':>9} {'avg set':>8} {'τ':>6}")
    for alpha in [0.10, 0.20]:
        tau = lac_threshold(cal_probs, cal_true, alpha)
        covered, sizes = 0, []
        for probs, o in test_units:
            ps = prediction_set(probs, tau)
            covered += (o in ps)
            sizes.append(len(ps))
        n = len(test_units)
        print(f"  {1-alpha:6.0%}  {covered/n:8.1%}  {np.mean(sizes):7.2f}  {tau:6.3f}")
    print("\n(coverage ≈ target ⇒ the guarantee holds; avg set < 3 ⇒ it's informative)")


if __name__ == '__main__':
    main()
