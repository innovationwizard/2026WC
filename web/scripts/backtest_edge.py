#!/usr/bin/env python3
"""
backtest_edge.py — does any model find betting EDGE vs Pinnacle? (Batch E)

Calibration is not the goal (Pinnacle wins that). The research (Hubáček & Šír 2023;
Koopman & Lit 2019) says a model can still profit if it identifies the DIRECTION of the
market's mispricing — capturing signal Pinnacle underprices. We test that directly.

Method (Koopman-Lit "quality bet" strategy), OUT-OF-SAMPLE on frozen kickoff predictions:
  For each finalized match with a Pinnacle line, for each outcome o:
      EV(o) = p_model(o) · decimal_odds(o) − 1        (odds carry Pinnacle's vig)
  Bet 1 unit on every outcome whose EV(o) > τ (a "quality" / value bet). Settle at the
  real result. Sweep τ and report bets / staked / returned / ROI per model line. w=flat
  random betting loses the vig (~−overround); the model must clear that AND profit.

  python web/scripts/backtest_edge.py
"""
import os, csv, json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
MATCHES = os.path.join(ROOT, 'web', 'static', 'data', 'matches.json')
MARKET = os.path.join(ROOT, 'web', 'data', 'market_odds.csv')
OUTCOMES = ['home', 'draw', 'away']
LINES = ['M1', 'M2', 'M3', 'M3_frozen']  # model lines to test (not Mercado — that IS the market)


def load_odds():
    """{id: {home,draw,away}} decimal odds (with vig)."""
    out = {}
    with open(MARKET, newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            try:
                o1, ox, o2 = float(r['odd_1']), float(r['odd_X']), float(r['odd_2'])
            except (ValueError, KeyError, TypeError):
                continue
            if o1 > 1 and ox > 1 and o2 > 1:
                out[r['id']] = {'home': o1, 'draw': ox, 'away': o2}
    return out


def main():
    matches = json.load(open(MATCHES, encoding='utf-8'))['matches']
    odds = load_odds()

    # Samples: (model_probs_by_line, decimal_odds, actual_outcome)
    samples = []
    overrounds = []
    for m in matches:
        if m['status'] != 'finalizado' or not m.get('result'):
            continue
        od = odds.get(m['id'])
        if not od:
            continue
        overrounds.append(sum(1 / od[o] for o in OUTCOMES) - 1)
        preds = {}
        for L in LINES:
            p = (m['predictions'].get(L) or {}).get('probs')
            if p:
                preds[L] = p
        samples.append((preds, od, m['result']['outcome']))

    n = len(samples)
    avg_vig = 100 * sum(overrounds) / len(overrounds) if overrounds else 0
    print(f"Edge backtest: {n} finalized matches with a Pinnacle line · avg overround (vig) {avg_vig:.1f}%\n")

    taus = [0.0, 0.05, 0.10, 0.15, 0.20, 0.30, 0.40]
    for L in LINES:
        print(f"── {L} ──")
        print(f"   {'τ':>5} {'bets':>5} {'staked':>7} {'return':>7} {'ROI':>8}")
        best = None
        for tau in taus:
            staked = ret = 0.0
            bets = 0
            for preds, od, actual in samples:
                p = preds.get(L)
                if not p:
                    continue
                for o in OUTCOMES:
                    ev = p[o] * od[o] - 1
                    if ev > tau:
                        bets += 1; staked += 1
                        if o == actual:
                            ret += od[o]
            roi = (ret - staked) / staked if staked else 0.0
            print(f"   {tau:>5.2f} {bets:>5d} {staked:>7.0f} {ret:>7.1f} {roi*100:>7.1f}%")
            if staked >= 10 and (best is None or roi > best[1]):
                best = (tau, roi, bets)
        if best:
            print(f"   best (≥10 bets): τ={best[0]}  ROI {best[1]*100:.1f}%  ({best[2]} bets)")
        print()

    print("Reading: positive ROI that persists across τ (with enough bets) = genuine edge vs Pinnacle.")
    print("Flat/random betting returns ≈ −vig. Beating a sharp CLOSING line is very hard (research finding #5);")
    print("treat small-sample positive ROI with caution — it is an in-tournament signal, not a proven system.")


if __name__ == '__main__':
    main()
