#!/usr/bin/env python3
"""
build_narrative.py — emit web/static/data/narrative.json for the /historia story.
Assembles REAL model output (no mock):
  - champion_dist : M2 headline champion distribution (Act 1 histogram target)
  - champion_3way : M1/M2/M3 champion odds for the top teams (Act 2 agreement)
  - backtest      : held-out RPS for M1/M2/M3 (Act 2 'measured skill')   ← from eval.json
  - calibration   : reliability curve for M3 (Act 3)                      ← from eval.json

Run:  .venv/bin/python web/scripts/build_narrative.py   (after v2/eval_export.py)
"""
import json, os, datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
_V2 = os.path.join(ROOT, 'v2', 'output', 'predictions.json')
PRED = _V2 if os.path.exists(_V2) else os.path.join(ROOT, 'output', 'predictions.json')
EVAL = os.path.join(ROOT, 'v2', 'output', 'eval.json')
OUT = os.path.join(ROOT, 'web', 'static', 'data', 'narrative.json')


def main():
    pred = json.load(open(PRED))
    m2 = pred['team_probabilities']
    m1 = pred.get('elo_baseline', {})
    m3 = pred.get('m3_team_probabilities', {})

    dist = sorted(((t, p['champion']) for t, p in m2.items()), key=lambda x: -x[1])
    champion_dist = [{'team': t, 'p': round(p, 4)} for t, p in dist[:16]]
    top8 = [t for t, _ in dist[:8]]
    champion_3way = [{
        'team': t,
        'M1': round(m1.get(t, {}).get('champion', 0), 4),
        'M2': round(m2[t]['champion'], 4),
        'M3': round(m3.get(t, {}).get('champion', 0), 4),
    } for t in top8]

    ev = json.load(open(EVAL)) if os.path.exists(EVAL) else {}

    out = {
        'generated': datetime.date.today().isoformat(),
        'source': 'v2/output/predictions.json + eval.json (held-out backtest)',
        'champion_dist': champion_dist,
        'champion_3way': champion_3way,
        'backtest': {'n_matches': ev.get('n_matches'), 'cutoff': ev.get('cutoff'), 'rps': ev.get('rps', {})},
        'calibration': ev.get('calibration', []),
        'tau_by_coverage': ev.get('tau_by_coverage', {}),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"wrote {OUT}")
    print(f"  champion_3way top: {champion_3way[0] if champion_3way else '—'}")
    print(f"  backtest rps: {out['backtest']['rps']} | calibration pts: {len(out['calibration'])}")


if __name__ == '__main__':
    main()
