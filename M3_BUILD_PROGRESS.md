# M3 BUILD PROGRESS — "Conjunto" (LIVE TRACKER)

> Separate live tracker for building **Modelo 3 (Conjunto)**. Survives context compaction.
> **Update after EVERY sub-batch.** Fresh context: read this top-to-bottom first.
> Parent tracker: `BUILD_PROGRESS.md`. Story so far: `THE_JOURNEY.md`.

---

## ⏩ CURRENT STATE — READ FIRST
- **Goal:** make M3 a real 4th line (currently `null`/"pendiente") + unlock Act 3 of the narrative site.
- **Last completed:** **M3 IS LIVE** — Batches A–D COMPLETE. N=50 run done; M3 champion France 16.7/Spain 16.3/England 10.0 (distinct from M2, consensus-grade). Exporter emits M3 line + conformal set (default 80% coverage, avg set 1.71 — informative); MatchRow shows `80% conf: México` / `cualquier resultado`. Site builds OK. 4-line scoreboard complete.
- **In progress:** — (core M3 DONE + pushed CP10 `489f8c8`)
- **NEXT ACTION:** none required. Optional later: M3.E (market anchor when odds entered; Act-3 exports when narrative Act 3 is built).
- **Blockers:** none. Jorge drives git (I prepare commands).

---

## 🔒 What M3 IS (locked)
**M3 = Conjunto = a DISTINCT point-forecaster + honest uncertainty.** Three parts:
1. **Distinct point model** = blend of the **M2 neural ensemble** (50 nets) + a **GBT Poisson model** (gradient-boosted trees). λ_M3 = weighted avg of the two. (This is what makes M3 ≠ M2 — the lineup requires it.)
2. **Conformal intervals** — match-level, coverage-validated honest uncertainty (the Act-3 centerpiece).
3. **Market anchor** — convex blend with Mercado implied probs `α·model + (1-α)·market`; activates when odds entered (α default = pure model until then).
- **LEAN:** GBT = sklearn `HistGradientBoostingRegressor` (ALREADY installed — no new deps). No XGBoost/CatBoost.
- **Validation rule (from the heavy-lift):** ship a change only if the **backtest** says it helps (RPS), never to chase a number.
- Mercado is pick-only (no scoreline). M3 carries scoreline + probs + interval.
- All model work in `/v2` (root baseline frozen).

---

## 📋 PLAN — batches → sub-batches

### Batch M3.A — Distinct point model (GBT + blend) ✅ COMPLETE
- [x] M3.A.1 `GBTPoissonModel` (sklearn HistGradientBoosting, loss=poisson) — trains 77 iters, λ mean 1.36, sane.
- [x] M3.A.2 `ConjuntoModel` (λ_M3 = w·net + (1-w)·gbt, default w_net=0.5, slots into pipeline interface).
- [x] M3.A.3 `/v2/m3_backtest.py` swept w → **w_net=0.5 best (RPS 0.1648), blend beats both pure net (0.1655) and pure GBT (0.1653)** on 1,267 held-out. Validated, distinct, robust.

### Batch M3.B — Conformal (honest uncertainty) ✅ COMPLETE — form = OUTCOME PREDICTION SET (LAC)
- [x] M3.B.1 `/v2/conformal.py` — LAC: `lac_threshold` (calibrate τ) + `prediction_set` (outcomes with p≥τ, never empty).
- [x] M3.B.2 `/v2/m3_conformal_validate.py` — proper-train<2024 / cal 2024 / test 2025+: coverage 90→92.9%, 80→85.0%, avg set 2.17/1.83. **Guarantee holds + informative.**
- [ ] M3.B.3 Per-match prediction set into matches.json `M3.set` (done in M3.C/D).

### Batch M3.C — Pipeline integration ✅ COMPLETE
- [x] M3.C.1 `/v2/main.py`: GBT + blended `m3_predict` + 3rd Monte Carlo + `m3_*` keys + `conformal_tau`. Smoke N=2 PASSED. (Also: `N_ENSEMBLE` now env-overridable for smoke tests.)
- [x] M3.C.2 Full N=50 run done. M3 champion France 16.7/Spain 16.3/England 10.0 — distinct from M2 (Spain 17.6/France 17.5), consensus-grade.

### Batch M3.D — Wire into site ✅ COMPLETE
- [x] M3.D.1 Exporter emits M3 line (scoreline+probs) + conformal `set`/`coverage`. **Default display = 80% coverage** (avg set 1.71, informative; 90%+ → Act-3 slider). Meta stub → only Mercado.
- [x] M3.D.2 `MatchRow.svelte`: green `80% conf: México` / `cualquier resultado`. Site builds OK. Scoreboard/verdicts already generic over 4 lines.

### Batch M3.E — Market anchor + Act-3 exports  *(DEFERRED — both optional/future)*
- [ ] M3.E.1 Market-anchor blend `α·M3 + (1-α)·Mercado` — deferred: needs odds (absent), and M3 is already consensus-grade with Mercado as a separate line. Mechanism can be added later.
- [ ] M3.E.2 Act-3 exports (conformal/calibration data) — deferred: not needed until the narrative Act 3 is built.

---

## 🧭 Git checkpoints (Jorge runs)
- [x] **CP10** `489f8c8` — entire M3 build (A–D): blend + conformal + pipeline + live site — **pushed to origin/v2**.

---

## 📝 PROGRESS LOG (append-only; newest at bottom)
- Plan created. M3 = blend(M2 ensemble, GBT-poisson) + conformal + market anchor. Lean (sklearn HGB, no new deps). Starting M3.A.1.
- **Batch M3.A ✓.** Files: `/v2/neural_poisson.py` (+GBTPoissonModel, +ConjuntoModel), `/v2/m3_backtest.py` (new). HistGradientBoostingRegressor(loss='poisson') — no new deps. Backtest: w_net=0.5 → RPS 0.1648 beats pure net 0.1655 & pure GBT 0.1653 (the blend of two model families helps; GBT slightly beats the net alone here). M3 is now a distinct, validated point forecaster. Next: M3.B conformal intervals.
- **Batch M3.B ✓ — conformal OUTCOME PREDICTION SETS (LAC).** Files: `/v2/conformal.py` (lac_threshold + prediction_set), `/v2/m3_conformal_validate.py`. Coverage validated on held-out: **90%→92.9% (τ=0.185), 80%→85.0% (τ=0.236)**, avg set 2.17/1.83 — guarantee holds (≥target) + informative (usually rules out ≥1 outcome). **τ DECISION for production:** use these validated τ as fixed, pre-validated thresholds (calibrated on 2024 / tested 2025+); apply to production M3 probs in the exporter. Documented approximation (production N=50 vs validation N=5); acceptable since the ensemble is well-calibrated. Next: M3.C pipeline integration (emit M3 + 3rd MC).
- **Batches M3.C + M3.D ✓ — M3 LIVE.** Files: `/v2/main.py` (GBT + m3_predict + 3rd MC + m3_* keys + conformal_tau + N_ENSEMBLE env), `web/scripts/build_matches.py` (M3 line + conformal set, stub→Mercado only), `web/src/lib/components/MatchRow.svelte` (conformal-set display, `.conf` style), regenerated predictions.json + matches.json. N=50: M3 champion France 16.7/Spain 16.3/England 10.0. **Default display coverage = 80%** (production 90% sets too wide — 35/72 'all three'; 80% gives avg 1.71, 42/72 single confident pick — informative + honest; 90%+ reserved for Act-3 slider). 4-line scoreboard complete. **M3.E (market anchor + Act-3 exports) DEFERRED.** ▶ CP available.
