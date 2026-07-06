#!/usr/bin/env python3
"""
backtest_blend_w.py — find the optimal model↔market blend weight w (Batch B).

Blend = logarithmic opinion pool of the model (M3) and Pinnacle:
    p_blend(o) ∝ p_M3(o)^(1-w) · p_pinnacle(o)^w,   renormalized over {home,draw,away}.

Over every finalized match that has BOTH an M3 forecast and a Pinnacle line, we sweep
w ∈ [0,1] and score the blend against the actual 90-min outcome with BOTH proper scoring
rules the research recommends: RPS (ordinal) and log-loss / ignorance. w=0 is the pure
model; w=1 is pure Pinnacle. Reports the curve and the w* that minimizes each metric.

  python web/scripts/backtest_blend_w.py
"""
import os, json, math

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
MATCHES = os.path.join(ROOT, 'web', 'static', 'data', 'matches.json')
OUTCOMES = ['home', 'draw', 'away']


def rps(p, outcome):
    """Ranked Probability Score for ordered {home,draw,away}. Lower = better."""
    o = {'home': [1, 0, 0], 'draw': [0, 1, 0], 'away': [0, 0, 1]}[outcome]
    cp = co = s = 0.0
    for i in range(2):
        cp += p[i]; co += o[i]
        s += (cp - co) ** 2
    return s / 2


def logloss(p, outcome):
    """Ignorance / log score: -log2 p[outcome]. Lower = better."""
    idx = OUTCOMES.index(outcome)
    return -math.log2(max(p[idx], 1e-12))


def blend(m3, merc, w):
    """Log opinion pool, renormalized."""
    raw = [m3[i] ** (1 - w) * merc[i] ** w for i in range(3)]
    s = sum(raw) or 1.0
    return [x / s for x in raw]


def main():
    matches = json.load(open(MATCHES, encoding='utf-8'))['matches']
    samples = []
    for m in matches:
        if m['status'] != 'finalizado' or not m.get('result'):
            continue
        m3 = (m['predictions'].get('M3') or {}).get('probs')
        merc = (m['predictions'].get('Mercado') or {}).get('probs')
        if not m3 or not merc:
            continue
        samples.append(([m3['home'], m3['draw'], m3['away']],
                        [merc['home'], merc['draw'], merc['away']],
                        m['result']['outcome']))

    print(f"Backtest sample: {len(samples)} finalized matches with both M3 and Pinnacle\n")
    print(f"{'w':>4}  {'RPS':>8}  {'logloss':>8}")
    grid = [round(i * 0.05, 2) for i in range(21)]
    rows = []
    for w in grid:
        r = sum(rps(blend(a, b, w), o) for a, b, o in samples) / len(samples)
        l = sum(logloss(blend(a, b, w), o) for a, b, o in samples) / len(samples)
        rows.append((w, r, l))
        bar = '█' * int((r) * 200)
        print(f"{w:>4.2f}  {r:>8.4f}  {l:>8.4f}  {bar}")

    w_rps = min(rows, key=lambda x: x[1])
    w_ll = min(rows, key=lambda x: x[2])
    print(f"\nPure model (w=0):    RPS {rows[0][1]:.4f}  logloss {rows[0][2]:.4f}")
    print(f"Pure Pinnacle (w=1): RPS {rows[-1][1]:.4f}  logloss {rows[-1][2]:.4f}")
    print(f"Best RPS:      w* = {w_rps[0]}  (RPS {w_rps[1]:.4f})")
    print(f"Best logloss:  w* = {w_ll[0]}  (logloss {w_ll[2]:.4f})")


if __name__ == '__main__':
    main()
