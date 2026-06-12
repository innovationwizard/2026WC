#!/usr/bin/env python3
"""
Estimate the Dixon-Coles dependence parameter ρ for OUR model (conditional on the
model's λ's) over held-out matches, and show how much it actually changes the
low-score cells and W/D/L. This is the "is it even worth it?" measurement.

ρ enters only the four low-score cells via the DC correction τ:
  τ(0,0)=1−λμρ   τ(0,1)=1+λρ   τ(1,0)=1+μρ   τ(1,1)=1−ρ   (else 1)
ρ̂ = argmax Σ log τ(home,away)  (the Poisson factors don't depend on ρ).

Run:  .venv/bin/python v2/dc_estimate.py
"""
import sys, os, math, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
from scipy.optimize import minimize_scalar
from scipy import stats
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from feature_engine import build_training_data
from neural_poisson import EnsembleNeuralPoisson, GBTPoissonModel
from backtest import MIN_DATE, CUTOFF

N_ENSEMBLE, W_NET = 5, 0.5


def tau(x, y, lh, la, rho):
    if x == 0 and y == 0: return 1 - lh * la * rho
    if x == 0 and y == 1: return 1 + lh * rho
    if x == 1 and y == 0: return 1 + la * rho
    if x == 1 and y == 1: return 1 - rho
    return 1.0


def neg_ll(rho, rows):
    s = 0.0
    for x, y, lh, la in rows:
        t = tau(x, y, lh, la, rho)
        if t <= 0: return 1e9
        s += math.log(t)
    return -s


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
    gbt = GBTPoissonModel(feat); gbt.fit(train[feat], train['goals_scored'])
    lam = W_NET * net.predict_lambda(test[feat]) + (1 - W_NET) * gbt.predict_lambda(test[feat])
    test = test.assign(lam=lam)

    pairs = {}
    for i, r in test.iterrows():
        pairs.setdefault((r['date'], frozenset((r['team'], r['opponent']))), []).append(i)
    rows, n_low = [], 0
    for v in pairs.values():
        if len(v) != 2: continue
        i, j = sorted(v, key=lambda k: test.loc[k, 'team'])
        x, yy = int(test.loc[i, 'goals_scored']), int(test.loc[j, 'goals_scored'])
        rows.append((x, yy, test.loc[i, 'lam'], test.loc[j, 'lam']))
        if x <= 1 and yy <= 1: n_low += 1

    res = minimize_scalar(neg_ll, args=(rows,), bounds=(-0.3, 0.3), method='bounded')
    rho = res.x
    ll1, ll0 = -neg_ll(rho, rows), -neg_ll(0.0, rows)
    lr = 2 * (ll1 - ll0)                      # likelihood-ratio vs ρ=0
    p_lr = stats.chi2.sf(lr, df=1)
    # crude SE from the curvature (finite diff of the score)
    h = 1e-3
    info = (neg_ll(rho + h, rows) - 2 * neg_ll(rho, rows) + neg_ll(rho - h, rows)) / h**2
    se = 1 / math.sqrt(info) if info > 0 else float('nan')

    print(f"\nn matches = {len(rows)}   (low-score, both ≤1 goal = {n_low})")
    print(f"ρ̂ = {rho:+.4f}   SE ≈ {se:.4f}   LR vs ρ=0: χ²={lr:.2f}, p={p_lr:.3g}")

    # Effect on the example match (México 1.74 vs Sudáfrica 0.86, M3 λ)
    lh, la = 1.74, 0.86
    def pmf(k, l): return math.exp(-l) * l**k / math.factorial(k)
    print(f"\nExample México({lh}) vs Sudáfrica({la}) — independiente → Dixon-Coles(ρ={rho:+.3f}):")
    for (x, yy) in [(0, 0), (1, 0), (0, 1), (1, 1)]:
        ind = pmf(x, lh) * pmf(yy, la)
        dc = ind * tau(x, yy, lh, la, rho)
        print(f"  {x}-{yy}:  {ind*100:5.2f}%  →  {dc*100:5.2f}%   (×{tau(x,yy,lh,la,rho):.3f})")
    # W/D/L shift
    for label, use_dc in [('independiente', False), ('Dixon-Coles', True)]:
        ph = pdr = pa = 0.0
        for x in range(11):
            for yy in range(11):
                p = pmf(x, lh) * pmf(yy, la) * (tau(x, yy, lh, la, rho) if use_dc else 1)
                ph += p if x > yy else 0; pdr += p if x == yy else 0; pa += p if x < yy else 0
        tot = ph + pdr + pa
        print(f"  W/D/L {label:13s}: {ph/tot*100:.1f} / {pdr/tot*100:.1f} / {pa/tot*100:.1f}")


if __name__ == '__main__':
    main()
