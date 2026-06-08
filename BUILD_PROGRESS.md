# BUILD PROGRESS — WC2026 v2 (LIVE TRACKER)

> **Purpose:** survive context compaction. This is the resume-from-here document. **Update it after EVERY sub-batch** (check the box + append a line to the Progress Log). If a fresh context starts, READ THIS FILE FIRST, top to bottom.

---

## ⏩ CURRENT STATE — READ FIRST
- **Phase:** 1 — Context page MVP (live scoreboard for June 11 kickoff)
- **Last completed:** Batch 0 (scaffold builds ✓) + 1.1 (data contract)
- **In progress:** — (ready to start 1.2)
- **NEXT ACTION:** **1.2** — write export script → `web/static/data/matches.json` from `results.csv` fixtures + v1 `output/predictions.json` (M1/M2 real; M3/Mercado `null` stubs). Contract: `web/static/data/README.md`.
- **Blockers:** none
- **Verify anytime:** `npm --prefix web run build` (must end "✔ done") or `npm --prefix web run dev` for live preview.
- **Greenlit to build:** YES (Jorge, 2026-06-08). Still: **Jorge drives all git** — I never run add/commit/push/branch/tag; I prepare commands for him (see Git checkpoints).

---

## 🔒 Locked decisions (do NOT re-litigate — pointers to detail)
- **Stack:** SvelteKit + scrollama + D3, static (`@sveltejs/adapter-static`, prerendered). → design `WEBSITE_STORYTELLING_DESIGN.md` §6
- **Repo layout:** `/web` = SvelteKit site · `/v2` = Python model fork · both branch off `v1.0-baseline`. Baseline files (root `*.py`, `results.csv`, `output/`) are FROZEN — never edit. → `memory/baseline-locked.md`
- **Model lineup (4 lines):** M1 Azar (Elo foil) · M2 Red Neuronal (pure ANN, no odds) · M3 Conjunto (market-anchored ensemble + conformal) · **Mercado** (raw bookies, pick-not-scoreline, no ⭐). → design §0.5
- **Context page:** date-grouped Lista (default) + Grupos + Llaves; 2 single-day cards (Recientes = last day w/ finished match, Próximos = next day w/ unplayed); match-row 3 states; predicted **SCORELINE** in-row (modal, not rounded λ); 4-line **scoreboard** = hit-rate (color) + RPS (muted) + exactos; outcome-graded, ⭐ for exact. → design §10
- **Copy:** LatAm Spanish, formal **usted**, no slang. **Marcador** = historic score; **Predicción** = forecast; **Resultado** = outcome. `COPY_ES.md` = single source of truth for all user-facing strings. → `memory/spanish-usted-standard.md`
- **Naming namespaces:** M# = models · P# = roadmap recommendations (P0–P14) · Step A–D = build steps · Round = tournament only.
- **First build target:** P0 (data integrity) + Context-page scaffold against current data; M3/Mercado stubbed until built.

---

## 🧭 Git checkpoints — JORGE runs these (I never mutate git)
- [ ] **CP0 (do before first commit):** `git checkout -b v2`  ← keeps `main` frozen at `v1.0-baseline`
- [ ] **CP1:** after Batch 0 (scaffold runs) — stage `web/` + `BUILD_PROGRESS.md`, commit `"v2 scaffold: SvelteKit skeleton"`
- [ ] **CP2:** after Batch 2 (context page core renders) — commit `"context page core"`
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
- [ ] 1.2 Export script `web/scripts/build_matches.mjs` (or py): `results.csv` fixtures + v1 `output/predictions.json` → `web/static/data/matches.json` (M1/M2 real, M3/Mercado stubbed)
- [ ] 1.3 Run export, validate JSON shape

**Batch 2 — Context page core**
- [ ] 2.1 `MatchRow.svelte` — 3 states (por jugarse / en vivo / finalizado) + 4-line prediction strip
- [ ] 2.2 Date-grouped `Lista` with sticky day headers
- [ ] 2.3 `Recientes` / `Próximos` single-day cards
- [ ] 2.4 4-line `Tablero de aciertos` (hit-rate color + RPS muted + exactos)
- [ ] 2.5 Wire to `matches.json`; browser smoke test

**Batch 3 — Filters, views, polish**
- [ ] 3.1 Filters: Grupo A–L chips · Fase · Equipo search
- [ ] 3.2 `Grupos` view (standings, predicted vs actual) — *stretch*
- [ ] 3.3 `Llaves` view (knockout bracket) — *stretch*
- [ ] 3.4 Expand-on-click row detail (W/D/L, λ, M3 interval, why)
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
- **▶ Jorge git checkpoint CP1 available:** scaffold is commit-ready (do CP0 `git checkout -b v2` first). Files: `web/`, `BUILD_PROGRESS.md`, `web/static/data/README.md`.
