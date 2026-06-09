"""
Conformal prediction for the 1X2 match outcome — LAC (Least Ambiguous set-valued
Classifier). Gives M3 its honest-uncertainty layer: at coverage 1-α, output the SET
of plausible outcomes and rule out the rest. Distribution-free; only assumes the
calibration matches are exchangeable with the matches we predict.

Score:  s_i = 1 - p_i[true_i]            (nonconformity = how surprised we were)
Quantile:  q̂ = ⌈(n+1)(1-α)⌉/n empirical quantile of the s_i
Set(x) = { o : p_x[o] ≥ 1 - q̂ }          → coverage  P(true ∈ Set) ≥ 1-α
"""
import numpy as np

OUTCOMES = ['home', 'draw', 'away']   # index 0/1/2


def lac_threshold(cal_probs, cal_true_idx, alpha=0.10):
    """Calibrate the LAC probability threshold τ from held-out matches.
    cal_probs: (n,3) predicted [home,draw,away]; cal_true_idx: (n,) in {0,1,2}."""
    cal_probs = np.asarray(cal_probs, dtype=float)
    idx = np.asarray(cal_true_idx, dtype=int)
    n = len(idx)
    scores = 1.0 - cal_probs[np.arange(n), idx]            # nonconformity
    level = min(1.0, np.ceil((n + 1) * (1 - alpha)) / n)   # finite-sample correction
    qhat = np.quantile(scores, level, method='higher')
    return float(1.0 - qhat)                               # τ: keep outcomes with p ≥ τ


def prediction_set(probs, tau):
    """Outcome indices with prob ≥ τ. Never empty (fall back to the argmax)."""
    probs = np.asarray(probs, dtype=float)
    s = [int(o) for o in range(len(probs)) if probs[o] >= tau]
    return s or [int(np.argmax(probs))]
