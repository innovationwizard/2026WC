# PROGRESS — Adaptive Elo + Market Blend + Dual-Line Evaluation

> **LIVE DOCUMENT.** Update after every sub-batch. This is the source of truth if the conversation is compacted/summarized. Do not delete history — mark items done, append to the log.

---

## ⛳ HOW TO RESUME (read this first, always)

- **What this is:** implementing the 4-step adaptive-forecasting proposal. Full plan: [PLAN_adaptive_elo_market_eval.md](PLAN_adaptive_elo_market_eval.md). Rationale/literature: [RESEARCH_in_tournament_updating.md](RESEARCH_in_tournament_updating.md). **Clean explained findings: [FINDINGS_adaptive_forecasting.md](FINDINGS_adaptive_forecasting.md) ← read this for the results.**
- **Big idea:** the finals results are stranded in `results_live.csv` (display) and never reach training (`results.csv`, where WC rows are `NA`). `compute_elo` already uses K=60 for the World Cup — so feeding the finals in makes Elo/form update automatically. Then add a market-blend line and grade frozen-vs-updated-vs-blend vs Pinnacle on RPS + log-loss.
- **Current phase:** `Batch A + freeze-at-kickoff + edge backtest COMPLETE. Priority pivoted to EDGE (Jorge). Edge result: DECISIVE NEGATIVE. Awaiting Jorge's call on next step.`
- **Last completed sub-batch:** `v2 rerun (synced corpus) + rebuild ✅ — octavos carry updated forward predictions frozen at kickoff; played matches stay clean-frozen (verified gA-01 M3==M3_frozen). Forward out-of-sample measurement of the tournament-updated model is now LIVE for octavos→final.`
- **Note:** `M3_frozen` is null for octavos (pre-tournament snapshot never predicted those matchups) — forward test is updated-model-vs-Pinnacle out-of-sample, which is the correct test. Nothing committed (Jorge drives git).
- **Next action:** Jorge decision — (a) keep forward out-of-sample measurement running (freeze-at-kickoff ready, near-free), (b) ship honest scoreboard, (c) invest in a better model (Batch D — likely futile vs Pinnacle). Also: v2 rerun finishing → rebuild to give octavos updated forward predictions.
- **What changed on disk in Batch A:** `results.csv` now contains the finals (72 group filled + 17 KO appended); `predictions.json` `elo_ratings` refreshed (nets untouched); `matches.json` rebuilt (M1 shifted). New scripts: `web/scripts/sync_results_to_corpus.py`, `web/scripts/refresh_elo.py`. Fixed: `build_matches.py` group loop now skips KO rows silently. Snapshots (never overwrite): `v2/output/predictions_frozen_pretournament.json`, `web/data/frozen_predictions.json`.
- **To re-run Batch A after a new round:** `record`/`autofetch` new results → `python web/scripts/sync_results_to_corpus.py --apply` → `python web/scripts/refresh_elo.py --apply` → `python web/scripts/build_matches.py`.
- **How to verify current real state:** `git status` (only the two planning .md files + prior KO work should be untracked/modified; no code changed yet). Nothing in `v2/` or `web/scripts/` has been touched by this plan yet.
- **Safety anchor:** once A0 runs, `v2/output/predictions_frozen_pretournament.json` is the frozen pre-tournament forecast — never overwrite it.

---

## 🚦 Status board

Legend: ⬜ not started · 🟡 in progress · ✅ done · ⏸️ blocked (needs decision/input)

### Decisions
- ✅ **D1** shootouts treated as draws in Elo (accept as-is) — confirmed 2026-07-05
- ✅ **D2** update cadence: fast Elo refresh + periodic full rerun — confirmed 2026-07-05
- ✅ **D3** blend base = M3, global `w` — confirmed 2026-07-05
- ✅ **D4** representation: add named lines `M3_frozen`, `Mercado_info` — confirmed 2026-07-05

### Batch A — Sync finals into corpus (Elo/form update)
- ✅ **A0** snapshot frozen benchmark — `v2/output/predictions_frozen_pretournament.json` (sha 3d06c0bc9448, 48 Elo, 89 match-preds) + `web/data/frozen_predictions.json` (sha 35e5132ac929, 96 matches). **Never overwrite these.**
- ✅ **A1** `web/scripts/sync_results_to_corpus.py` — dry-run verified (72 group + 17 KO, 0 flags/dupes)
- ✅ **A2** applied sync — corpus 49438→49455; 0 NA WC-2026 rows; 89 scored; 0 dupes; spot-checks OK
- ✅ **A3** `web/scripts/refresh_elo.py --apply` — elo_ratings refreshed in predictions.json (nets untouched); movers sane (see Key results)
- ✅ **A4** rebuilt matches.json (96, `missing/flagged: none`); M1 shifted (P94 USA↔Belgium pick flipped USA); frozen snapshot sha 35e5132ac929 unchanged. Fixed build_matches group loop to skip KO rows silently.

### Batch B — Market-informed blend line
- ✅ **B1** log-opinion-pool blend defined + `web/scripts/backtest_blend_w.py` built
- ✅ **B2** backtested on 89 finalized (group+R32) — **RESULT: monotonic, w*=1.0 (see Key results).** Frozen M3 does NOT beat/complement Pinnacle. ⚠ This used the FROZEN M3; re-backtest after the full rerun (updated M3) before deciding B3.
- ⏸️ **B3** emit `Mercado_info` line — **on hold:** at w*=1 the blend = pure Pinnacle (pointless). Decide after re-backtesting with tournament-updated M3.
- ⏸️ **B4** sanity-check — pending B3 decision
- 🔄 **Full v2 rerun LAUNCHED** (background, ~30–60 min) on the synced corpus → M2/M3 become tournament-aware. Log: `scratchpad/rerun_synced.log`. When done: rebuild matches.json → re-run backtest → then Batch C verdict.

### Batch C — Evaluation upgrade (log-loss + multi-line)
- ⬜ **C1** add log-loss to `grade.js` scoreboard
- ⬜ **C2** register `M3_frozen` + `Mercado_info` in LINES
- ⬜ **C3** render log-loss column + new lines (Scoreboard + MatchRow)
- ⬜ **C4** read the verdict (frozen vs updated vs blend vs Pinnacle)

### Batch D — State-space Poisson (longer term)
- ⬜ deferred — scope after A–C land and C4 justifies

---

## ⚠️ CRITICAL FINDING (2026-07-05) — evaluation leakage; design pivot needed

Grading the scoreboard after the Elo refresh exposed a **lookahead-leakage trap**:

- `build_matches` recomputes **every** match's M1 from the *final* `elo_ratings`. After A3, that Elo has already absorbed the finals — so M1's "prediction" for an already-played match uses ratings that include that match's result. **M1's RPS dropped 0.1530→0.1440 — but that's hindsight, not skill.** The same will happen to M2/M3 once the running rerun updates the nets.
- **You cannot evaluate an updated model on the matches it was updated with.** Grading the updated line on past matches is in-sample and meaningless.
- The **only clean out-of-sample forecast for the 89 played matches is `M3_frozen`** (the pre-tournament snapshot) — RPS 0.1530 / log 1.2391, vs Pinnacle 0.1276 / 1.0945. That is the honest "how good was the pre-tournament AI" number, and it **loses clearly to Pinnacle** (consistent with the research).

**The correct design (walk-forward / freeze-at-kickoff):** a match's M1/M2/M3 must be **frozen at kickoff** and never recomputed. Updated ratings/nets only change **future** (not-yet-played) matches' predictions. The updated model then earns a *clean* out-of-sample record going forward (predict round N before it's played → grade after). `frozen_predictions.json` becomes an **accumulating per-round snapshot** (kickoff predictions), not a one-time capture. The scoreboard grades those frozen kickoff predictions only.

**RESOLVED 2026-07-05:** Jorge confirmed **freeze-at-kickoff** (implemented — see below) and pivoted priority to **beating-the-market EDGE** (decorrelation / betting-ROI; Koopman-Lit goal-difference-for-betting) over chasing Pinnacle calibration parity.

**Freeze-at-kickoff DONE:** two snapshots — `frozen_predictions.json` (immutable A0 pre-tournament benchmark → `M3_frozen` line) and `kickoff_predictions.json` (accumulating; each match frozen at kickoff). `build_matches` now refreshes the kickoff snapshot only for not-yet-played matches and overrides played matches' M1/M2/M3 with their frozen kickoff value. **Verified: M1 reverted from leaky 0.1440 → honest 0.1643; M3 == M3_frozen for played.** Honest out-of-sample board: M2 0.1504 / M3 0.1530 / M1 0.1643 / **Pinnacle 0.1276** (all models lose to Pinnacle on calibration).

**New direction — Batch E (edge/ROI):** measure +EV betting ROI vs Pinnacle (`EV(o)=p_model(o)·odds(o)−1`, bet where EV>τ; τ-sweep; per model line; out-of-sample on frozen kickoff predictions). Blend line (B3) deferred — market dominates on calibration, so blending is pointless; the edge question is whether the model finds spots the market underprices.

---

## 🔑 Key results captured here (fill in as we go)
- Elo top movers after sync (A3): **↑ Mexico +104.7, USA +85.8, France +83.4, Cape Verde +79.1 (ET vs Argentina), Morocco +72.0 · ↓ Uzbekistan −104.9, Tunisia −84.0, Ecuador −69.4, Turkey −58.7.** D1 confirmed working: Netherlands/Germany penalty exits recorded as 90-min draws → only modest Elo loss (not top movers).
- Backtested blend weight `w*` + metrics (B2, **frozen M3**): **w*=1.0 (monotonic).** Pure M3: RPS 0.1530 / logloss 1.2392. Pure Pinnacle: RPS 0.1277 / logloss 1.0945. Pinnacle dominates; blending toward market monotonically helps → frozen model adds no info beyond the market. Matches research finding #5. Re-test pending updated M3.
- Frozen vs updated vs blend vs Pinnacle, RPS + log-loss (C4): **honest out-of-sample (freeze-at-kickoff): M2 0.1504 · M3 0.1530 · M1 0.1643 · Pinnacle 0.1276.** All models lose to Pinnacle on calibration.
- **Edge/ROI backtest (E1/E2, `backtest_edge.py`) — DECISIVE NEGATIVE EDGE:** betting model +EV picks vs Pinnacle (89 matches, vig 6.2%) → ROI M1 −55%, M2 −60%, M3 −50%. **ROI gets WORSE at higher τ** (the more the model disagrees with the sharp line, the more it loses) → the model's directional disagreements with Pinnacle are systematically wrong. No exploitable edge; the Hubáček "profit with inferior model" condition (correct direction of mispricing) FAILS here. Only open question: does the tournament-UPDATED model have forward out-of-sample edge on octavos→final (freeze-at-kickoff now measures this).

---

## 📓 Log (append-only, newest last)

- **2026-07-05** — Plan + this tracker created. Inspected `compute_elo` (K=60 for WC already present; skips NA scores) and the `results.csv` (WC=NA) vs `results_live.csv` (filled) split. No code touched yet. Awaiting D1–D4 confirmation to start A0.
- **2026-07-05 (later)** — Jorge confirmed freeze-at-kickoff + pivot to EDGE priority. Implemented **freeze-at-kickoff** (two snapshots: immutable `frozen_predictions.json` benchmark + accumulating `kickoff_predictions.json`; build_matches overrides played matches with frozen kickoff prediction). Fixed the M1 leakage (0.1440→0.1643 honest). Added **log-loss** to grade.js + `M3_frozen` scoreboard line + log-loss column (SCOREBOARD_LINES; site builds). Built **`backtest_edge.py`** → **DECISIVE: models have negative edge vs Pinnacle (ROI −50 to −60%, worse at higher τ).** No exploitable edge. New scripts: `sync_results_to_corpus.py`, `refresh_elo.py`, `backtest_blend_w.py`, `backtest_edge.py`. Full v2 rerun on synced corpus finishing. Blend line (B3) and Batch D deferred (calibration/edge both dominated by market). Everything reversible; frozen benchmark preserved.
- **2026-07-05** — D1–D4 confirmed (proposed defaults). **Batch A completed end-to-end:** A0 snapshot frozen benchmark; A1 built `sync_results_to_corpus.py` (dry-run 72 group + 17 KO); A2 applied (corpus +17, 0 NA, 0 dupes); A3 built `refresh_elo.py`, applied (Elo movers sane, nets untouched); A4 rebuilt matches.json (M1 shifted with Elo — e.g. USA↔Belgium pick flipped), fixed build_matches group loop to skip KO rows (no more false "group mismatch" flags), frozen snapshot verified unchanged. Net effect: **M1 is now tournament-aware; M2/M3 still frozen (await full v2 rerun); pre-tournament benchmark preserved.** Next: Batch B.
