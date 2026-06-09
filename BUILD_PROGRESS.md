# BUILD PROGRESS — WC2026 v2 (LIVE TRACKER)

> **Purpose:** survive context compaction. This is the resume-from-here document. **Update it after EVERY sub-batch** (check the box + append a line to the Progress Log). If a fresh context starts, READ THIS FILE FIRST, top to bottom.

---

## ⏩ CURRENT STATE — READ FIRST
- **Phase:** 1 — Context page MVP (live scoreboard for June 11 kickoff)
- **Last completed:** **BATCH 5 COMPLETE** — Mercado line (manual odds CSV → vig-free implied probs), verified end-to-end
- **In progress:** Phase 2 — next is M3 (Batch 6) or model-quality fixes
- **NEXT ACTION:** **Batch 6 prong-1 (M2 ensemble) SHIPPED** → exporter reads `v2/output/predictions.json`. Options next: (a) commit+deploy, (b) M3 (Batch 7), (c) deferred deep M2 = backtest P1 + validated feature fix (un-bury Spain/England/Argentina). Live workflow: `web/data/README.md` + **`web/data/HOW_TO_ENTER_RESULTS.md`**.
- **CONTEXT PAGE COMPLETE:** Lista (calendar+filters+cards) / Grupos (12 standings tables) / Llaves (stage-odds) views + 4-line scoreboard, expand detail, mobile, flag+short names, Dirty-George null handling. Deploy-ready (Vercel, Root Directory=web).
- **Preview it:** `npm --prefix web run dev`. Page now = legend + **4-line Tablero de aciertos** (zero-state until results) + **Recientes/Próximos** cards + **full date-grouped calendar** (72 fixtures, flag+short names, M1/M2 predictions).
- **Blockers:** none
- **Verify anytime:** `npm --prefix web run build` (must end "✔ done") or `npm --prefix web run dev` for live preview.
- **Greenlit to build:** YES (Jorge, 2026-06-08). Still: **Jorge drives all git** — I never run add/commit/push/branch/tag; I prepare commands for him (see Git checkpoints).

---

## 🔒 Locked decisions (do NOT re-litigate — pointers to detail)
- **Stack:** SvelteKit + scrollama + D3. **Deploy → Vercel** via `@sveltejs/adapter-vercel`; **Vercel Project → Root Directory = `web`** (do NOT move the app to repo root); all routes `prerender=true` → static output (+1 harmless fallback fn). → design `WEBSITE_STORYTELLING_DESIGN.md` §6
- **Repo layout:** `/web` = SvelteKit site · `/v2` = Python model fork · both branch off `v1.0-baseline`. Baseline files (root `*.py`, `results.csv`, `output/`) are FROZEN — never edit. → `memory/baseline-locked.md`
- **Model lineup (4 lines):** M1 Azar (Elo foil) · M2 Red Neuronal (pure ANN, no odds) · M3 Conjunto (market-anchored ensemble + conformal) · **Mercado** (raw bookies, pick-not-scoreline, no ⭐). → design §0.5
- **Context page:** date-grouped Lista (default) + Grupos + Llaves; 2 single-day cards (Recientes = last day w/ finished match, Próximos = next day w/ unplayed); match-row 3 states; predicted **SCORELINE** in-row (modal, not rounded λ); 4-line **scoreboard** = hit-rate (color) + RPS (muted) + exactos; outcome-graded, ⭐ for exact. → design §10
- **Copy:** LatAm Spanish, formal **usted**, no slang. **Marcador** = historic score; **Predicción** = forecast; **Resultado** = outcome. `COPY_ES.md` = single source of truth for all user-facing strings. → `memory/spanish-usted-standard.md`
- **Naming namespaces:** M# = models · P# = roadmap recommendations (P0–P14) · Step A–D = build steps · Round = tournament only.
- **First build target:** P0 (data integrity) + Context-page scaffold against current data; M3/Mercado stubbed until built.

---

## 🧭 Git checkpoints — JORGE runs these (I never mutate git)
- [x] **CP0:** `git checkout -b v2` ✓ (main frozen at v1.0-baseline)
- [x] **CP1:** `cc611b3` v2 scaffold + planning docs ✓
- [x] **CP2:** `9e3c353` Context page MVP ✓ — **pushed to origin/v2**
- [x] **CP3:** `bd35fd8` Context page filters + expand detail ✓ — **pushed to origin/v2**
- [x] **CP4:** `fc93240` Grupos+Llaves views + switcher + Valor tooltip ✓ — **pushed to origin/v2**
- [x] **CP5:** `052dfeb` live results-ingestion mechanism ✓ — **pushed to origin/v2**
- [x] **CP6:** `205cb46` Mercado line + HOW_TO_ENTER_RESULTS guide ✓ — **pushed to origin/v2**
- [x] **CP7:** `f35864c` /v2 fork + M2 ensemble + exporter rewire ✓ — **pushed to origin/v2**
- [x] **CP8:** `7e2835d` P0 data-integrity layer ✓ — **pushed to origin/v2**
- [ ] **CP9:** after next batch
- [ ] (further checkpoints appended as batches complete)

---

## 📋 PLAN — batches → sub-batches

### PHASE 1 — Context page MVP  *(highest ROI; live scoreboard for the tournament)*

**Batch 0 — Scaffold**
- [x] 0.1 Env check (node v22.17.1, npm 11.10.1, git main@737022d, tag v1.0-baseline ✓)
- [x] 0.2 SvelteKit skeleton files in `/web` (package.json, configs, app.html, placeholder route)
- [x] 0.3 `npm install` (85 packages, exit 0) — svelte 5, kit 2, vite 5, adapter-static, d3, scrollama
- [x] 0.4 Build smoke test ✓ (`npm run build` → adapter-static prerendered `web/build/index.html` in 1.53s)

**Batch 1 — Data contract & export**
- [x] 1.1 Define `matches.json` schema → `web/static/data/README.md` (store facts, derive verdicts; 4 lines; Mercado = pick-only)
- [x] 1.2 Export script `web/scripts/build_matches.py` → `web/static/data/matches.json` (M1 from Elo, M2 from neural; M3/Mercado null; venue preserved; modal scorelines)
- [x] 1.3 Ran export, validated: 72 matches, M1+M2 72/72, M3 0/72, 48 teams mapped, 0 flagged

**Batch 2 — Context page core**
- [x] 2.1 `MatchRow.svelte` — 3 states + 4-line prediction strip (M1/M2/M3/Mercado, color-keyed; ✓/✗/⭐ when finalizado) + `grade.js` (verdicts, scoreboard, RPS) + `teams.js`
- [x] 2.2 Date-grouped Lista with sticky day headers (`+page.svelte`, Spanish dates via Intl) + `+page.js` loader
- [x] 2.3 `Recientes` / `Próximos` single-day cards (`Cards.svelte` + `calendar.js` date selection; empty states handled)
- [x] 2.4 4-line `Tablero de aciertos` (`Scoreboard.svelte`: hit-rate full-contrast + RPS muted + exactos + muestra-pequeña tag; zero-state until results)
- [x] 2.5 Wired to `matches.json` ✓ — full page prerenders (scoreboard + cards + calendar). Grading engine `grade.js` unit-tested via `scripts/test_grade.mjs` (11/11 PASS).

**Batch 3 — Filters, views, polish**
- [x] 3.1 Filters: Grupo A–L chips + Equipo search (`FilterBar.svelte`, reactive `$state`/`$derived`/`$bindable`; calendar-only; count + empty state). Fase deferred (group stage only for now).
- [x] 3.2 `Grupos` view — 12 standings tables (Selección/Elo/Valor/Avanza/Campeón, sorted by advance); `Grupos.svelte`. Exporter extended (`build_standings`) → `groups` data; missing squad value → `null` → renders "—" (no phantom €0M).
- [x] 3.3 `Llaves` view — stage-odds table (Octavos→Campeón per team by champion%); `Llaves.svelte`; `knockout` data. Honest note: exact bracket defines after group stage (visual bracket deferred to P3/qualified teams).
- [x] 3.4 Expand-on-click row detail — `MatchRow` now a native `<details>`; per-model W/D/L stacked bars + xG (λ) + M3 interval (when present) + Mercado favorito; M3/Mercado show "— pendiente". `grade.js` LINE_NAMES added. ("why"/top-features deferred → P10 per-match attribution.)
- [x] 3.5 Mobile (strip → 2×2 grid ≤480px; teams/meta sized) + copy registered in COPY_ES §11 (all UI strings usted-clean; native review = launch gate, not build). [Stretch remaining: 3.2 Grupos, 3.3 Llaves]

### PHASE 2 — Make the scoreboard live + real models
**Batch 4 — Results ingestion (live scoreboard mechanism)** ✅ COMPLETE
- [x] 4.1 `web/data/results_live.csv` (separate from locked results.csv); exporter `load_or_init_results` writes blank template (72 ids) if missing, preserves edits on re-run
- [x] 4.2 `apply_results` merges → `status=finalizado` + `result{home,away,outcome}` (outcome derived)
- [x] 4.3 Verified end-to-end (sample Mexico 2–0): row→Finalizado + score 2–0 + M2 ✓⭐ (exact) + M1 ✓ + scoreboard 1/1 + "1 exactos" + Recientes filled; reverted clean (0 finalizado)
- [x] 4.4 Workflow documented → `web/data/README.md` (edit CSV → run exporter → commit/push → Vercel redeploys). No cron/websockets/DB.
- [x] Batch 5 — Mercado ✓: `web/data/market_odds.csv` (decimal 1X2) → exporter `load_or_init_market`/`apply_market` → vig-free implied probs → Mercado pick (no scoreline). Verified: odds 1.40/4.50/7.00 → home 66/21/13 (sum 1.0) → "México 66%"; reverted. Pick-only, outcome-graded (grade.js marketVerdict). Doc in web/data/README.md.
**Batch 6 — FIX M2 (Jorge's pick)** — make the neural model defensible; un-bury Spain (Bug A). ← IN PROGRESS
- [x] 6.1 `/v2` fork created + ran (238s). **CRITICAL FINDING: model NOT reproducible** — same code retrained gives Brazil 23.1%→11.6%, Spain 3.6%→6.6% (TF/hardware nondeterminism despite seed=42). The "Brazil 23%/Spain 3.6%" headline was largely a single noisy training instance. → Fix M2 now has TWO prongs:
- [x] 6.2 **STABILITY (ensemble)** ✓ — `EnsembleNeuralPoisson` (5 nets, avg λ) in /v2. Result: Brazil swing 23↔11.6 tamed → stable 14%; **headline #1 moved Brazil 23% → France 23.2% (consensus-defensible)**. Spain 3.6→7.5. Stable, no seed lottery. **Perf fix:** `predict_lambda` now eager `model(x)` (was `model.predict()` → tf retracing, made ensemble MC stall); + skip feature-importance on nets 2-5. Run 229s.
- [x] 6.6 ✓ Exporter reads `v2/output/predictions.json` (fallback v1); matches.json + Grupos/Llaves now show ensemble (France 23%); build OK; source label fixed.
- [ ] 6.3 **BIAS (features)** — DEFERRED ("train deeper later"). Spain/England/Argentina still buried, Germany inflated (raw `goals_scored_avg_5` opponent-blind). Needs **backtest P1** to validate (don't overfit to consensus) + opponent-adjusted/time-decay features.
- [x] 6.5 **P0 data-integrity ✓** — `/v2/data_integrity.py` (`audit_load` + `IntegrityReport`), wired into `/v2/main.py` at load (fail-loud before modeling). Counts drops (no silent loss), flags anomalies, hard-errors on leakage + unmatched WC team. Verified standalone (clean PASS; leakage tripwire + coverage guard both FIRE on bad input) and in the real pipeline. **Surfaced a real finding: 2 duplicate fixtures in results.csv** (flagged, non-fatal; baseline locked so left as-is but now visible).
- [ ] 6.4 (optional, deferred) Dixon-Coles ρ low-score correction.
**Batch 7 — DEEP M2 FIX (heavy-lift session, 2026-06-08 eve)** ← IN PROGRESS. Order matters: measure → fix → validate → ship.
- [x] 7.1 **Backtest harness (P1)** ✓ — `/v2/backtest.py` (temporal split train<2025 / test≥2025, RPS+Brier, M2 ensemble vs Elo). Added `return_frame` to build_training_data.
- [x] 7.2 **Feature fix** ✓ — the real bug was **TARGET LEAKAGE** (rolling features w/o `.shift(1)` included the current match's goals = label). Fixed with `.shift(1)`. (Opponent-adjust not even needed — leakage was the whole story.)
- [x] 7.3 **VALIDATED** ✓ — **M2 ensemble RPS 0.1662 vs Elo 0.1746 on 1,267 held-out matches (M2 beats Elo by 0.0084).** Real skill, not consensus-fitting. Eyeball: France 25 / Spain 21.6 / Brazil 8.2 / Germany 8.0 — consensus-aligned.
- [x] 7.5 **Final N=50 run** ✓ (1056s) → **France 21.9% / Spain 19.2% / Brazil 11.3% / Germany 7.1%** — consensus-aligned, max-stable. Exporter regenerated matches.json (Grupos/Llaves show it); site builds OK.
- [x] 7.6 **BATCH 7 COMPLETE.** ▶ CP9 available. (Optional later: surface backtest RPS 0.166 in site methodology; refine 1-match prediction staleness.)
- [ ] Batch 8 — M3 (blend+conformal) [deferred]; P3 bracket from fixtures (Bug B) [deferred]

### PHASE 3 — Narrative scrollytelling site  *(long-term / video)*
- [ ] Batch 10+ — shell + sticky-stepper engine; Modelo 1/2/3 guided sections; sandboxes; autoplay. (Detailed when reached.)

---

## 📝 PROGRESS LOG (append-only; newest at bottom)
- **0.1** ✓ Env: node v22.17.1, npm 11.10.1; git `main`@`737022d`; tag `v1.0-baseline` present. node/npm available → SvelteKit viable.
- **0.2** ✓ Wrote `/web` skeleton: `package.json`, `svelte.config.js` (adapter-static), `vite.config.js`, `.gitignore`, `src/app.html`, `src/routes/+layout.js` (prerender), `src/routes/+page.svelte` (placeholder), `static/.gitkeep`.
- **0.3** ✓ `npm --prefix web install` → 85 packages, exit 0. (svelte 5.x, @sveltejs/kit 2.x, vite 5.x, adapter-static 3.x, d3 7.x, scrollama 3.x)
- **0.4** ✓ `npm run build` → adapter-static prerendered `web/build/` (index.html + 404.html + _app + data) in 1.53s; placeholder text present. **Batch 0 DONE — stack confirmed working.**
- **1.1** ✓ Data contract: `web/static/data/README.md`. Key calls: store predictions+results, derive acierto/⭐/scoreboard in UI; M1/M2/M3 carry modal scoreline+probs (M3 +interval); Mercado pick+probs only (no scoreline, no ⭐); knockouts `home/away="Por definir"` + `predictions=null` until teams qualify.
- **Deploy decision (2026-06-08):** Jorge → **Vercel**. Switched `adapter-static` → **`adapter-vercel`** (local build ✓ `✔ done`). Vercel config: **Root Directory = `web`**, framework auto-detected, no other settings needed (don't move build to root). Output: prerendered static + 1 unused fallback fn. `.vercel/` gitignored.
- **▶ Jorge git checkpoint CP1 available:** scaffold is commit-ready (do CP0 `git checkout -b v2` first). Files: `web/`, `BUILD_PROGRESS.md`, `web/static/data/README.md`.
- **1.2/1.3** ✓ Exporter `web/scripts/build_matches.py` → `web/static/data/matches.json`. Inspection-first (Dirty George): verified 72/72 fixture pairs have an M2 prediction, 0 team-name mismatches. M1 = Elo baseline formula (computed from `elo_ratings`); M2 = neural (oriented to home/away from `match_predictions`); modal scoreline = floor(λ); M3/Mercado = null. Venue (city/country/neutral) preserved. Teams Spanish map (48) embedded — ⚠ pending native review (Catar/Arabia Saudita/RD del Congo/Curazao/Nueva Zelanda etc). Regenerate anytime: `.venv/bin/python web/scripts/build_matches.py`. **Batch 1 DONE.**
- **2.1/2.2/2.5** ✓ Context calendar renders. Files: `src/lib/teams.js`, `src/lib/grade.js` (LINES/colors, scoreVerdict/marketVerdict, rps, scoreboard), `src/lib/components/MatchRow.svelte` (3 states + 4-line strip), `src/routes/+page.js` (loads `/data/matches.json` at prerender), `src/routes/+page.svelte` (date-grouped Lista, sticky Spanish day headers, legend). Build verified: 72 `.row` in prerendered `index.html` (175 KB) with México/Sudáfrica/Grupo A/Por jugarse/scoreline/junio. **Calendar Lista WORKING.** Remaining Batch 2: 2.3 cards + 2.4 scoreboard.
- **Team-name display fix (Jorge req):** long names wrapped → ugly. Chose **flag + short name** (GUI-only). `src/lib/teams.js` now holds `{full,short,flag}` for all 48 (the presentation source of truth); `matches.json` reduced to canonical names only (exporter no longer emits `teams`). MatchRow renders `🇧🇦 Bosnia` (nowrap) with `title="Bosnia y Herzegovina"` on hover. Verified in prerender. Short forms (Chequia/Corea/EE. UU./P. Bajos/A. Saudita/C. de Marfil/N. Zelanda/RD Congo) flagged for native review → COPY_ES §10. Rejected pure CSS ellipsis (South Korea/South Africa both → "South…").
- **2.3/2.4/2.5** ✓ **Batch 2 DONE.** New files: `src/lib/calendar.js` (groupByDate, recientes/proximosDate, matchesOn, fmtDay), `src/lib/components/Scoreboard.svelte` (4-line tablero, hit-rate color + RPS muted + exactos + muestra-pequeña), `src/lib/components/Cards.svelte` (Recientes/Próximos single-day), `+page.svelte` (assembles all). Grading proven: `scripts/test_grade.mjs` → 11/11 PASS (acierto/exacto/fallo, market outcome-only, RPS perfect=0 & uniform=0.278, scoreboard agg, M2 RPS<M1). Prerender verified: Tablero/Recientes/Próximos/Calendario completo + zero-state (0/0, "Se activa cuando", "Aún no hay partidos"). Run test anytime: `node web/scripts/test_grade.mjs`. **▶ git checkpoint CP2 available** (context page core).
- **CP2 PUSHED** ✓ `9e3c353` on origin/v2 (Jorge). MVP banked.
- **3.1** ✓ `src/lib/components/FilterBar.svelte` + `+page.svelte` reactive filter (Grupo chips A–L + Equipo search over full/short/canonical names). Calendar filters; scoreboard/cards stay global. Build ✓; chips/search render at initial 'Todos' (72 rows). Interactivity via hydration. Next: 3.4 expand-row detail.
- **3.4** ✓ Expand detail via `<details>`/`<summary>` (accessible, no JS). Detail = per-line W/D/L bar (sky/slate/orange) + xG + Mercado favorito; M3/Mercado "— pendiente". Verified prerender: 74 `<details>`, "xG 2.68", "L 80% · E 13% · V 7%", "pendiente". **Context page MVP core complete** (calendar+filters+cards+scoreboard+detail). Remaining Batch 3 = polish (3.5 mobile/copy) + stretch views (3.2 Grupos, 3.3 Llaves).
- **3.5** ✓ Mobile: `MatchRow` strip → 2×2 grid ≤480px (even, no ragged wrap). Copy registered: COPY_ES §11 lists every implemented Context-page string for native review. Build ✓. **Context page MVP feature-complete + polished + deploy-ready.** Only optional stretch views (Grupos/Llaves) remain in Batch 3. ▶ CP4 available.
- **3.2/3.3** ✓ **BATCH 3 COMPLETE.** Exporter now also emits `groups` (12 standings) + `knockout` (48 stage-odds), missing values `null`. New files: `Grupos.svelte`, `Llaves.svelte`; `+page.svelte` rewritten with Lista/Grupos/Llaves tabs (`view` $state); `+page.js` loads groups/knockout. Verified by temporarily defaulting each view: Grupos (Selección/Avanza/€190M/"—" for S.Africa) + Llaves (Octavos/Cuartos/"El cuadro exacto…"/Brasil) render; reverted to lista. **CONTEXT PAGE (Phase 1) DONE.** ▶ CP4 available (Grupos+Llaves+switcher). Next: Phase 2 model work or deploy.
- **Polish:** "Valor" header tooltip added (Grupos) — "Valor de mercado del plantel (millones de €, Transfermarkt)", dotted-underline + help cursor; COPY_ES §11. (Jorge asked what € meant → not self-evident → clarified in UI.)
- **BATCH 4 ✓ (Phase 2 start) — LIVE SCOREBOARD MECHANISM.** Exporter gained `load_or_init_results` + `apply_results` (build_matches.py); new editable `web/data/results_live.csv` (blank 72-row template, separate from locked results.csv → no leakage, baseline frozen). Verified end-to-end with sample Mexico 2–0: Finalizado row + 2–0 + M2 ✓⭐ + M1 ✓ + scoreboard 1/1 + 1 exactos + Recientes filled; reverted to 0. Workflow doc: `web/data/README.md` (edit CSV→exporter→commit→Vercel; no cron/ws/DB). **The page now lights up automatically when scores are entered.** ▶ CP5 available. Next: Batch 5 Mercado (real odds → 4th line).
- **BATCH 5 ✓ — MERCADO LINE.** Exporter gained `load_or_init_market` + `apply_market`; new editable `web/data/market_odds.csv` (blank 72-row template, decimal 1X2). Converts odds → vig-free implied probs (1/odd normalised) → Mercado {pick, probs} (pick-only, no scoreline, no ⭐). Verified: 1.40/4.50/7.00 → {home:.662,draw:.206,away:.132} sum 1.0 → "México 66%"; reverted. Now 3 of 4 lines real (M1/M2/Mercado); only M3 still pendiente. ▶ CP6 available. Next: Batch 6 M3 ensemble (heavier) OR Batch 8 model-quality (P2 Dixon-Coles → fixes Spain/Bug-A).
- **BATCH 6 (prong-1) ✓ — M2 ENSEMBLE.** Forked pipeline → `/v2` (root frozen). **KEY FINDING: model non-reproducible** (same code retrained: Brazil 23→11.6, Spain 3.6→6.6) — the v1 headline was training noise. Fix: `EnsembleNeuralPoisson` (5 nets, avg λ) → stable + **France-top (defensible) instead of Brazil**. Spain 3.6→7.5 (still low; bias deferred per Jorge "train deeper later"). Perf: eager `model(x)` predict (kills tf-retracing that stalled ensemble MC) + skip redundant feature-importance. Exporter now reads `v2/output/predictions.json`. Files: `/v2/{feature_engine,neural_poisson,monte_carlo,main}.py` + README. **DEFERRED for deep M2:** backtest P1 (RPS) then validated opponent-adjusted/time-decay features. ▶ CP7 available (the /v2 fork + ensemble + exporter rewire).
- **HEAVY-LIFT (Batch 7) IN PROGRESS — 2026-06-08 eve.** **MAJOR FINDING: target leakage in rolling features.** `compute_rolling_features` used `x.rolling(w)` with NO `.shift(1)` → `goals_scored_avg_5` at match T includes T's own goals (= the training label y). Net over-weighted raw recent goals (artificially predictive in-sample) → buried low-scoring Spain. **FIX applied in `/v2/feature_engine.py`: `.shift(1)` on all rolling stats** (use only prior matches). Also added `return_frame` to build_training_data + wrote **`/v2/backtest.py`** (P1: temporal split train<2025/test≥2025, RPS M2-ensemble vs Elo). Minor known item: prediction features now 1-match stale (shift in compute, not split-aware) — refine later if results good. Running shift-fixed pipeline (N=5) to check Spain; backtest queued to validate RPS. **/v2 files edited: feature_engine.py (shift+return_frame), backtest.py (new).** Not yet committed.
- **🎯 LEAKAGE FIX = SPECTACULAR.** Shift-fixed N=5 ensemble champion odds: **France 25.0% (#1), Spain 21.6% (#2!), Brazil 8.2%, Germany 8.0%, Netherlands 4.6%, England 3.1%.** vs before: France 23 / **Spain 7.5 / Germany 20.9 / Brazil 14**. The `.shift(1)` **un-buried Spain (7.5→21.6) AND de-inflated Germany (20.9→8.0) AND tempered Brazil (14→8.2)** — model is now CONSENSUS-ALIGNED (France/Spain top-2). The target leakage WAS Bug A. England still low (3.1 vs ~11 consensus) — secondary. **This is the headline win of the heavy-lift.** Validating via backtest (RPS) next, then final N=50 production run.
- **✅ HEAVY-LIFT COMPLETE (Batch 7).** Backtest VALIDATED: M2 RPS **0.1662** vs Elo 0.1746 on **1,267 held-out matches** (M2 beats Elo). CV in-sample loss rose 0.66→0.78 post-fix = confirmation the leakage was real (no more label-peeking). **Final N=50 production: France 21.9 / Spain 19.2 / Brazil 11.3 / Germany 7.1** — consensus-aligned + max-stable. Shipped to site. **Net result: v1 Brazil-23%/Spain-3.6% outlier → v2 France/Spain top-2, one bug fixed (target leakage), backtest-proven (RPS 0.166), 50-net ensemble.** Uncommitted (CP9): v2/feature_engine.py (shift+return_frame), v2/backtest.py (new), v2/main.py (N=50), v2/output/predictions.json + web/static/data/matches.json (regenerated).
- **P0 DATA-INTEGRITY ✓ (6.5).** `/v2/data_integrity.py` — Dirty George guard: provenance report (rows in→usable→dropped w/ reasons), fail-loud on leakage (future-dated scored row) + unmatched WC team, flags dups/missing-value. Wired into `/v2/main.py` load. Tested: clean PASS + both guards fire on injected bad input + runs in real pipeline. Found 2 dup fixtures in results.csv (flagged). ▶ CP8 available (P0 module + main.py integration).
