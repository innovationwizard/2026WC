# /v2 — model fork (v2)

A working copy of the WC2026 prediction pipeline, forked from the **locked** `v1.0-baseline`
(root `*.py` are frozen — never edit them). All model improvements happen HERE.

- Reads the locked root `../results.csv` (read-only).
- Writes to `v2/output/` (isolated from baseline `output/`).
- Run: `.venv/bin/python v2/main.py`  → `v2/output/predictions.json`
- Goal of this fork: **P2 (Dixon-Coles + time-decay) to fix Bug A — un-bury Spain in M2.**
