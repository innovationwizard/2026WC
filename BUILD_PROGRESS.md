# BUILD PROGRESS — WC2026 v2 (LIVE TRACKER)

> **Purpose:** survive context compaction. This is the resume-from-here document. **Update it after EVERY sub-batch** (check the box + append a line to the Progress Log). If a fresh context starts, READ THIS FILE FIRST, top to bottom.

---

## ⏩ CURRENT STATE — READ FIRST
- **Phase:** 1 — Context page MVP (live scoreboard for June 11 kickoff)
- **Last completed:** 3.4 expand-on-click row detail (`<details>`: per-model W/D/L bars + xG; M3/Mercado "pendiente")
- **In progress:** Batch 3 (remaining = stretch views + polish)
- **NEXT ACTION:** **3.5** mobile responsiveness + full usted copy pass against COPY_ES → then stretch: 3.2 Grupos view (standings) + 3.3 Llaves view (bracket). (Fase filter + per-match "why" deferred — "why" needs per-match feature attribution = roadmap P10.)
- **MVP core COMPLETE:** legend + scoreboard + cards + filterable calendar + expand detail. The June-11 live-scoreboard skeleton is built.
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
- [ ] **CP3:** after Batch 3 (filters/views) — commit `"context page filters"`
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
- [ ] 3.2 `Grupos` view (standings, predicted vs actual) — *stretch*
- [ ] 3.3 `Llaves` view (knockout bracket) — *stretch*
- [x] 3.4 Expand-on-click row detail — `MatchRow` now a native `<details>`; per-model W/D/L stacked bars + xG (λ) + M3 interval (when present) + Mercado favorito; M3/Mercado show "— pendiente". `grade.js` LINE_NAMES added. ("why"/top-features deferred → P10 per-match attribution.)
- [ ] 3.5 Mobile/responsive + full `usted` copy pass against COPY_ES

### PHASE 2 — Model integrity & real predictions  *(after MVP; feeds the page real data)*
- [ ] Batch 4 — `/v2` Python fork + **P0** data-integrity/leakage layer
- [ ] Batch 5 — **P1** walk-forward backtest (RPS/Brier) → real scoreboard metrics
- [ ] Batch 6 — **P2** Dixon-Coles ρ + time-decay (M2 upgrade, fixes Bug A)
- [ ] Batch 7 — **P3** derive bracket from real fixtures (fixes Bug B)
- [ ] Batch 8 — **P4/P7** market anchor + ensemble (builds M3 point forecast)
- [ ] Batch 9 — **P12** match-level conformal (M3 intervals)

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
