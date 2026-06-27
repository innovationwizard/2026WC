# M3 Player-State — LIVE PROGRESS LEDGER

> **This is the single source of truth for WHERE WE ARE.** Update it after EVERY sub-batch — check the box, append to the log, update the artifact inventory and the NEXT ACTION line. Keep entries terse. If you (a future session) just compacted/resumed, read the RECOVERY PROTOCOL in [`M3_BUILD_PLAN.md`](M3_BUILD_PLAN.md) before doing anything.

**Last updated:** 2026-06-26
**Overall phase:** BUILD COMPLETE (B1–B6 + memory). B6 gate verdict = DO NOT SHIP into λ. B7 λ-hook gated out. Only open item: optional informational suspension display for 2026 (Jorge's call).
**FINAL RESULT:** Effect is real & robust in the goals model (b_susp=-0.078, CI excludes 0, stage-confound ruled out, LOTO-stable) BUT too small (~1-3% λ) and too rare (16/290 matches) to significantly improve match-outcome RPS (ΔRPS=+0.000039, DM p=0.137). Honest gate → don't ship; machinery kept dormant; re-run after 2026 adds events.

## ▶ NEXT ACTION
DECIDED (Jorge, 2026-06-26): **Accept do-not-ship; keep dormant; re-run the gate after the 2026 group stage.** No informational display, no weight-definition change. Nothing pending until 2026 data exists.

### RE-RUN RECIPE (after 2026 group stage adds suspension events)
1. Add `('World Cup 2026', 1, 2026)` to `TOURNAMENTS` in `v2/m3/af_backfill.py` (and its expected count to `EXPECTED_TOTAL`). WC2026 yellow-wipe rule is ALREADY encoded in `rules.py` (`RESET_AFTER[(1,2026)] = {'group','qf'}`).
2. `python v2/m3/af_backfill.py fixtures` then `detail` then `audit` (cached; only fetches new 2026 matches).
3. `python v2/m3/parse_corpus.py` → rebuild corpus tables.
4. `python v2/m3/rules.py` → suspensions (check cross-check still ~100%).
5. `python v2/m3/weights.py` → modeling_rows.
6. `python v2/m3/model.py` → refit b_susp + CI.
7. `python v2/m3/backtest_m3.py` → **the gate.** If now significant (CI>0 & DM p<0.05), proceed to B7 (wire `exp(b_susp·w)` into `v2/feature_engine.py`/`main.py`). Else keep dormant.

Legend: `[ ]` todo · `[~]` in progress · `[x]` done & verified · `[!]` blocked/flagged

---

## Batch checklist

### B1 — Raw ingestion (cache everything)
- [x] B1.1 Client + config (`af_client.py`, `cache/`) — cache hit = 0 live calls (verified); `cache/` gitignored; quota via rate-limit headers
- [x] B1.2 Fixtures backfill (`af_backfill.py`) — 290 finished finals matches, all counts ✓. CAUGHT: Euro 2020 (league 4) bundles qualifiers (313 raw); fixed with a by-content `is_finals()` filter excluding "qualifying" rounds → 51.
- [x] B1.3 Per-fixture detail backfill (events/lineups/players) — 290/290 fixtures, 870 live calls, quota 6843 left
- [x] B1.4 Ingestion audit — CLEAN: 290 fixtures, 4552 events, 580 lineup rows (=290×2), 13936 player rows, 0 errors/0 gaps

### B2 — Parse → clean corpus
- [x] B2.1 Matches table — `corpus/matches.csv`, 290 rows, no null scores
- [x] B2.2 Card events table — `corpus/cards.csv`, 1104 rows (1070 yellow / 34 red)
- [x] B2.3 Squad table — `corpus/squads.csv`, 13940 rows (24/team avg, start+bench)
- [x] B2.4 Player-match stats — `corpus/player_match.csv`, 13936 rows, 0 nulls (null→0 ok), max min 120
- [!] B2.5 Canonical team map — DEFERRED to B7.2. Only needed for the LIVE 2026 join (apply model to current teams); historical model B3–B6 works entirely in API-Football's own team_ids, no join needed. Building a 2018–2024→2026 map now is premature.
- [x] B2.6 Integrity pass — `corpus/_integrity_report.json`, ALL GREEN (0 orphans, 2 teams/fixture ×290, squad↔player_match gap=24 explained, domains valid)

### B3 — Disciplinary rule engine (`rules.py`)
- [x] B3.1 Encode rules per edition — `rules.py`; verified via web: all 6 corpus editions wipe yellows after QF only; WC 2026 (live) ALSO wipes after group stage (new FIFA rule) — encoded per-edition. Data finding: red-match yellows carry 0 forward.
- [x] B3.2 Per-(player,fixture) ban derivation — `corpus/suspensions.csv`, 68 events (21 red, 47 2-yellow). Fixed 2 bugs caught by cross-check: (a) accumulation leaked across editions → keyed per (team,league,season); (b) QF amnesty must also clear a pending 2-yellow ban (Cornelius case).
- [x] B3.3 Cross-check vs observed absence — 100% agreement (68/68 banned players absent)
- [x] B3.4 Unit tests — `rules_test.py`, 8 checks pass (incl. Hennessey red positive, Cornelius amnesty negative, no cross-edition leak)

### B4 — Weights + modeling dataset (`weights.py`)
- [x] B4.1 As-of-date key-player weights — `weights.py`; mirrors player_state.py (goals+0.7·assists share); 138/138 sum-to-1 & 138/138 strict point-in-time verified
- [x] B4.2 Modeling rows — `corpus/modeling_rows.csv` (580 team-fixtures); 63 fixtures w/ a suspension, but only **17 with susp_weight>0** (key attacking player). Max susp_weight 0.370, mean(nz) 0.177
- [x] B4.3 General-absence tag — absence_weight in 51 fixtures; suspension⊆absence: 0 violations

### B5 — Partial-pooling model (`model.py`)
- [x] B5.1 Spec + tooling — DECIDED: empirical-Bayes (scipy/numpy/sklearn, no new dep). L2-regularized Poisson GLM; L2 = partial pooling; CV-chosen alpha = data-set bound.
- [x] B5.2 Fit → `corpus/m3_posterior.json`. b_susp=-0.078, 95% CI [-0.130, -0.022] (excludes 0). Downweight exp(b_susp·w); ×0.984 at w=0.2. b_absence≈0 (good sanity).
- [x] B5.3 Robustness — LOTO all 6 editions negative (-0.052..-0.096); CONFOUNDER CHECK: adding knockout-stage control did NOT collapse the effect (-0.070→-0.078), so not a "late rounds score less" artifact.

### B6 — Backtest gate (`backtest_m3.py`)
- [x] B6.1 Test-harness wiring — `backtest_m3.py`, LOTO RPS (out-of-sample b_susp), baseline λ identical both arms
- [x] B6.2 Significance gate — ΔRPS=+0.000039, 95% CI [-0.000009,+0.000092], DM p=0.137; only 16/290 matches affected
- [x] B6.3 Decision — **DO NOT SHIP into production λ.** Direction correct (downweight helps) but not significant. Keep machinery; re-run gate after 2026 adds events. `corpus/m3_gate.json`.

### B7 — Integration (GATED OUT by B6 — λ hook not done)
- [!] B7.1 Hook into λ — NOT DONE: B6 verdict is do-not-ship. Would violate the bulletproof gate.
- [ ] B7.2 Live 2026 derivation — OPTIONAL/informational only (suspension display, no λ change) — Jorge's call
- [ ] B7.3 Site provenance (usted) — only if B7.2 informational display is chosen
- [x] B7.4 Memory + docs — updated `memory/m3-player-state-variables.md` + plan with the B6 verdict

---

## Artifact inventory (verify these exist when the ledger says done)
Run this to check (a missing file marked done = possible erasure → STOP, tell Jorge):
```
ls -la v2/m3/ v2/m3/cache/ v2/m3/corpus/ 2>/dev/null
```
| File | Status | Purpose |
|---|---|---|
| `v2/M3_PLAYER_STATE_PLAN.md` | EXISTS | decisions/rationale |
| `v2/M3_BUILD_PLAN.md` | EXISTS | batched build spec |
| `v2/M3_BUILD_PROGRESS.md` | EXISTS | this ledger |
| `v2/M3_STORY.md` | EXISTS | prose narrative of the whole effort (human-readable) |
| `v2/player_state.py` | EXISTS (committed be7743f) | live collector (data only) |
| `scratchpad/af_probe.py`, `af_probe2.py` | EXISTS (scratchpad) | coverage probes (throwaway) |
| `v2/m3/af_client.py` | EXISTS | B1.1 — cached client, self-test PASS |
| `v2/m3/cache/status.json` | EXISTS (gitignored) | first cached response |
| `v2/m3/af_backfill.py` | EXISTS | B1.2/B1.3 — fixtures + detail, finals filter |
| `v2/m3/cache/fixtures__*.json` | EXISTS (gitignored) | 6 tournament fixture lists |
| `v2/m3/cache/fixtures_{events,lineups,players}__*` | EXISTS (gitignored) | 290×3 detail files |
| `v2/m3/corpus/_ingestion_audit.json` | EXISTS | B1.4 audit report (clean) |
| `v2/m3/parse_corpus.py` | EXISTS | B2 — 4 table parsers + integrity |
| `v2/m3/corpus/matches.csv` | EXISTS | 290 matches |
| `v2/m3/corpus/cards.csv` | EXISTS | 1104 card events |
| `v2/m3/corpus/squads.csv` | EXISTS | 13940 squad rows |
| `v2/m3/corpus/player_match.csv` | EXISTS | 13936 player-match rows |
| `v2/m3/corpus/_integrity_report.json` | EXISTS | B2.6 integrity (all green) |
| `v2/m3/rules.py` | EXISTS | B3 — disciplinary rule engine |
| `v2/m3/rules_test.py` | EXISTS | B3.4 — 8 unit tests (pass) |
| `v2/m3/corpus/suspensions.csv` | EXISTS | 68 derived suspensions (100% cross-check) |
| `v2/m3/weights.py` | EXISTS | B4 — as-of-date weights + dataset |
| `v2/m3/corpus/modeling_rows.csv` | EXISTS | 580 team-fixture modeling rows |
| `v2/m3/model.py` | EXISTS | B5 — empirical-Bayes Poisson GLM |
| `v2/m3/corpus/m3_posterior.json` | EXISTS | b_susp + CI + LOTO + downweight |
| `v2/m3/backtest_m3.py` | EXISTS | B6 — LOTO RPS gate |
| `v2/m3/corpus/m3_gate.json` | EXISTS | B6 verdict (do-not-ship) |
| `v2/m3/af_backfill.py` | not yet | B1.2–B1.3 |
| `v2/m3/cache/` | not yet | raw API JSON |
| `v2/m3/corpus/` | not yet | clean tables |
| `v2/m3/rules.py` | not yet | B3 |
| `v2/m3/weights.py` | not yet | B4 |
| `v2/m3/model.py` | not yet | B5 |
| `v2/m3/backtest_m3.py` | not yet | B6 |
| `v2/m3/integrate.py` | not yet | B7 |

---

## Running log (append-only; newest at bottom)
- **2026-06-26** — Plan & ledger created. All upstream decisions resolved: scope = suspension+yellow (availability+form deferred); single-source API-Football Pro (key in `.env`, gitignored); suspensions DERIVED from card events + FIFA rules (not editorial labels); StatsBomb dropped; cross-source join eliminated; bounds data-derived via partial pooling. Probes confirmed spine (cards/lineups/stats) present for WC18/22, Euro20/24, Copa21/24; `injuries=False` on history (irrelevant — we derive suspensions). 9/7500 API calls used. **Build not started.**
- **2026-06-26** — B1.1 DONE. `v2/m3/af_client.py` built: reads `API-KEY` from `.env`, on-disk cache, live-call counter, quota from rate-limit headers. Self-test PASS (cache hit makes 0 live calls). Decision recorded: `v2/m3/cache/` gitignored (raw API redistribution not permitted; repo is public). `.gitignore` updated. Quota after self-test: 7492 remaining.
- **2026-06-26** — BATCH 6 COMPLETE + BUILD DONE. `backtest_m3.py` LOTO RPS gate: ΔRPS=+0.000039 (direction correct), 95% CI [-0.000009,+0.000092], DM p=0.137, 16/290 affected. VERDICT: DO NOT SHIP into production λ (not significant). B7 λ-hook gated out (would violate the gate). Machinery kept dormant; re-run gate after 2026 group stage adds suspension events. Memory updated. The bulletproof discipline held: no taste-based number, no shipping an effect the data can't support.
- **2026-06-26** — BATCH 5 COMPLETE. `model.py` empirical-Bayes Poisson GLM (chosen by Jorge over PyMC; no new dep). b_susp=-0.078, bootstrap 95% CI [-0.130,-0.022] excludes 0. Downweight=exp(b_susp·w) (×0.984 at w=0.2). LOTO stable (all 6 editions negative). Confounder ruled out: stage control did not collapse the effect. b_absence≈0. `m3_posterior.json` written.
- **2026-06-26** — BATCH 4 COMPLETE. `weights.py`: as-of-date goal-involvement weights (mirrors player_state.py), strict point-in-time (138/138 verified), normalize to 1. `modeling_rows.csv` (580 team-fixtures). KEY REALITY: only 17 key-player suspension events (susp_weight>0) — thin; broader absence prior = 51. B5 leans on partial pooling; B6 gate may return null (honest). suspension⊆absence: 0 violations.
- **2026-06-26** — BATCH 3 COMPLETE. `rules.py` derives suspensions deterministically from cards + per-edition FIFA/UEFA/CONMEBOL rules (verified via web; WC2026 group-stage wipe is new). 68 events (21 red, 47 2-yellow), 100% cross-check vs observed absence. Two bugs caught BY the cross-check and fixed: cross-edition accumulation leak (Ronaldo 2018→2020) and QF-amnesty not clearing a pending 2-yellow ban (Cornelius). `rules_test.py`: 8 checks pass. Data finding confirmed: same-match 2nd yellow = [Y,Y,R]; red-match yellows carry 0 forward.
- **2026-06-26** — BATCH 2 COMPLETE. `parse_corpus.py` built 4 clean tables from cache (0 API calls): matches(290), cards(1104: 1070Y/34R), squads(13940), player_match(13936, null→0, 0 nulls). B2.6 integrity ALL GREEN (no orphans, 2 teams/fixture ×290, squad↔player_match gap 24 explained as roster-edge cases). B2.5 (canonical team map) DEFERRED to B7.2 — only needed for live 2026 join, not the historical model.
- **2026-06-26** — BATCH 1 COMPLETE. B1.2: `af_backfill.py`, 290 finished finals matches (caught+fixed Euro-2020 qualifier bundling via by-content `is_finals()` filter). B1.3: cached events/lineups/players for all 290 (870 live calls). B1.4: ingestion audit CLEAN (0 errors/0 gaps); `corpus/_ingestion_audit.json` written. Inspection findings recorded in build plan: card feed has only Yellow/Red detail values (2nd-yellow→Red Card; verify no double-yellow double-count in B3); player stats null→0 needed; per-match position/substitute fields available. Quota: 6843 remaining.
