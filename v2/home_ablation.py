#!/usr/bin/env python3
"""
Counterfactual: how much does the model weight México's home/host status in
México vs Sudáfrica? Predict the match under several settings of the home features,
and show what an explicit home-advantage multiplier would do.
Run:  .venv/bin/python v2/home_ablation.py
"""
import sys, os, math, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from feature_engine import build_training_data, get_team_features_for_prediction
from neural_poisson import EnsembleNeuralPoisson, GBTPoissonModel

HOME, AWAY = 'Mexico', 'South Africa'


def wdl(lh, la, mx=10):
    ph = pd_ = pa = 0.0
    hp = [math.exp(-lh) * lh**i / math.factorial(i) for i in range(mx + 1)]
    ap = [math.exp(-la) * la**j / math.factorial(j) for j in range(mx + 1)]
    for i in range(mx + 1):
        for j in range(mx + 1):
            p = hp[i] * ap[j]
            if i > j: ph += p
            elif i == j: pd_ += p
            else: pa += p
    return ph, pd_, pa


def main():
    df = pd.read_csv(os.path.join(os.path.dirname(__file__), '..', 'results.csv'))
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    X, y, elo, tv = build_training_data(df, min_date='2020-01-01')
    feat = list(X.columns)
    net = EnsembleNeuralPoisson(feat, n_models=5)
    net.fit(X, y, epochs=300, batch_size=64, verbose=0)
    gbt = GBTPoissonModel(feat); gbt.fit(X, y)

    def lam(fd):
        d = pd.DataFrame([{**{f: 0.0 for f in feat}, **fd}])[feat]
        return 0.5 * net.predict_lambda(d)[0] + 0.5 * gbt.predict_lambda(d)[0]

    fm = get_team_features_for_prediction(tv, elo, HOME, AWAY)
    fs = get_team_features_for_prediction(tv, elo, AWAY, HOME)

    def show(label, fmh, fsa, mult=1.0):
        lh, la = lam(fmh) * mult, lam(fsa)
        w, d, a = wdl(lh, la)
        print(f"  {label:38s} λ {lh:.2f}–{la:.2f}   L/E/V {w*100:4.0f}/{d*100:3.0f}/{a*100:4.0f}")
        return w

    print(f"\nMéxico is_host={fm.get('is_host')}  is_neutral={fm.get('is_neutral')}  (como se publica)\n")
    base = show('Como se publica (host=1, neutral=1)', fm, fs)
    nohost = show('Contrafactual: is_host = 0', {**fm, 'is_host': 0.0}, fs)
    nonneu = show('Contrafactual: is_neutral = 0 (local)', {**fm, 'is_neutral': 0.0}, {**fs, 'is_neutral': 0.0})
    print("\n  — Con un factor de ventaja local explícito sobre λ de México —")
    for g in (1.15, 1.25, 1.35):
        show(f'×{g} en λ local (ventaja ~{(g-1)*100:.0f}%)', fm, fs, mult=g)

    print(f"\n  Peso del 'host' que el modelo YA aplica: {(base-nohost)*100:+.1f} pp de victoria")
    print(f"  Efecto de marcar el partido como local (neutral=0): {(nonneu-base)*100:+.1f} pp")


if __name__ == '__main__':
    main()
