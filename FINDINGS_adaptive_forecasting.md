# Findings — Adaptive Forecasting & the Market-Edge Question

**What this is.** A clear, standalone record of everything we learned while trying to (a) make the World Cup 2026 models learn from the tournament as it happens, and (b) find out whether they can beat the sharpest betting market (Pinnacle). Written to be read on its own.

**Companion docs:** [RESEARCH_in_tournament_updating.md](RESEARCH_in_tournament_updating.md) (the literature — 25 verified findings) · [PLAN_adaptive_elo_market_eval.md](PLAN_adaptive_elo_market_eval.md) (the implementation plan) · [PROGRESS_adaptive_elo_market_eval.md](PROGRESS_adaptive_elo_market_eval.md) (the live batch-by-batch tracker).

**Date:** 2026-07-05. **Scoreboard state at time of writing:** group stage + Round of 32 complete (89 matches), Round of 16 (octavos) upcoming.

---

## TL;DR

1. **The models were frozen at pre-tournament strength.** Results of the actual World Cup lived only in the display file; they never reached the training data. Fixed.
2. **Feeding the finals into the model's Elo/form is easy and correct** — the rating code already uses a World-Cup K-factor; it just needed the data. The updated ratings move exactly as reality dictates (Morocco ↑, Uzbekistan ↓, …).
3. **You cannot grade an updated model on the matches it learned from.** Doing so is lookahead leakage and produces a flattering-but-fake number. We caught it (M1's score "improved" to 0.144 by hindsight; the honest value is 0.164) and fixed it with a **freeze-at-kickoff** rule.
4. **The honest verdict: the models lose to Pinnacle — decisively — on both fronts.**
   - *Calibration:* best model RPS 0.150 vs Pinnacle 0.128.
   - *Betting edge:* every model has **negative** ROI (−50% to −60%), and it gets **worse** the more the model disagrees with the market. There is no exploitable edge; there is anti-edge.
5. This matches the research consensus (sharp closing lines are very hard to beat) and is, itself, the valuable result: an honest measurement instead of a vanity metric.
6. **Still open (measurable now):** does *updating* the model help it going forward? The freeze-at-kickoff harness will answer this cleanly over octavos → final.

---

## 1. The core problem: the models never saw the tournament

The prediction stack (50-net Poisson ensemble = M2, neural+GBT blend = M3, Elo foil = M1, Monte Carlo bracket) trains on `results.csv` (~49k historical matches). We discovered that the **actual World Cup 2026 results were not in that file**:

- The 72 group fixtures were present but with **`NA` scores** (schedule only).
- The knockout matches were **absent entirely**.
- Live results lived only in `results_live.csv` — which drives the **scoreboard and website, but is never read by training**.

So every forecast — group and knockout — was effectively **frozen at pre-tournament strength**. Canada beating South Africa, Morocco knocking out the Netherlands, Paraguay eliminating Germany: the models had absorbed none of it.

---

## 2. Making the models learn: online Elo (the cheap, high-impact move)

The deep-research pass concluded the highest-value, lowest-effort intervention is **online rating updating** (Elo/Glicko/TrueSkill are all one approximate-Kalman-filter), and that the World Football Elo standard already prescribes a **3× faster K-factor (K=60) for World Cup matches**.

**Key discovery:** our `compute_elo` (`v2/feature_engine.py`) **already used K=60 for the World Cup** — it simply skipped the `NA` rows. So "online Elo" was a *data-sync problem, not a new engine*.

We built:
- **`sync_results_to_corpus.py`** — carries the played finals into `results.csv` (fills the 72 group `NA`s by content-matching; appends the 17 knockout rows, tagged World Cup so they get K=60; uses the **90-minute** score, so a penalty tie stays a draw). Idempotent, dry-run-first.
- **`refresh_elo.py`** — recomputes Elo the same way the full pipeline does and writes just the ratings back (nets untouched — the fast overlay).

**Result — the ratings moved exactly as reality dictates** (change vs pre-tournament):

| ↑ risers | | ↓ fallers | |
|---|---|---|---|
| Mexico | +104.7 | Uzbekistan | −104.9 |
| USA | +85.8 | Tunisia | −84.0 |
| France | +83.4 | Ecuador | −69.4 |
| Cape Verde | +79.1 (ET vs Argentina) | Turkey | −58.7 |
| Morocco | +72.0 | | |

Note the design choice working correctly: Netherlands and Germany went *out* on penalties, but because we record the **90-minute draw**, their Elo loss is modest — not a full defeat. That is the right way to treat shootouts.

---

## 3. The trap we caught: you can't grade a model on what it learned

After the Elo update, M1's score appeared to *improve* (RPS 0.153 → 0.144). **This was fake.** `build_matches` recomputes every match's prediction from the *current* ratings — which now include that match's own result. So M1 "predicted" the opening Mexico 2–0 South Africa using Mexico's *end-of-run* rating (inflated by winning the whole group + R32). That is **lookahead leakage / in-sample evaluation**, and it makes any updated model look artificially good.

**The fix — freeze-at-kickoff.** A match's prediction is captured at kickoff and **never recomputed**. Updated ratings only change *not-yet-played* matches. Concretely:
- `frozen_predictions.json` — the **immutable** pre-tournament snapshot (the `M3₀` benchmark line).
- `kickoff_predictions.json` — an **accumulating** snapshot; `build_matches` refreshes it only for pending matches, then overrides every played match's M1/M2/M3 with its frozen kickoff value.

After the fix, M1 reverted to its honest **0.164**, and played matches read identically to the frozen benchmark (verified: `M3 == M3_frozen` on played matches). The updated model now earns a **clean out-of-sample record going forward** — which is the only legitimate way to ask "did updating help?".

---

## 4. Honest result #1 — calibration: the models lose to Pinnacle

Out-of-sample (freeze-at-kickoff), over the 89 played matches, scored against the real 90-minute outcome. Lower is better for both metrics. Log-loss (ignorance score) is included because the research argues it is a stricter proper scoring rule than RPS.

| Line | Aciertos | RPS | Log-loss |
|---|---|---|---|
| M2 (neural, best model) | 57/89 | 0.1504 | 1.231 |
| M3 (conjunto) | 56/89 | 0.1530 | 1.239 |
| M1 (Elo foil) | 57/89 | 0.1643 | 1.296 |
| **Pinnacle** | **62/89** | **0.1276** | **1.095** |

Pinnacle is clearly better calibrated than every model — as expected for the sharpest market.

---

## 5. Honest result #2 — betting edge: negative, and revealing

We asked the harder, research-motivated question: even if worse-calibrated, can a model **profit** by betting where it thinks the market is mispriced? (Koopman-Lit "quality bet" strategy: bet outcome `o` when `EV(o) = p_model(o) · Pinnacle_odds(o) − 1 > τ`.) Measured out-of-sample on frozen kickoff predictions, 89 matches, average vig 6.2%:

| Model | ROI @ τ=0 | Best ROI (≥10 bets) | Trend as τ ↑ |
|---|---|---|---|
| M1 | −55.5% | −54.6% | worse |
| M2 | −59.7% | −59.7% | worse |
| M3 | −49.7% | −49.7% | worse |

**Two things stand out:**
- The ROI is not just negative — it is *far* worse than the 6.2% vig you'd lose betting at random. The models are actively bad against these lines.
- **ROI gets worse as τ rises.** τ is how strongly the model must disagree with the market to place a bet. So *the more confidently the model diverges from Pinnacle, the more it loses.* The model's disagreements with the sharp line are **systematically wrong in direction.**

This is the decisive point. The research (Hubáček & Šír) proved you *can* profit with an inferior model — **but only if you correctly identify the *direction* of the market's mispricing.** Our models do the opposite: where they most disagree with Pinnacle, they are most wrong. So the "beat the market with a worse model" escape hatch is closed for us.

---

## 6. What it means

- **Against the sharpest market, these models have no edge — they have anti-edge.** This is consistent with market-efficiency evidence and with the research finding that no dynamic Bayesian model in the literature beat bookmaker odds out-of-sample.
- **This is a feature of the honest harness, not a bug in the work.** Before the freeze-at-kickoff fix, the system could have shown a flattering (leaky) number. Now it tells the truth.
- **The valuable product is transparency, not conquest.** An honest, out-of-sample "AI vs the world's sharpest market" scoreboard — models + a frozen pre-tournament benchmark, graded on RPS *and* log-loss — is rare and credible precisely because it does not overclaim.

---

## 7. The one open question (now measurable)

Everything above concerns the **pre-tournament** models. The whole point of Batch A was to test whether **updating** helps. That can only be judged forward, out-of-sample — and the machinery is now in place:

- The octavos already carry **tournament-updated** forecasts, frozen at their kickoff.
- As octavos → final play out, the updated model accrues a clean out-of-sample record, gradable against Pinnacle on RPS, log-loss, and betting ROI.

The prior is pessimistic (the pre-tournament models' −50% edge is a big hole to climb out of), but this is the honest, remaining experiment.

---

## 8. Reproducibility — what each piece does

| Script | Role |
|---|---|
| `web/scripts/sync_results_to_corpus.py` | Feed played finals into `results.csv` (fills group `NA`s, appends KO rows; 90-min scores; idempotent; `--apply`). |
| `web/scripts/refresh_elo.py` | Fast net-free Elo recompute → `predictions.json` (K=60 for WC; `--apply`). |
| `web/scripts/build_matches.py` | Emits `matches.json`; now also does **freeze-at-kickoff** and the `M3_frozen` benchmark line. |
| `web/scripts/backtest_blend_w.py` | Model↔Pinnacle log-opinion-pool weight sweep (found `w*`=1 → market dominates). |
| `web/scripts/backtest_edge.py` | +EV betting ROI vs Pinnacle, τ-sweep, per model (the negative-edge result). |
| `web/src/lib/grade.js` | Adds log-loss; `SCOREBOARD_LINES` incl. `M3_frozen`. |
| `web/src/lib/components/Scoreboard.svelte` | Renders log-loss column + `M3₀` benchmark + best-metric highlight. |

**Per-round refresh recipe (fast overlay):**
`record`/`autofetch` new results → `sync_results_to_corpus.py --apply` → `refresh_elo.py --apply` → `build_matches.py`. Run the full `v2/main.py` once per round to also update M2/M3.

**Snapshots (never overwrite):** `v2/output/predictions_frozen_pretournament.json`, `web/data/frozen_predictions.json`.

---

## 9. Caveats

- The Pinnacle lines are "Pinnacle or sharp-market aligned"; some group-stage prices were sharp-aligned rather than exact Pinnacle closing lines. The direction of the result (models lose, negative edge) is robust, but the exact ROI magnitude would tighten with true closing lines.
- 89 matches is a **small sample**; treat point estimates as directional, not precise.
- The betting ROI ignores transaction costs, liquidity, and staking — it is a diagnostic of edge, not a real-money projection.
- The forward test (updated model over octavos→final) is even smaller-sample; read it as a signal, not proof.
