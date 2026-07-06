# In-Tournament Updating — Deep Research

**Question:** With the group stage + Round of 32 complete (~89 same-tournament results), how should our World Cup 2026 forecasting system incorporate this data — and what would the world's best data scientists actually do?

**Method:** Multi-source deep-research pass — 6 search angles → 21 sources fetched → 87 claims extracted → 25 adversarially verified (3-vote, need 2/3 to refute). 18 confirmed, 0 refuted, 7 unverified (verifier/API failures, not refutations). Sources are majority primary peer-reviewed (IJF, JRSS-C, JQAS, J. Sports Analytics) plus 2025–2026 arXiv preprints.

_Generated 2026-07-04. Context: M1 (Elo foil), M2 (50-net Poisson ensemble), M3 (net+GBT blend), Monte Carlo bracket, graded by RPS + hit-rate vs Pinnacle closing 1X2. Models trained once pre-tournament on ~49k matches; finals results not fed back. See [[v2-direction]]._

---

## TL;DR — the state-of-the-art answer

> **Don't naively retrain the 50-net ensemble on 49k+89 rows, and don't leave the forecast fully frozen. Layer a fast, principled _online-updating_ mechanism on top of the frozen model, shrink it hard toward the prior on the small sample, and anchor/blend the result toward the Pinnacle closing line.**

The literature converges on three high-leverage, low-effort moves:

1. **Sequentially update team strengths mid-tournament** via an online rating / state-space mechanism. Elo, Glicko, and TrueSkill are all special cases of a single approximate-Kalman-filter; World Football Elo already prescribes a **3× faster K-factor (60) for World Cup matches**. Bayesian state-space Poisson models do the same per-match **without reprocessing the full history**.
2. **Shrink hard toward the prior** when updating on ~89 games (commensurate / spike-and-slab priors, partial pooling) — borrow from the historical estimate to the extent the data support it. This is where the real signal is, *not* in retraining nets on 89 extra rows.
3. **Blend toward Pinnacle's closing line.** It aggregates syndicate information, is better-calibrated than academic models, and **has not been beaten out-of-sample by even the best dynamic Bayesian models.** Beating a sharp closing line is theoretically foreclosed under EMH and empirically very hard.

**Evaluation:** RPS is the stated benchmark but the **Ignorance (log) score is argued to be strictly better**; report both, computed against Pinnacle-implied probabilities.

---

## Ranked shortlist — impact-to-effort

| # | Intervention | Impact | Effort | Why |
|---|---|---|---|---|
| **1** | **Online Elo overlay with WC K=60**, updated after every finals match, feeding the existing feature pipeline | High | Low | Elo/form recency is the real signal; canonical, battle-tested; our Elo feature already exists — just needs to ingest finals results with the WC weight |
| **2** | **Blend/anchor model output toward Pinnacle** (logarithmic opinion pooling) | High | Low–Med | The market is the SOTA benchmark; blending raises accuracy immediately (mind the edge tradeoff, below) |
| **3** | **Shrink the update toward the prior** (commensurate / spike-and-slab; or simply a conservative K / strong Bayesian prior) | High | Med | Prevents overfitting 89 high-variance games — the #1 failure mode |
| **4** | **Report the Ignorance (log) score alongside RPS**, both vs Pinnacle-implied probs | Med | Low | Better scoring rule; cheap to add; makes "did the update help?" answerable |
| **5** | **Bayesian state-space Poisson** (dynamic attack/defense with forgetting factors) as the principled successor to the static nets | High | High | The "correct" long-term architecture; updates per-match without full retrain; bigger build |
| **6** | **Keep the frozen pre-tournament nets as a parallel clean-benchmark line** and grade both against Pinnacle | Med | Low | Resolves the adaptivity-vs-integrity tension by *measuring* whether updating actually helps (see below) |

**The move that satisfies both goals (recommended):** run the frozen nets *and* an online-updated overlay in parallel, blend the overlay toward Pinnacle, and grade all three (frozen / updated / market) on RPS **and** log-loss. You keep a clean out-of-sample benchmark *and* get adaptivity, and you empirically learn whether the update helps rather than assuming it.

---

## Findings by theme (with citations & confidence)

### 1. Online rating systems are the canonical mid-tournament update mechanism — `HIGH` (3-0)
Elo, Glicko, and TrueSkill are all **special cases of one approximate-Kalman-filter Bayesian framework** that updates skill estimates after each game. Between full retrains, an Elo-style / Kalman online update is the right way to absorb in-tournament results.
→ Szczecinski & Tihon, *A unified framework for rating systems*, arXiv **2104.14012** (JQAS 2023): "may be seen as an approximate Kalman filter… generic enough to be used with any skills-outcome model."

### 2. World Football Elo already prescribes 3× faster updates for WC matches — `HIGH` (3-0)
K = **60 (World Cup)**, 50 (continental), 40 (qualifiers), 30 (other), 20 (friendlies). A concrete, published prescription for how fast ratings should move on high-stakes games (60/20 = 3×).
→ [World Football Elo Ratings](https://en.wikipedia.org/wiki/World_Football_Elo_Ratings) (secondary, but the canonical documented spec; independently corroborated).

### 3. Bayesian state-space Poisson updates per-match without reprocessing history — `HIGH` (3-0)
Each team's dynamic attack/defense strength + home advantage is updated sequentially after every match (conjugate Gamma + mean-field VI), using **learned within-season and between-season forgetting factors** — the state-space analogue of Dixon-Coles exponential time-weighting. "Every time the result of a game has been observed, the relevant dynamic parameters… are updated using only that observation. Unlike the likelihood or a weighted likelihood approach the rest of the data does not need to be reprocessed."
→ Ridall / Santos-Fernandez et al., **JRSS-C 74(3):717** (2024/25).

### 4. On small samples, shrink hard toward the prior — `HIGH` (3-0 / 2-0)
Commensurate / spike-and-slab priors adaptively borrow from the historical estimate "only to the extent that the data support it": spike (strong shrinkage) when current and historical parameters look similar, slab (weak) when performance genuinely changed. Directly answers "where is the signal": **recency-weighted shrinkage, not retraining a net on 49k+89 rows.**
→ *Bayesian weighted discrete-time dynamic models*, arXiv **2508.05891v1** (2025).

### 5. The sharp market is the SOTA benchmark and is very hard to beat — `HIGH` (3-0)
Sharp books absorb information from professional syndicates ("one business line… is providing forecast probabilities for a fee to soft bookmakers"). Odds-based forecasts beat official FIFA rankings out-of-sample, and **"none of the [dynamic Bayesian] models exceeded bookmakers' odds performance."**
→ Int. J. Forecasting 2024 ([S0169207024000670](https://www.sciencedirect.com/science/article/pii/S0169207024000670)); Leitner et al. 2010 (via arXiv 2604.17194); JRSS-C 2025.

### 6. Blending toward the market raises accuracy but shrinks edge — `HIGH` (3-0)
Adding bookmaker odds as a feature lifts accuracy (Pearson **0.87 → 0.95**), but the higher market correlation **reduces the exploitable edge** — a real tradeoff. Under EMH, model-based edges over an efficient closing line are theoretically foreclosed.
→ Hubáček & Šír, arXiv **2010.12508** (IJF 2023); arXiv 2604.17194 (2026).

### 7. You can beat the market on ROI with an *inferior* model — `MEDIUM` (3-0 / 2-1)
It is provably possible to profit with a strictly inferior predictive model by **decorrelating its residual error from the market** (requires correctly identifying the *direction* of mispricing; assumes negligible costs). A deliberately simple isotonic-calibrated xG→Skellam model returned ~10% simulated ROI at average odds (~15% at best prices) over 11 Bundesliga seasons **despite the bookmaker being better-calibrated** — it captured signal the market underpriced.
→ Hubáček & Šír (IJF 2023); Wilkens 2026, [J. Sports Analytics](https://journals.sagepub.com/doi/10.1177/22150218261416681). _Caveat: simulated upper bound; ignores costs/liquidity; profit concentrated in home wins; single study._

### 8. Report the log/Ignorance score, not just RPS — `HIGH` (3-0)
In simulation the **Ignorance (logarithmic) score outperformed both RPS and Brier**; RPS's touted ordinal-distance sensitivity "adds nothing in terms of the actual aims of using scoring rules." Validate updates against Pinnacle-implied probabilities using log-loss **alongside** RPS.
→ Wheatcroft, *The case against the RPS*, arXiv **1908.08980** (JQAS 2022). _Caveat: contested — Constantinou & Fenton (2012) defend RPS for football's ordinality; report both._

### 9. Hybrid ML (ability params → tree model) validates the M3 blend — `HIGH` (3-0)
Feeding Poisson/ranking team-ability parameters into a tree model beats either component alone; on the 2014 WC hold-out the hybrid beat all methods **including betting odds**. Implication: **the highest-value move is upgrading the ability parameters that feed the ensemble (via online updating/shrinkage) — not retraining the nets wholesale.**
→ Groll, Ley, Schauberger & Van Eetvelde, arXiv **1806.03208** (JQAS).

---

## Mistakes to avoid (explicit warnings)

- ❌ **Naive full retrain of the 50-net ensemble on 49k+89 rows.** 89 new rows out of ~49k barely move net weights — high cost, near-zero learning. The signal lives in the *ability parameters / Elo / recency*, which nets update glacially.
- ❌ **Overfitting the ~89-game sample.** A tiny, high-variance, high-stakes sample. Fast unshrunk updates chase noise (e.g., a penalty-shootout "loss" is a coin flip, not evidence of weakness). Always shrink toward the prior.
- ❌ **Ignoring the market.** Pinnacle's closing line is the strongest available forecast; a model that doesn't at least benchmark/blend against it is leaving accuracy on the table.
- ⚠️ **Blindly blending everything toward the market.** It raises calibration but erodes the decorrelated edge that would let you *beat* it. The edge comes from divergence where the market is wrong, not from matching it.
- ⚠️ **Grading only on RPS.** Add log-loss; and note that **beating Pinnacle on ROI ≠ beating it on calibration** — don't conflate the two.

---

## Concrete proposal for THIS system

1. **Feed finals results into Elo with WC weight (K≈60), applied after each match.** This is the cheapest high-impact change; the Elo feature already exists — it just needs to ingest `results_live.csv` outcomes with the tournament K-factor, then flow into M1/M2/M3 features on the next build. (Handle penalty shootouts as draws for rating purposes, or down-weight them.)
2. **Add a market-blend line ("Mercado-informado"):** `p_final = normalize(p_model^(1−w) · p_pinnacle^w)` (log opinion pool), tune `w` on the group+R32 out-of-sample. Keep the pure model line too.
3. **Keep the frozen pre-tournament nets as a clean benchmark line.** Grade *frozen*, *Elo-updated*, and *market-blend* against Pinnacle on **both RPS and log-loss**. Now "does updating help?" is measured, not assumed — resolving the adaptivity-vs-integrity tension empirically.
4. **Longer term:** migrate M2/M3's static ability parameters to a **Bayesian state-space Poisson** with forgetting factors (per-match update, no full retrain). This is the "correct" architecture but a larger build — sequence it after the Elo overlay proves out.

---

## The adaptivity-vs-integrity tension — resolved

There's a genuine principled case for *freezing* (a clean out-of-sample test is the most honest measure of "can the pre-tournament AI beat Pinnacle?"). But you don't have to choose: **run both lines and grade them.** Proper-scoring-rule theory says update on genuine evidence — but only in proportion to its weight (hence shrinkage). The frozen line is your integrity benchmark; the updated line is your best forecast; the scoreboard tells you which wins.

---

## Caveats & open questions

**Caveats:** (1) ~~7 claims went unverified due to verifier/API failures~~ **→ RE-VERIFIED 2026-07-05: all 7 now CONFIRMED (0 refuted)** — see the "Re-verification" section below. The dynamic bivariate-Poisson state-space (Koopman & Lit TI 2012-099), score-driven/GAS models (Koopman & Lit 2019 IJF), the 50%-return EPL betting result, and the Asian-Handicap-efficient / 1X2-biased claim are all confirmed against primary sources (with a small-sample caveat on the 50% figure — see below). (2) The "beat the market with an inferior model" result requires correctly identifying the direction of mispricing and assumes negligible transaction costs — **not** a promise of real-money profit against Pinnacle's low-margin line after vig. (3) The xG ROI figure is a simulated upper bound (2-1 vote). (4) RPS-vs-Ignorance is a live scholarly disagreement. (5) Most evidence is league football; tournament dynamics (short samples, motivation, rotation) may differ.

**Open questions:**
- Optimal K / forgetting-factor magnitude for a 3–4 week, ~89-game World Cup: faster than standard K=60, or does the small high-stakes sample argue for *stronger* shrinkage / slower movement?
- Which dynamic-Poisson family (bivariate state-space vs score-driven/GAS vs commensurate-prior discrete-time) actually delivers the best out-of-sample RPS/log-loss for tournament updating? (Verifier failed on the key sources — worth a follow-up read of Koopman & Lit and Tinbergen 12099.)
- Empirically optimal blend weight `w` between the frozen model and Pinnacle for this system — and does adding odds as a *feature* vs. *post-hoc pooling* better preserve any decorrelated edge?

---

## Re-verification (2026-07-05)

The 7 claims left unverified in the original run (API/verifier failures, not refutations) were re-checked directly against primary sources. **All 7 CONFIRMED, 0 refuted.**

| # | Claim | Verdict | Evidence |
|---|---|---|---|
| 1 | Dynamic discrete-time model uses **random-walk** state evolution for attack/defence | ✅ CONFIRMED | "the evolution component is specified as a random walk for both the attack and defence parameters" — arXiv 2508.05891v1 |
| 2 | Dynamic **bivariate Poisson state-space** (Kalman / importance sampling) | ✅ CONFIRMED | "bivariate Poisson distribution with intensity coefficients that change stochastically over time… state space and importance sampling methods… Kalman filter smoother" — Koopman & Lit, TI 2012-099 (JRSS-A 2015) |
| 3 | Betting: **τ=0.40, 50 bets, 75 units returned on 50 staked, 50% return** | ✅ CONFIRMED (exact) | "when we set τ equal to 0.40, we take 50 bets… play with 1 unit for each of the 50 bets, we expect to receive 75 units… a profit of 25 units, a 50% return, on average" — TI 2012-099, p.21 |
| 4 | Score-driven (GAS) updates on the score of the predictive likelihood | ✅ CONFIRMED | "based on the score of the predictive observation mass function" — Koopman & Lit 2019 IJF 35(2):797 |
| 5 | Pairwise-goal-counts model → **most precise** forecasts | ✅ CONFIRMED (verbatim) | "the dynamic model for pairwise counts delivers the most precise forecasts" — ibid. abstract |
| 6 | Goal-difference model → **best for betting**; both beat benchmarks | ✅ CONFIRMED (verbatim) | "the dynamic model for the difference between counts is most successful for betting, but that both outperform benchmark and other competing models" — ibid. abstract |
| 7 | Asian Handicap efficient/unbiased; 1X2 favourite-longshot bias | ✅ CONFIRMED | "Asian handicap… unbiased estimates of the win rate"; 1X2 "strong pattern of favourite–longshot bias" — "A Tale of Two Markets", MPRA 116925 / IJF 2024 |

**Caveat on claim 3 (do not over-read):** the 50% is an *expected* return from a 1,000-sample bootstrap, on a **small sample (50 bets)**, against **average odds from 28–40 soft bookmakers** on EPL 2010/11–2011/12 — the paper itself flags τ>0.45 as unreliable (<40 bets) and positive returns only emerge for τ>0.12. Beating average soft-book odds is **not** the same as beating Pinnacle's low-margin closing line, so this does not contradict finding #5 (sharp closing lines are very hard to beat).

**Implication for our decision:** claims 2/4/5/6 strengthen finding #3 — the canonical "correct" successor to our static nets is a **dynamic state-space / score-driven Poisson** that updates team attack/defense per match; and the split between "most precise" (pairwise counts) vs "best for betting" (goal difference) is a concrete, verified design signal if betting ROI (not just RPS) becomes a goal.

---

## Sources (primary unless noted)

- Szczecinski & Tihon — unified rating framework (approx. Kalman): arXiv 2104.14012 (JQAS 2023)
- Ridall/Santos-Fernandez et al. — Bayesian state-space Poisson: JRSS-C 74(3):717 (2024/25)
- *Bayesian weighted discrete-time dynamic models* — commensurate/spike-and-slab priors: arXiv 2508.05891v1 (2025)
- *Forecasting soccer with betting odds: a tale of two markets*: Int. J. Forecasting, S0169207024000670 (2024)
- Hubáček & Šír — beating the market / odds-as-feature: arXiv 2010.12508 (IJF 2023)
- arXiv 2604.17194 (2026) — EMH, odds-based vs FIFA-ranking forecasts (cites Leitner et al. 2010)
- Wilkens — xG→Skellam ROI: J. Sports Analytics, 10.1177/22150218261416681 (2026)
- Wheatcroft — *The case against the RPS*: arXiv 1908.08980 (JQAS 2022)
- Groll, Ley, Schauberger & Van Eetvelde — hybrid RF + ability params (WC 2018): arXiv 1806.03208 (JQAS)
- World Football Elo Ratings (K-factor table): en.wikipedia.org/wiki/World_Football_Elo_Ratings (secondary)
- _Unverified (plausible, verifier failed):_ Koopman & Lit — score-driven/GAS (IJF, S0169207018302048); Tinbergen 12099 — dynamic bivariate Poisson state-space
