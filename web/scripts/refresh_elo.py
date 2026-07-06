#!/usr/bin/env python3
"""
refresh_elo.py — fast, net-free Elo refresh from the (synced) training corpus.

After sync_results_to_corpus.py feeds the finals into results.csv, this recomputes the
Elo ratings the SAME way v2/main.py does (sort by date → compute_elo, which already uses
K=60 for the World Cup) and writes ONLY the `elo_ratings` block back into predictions.json.

Nets (M2/M3) are untouched — this is the cheap "online overlay": M1 (the Elo foil, computed
in build_matches from elo_ratings) becomes tournament-aware immediately; M2/M3 update on the
next full v2 rerun (decision D2). Run after each round, then rebuild matches.json.

  python web/scripts/refresh_elo.py            # dry-run: show top Elo movers
  python web/scripts/refresh_elo.py --apply     # write elo_ratings into predictions.json
"""
import os, sys, json, argparse
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'v2'))
from feature_engine import compute_elo, WC_TEAMS  # noqa: E402

CORPUS = os.path.join(ROOT, 'results.csv')
PRED = os.path.join(ROOT, 'v2', 'output', 'predictions.json')
FROZEN = os.path.join(ROOT, 'v2', 'output', 'predictions_frozen_pretournament.json')


def compute_ratings():
    """Replicates v2/main.py's Elo: sort corpus by date, then compute_elo (K=60 for WC)."""
    df = pd.read_csv(CORPUS)
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.sort_values('date').reset_index(drop=True)
    elo_ratings, _ = compute_elo(df)
    return {t: round(elo_ratings.get(t, 1500), 1) for t in WC_TEAMS}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--apply', action='store_true', help="write elo_ratings into predictions.json")
    args = ap.parse_args()

    new = compute_ratings()
    # Baseline = the frozen pre-tournament ratings (fallback to current predictions.json).
    base_path = FROZEN if os.path.exists(FROZEN) else PRED
    base = json.load(open(base_path)).get('elo_ratings', {})

    movers = sorted(
        ((t, new[t], base.get(t), round(new[t] - base[t], 1)) for t in new if t in base),
        key=lambda x: abs(x[3]), reverse=True,
    )
    print(f"Elo refreshed from {os.path.relpath(CORPUS, ROOT)} (baseline: {os.path.relpath(base_path, ROOT)})")
    print("Top movers (finals effect):")
    for t, n, b, d in movers[:12]:
        print(f"    {t:26s} {b:6.1f} → {n:6.1f}   {'+' if d >= 0 else ''}{d}")

    if not args.apply:
        print("\n(dry-run — use --apply to write elo_ratings into predictions.json)")
        return

    pred = json.load(open(PRED))
    pred['elo_ratings'] = new
    with open(PRED, 'w') as f:
        json.dump(pred, f, indent=2, default=str)
    print(f"\n✓ wrote elo_ratings ({len(new)} teams) into {os.path.relpath(PRED, ROOT)} (nets/M2/M3 untouched)")


if __name__ == '__main__':
    main()
