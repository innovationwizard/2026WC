# M3 Player-State — BUILD PLAN (batched, compaction-resilient)

**Companion files:**
- [`M3_PLAYER_STATE_PLAN.md`](M3_PLAYER_STATE_PLAN.md) — WHY (decisions, sourcing, all the resolved Q&A). Read for rationale.
- [`M3_BUILD_PROGRESS.md`](M3_BUILD_PROGRESS.md) — WHERE WE ARE. The live ledger. **Update after every sub-batch.**
- THIS file — WHAT to build, broken into small batches → tiny sub-batches.

---

## ⚠️ RECOVERY PROTOCOL — read this first if you are a fresh / post-compaction session
1. Read [`M3_BUILD_PROGRESS.md`](M3_BUILD_PROGRESS.md) top-to-bottom. It names the **NEXT ACTION** and the last completed sub-batch.
2. Read this file's batch for that sub-batch.
3. **Verify reality against the ledger:** run the "Artifact inventory" check in the progress file — confirm every file the ledger says exists actually exists on disk and is non-empty. If a file is missing that the ledger claims done, STOP and tell Jorge (possible erasure during compaction — exactly the failure mode this system exists to catch).
4. Resume at the NEXT ACTION. Do not redo completed, verified sub-batches.
5. Never delete or overwrite a completed artifact without checking the ledger first.

## Operating conventions (apply to every batch)
- **Cache raw API responses to disk, never re-hit the API for the same call.** Raw JSON is the auditable record; parsing happens later off the cache. (Dirty George.)
- **Find by content, never by position** — team/player matched by name+id, not row index.
- **Point-in-time:** any "state as of date D" aggregates only matches with date < D. No leakage.
- **No silent failure / no silent drop:** every anomaly emits a flag; nothing is discarded quietly.
- **No magic numbers from football taste:** every coefficient is data-derived. (Q3 decision.)
- **`null` → `0`** on stat ingest (API returns null for zero stats).
- **Jorge drives git.** Prepare file lists + messages; never run add/commit/push.
- All new code lives under `v2/m3/` (new subpackage) to keep the locked v1 baseline untouched.

## Target file layout (created progressively, not all at once)
```
v2/m3/
  af_client.py        # B1 — API-Football client: .env key, cached GET, call counter
  af_backfill.py      # B1 — pull fixtures + per-fixture detail to cache/
  cache/              # B1 — raw API JSON, one file per call (gitignored? decide B1.1)
  parse_corpus.py     # B2 — raw cache → clean tables
  corpus/             # B2 — clean parquet/csv tables (matches, cards, squads, player_match)
  rules.py            # B3 — disciplinary rule engine
  weights.py          # B4 — as-of-date key-player weights + modeling dataset
  model.py            # B5 — partial-pooling fit → downweight posterior
  backtest_m3.py      # B6 — point-in-time gate (bootstrap CI + DM test)
  integrate.py        # B7 — wire into λ (only if B6 passes)
  README.md           # short pointer to the two plan docs
```
Tournament scope (league id / seasons): World Cup=1 (2018, 2022) · Euro=4 (2020, 2024) · Copa América=9 (2021, 2024). ~380 matches.

---

## BATCH 1 — Raw ingestion from API-Football  (cache everything, parse nothing yet)
**Why first:** get an immutable on-disk record before any logic, so re-runs cost 0 API calls and parsing bugs never force re-fetching.

- **B1.1 — Client + config.** `af_client.py`: read `API-KEY` from `.env` (note the hyphen in the name), host `https://v3.football.api-sports.io`, header `x-apisports-key`, a `get(path)` that caches responses under `v2/m3/cache/<sanitized-path>.json` and returns cache on hit, a global call counter, and a guard that warns near the 7,500/day cap. Decide & record whether `cache/` is gitignored.
  - *DoD:* `get('/status')` returns Pro plan from cache on 2nd call without an API hit; call counter works.
- **B1.2 — Fixtures backfill.** `af_backfill.py`: for each (league, season) pull `/fixtures`, cache. Print counts; assert vs expected (WC=64, Euro 2020=51 / 2024=51, Copa varies).
  - *DoD:* a cached fixtures file per tournament-season; counts logged and sanity-checked.
- **B1.3 — Per-fixture detail backfill.** For each FINISHED fixture: `/fixtures/events`, `/fixtures/lineups`, `/fixtures/players` → cache. Skip already-cached (resumable). ~380×3 ≈ 1,140 calls; pace under the daily cap; safe to run across days.
  - *DoD:* every finished fixture has 3 cached detail files; a manifest lists fixture_id → which detail files exist.
- **B1.4 — Ingestion audit.** Count cached files, list any fixture missing a detail file or any call that returned an API error, report. No silent gaps.
  - *DoD:* an audit report (printed + written to `corpus/_ingestion_audit.json`) with zero unexplained gaps, or every gap flagged with a reason.

## BATCH 2 — Parse raw cache → clean tabular corpus
- **B2.1 — Matches table.** Parse fixtures → `corpus/matches.*`: fixture_id, league, season, date, home/away team id+name, goals_home, goals_away, status.
  - *DoD:* one row per fixture; scores non-null for finished matches.
- **B2.2 — Card events table.** Parse events → `corpus/cards.*`: fixture_id, date, player_id, player_name, team_id, minute, color (yellow/red/second-yellow). Map detail strings by content.
  - *DoD:* counts of yellow/red sane; spot-check one known match (e.g. fixture 855757 Korea–Ghana = 4 yellows).
- **B2.3 — Squad table.** Parse lineups → `corpus/squads.*`: fixture_id, team_id, player_id, role (start/bench). Full bench captured.
  - *DoD:* ~26 players per team per match (11 start + ~15 bench).
- **B2.4 — Player-match stats.** Parse players → `corpus/player_match.*`: fixture_id, team_id, player_id, minutes, goals, assists, shots/sot if present. **Coalesce null→0.**
  - *DoD:* no nulls in numeric columns; minutes ≤ 120.
- **B2.5 — Canonical team map.** Build API-Football team-name → our `web/static/data/matches.json` canonical names (for the eventual live 2026 join). Reuse/extend the alias approach in `v2/player_state.py`.
  - *DoD:* every team in the corpus maps to a canonical name or is explicitly flagged unmapped.
- **B2.6 — Integrity pass.** Row-count reconciliation, orphan checks (cards/stats referencing unknown fixture or player), anomaly flags. Mirror `v2/data_integrity.py` discipline.
  - *DoD:* `corpus/_integrity_report.json` with all checks green or every exception flagged.

## BATCH 3 — Disciplinary rule engine  (`rules.py`)
- **B3.1 — Encode rules per edition.** Yellow threshold (2 separate matches → 1-game ban), the yellow-wipe stage (historically after QF — VERIFY per edition, it has changed), straight red → ≥1 game. Document the source for each rule inline.
  - *DoD:* a documented rule table; assumptions explicit and cited.
  - **DATA FINDING (B1.3 inspection 2026-06-26):** the events feed `Card` type has ONLY two `detail` values — `Yellow Card` and `Red Card` (no "second yellow" value); offence is in free-text `comments`. So a same-match 2nd yellow surfaces as a `Red Card`. Consequences for B3.2: (a) both straight reds and 2nd-yellow dismissals → `Red Card` → banned next match (same outcome, so we need NOT distinguish them for the suspension feature); (b) **MUST verify** whether a same-match 2nd yellow also emits a separate `Yellow Card` event — if so, naive cross-match yellow counting would double-count. Check on a known 2-yellow sending-off once the full cache lands, and count cross-match yellows from `Yellow Card` events only, treating any `Red Card` as a same-match dismissal (not a carried yellow).
- **B3.2 — Per-(player,fixture) ban derivation.** Sequence matches by date; accumulate cards as-of-date; output banned True/False per upcoming fixture, with triggering cards as provenance.
  - *DoD:* a `suspensions` table: player_id, fixture_id (the missed match), trigger (2yc/red), provenance card ids.
- **B3.3 — Cross-check vs observed absence.** Banned-by-rule players should be absent from the next fixture's full squad. Compute agreement rate; flag disagreements (don't drop).
  - *DoD:* agreement rate reported; disagreements listed with hypotheses.
- **B3.4 — Unit tests on known cases.** Hand-verify a few famous suspensions (e.g. a player who missed a WC semfinal on yellows) against the engine output.
  - *DoD:* ≥3 hand-verified cases pass; written into a small test.

## BATCH 4 — Key-player weights + modeling dataset  (`weights.py`)
- **B4.1 — As-of-date weights.** Per player, per tournament, compute contribution weight as-of-date using the SAME definition as `v2/player_state.py` (goal+assist share), from prior matches only.
  - *DoD:* weights per (team, fixture, player) summing ~1 per team; point-in-time verified (no future leakage).
- **B4.2 — Modeling rows.** One row per (team, fixture): team goals scored, and for the most-key suspended player (if any) their as-of-date weight; plus controls available (opponent strength proxy, home/neutral). This is the unit the model consumes.
  - *DoD:* dataset built; rows with a key suspension flagged; counts logged (~60–120 suspension rows expected).
- **B4.3 — General-absence tag.** Also tag rows where a key player was absent for ANY reason (broader prior), suspension as a labeled subset.
  - *DoD:* absence column populated; suspension ⊆ absence verified.

## BATCH 5 — Partial-pooling model  (`model.py`)
- **B5.1 — Spec + tooling decision.** Hierarchical model: effect of a key suspension (scaled by weight) on team λ, partially pooled across teams/tournaments, weakly-informative prior. **DECIDE tooling here based on installed deps:** PyMC (full Bayesian, credible intervals) vs. empirical-Bayes / shrinkage via statsmodels+numpy (lighter, no new heavy dep). Record the choice and why.
  - *DoD:* model spec written down; tooling chosen; deps confirmed installed (or install path noted for Jorge).
- **B5.2 — Fit.** Fit on the corpus; produce posterior point estimate + credible interval for the suspension downweight (and the yellow-card effect). These ARE the data-derived bounds (Q3).
  - *DoD:* posterior/coefficients saved to `corpus/m3_posterior.json` with intervals.
- **B5.3 — Robustness.** Leave-one-tournament-out stability; posterior-predictive sanity; confirm the effect isn't a single-tournament artifact.
  - *DoD:* stability report; coefficient sign/magnitude stable or flagged unstable.

## BATCH 6 — Point-in-time backtest gate  (`backtest_m3.py`)
- **B6.1 — Test-harness wiring.** Apply the suspension/yellow downweight to baseline λ in a TEST harness only (not production), strictly as-of-date. Reuse `v2/backtest.py` helpers (`wdl`, `rps`, `CUTOFF`).
  - *DoD:* harness produces baseline-λ and adjusted-λ predictions on the held-out split.
- **B6.2 — Significance gate.** Bootstrap CI on ΔRPS + `v2/dm_test.py`. Ship only if adjusted beats baseline with the difference distinguishable from noise.
  - *DoD:* ΔRPS + CI + DM p-value reported.
- **B6.3 — Decision record.** Write the verdict (ship / don't ship) into the progress ledger AND `M3_PLAYER_STATE_PLAN.md`, positive or negative. A null result is a valid, honest outcome — collector + machinery stay, effect dormant.
  - *DoD:* verdict recorded with numbers.

## BATCH 7 — Integration  (ONLY if B6 passes)  (`integrate.py`)
- **B7.1 — Hook into λ.** Wire the downweight into `v2/feature_engine.py` / `v2/main.py` λ path, single entry point.
  - *DoD:* production λ reflects suspensions; baseline numbers unchanged when no suspension applies.
- **B7.2 — Live 2026 derivation.** Derive current-tournament suspensions from API-Football live (+ existing `player_state.py`). Check if WC-2026 season has `injuries=True` for the deferred availability feature.
  - *DoD:* live suspension feed produces a per-team adjustment for upcoming fixtures.
- **B7.3 — Site provenance.** Surface the adjustment on the site with provenance, formal usted Spanish.
  - *DoD:* user-facing copy reviewed; usted standard held.
- **B7.4 — Memory + docs.** Update `memory/m3-player-state-variables.md` with the outcome.
  - *DoD:* memory reflects shipped state.

---

## Open sub-decisions deferred to their batch (don't pre-bake)
- B1.1: is `cache/` committed or gitignored? (Size vs reproducibility.)
- B2: parquet vs csv for corpus tables (depends on installed deps; csv is the safe default).
- B5.1: PyMC vs empirical-Bayes shrinkage (depends on deps + sample size).
