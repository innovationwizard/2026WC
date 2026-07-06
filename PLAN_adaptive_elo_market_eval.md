# Implementation Plan — Adaptive Elo + Market Blend + Dual-Line Evaluation

**Derived from:** [RESEARCH_in_tournament_updating.md](RESEARCH_in_tournament_updating.md) (the 4-step proposal).
**Live progress tracker:** [PROGRESS_adaptive_elo_market_eval.md](PROGRESS_adaptive_elo_market_eval.md) — update it after every sub-batch.
**Created:** 2026-07-05.

> **Goal.** Stop the models being frozen at pre-tournament strength. Layer a fast, principled online update on top (Elo/form absorb the finals), add a market-informed blend line, and — critically — keep the frozen pre-tournament forecast as a clean benchmark and *measure* whether updating actually helps (RPS **and** log-loss vs Pinnacle). This is the research's recommended "have both and measure" design.

---

## Operating rules for this plan (read every batch)

- **Tiny, reversible sub-batches.** One concept per sub-batch. Verify before moving on.
- **The frozen pre-tournament forecast is sacred.** Snapshot it (A0) before anything mutates Elo. It is the benchmark; never overwrite it.
- **No mock data. Production-first.** Real `results_live.csv` / `results.csv` only.
- **Jorge drives git.** I prepare staging lists; I do not commit/push.
- **Update [PROGRESS](PROGRESS_adaptive_elo_market_eval.md) after each sub-batch** — status, what changed, how to verify, how to roll back. If the conversation compacts, the tracker is the source of truth.

---

## Key code facts (inspected 2026-07-05 — ground truth)

- **`v2/feature_engine.py:99 compute_elo`** already uses `K_MAP['FIFA World Cup'] = 60` and a goal-margin multiplier `g = 1 + ln(gd)`; updates ratings per match **but skips rows where `home_score` is NA** (line 121). → Finals don't move Elo only because the corpus rows are NA.
- **`results.csv`** = training corpus (~49k rows). The 72 WC group fixtures are present with **`NA` scores**; the **KO matches are absent** entirely (latest date 2026-06-27).
- **`results_live.csv`** = live results (group filled + KO rows with `advances`), display-only, never read by training.
- **M1 (Elo foil)** is computed in `web/scripts/build_matches.py` from `predictions.json['elo_ratings']`. **M2/M3** come from the trained nets in `predictions.json` (only refreshed when `v2/main.py` runs, ~30–60 min). **Mercado** from `web/data/market_odds.csv`.
- **`web/src/lib/grade.js`**: `LINES = ['M1','M2','M3','Mercado']`; `rps()` exists; `scoreboard()` aggregates aciertos/exactos/rps; **no log-loss yet**. Frontend: `Scoreboard.svelte`, `MatchRow.svelte`.

---

## DECISION POINTS (confirm before or during the relevant batch)

- **D1 — Shootouts in Elo.** The recorded 90-min score already treats a penalty tie as a draw (e.g. Germany 1–1 Paraguay). So `compute_elo` will treat it as a draw automatically — which *aligns* with the research (down-weight/treat shootouts as draws). **Proposed: accept as-is** (no special handling). Confirm.
- **D2 — Update cadence.** (a) *Elo-only fast refresh* per round (light script recomputes `elo_ratings` → `predictions.json`; M1 updates immediately, M2/M3 unchanged), vs (b) *full `v2/main.py` rerun* per round (Elo + form + marginal net retrain; ~30–60 min; M2/M3 become tournament-aware via updated features). **Proposed: both — fast Elo refresh as the online overlay after each match, full rerun once per round.** Confirm.
- **D3 — Blend base + weight.** Which model to blend with Pinnacle (proposed **M3**, the best line), and whether the blend weight `w` is global or per-stage (proposed **global**, backtested on group+R32). Confirm.
- **D4 — Line representation.** How to show frozen vs updated: **new named lines** in `LINES` (e.g. `M3_frozen`, `Mercado_info`) vs a snapshot file. **Proposed: add named lines** so the scoreboard compares them directly. Confirm.

---

## BATCH A — Sync finals into the corpus so Elo + form update
*The #1 low-effort/high-impact move. Because `compute_elo` already does K=60, this is a data-sync, not a new engine.*

- **A0 — Snapshot the frozen benchmark.** Copy `v2/output/predictions.json` → `v2/output/predictions_frozen_pretournament.json`. Also snapshot the current `matches.json` per-line predictions (M1/M2/M3) into a `web/data/frozen_predictions.json` keyed by match id. *This is the clean pre-tournament forecast — captured before any mutation.* **Verify:** both snapshot files exist and are non-empty; record their sha/row counts in PROGRESS.
- **A1 — Build the sync script (dry-run).** `web/scripts/sync_results_to_corpus.py`: read `results_live.csv` + `knockout_fixtures.csv`; for each finalized result, **fill the matching `NA` group row** in `results.csv` (match by content: date+teams, not row position) and **append missing KO rows** (`tournament='FIFA World Cup'`, correct neutral/city/country, 90-min score). Idempotent; `--apply` gates writes; default dry-run prints a diff. **Verify:** dry-run reports the expected counts (72 group scores to fill, N KO rows to add) and zero ambiguous/dup matches.
- **A2 — Apply the sync + verify the corpus.** Run `--apply`. **Verify:** `results.csv` now has 0 `NA` for played WC finals; KO rows present with correct scores; no duplicate (date,home,away) rows; spot-check 3 matches (1 group, 1 FT KO, 1 penalty KO) by hand.
- **A3 — Elo-only fast refresh.** `web/scripts/refresh_elo.py`: run `compute_elo` on the synced `results.csv`, write the updated `elo_ratings` back into `predictions.json` (leave nets/M2/M3 untouched). **Verify:** Elo moved in the sane direction — Morocco/Canada/Argentina ↑, Netherlands/Germany ↓ vs the frozen snapshot; print top-10 movers.
- **A4 — Rebuild + confirm M1 shifted, frozen intact.** Run `build_matches.py`. **Verify:** M1 picks/probs shifted for a few ties consistent with the Elo moves; the frozen snapshot (A0) is byte-identical/unchanged; `matches.json` still valid (96 matches).

---

## BATCH B — Market-informed blend line ("Mercado-informado")
*Log opinion pool of the model and Pinnacle where odds exist.*

- **B1 — Define the blend.** `p_blend ∝ p_model^(1−w) · p_pinnacle^w`, renormalized over {home,draw,away}. Base model = M3 (D3). Where no Pinnacle odds exist, fall back to pure model (flagged). Decide implementation site (build_matches vs grade.js) — **proposed build_matches**, so it's a real stored line.
- **B2 — Backtest `w`.** Script `web/scripts/backtest_blend_w.py`: over all finalized group+R32 matches that have both M3 and Mercado, grid `w ∈ {0,0.1,…,1}`, compute RPS **and** log-loss of the blend vs actual outcome; report the curve and `w*`. **Verify:** curve is sane (w=0 → pure model, w=1 → pure Pinnacle) and `w*` is reported with both metrics.
- **B3 — Emit the blend line.** Add `Mercado_info` to the emitted predictions in `build_matches.py` using `w*`. **Verify:** blended probs lie between M3 and Pinnacle; present only where Mercado exists.
- **B4 — Sanity-check.** Spot-check 3 matches: blend between model and market, picks reasonable. Update PROGRESS with `w*` and metrics.

---

## BATCH C — Evaluation upgrade (log-loss + multi-line scoreboard)
*Grade frozen / updated / blend against Pinnacle on RPS AND log-loss — the measurement that resolves adaptivity-vs-integrity.*

- **C1 — Add log-loss to grading.** In `grade.js`, add an ignorance/log score to `scoreboard()` accumulation (`−log p[outcome]`), alongside RPS. **Verify:** unit-sanity on a known case; NaN-guard for p=0.
- **C2 — Register the new lines.** Add the frozen benchmark line (`M3_frozen`, from A0 snapshot) and `Mercado_info` to `LINES` + `LINE_LABELS/NAMES/COLORS`. **Verify:** grade.js handles them (scoreline vs market verdict types correct).
- **C3 — Render.** `Scoreboard.svelte`: add a **log-loss column** next to the % column; show the new lines. `MatchRow.svelte`: render the new lines' cells (reuse existing null-safe logic). **Verify:** site builds; board shows M1/M2/M3/Pinnacle/M3-frozen/Mercado-info each with aciertos, %, RPS, log-loss.
- **C4 — Read the verdict.** With everything graded, compare **frozen vs Elo-updated vs blend vs Pinnacle** on RPS + log-loss over group+R32. **Verify:** the comparison is visible and interpretable; write the finding (did updating help? does the blend beat pure model?) into PROGRESS + a short note back to the research doc.

---

## BATCH D — (Longer term, separate) Dynamic state-space / score-driven Poisson
*Per-match dynamic attack/defense (Koopman & Lit style — verified in the research) so M2/M3 update without a full net retrain. Larger; scope its sub-batches only after Batches A–C land and the measurement (C4) justifies it.* Placeholder — not started.

---

## Global acceptance criteria
- Frozen pre-tournament forecast preserved and graded as a benchmark.
- Elo/form demonstrably absorb the finals (Elo movers sane; M1 shifts).
- A market-blend line exists with a backtested weight.
- Scoreboard grades every line on RPS **and** log-loss vs Pinnacle.
- Every batch independently reversible; PROGRESS reflects true state at all times.

## Rollback anchors
- A0 snapshot = the anchor to restore pre-tournament predictions.
- `results.csv` sync is additive + idempotent; a `--revert` (or git checkout of results.csv) undoes it.
- New lines/log-loss are purely additive to grade.js/frontend; removing them restores the current board.
