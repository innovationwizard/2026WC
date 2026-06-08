# WC2026 Prediction Model — Research Findings & v2 Roadmap

**Date:** 2026-06-07
**Status:** Research + recommendations. The v1 pipeline is the locked baseline (`v1.0-baseline`); everything here targets a future **v2** branch. Nothing in the baseline is modified.
**Purpose:** Make the model *more accurate*, *more robust*, and give the ANN a *defensible, braggable edge* — because (per the genesis brief) "the accuracy of the results is my entrance ticket… the real reputation test score is the sophistication of the model built from the ground up."

---

## 0. The one-paragraph executive summary

The serious public systems (Opta, FiveThirtyEight, academic Dixon-Coles/bivariate-Poisson work) all do three things our v1 does **not**: (1) they **correlate the two teams' goals and time-decay-weight recent matches** instead of assuming independent Poisson on hard 5-match windows; (2) they **anchor to, or blend with, betting-market odds** — empirically the single most accurate forecast source; and (3) they **publish a backtested score (RPS/Brier)** as proof of skill. Our v1 does none of these, and as a result it is a **severe outlier**: it buries Spain (everyone else's #1) at 3.6% and inflates Brazil to 23%. The v2 plan below fixes the two concrete bugs causing that, adds the three missing pillars, and — crucially — turns the ANN from a liability into the brag: a **neural bivariate-Poisson with a market-calibration layer**, validated by a backtest that prints a hard RPS number nobody else in the office can produce.

---

## 1. The benchmark we're being judged against

The friend's slides give us the exact consensus. Champion probabilities, top of each source:

| Source | #1 | #2 | #3 | #4 | Spain | Germany |
|---|---|---|---|---|---|---|
| **Opta supercomputer** (25k sims) | Spain **16.1%** | France 13% | England >10% | Argentina >10% | **#1** | not top-10ish |
| Polymarket | France 18.1% | Spain 16.6% | England 11.3% | Brazil 9% | **#2** | — |
| Kalshi | France 18.4% | Spain 16% | England 11.1% | Argentina 9.6% | **#2** | — |
| Bet365 | Spain 18.2% | France 16.7% | England 14.3% | Brazil 11.1% | **#1** | — |
| OPTA/Elo | Spain 16.08% | France 12.78% | England 11.01% | Argentina 10.02% | **#1** | — |
| ChatGPT 5.5 | France 18% | Spain 16-17% | England 12-13% | Argentina 9-10% | **#2** | — |
| Gemini 3.1 Pro | Spain 16% | France 12.5% | England 10.6% | Argentina 10.1% | **#1** | — |
| Grok Expert | France 19% | Spain 16.7% | England 11.3% | Brazil 9% | **#2** | — |
| Claude Sonnet 4.6 | France 19% | Spain 17% | Argentina 11% | England 10% | **#2** | — |
| **OUR v1 (neural)** | **Brazil 23.1%** | France 18.3% | **Germany 15.6%** | Belgium 9.1% | **3.6% ⚠️** | **#3 ⚠️** |
| OUR v1 (Elo baseline) | Spain 18.7% | France 10.0% | Brazil 6.8% | Germany 4.7% | **#1 ✓** | — |

**The pattern is unambiguous:** every external source — markets, betting houses, and four rival AIs — puts **Spain and France at the top and England top-4**. Our **Elo baseline agrees** (Spain #1). Only our **neural layer** disagrees, and violently: Spain → 3.6%, Germany → #3, Brazil → 23% (≈2× the market). Being a contrarian is fine *if you can defend the edge with a backtest*. Being a contrarian who also can't show a skill score is how the reputation dies. So v2 has two jobs: **fix what's broken, and arm the divergences with evidence.**

---

## 2. Why v1 diverges — diagnosed from our own output

Pulled from `output/predictions.json`:

| Team | Elo (rank) | Group adv. | R16 | QF | SF | Champion |
|---|---|---|---|---|---|---|
| Brazil | 2090 (5) | 92.5% | 82.1% | 61.5% | 49.1% | **23.1%** |
| France | 2160 (3) | 89.5% | 81.2% | 64.3% | 44.6% | 18.3% |
| Germany | 2070 (8) | 89.7% | 76.4% | 51.9% | 38.2% | 15.6% |
| **Spain** | **2258 (1)** | 84.8% | 61.4% | 34.9% | 16.2% | **3.6%** |
| **Argentina** | **2210 (2)** | 94.0% | **14.4%** | 9.5% | 7.2% | **3.3%** |
| **England** | **2136 (4)** | **52.0%** | 27.5% | 13.0% | 4.7% | **0.4%** |

Two independent root causes:

### Bug A — λ mis-calibration: recent form swamps team strength
Spain's modeled expected goals are anemic even against minnows: **1.87 vs Cape Verde, 1.72 vs Saudi Arabia, 1.28 vs Uruguay**. A genuine #1-Elo side should be posting λ ≈ 2.3–2.8 against that group. The feature-importance table explains it: `elo_diff` (0.228) and **`goals_scored_avg_5` (0.179)** dominate; the next 45 features are noise by comparison. The ANN has essentially learned "*recent raw goal tallies*" as a second master signal. Teams that win 1–0 / play controlled football (Spain, England) get low λ; teams on flashy recent goal sprees (Brazil, Germany) get high λ. Result: the strongest teams by *rating* are under-projected, and the model's whole title race tilts toward whoever scored a lot in friendlies. England (52% to even escape Group L) is the reductio: a top-4 side modeled as a coin-flip to advance.

### Bug B — the hard-coded "simplified" bracket mis-seeds teams
Argentina advances **94%** but reaches R16 only **14.4%** — i.e. it almost always loses its *first knockout match*. That's not a strength signal; it's [`monte_carlo.py:332-351`](monte_carlo.py#L332-L351), where the R32 pairings are explicitly a hand-written "simplified FIFA bracket." Some group winners get fed a brutal path while others get a soft one, independent of merit. Deep-run probabilities therefore partly measure *bracket luck baked into the code*, not football.

These two bugs compound: Bug A decides who has a high λ, Bug B decides whose path is soft, and Brazil happens to win on both (high recent-goal λ **and** a soft group C of Morocco/Haiti/Scotland + a favorable hand-coded path).

---

## 3. How the serious systems do it (research)

### 3.1 Dixon-Coles: the canonical upgrade to independent Poisson
The 1997 Dixon-Coles model is the standard improvement over plain Poisson, and it fixes *exactly our Bug A and our independence assumption*:
- **Low-score correlation (ρ):** an explicit dependence parameter between the two teams' goals, correcting the well-known fact that independent Poisson mis-prices 0-0, 1-0, 0-1, 1-1 — the scorelines that decide knockout football. Our Monte Carlo samples `Poisson(λ_a)` and `Poisson(λ_b)` **independently** ([`monte_carlo.py:140-141`](monte_carlo.py#L140-L141)), so every penalty-shootout-adjacent scoreline is mispriced.
- **Exponential time-decay weighting:** instead of a hard "last 5 matches" window, every historical match is weighted `exp(-ξ·Δt)`. Recent matches matter more *smoothly*, and an optimally-tuned decay drove RPS down to **~0.189** in published tests. Our `goals_scored_avg_5` is the crude, high-variance version of this — a 5-game window is why one low-scoring friendly can tank a team.
  Sources: [dashee87 — Dixon-Coles & time-weighting](https://dashee87.github.io/football/python/predicting-football-results-with-statistical-modelling-dixon-coles-and-time-weighting/), [opisthokonta.net](https://opisthokonta.net/?cat=48), [Dixon-Coles explained](https://football-bet-prediction.com/articles/dixoncoles-model-explained-improving-poisson/).

### 3.2 Karlis-Ntzoufras bivariate Poisson
Generalises Dixon-Coles: goals are modeled as a genuine **bivariate Poisson** with a shared covariance term. "The bivariate Poisson model and its independent counterpart are the best-performing maximum-likelihood models for football"; published bivariate-Poisson RPS ≈ **0.2103**. This is the principled target for our goal-generation layer. Source: [ML vs Poisson approaches (arXiv 2408.08331)](https://arxiv.org/pdf/2408.08331).

### 3.3 Opta supercomputer — the thing we're directly compared to
Opta's model "estimates the probability of each outcome **using betting-market odds and the Opta Power Rankings**," then runs **25,000** tournament simulations with attack/defence strengths calibrated on thousands of internationals. It predicts **Spain 16.1%, France 13%**, England & Argentina >10%. Two takeaways: (1) they **blend market odds in**, and (2) their sim count and structure are like ours — *the difference in output is entirely the inputs and the goal model.* Source: [Opta Analyst — Who will win the 2026 World Cup](https://theanalyst.com/articles/who-will-win-2026-fifa-world-cup-predictions-opta-supercomputer).

### 3.4 FiveThirtyEight SPI — the 75/25 split we should copy
SPI gives every team an **offensive** and a **defensive** rating (expected goals for/against vs an average team on neutral ground) — structurally identical to a two-headed λ model. For the World Cup, SPI = **75% match-results-based + 25% roster-based** (squad quality from club data). We already *have* squad market value as a feature but it's near-dead in the importance table (0.009); SPI's lesson is to give roster strength a **structural 25% weight**, not let the ANN discover it competes with recent form. Source: [FiveThirtyEight — How our 2022 World Cup predictions work](https://fivethirtyeight.com/features/how-our-2022-world-cup-predictions-work/).

### 3.5 Blending bookmaker odds — the highest-leverage single change
"There is empirical evidence that betting odds are **the most accurate available source** of probability forecasts for sports." Egidi, Pauli & Torelli (2018) build a hierarchical Bayesian Poisson where each team's scoring rate is a **convex combination of a historical-data estimate and a betting-odds estimate**; the blended model "almost matches Betfair's accuracy (70.2% vs 70.6%)" while staying interpretable. Combining-experts work shows the same. This is how we both improve accuracy *and* keep an interpretable model. Sources: [Egidi et al. (arXiv 1802.08848)](https://arxiv.org/pdf/1802.08848), [Combining ML & human experts (arXiv 2012.04380)](https://arxiv.org/pdf/2012.04380).

### 3.6 What actually wins ML benchmarks (and what doesn't)
On the public Soccer Prediction Challenge data: **gradient-boosted trees on rating features win** — CatBoost + pi-ratings hit **55.8% accuracy / 0.1925 RPS**, beating all 2017 entries; XGBoost + ratings ≈ 0.2054 RPS. Deep nets (TabNet) reach **0.1956 RPS / 55.8% acc** — *comparable, not superior*. **Implication for our brag:** a pure ANN is not automatically the most accurate thing; the defensible, braggable architecture is a **neural network that outputs bivariate-Poisson parameters** (a real modeling contribution) **inside an ensemble that also contains a GBT and a market anchor** — i.e. the ANN earns its place rather than being assumed best. Sources: [Springer — Evaluating soccer prediction models (10.1007/s10994-024-06608-w)](https://link.springer.com/article/10.1007/s10994-024-06608-w), [arXiv 2309.14807](https://arxiv.org/html/2309.14807), [ML for soccer result prediction (arXiv 2403.07669)](https://arxiv.org/pdf/2403.07669).

### 3.7 The metric that *is* the reputation test: RPS
Forecast skill in football is measured by the **Ranked Probability Score** (distance-sensitive: a home-win prediction is "closer" to a draw than to an away-win), with **Brier** and the **ignorance/log score** as companions. Good systems publish a backtested RPS on held-out matches. Right now we publish a Poisson training loss (0.6613) and MAE (0.828) — *goodness-of-fit, not forecast skill.* The single most credibility-building thing we can add is a **walk-forward backtest reporting RPS vs the Elo baseline and vs market-implied odds**. Sources: [The case against RPS (arXiv 1908.08980)](https://arxiv.org/abs/1908.08980), [penaltyblog — better metrics](https://pena.lt/y/2025/05/01/better-metrics-for-football-forecasts-moving-beyond-the-ranked-probability-score/).

---

## 4. v2 recommendations — prioritized

Ranked by (impact on accuracy/credibility) ÷ (effort). Each is additive; none touches the locked baseline.

### Tier 0 — Data Integrity (THE DIRTY GEORGE LAYER — do this before anything else)

*Rationale: every λ, every champion probability, and every backtested RPS is only as trustworthy as the inputs. We currently implement the Dirty George Principle at zero layers — the pipeline inspects nothing, flags nothing, and drops silently. It works only because the data is hand-curated today. The principle exists because that breaks the moment real WC results land in `results.csv`. This tier must precede P1, because an RPS backtest on silently-corrupted data is worse than no backtest — it's false confidence.*

**The principle, restated:** (1) data is dirtier than you think — inspect before trusting; (2) the parser fails neither loudly nor silently — captures every cell, **drops nothing**, flags anomalies, surfaces with provenance; (3) find by **content, never by position/assumed name-match**.

**Audit findings (2026-06-07) that this tier must fix:**
- **Silent drop:** [`feature_engine.py:147`](feature_engine.py#L147) drops every unscored row with no count/flag — currently **72 rows, which ARE the WC2026 fixtures themselves** (the schedule is already in the CSV, unscored).
- **No leakage guard:** verified 0 future-dated rows carry scores *today*, but nothing in the code prevents it. The instant played 2026 results are appended, they flow silently into Elo + training and the "prediction" becomes a retrodiction with **no warning**.
- **Silent defaults:** `defaultdict(1500.0)` in Elo and `.get(team, 1500)` / `setdefault(0.0)` throughout mean any unknown/misspelled team or missing feature becomes a confident average with no flag. **South Africa is missing from `SQUAD_MARKET_VALUE` → renders as "€0M"** in the report as if real.
- **Unenforced name-matching:** all 48 WC teams happen to match `results.csv` exactly today, but nothing *asserts* it. A single rename ("Czechia" for "Czech Republic") would silently default to Elo 1500.
- **Two sources of truth / position-based bracket:** the real fixture list lives in the CSV, but the bracket is hard-coded in `GROUPS`/`R32_MATCHUPS` by position ([`monte_carlo.py:23`](monte_carlo.py#L23), [`332-351`](monte_carlo.py#L332)). Nothing reconciles them.

**P0. Build a validation + provenance layer the pipeline runs on load.** It must: assert every WC team resolves to a real CSV identity (**fail loud** otherwise); count and log every dropped/defaulted/coerced row instead of dropping silently; hard-error on any future-dated row that carries a score (leakage tripwire); replace silent `0`/`1500` defaults with explicit flags that the HTML surfaces as a visible "missing data" marker (no more phantom "€0M"); and emit a provenance summary (rows in → rows used → rows dropped, with reasons). This is the literal implementation of "doesn't fail AND doesn't drop data." It pairs with **P3** (derive the bracket from the CSV's actual fixture list — content, not the hard-coded `GROUPS` — killing Bug B and the two-sources-of-truth problem at once).

### Tier 1 — fix the embarrassment + prove skill

**P1. Build a walk-forward backtest harness reporting RPS / Brier / log-loss.**
*The real test score.* Replay 2022–2026 internationals (and ideally the 2022 WC) match-by-match, training only on prior data, and report RPS for: our neural model, our Elo baseline, and market-implied odds where available. This is what converts "nice HTML" into "demonstrably skillful." Without it, every other change is unvalidated. **This is the headline brag.**

**P2. Fix Bug A — replace hard 5-match windows with exponential time-decay (Dixon-Coles style).**
Swap `goals_scored_avg_5/10` for `exp(-ξ·Δt)`-weighted attack/defence rates; tune ξ by P1's backtest. Expected effect: Spain/England stop being punished for low-variance recent form; the title race re-centres toward the consensus *on the merits*, not by fiat.

**P3. Fix Bug B — replace the hand-coded bracket with the real 2026 seeding (or randomized-but-fair pots).**
Make deep-run probabilities reflect football, not [`monte_carlo.py:332-351`](monte_carlo.py#L332-L351). Until the official bracket is final, draw knockout pairings under the actual FIFA rules so no group winner is structurally doomed (Argentina's 94%→14.4% cliff disappears).

**P4. Add a market-anchor / calibration layer (the Opta move).**
Blend model λ (or final champion probabilities) with betting-market-implied probabilities as a convex combination `α·model + (1-α)·market`, α tuned by backtest. This pulls us off the Spain-3.6% island *and* gives a principled, defensible reason for any remaining divergence ("we deviate from the market by X because our backtested edge is Y"). Polymarket/Kalshi/Bet365 odds are publicly scrapeable.

### Tier 2 — the braggable ANN edge

**P5. Upgrade the goal model to a neural bivariate Poisson.**
Keep the ANN, but have it output the **two λ's plus a correlation/covariance term**, and sample from a **bivariate Poisson with Dixon-Coles low-score correction** instead of two independent Poissons. This is a genuine, citable modeling contribution ("deep bivariate-Poisson with learned dependence") — far more impressive and more *correct* than independent sampling.

**P6. Two-headed offence/defence architecture (SPI-structured).**
Split the network into an attack head and a defence head per team, and give roster/squad-value a structural input path so it can't be washed out. Mirrors SPI's 75/25 intuition while keeping the neural flavour.

**P7. Ensemble: ANN + gradient-boosted trees + market, stacked.**
Since GBTs match or beat nets on goals-only data, make the ANN one expert in a small stack (ANN bivariate-Poisson + CatBoost-on-ratings + market), weighted by backtested RPS. "My model is an ensemble whose neural component contributes a learned goal-dependence the tree model can't" is both true and braggable.

### Tier 3 — robustness & polish

**P8. Calibration report in the HTML** — reliability diagram + the headline RPS vs Elo vs market. Turns the output page into evidence.
**P9. Uncertainty bands** — Monte Carlo already gives distributions; surface 90% intervals on champion odds so we show honesty about uncertainty (the friend's own disclaimer #2 makes this *on-theme*).
**P10. Per-match provenance** — show which features drove each λ, so any surprising call is explainable on the spot when colleagues "pounce."
*(Data-quality work that was here is promoted to **Tier 0 / P0** — it's foundational, not polish.)*

---

## 5. The 30-second pitch for the office

> "It's a Monte Carlo tournament engine — 10,000 simulations — but the goal model is a **neural bivariate-Poisson**: a network that learns each team's attack and defence *and the correlation between the two scorelines*, which plain Poisson models get wrong on exactly the 1-0s and 0-0s that decide knockouts. I **anchor it to the betting markets** the way Opta does, and — the part nobody else here has — I **backtested it on four years of internationals and it scores an RPS of [X], beating a pure-Elo baseline.** When I disagree with the market, it's because the backtest earned the right to."

That sentence is the reputation insurance: a real method, a market anchor, and a hard skill number.

---

## 6. Sources
- Opta supercomputer 2026 — https://theanalyst.com/articles/who-will-win-2026-fifa-world-cup-predictions-opta-supercomputer
- Dixon-Coles + time-weighting (dashee87) — https://dashee87.github.io/football/python/predicting-football-results-with-statistical-modelling-dixon-coles-and-time-weighting/
- Dixon-Coles (opisthokonta) — https://opisthokonta.net/?cat=48
- Bivariate Poisson / ML vs Poisson (arXiv 2408.08331) — https://arxiv.org/pdf/2408.08331
- FiveThirtyEight SPI / 2022 WC method — https://fivethirtyeight.com/features/how-our-2022-world-cup-predictions-work/
- Egidi, Pauli, Torelli — combining historical data & bookmaker odds (arXiv 1802.08848) — https://arxiv.org/pdf/1802.08848
- Combining ML & human experts (arXiv 2012.04380) — https://arxiv.org/pdf/2012.04380
- Soccer prediction models / GBT feature optimization (Springer) — https://link.springer.com/article/10.1007/s10994-024-06608-w
- Deep learning + GBT benchmark (arXiv 2309.14807) — https://arxiv.org/html/2309.14807
- ML for soccer result prediction, survey (arXiv 2403.07669) — https://arxiv.org/pdf/2403.07669
- The case against RPS (arXiv 1908.08980) — https://arxiv.org/abs/1908.08980
- Better metrics beyond RPS (penaltyblog) — https://pena.lt/y/2025/05/01/better-metrics-for-football-forecasts-moving-beyond-the-ranked-probability-score/

---
---

# ADDENDUM — 2026-06-08: External AI reviews integrated + three-horizon execution plan

**What changed:** Jorge ran the v1 concept past Gemini (a 3-round talk structure) and Opus 4.6 Max (a point-by-point audit of Gemini), captured in `comments/`. This addendum folds those in, **by addition only** (nothing above is altered), and reorganizes the work around the three goals Jorge is actually optimizing: **the day, the week, and the long term.**

**Decisions locked in the 2026-06-08 Q&A (these constrain everything below):**
1. **Binding deadline = tournament kickoff, June 11** (~3 days). Anything meant to be *live during the WC* must be built before the first match.
2. **Planning / doc-only for now — no new code yet.** The plan below is execution-ready but un-started. ⚠️ *Tension to surface, not bury:* with June 11 three days out and the build gate closed, **nothing here will be live for kickoff unless building starts almost immediately.** The day/week items are therefore *options pending a go-ahead*, not commitments.
3. **Positioning = Hybrid:** a from-scratch model stays the star; betting-market odds are shown *alongside*, with blending an optional, backtest-gated toggle. (Reframes P4 — see §8.)
4. **Conformal claim = match-level rigor + labeled simulation bands.** No "guaranteed" interval on the champion number (see §7.3).

---

## 7. Reconciling the external reviews (Gemini + Opus 4.6) — adopt / reject / sharpen

### 7.1 The convergence signal
Three models that did **not** see each other's work — Gemini's *legitimate* parts, Opus 4.6's audit, and this roadmap's own research — independently converge on the same spine: **Dixon-Coles correlation + time-decay, a published backtest score (RPS/Brier), honest uncertainty quantification, and an explicit rejection of buzzword methods.** Convergence across independent reasoners is itself evidence the spine is right. Build on it with confidence.

### 7.2 Adopt / Reject table
| Idea (source) | Verdict | Where it lives here |
|---|---|---|
| Dixon-Coles ρ correction + time-decay | **Adopt** | already P2 (Tier 1) |
| Backtest with RPS/Brier | **Adopt** | already P1 (Tier 1) |
| **Conformal Prediction** (match-level) | **Adopt — NEW** | **P12 (§8)** |
| **Dynamic Bayesian updating** (re-estimate as results arrive) | **Adopt — NEW** | **P13 (§8)** |
| **Interactive "Quiniela" in the HTML** | **Adopt — NEW** | **P14 (§8)** |
| "Topological Dynamics" / Spatio-temporal **GNNs** | **Reject** | best published GNN ≈ 52% acc; tracking data doesn't exist for international football; GNNs *worsen* small-sample problems |
| **LLM multi-agent swarms** | **Reject** | zero peer-reviewed evidence; sentiment-based football prediction ≈ 50% (coin flip) |
| "Principal AI Architect" framing, compliance cosplay | **Reject** | theater, not substance |

**Rejecting with evidence is itself an authority move.** On stage/video, the line *"I evaluated GNNs and LLM swarms and rejected them — here's the accuracy data showing they don't help structured outcome prediction"* earns more credibility from technical people than any demo of them would.

### 7.3 Three places I sharpen the comments (the reasoning that matters)
1. **The conformal "guarantee" is a loaded gun above the match level.** Conformal prediction gives real, distribution-free coverage *over exchangeable instances*. You have ~thousands of those at the **match** level — so conformal intervals on match outcomes/goals are rigorous and braggable. But Opus's doc staples a *"95% guaranteed"* interval onto the **champion probability**, and that does **not** hold: there is exactly **one** 2026 World Cup (n=1), and team-strength drift breaks exchangeability over time. A coverage guarantee on a single unrepeatable event is the precise slide a mathematician — the very critic the doc warns about — will destroy. **Resolution (locked):** conformal at match level only; the champion number gets a **Monte Carlo / bootstrap band, explicitly labeled as simulation spread, not a coverage guarantee.**
2. **"Dynamic updating" and "data leakage" are the same act — intent is the only difference.** Re-running the model as real results arrive (P13, the brag) is mechanically identical to the leakage failure Tier 0/P0 guards against. The boundary between "live model" and "accidental retrodiction" is whether ingestion is **deliberate and flagged**. ∴ **P13 depends on P0's leakage tripwire** — they ship together or not at all.
3. **v1 is *not* fully safe for a football-literate room.** Opus says "v1 is sufficient for today." For a purely non-technical crowd, yes. But v1 fails **face validity to casual fans**: England eliminated in the group stage (0.4%), Spain 6th, Germany 3rd. An England or Spain supporter objects without knowing a single equation. Mitigation in §9/§11-TODAY: don't present the raw champion list as truth — present the **dual-model disagreement** (ANN vs Elo vs market) as the honest story.

---

## 8. New work items (added to §4's R-list; existing P0–P10 unchanged)

**P12. Conformal prediction at the match level (the Modelo-3 differentiator).**
Split data train/calibration; nonconformity score on calibration matches; emit distribution-free intervals on match outcome / goal counts with guaranteed coverage. *No published 2026 model does this* — it's the genuinely cutting-edge, defensible brag. **Do NOT extend the guarantee to the champion %** (§7.3.1); champion uncertainty = labeled bootstrap band over the 10K sims. Effort ≈ 1 day. Libs: `mapie` or ~50 lines. Pairs with P8 (calibration report).

**P13. Dynamic Bayesian updating (the live, 5-week engagement loop).**
After each tournament round, *deliberately* append real results, re-run Elo + features + Monte Carlo (ANN weights frozen; only inputs change), and show how the model's beliefs shifted. This is what keeps the model — and Jorge — relevant for the whole tournament, and it directly honors the friend's own disclaimer #2 ("persistence of the heuristic and *proper updating*"). **Hard dependency: P0's leakage tripwire** (§7.3.2). Effort ≈ 1 day after P0.

**P14. Interactive "Quiniela" panel in the HTML (engagement bait).**
Let a colleague pick any match and see the model's call + the dual-model disagreement + the conformal interval, comparing their gut to the AI. Cheap, high-engagement for the office and great B-roll for the video. Effort ≈ 2–3 hours. Pure presentation layer.

**P4 — reframed under the Hybrid decision (not removed).** Keep the from-scratch model as the headline; render market-implied odds **side-by-side** in the output; make `α·model + (1-α)·market` an **optional toggle** whose α is chosen by P1's backtest (ship blending only if it actually lowers RPS). This gets the accuracy benefit of market awareness *and* preserves the "I built it from scratch" claim — and lets the evidence, not ego, decide whether to blend.

---

## 9. The honesty principle: calibration, not narrowing

Gemini's three graphs imply each model *narrows* uncertainty (σ shrinks 1 → 0.5 → 0.2). **That story is false and dangerous.** Football is irreducibly high-variance — 2022 alone: Saudi Arabia beat Argentina, Morocco reached the semis, Japan beat Germany *and* Spain. The best models sit at ~60–65% on 3-way match outcomes; a *tighter* distribution doesn't mean *better*, it means **overconfident**. The correct arc is **certainty → intelligence → honesty**:
- Modelo 1: wide, *poorly* calibrated — "I don't know much, and my uncertainty is vague."
- Modelo 2: wide, *well* calibrated — "I still don't know, but I know exactly how much I don't know."
- Modelo 3: marginally tighter *with guaranteed coverage* — "My uncertainty is honest and mathematically backed."

This is the same ethic as the Dirty George layer (don't fail silently, surface the truth with provenance) and as the friend's disclaimer that early forecasts "rara vez aciertan." Selling the true, humble story is what separates an authority from a charlatan — and it's defensible against anyone who knows the math.

---

## 10. Benchmark addendum — one more independent Spain-at-top vote

| Model | Group | Approach | Champion |
|---|---|---|---|
| **Zeileis et al. 2026** (Univ. Innsbruck) | most-respected academic WC forecast | bivariate Poisson + **bookmaker odds** + player ratings + market values | **Spain ~14%** |

This is the *fourth class* of source (academic) to put Spain at the top, alongside markets, betting houses, and rival AIs. It also independently validates the Hybrid call (P4): the leading academic model *does* fold in bookmaker odds. And it reinforces the **Bug A** diagnosis — every serious method lands Spain top-2; only our neural λ doesn't.

---

## 11. The three-horizon execution plan (binding deadline: June 11 kickoff)

> ⚠️ Build gate is currently **closed** (planning-only). The items below are sequenced and ready; none start until Jorge says go. Given the deadline, the realistic read: **TODAY items are doable; the WEEK items are live-by-kickoff *only if building starts now*; everything else is post-kickoff or video.**

### TODAY — office reputation (works with v1 as-is)
- **Frame, don't hide, the divergence.** Present the **dual-model story** (ANN vs Elo vs market consensus), not a bare "Brazil wins" — it converts v1's face-validity problem (§7.3.3) into a teaching moment about model humility, which is *more* impressive than a clean answer. 
- **Optional quick win (needs go-ahead):** P14 interactive Quiniela.
- *No modeling change is safe to rush before today.*

### THIS WEEK — technical debates / live-by-June-11 (needs go-ahead **now**)
Priority order (each gates the next's credibility):
1. **P0** — data-integrity / leakage tripwire (foundation; also unlocks P13).
2. **P2** — Dixon-Coles ρ + time-decay (fixes Bug A → fixes the face-validity embarrassment on the merits).
3. **P1** — backtest reporting RPS/Brier (the skill number; the headline brag).
4. **P12** — match-level conformal intervals.
5. **P3** — derive the bracket from the real CSV fixtures (fixes Bug B).
- These are exactly the "your stats friends will pounce on goal correlation / calibration / your Spain number" defenses.

### LONG-TERM — the video / international authority
- **The corrected 3-model talk** (replaces Gemini's): **Modelo 1 — Mathematical Foundation** (Poisson → Monte Carlo, wide honest uncertainty) → **Modelo 2 — Deep Learning Eats the Feature Space** (the ANN, Dixon-Coles, dual-model disagreement, feature importance) → **Modelo 3 — Conjunto + Honest Uncertainty** (market-anchored ensemble [P7/P4] + match-level conformal [P12] + labeled tournament bands). Arc = certainty → intelligence → honesty. *(Model lineup locked 2026-06-08: M1 Azar = Elo baseline; M2 Red Neuronal = pure ANN, no odds [P2/P5]; M3 Conjunto = market-anchored ensemble + conformal; **Mercado** tracked as a 4th line. See WEBSITE_STORYTELLING_DESIGN.md §0.5.)*
- **P13 dynamic updating** as the live, weekly "watch the model learn" loop across the 5-week tournament (depends on P0).
- **P5** neural bivariate-Poisson and **P7** ensemble (ANN + GBT + market) as the deep modeling contributions.
- **The reject-and-explain move** (§7.2) on GNNs/LLM swarms.
- **Hybrid pitch** (§8/P4): "from-scratch model, shown honestly against the markets, backtested to an RPS that earns its disagreements."

---

## 12. Additional sources (addendum)
- Zeileis et al. 2026, Univ. Innsbruck WC forecast (bivariate Poisson + bookmaker odds + market values) — academic SOTA, predicts Spain ~14%
- Conformal prediction foundations — Vovk, Gammerman & Shafer (2005); Angelopoulos & Bates, *A Gentle Introduction to Conformal Prediction* (2021)
- `mapie` — Python conformal-prediction library
- GNN football-prediction ceiling ≈ 52% (SFU thesis, 2022); sentiment-based prediction ≈ 50% (Schumaker et al., 2016) — cited as the *reject* evidence
