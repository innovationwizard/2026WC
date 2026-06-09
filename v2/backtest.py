#!/usr/bin/env python3
"""
Backtest harness (P1) — the measuring stick.
Temporal split: train on matches < CUTOFF, test on scored internationals >= CUTOFF
(held-out, the model never saw them). Reports Ranked Probability Score (RPS, lower
is better) for the M2 neural ensemble vs the Elo baseline. This is what VALIDATES a
feature change: does it lower held-out RPS? (Not: does Spain's % look like consensus.)

Features are point-in-time (Elo sequential; rolling shifted) so there is no leakage.
Run:  .venv/bin/python v2/backtest.py
"""
import sys, os, math, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from feature_engine import build_training_data
from neural_poisson import EnsembleNeuralPoisson, EloBaselineModel

MIN_DATE = '2018-01-01'   # training pool start
CUTOFF   = '2025-01-01'   # train < CUTOFF ; test >= CUTOFF
N_ENSEMBLE = 5


def poisson_pmf(k, lam):
    return math.exp(-lam) * lam ** k / math.factorial(k)


def wdl(lh, la, maxg=10):
    """P(team1 win), P(draw), P(team1 lose) from independent Poisson(λ)."""
    h = [poisson_pmf(i, lh) for i in range(maxg + 1)]
    a = [poisson_pmf(j, la) for j in range(maxg + 1)]
    pw = pd_ = pl = 0.0
    for i in range(maxg + 1):
        for j in range(maxg + 1):
            p = h[i] * a[j]
            if i > j:  pw += p
            elif i == j: pd_ += p
            else: pl += p
    return pw, pd_, pl


def rps(probs, outcome_idx):
    """RPS for ordered 3-outcome [win, draw, lose]. outcome_idx in {0,1,2}."""
    o = [0, 0, 0]; o[outcome_idx] = 1
    cp = co = s = 0.0
    for i in range(2):
        cp += probs[i]; co += o[i]; s += (cp - co) ** 2
    return s / 2


def brier(probs, outcome_idx):
    o = [0, 0, 0]; o[outcome_idx] = 1
    return sum((probs[i] - o[i]) ** 2 for i in range(3)) / 3


def main():
    df = pd.read_csv(os.path.join(os.path.dirname(__file__), '..', 'results.csv'))
    df['date'] = pd.to_datetime(df['date'], errors='coerce')

    print(f"Building features (min_date={MIN_DATE})...")
    X, y, elo, tv, frame = build_training_data(df, min_date=MIN_DATE, return_frame=True)
    feat = list(X.columns)
    frame['date'] = pd.to_datetime(frame['date'])
    train = frame[frame['date'] < CUTOFF]
    test = frame[frame['date'] >= CUTOFF].reset_index(drop=True)
    print(f"  train rows {len(train):,} (<{CUTOFF}) | test rows {len(test):,} (>={CUTOFF})")

    print(f"Training ensemble (N={N_ENSEMBLE}) on the train split...")
    model = EnsembleNeuralPoisson(feat, n_models=N_ENSEMBLE)
    model.fit(train[feat], train['goals_scored'], epochs=300, batch_size=64, verbose=0)

    test = test.assign(lam=model.predict_lambda(test[feat]))
    elob = EloBaselineModel()

    # Pair the two team-rows per match.
    matches = {}
    for _, r in test.iterrows():
        matches.setdefault((r['date'], frozenset((r['team'], r['opponent']))), []).append(r)

    rps_m2, rps_elo, br_m2, br_elo = [], [], [], []
    for rows in matches.values():
        if len(rows) != 2:
            continue
        r1, r2 = sorted(rows, key=lambda r: r['team'])
        g1, g2 = r1['goals_scored'], r2['goals_scored']
        outcome = 0 if g1 > g2 else (1 if g1 == g2 else 2)
        pm2 = wdl(r1['lam'], r2['lam'])
        rps_m2.append(rps(pm2, outcome)); br_m2.append(brier(pm2, outcome))
        l1, l2 = elob.predict_match(r1['elo'], r2['elo'])
        pe = wdl(l1, l2)
        rps_elo.append(rps(pe, outcome)); br_elo.append(brier(pe, outcome))

    n = len(rps_m2)
    print(f"\n=== BACKTEST ({n} held-out matches, >= {CUTOFF}) ===")
    print(f"  M2 ensemble : RPS {np.mean(rps_m2):.4f}  Brier {np.mean(br_m2):.4f}")
    print(f"  Elo baseline: RPS {np.mean(rps_elo):.4f}  Brier {np.mean(br_elo):.4f}")
    print(f"  (RPS lower = better; strong published models ~0.19–0.21)")
    better = "M2 beats Elo" if np.mean(rps_m2) < np.mean(rps_elo) else "Elo beats M2"
    print(f"  → {better} by {abs(np.mean(rps_m2)-np.mean(rps_elo)):.4f} RPS")


if __name__ == '__main__':
    main()
