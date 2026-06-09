# NARRATIVE SITE — BUILD PROGRESS (LIVE TRACKER)

> Separate live tracker for building the **narrative scrollytelling site** (`/historia`).
> Survives context compaction. **Update after EVERY sub-batch.** Fresh context: read this first.
> Spec: `WEBSITE_STORYTELLING_DESIGN.md` (esp. §ADDENDUM 2). Parent: `BUILD_PROGRESS.md`.

---

## ⏩ CURRENT STATE — READ FIRST
- **Goal:** the self-narrating 3-act scroll story (Modelo 1/2/3) at `/historia`, + the unlisted `/la-caceria` (Hunt) page.
- **Last completed:** **🎉 NARRATIVE SITE COMPLETE — all batches N.A–N.E done.** 3-act story + 3 sandboxes + math pills + autoplay + unlisted Hunt page. Clean build 0 warnings; 3 pages prerender (historia/index/la-caceria).
- **In progress:** — (done)
- **NEXT ACTION:** none required. Optional: eyeball scroll/sandboxes in `npm run dev` (headless can't test interaction); then deploy. Possible polish later: per-match feature attribution, voice for the video (separate).
- **Blockers:** none. Jorge drives git.

---

## 🔒 Locked design (from §ADDENDUM 2 — do NOT re-litigate)
- **Routes (same /web app):** `/` Context (exists) · `/historia` narrative · `/la-caceria` UNLISTED Hunt (no nav link, direct URL only).
- **Stack:** SvelteKit + scrollama + d3 (ALL already installed — **no new deps**), prerendered static → Vercel.
- **Shape:** 3-act staircase, each act hands off on its own weakness. Arc **Certeza → Inteligencia → Honestidad**.
- **Mechanism:** sticky-stepper (pinned visual + scroll-driven narrated text steps that morph it). Guided → sandbox (martini glass). Scroll = pacing.
- **Acts:** A1 Azar (HOPs + 10k histogram) · A2 Red Neuronal (3-way agreement + backtest RPS 0.166, NOT the old "disagreement") · A3 Conjunto (conformal sets + calibration + "tighter≠better").
- **Per-act math pill** `▸ Ver la mate que hay detrás` (text-only, formulas, names models, ~4-5 lines). Drafts in §ADDENDUM 2.
- **Autoplay = TEXT-ONLY** (no voice — that's the video).
- **Data: real, from the pipeline.** New export needed: champion distribution, backtest summary, 3-model champion odds, calibration curve.
- **Numbers (live):** France/Spain ~17-18%, England ~10-13%. Backtest RPS 0.166 (M2) vs 0.175 (Elo).
- **All user text:** Latin-American Spanish, formal **usted**.

---

## 📋 PLAN — batches → sub-batches

### Batch N.A — Skeleton + sticky-stepper engine ✅ COMPLETE
- [x] N.A.1 Routes `/historia/+page.svelte` + `/la-caceria/+page.svelte` (noindex) — both prerender; Hunt unlisted.
- [x] N.A.2 `src/lib/components/Scrolly.svelte` — scrollama sticky-stepper (visual + stepBody snippets, bind:active, mobile = visual pins top).
- [x] N.A.3 Shell: hero + fixed progress rail (01 Azar/02 Red Neuronal/03 Conjunto) + finale scaffold + dark/gold theme.
- [x] N.A.4 Act 1 wired via Scrolly: real-data Monte Carlo histogram (1→16→500→10k tournaments, client-side sampling from real champion dist). Clean build, 0 warnings. `historia/+page.js` loads matches.json.

### Batch N.B — Narrative data export ✅ COMPLETE
- [x] N.B.1 `v2/eval_export.py` → `v2/output/eval.json` (held-out RPS M1/M2/M3 + calibration curve) + `web/scripts/build_narrative.py` → `narrative.json` (champion 3-way, backtest, calibration). **Real numbers: RPS M3 0.165 < M2 0.166 < Elo 0.175; calibration on the diagonal.**

### Batch N.C — The three acts ✅ COMPLETE
- [x] N.C.1 Act 1 · Azar — Monte Carlo histogram (1→16→500→10k), real dist.
- [x] N.C.2 Act 2 · Red Neuronal — champ 3-way bars (M1 vs M2) → RPS bars (backtest trophy). Visual switches by step mode.
- [x] N.C.3 Act 3 · Conjunto — conformal set examples → `Calibration.svelte` reliability curve + "tighter≠better".
- [x] N.C.4 `MathPill.svelte` + per-act math (unicode formulas, NO katex dep). + finale podium + rail IntersectionObserver tracking.

### Batch N.D — Sandboxes ✅ COMPLETE
- [x] N.D.1 `DiceRoller.svelte` — pick fixture → roll +1/+25/+1000 → scoreline histogram + W/D/L (real Poisson from match λ).
- [x] N.D.2 `MatchupExplorer.svelte` — pick fixture → M1/M2/M3/Mercado picks+probs + λ + conformal set.
- [x] N.D.3 `CoverageSlider.svelte` — 80→99% slider → set widens (uses `tau_by_coverage` 0.258→0.067; added to eval_export + narrative.json).

### Batch N.E — Autoplay + Hunt page + polish ✅ COMPLETE
- [x] N.E.1 Autoplay — `▶ Reproducir solo` (text-only ~84px/s auto-scroll, pauses on wheel/touch).
- [x] N.E.2 Hunt page `/la-caceria` — `build_journey.py` (md→html, no dep) → `the-journey.html`, rendered with serif typography. Unlisted (noindex, no link).
- [x] N.E.3 Reduced-motion (all steps legible, no transitions) + mobile (visual pins top) + aria labels on controls.

---

## 🧭 Git checkpoints (Jorge runs)
- [x] **`d6966eb`** — N.A+N.B+N.C: skeleton + engine + 3 acts + math pills + finale + data exports — **pushed to origin/v2**.
- [ ] CP after N.E (sandboxes + autoplay + Hunt + polish)

---

## 📝 PROGRESS LOG (append-only; newest at bottom)
- Plan created. Deps already present (scrollama, d3). Routes pattern: prerender + fetch('/data/*.json'). Starting N.A.1.
- **Batch N.A ✓.** Files: `src/routes/historia/{+page.svelte,+page.js}`, `src/routes/la-caceria/+page.svelte`, `src/lib/components/Scrolly.svelte`. Hero + rail + Act-1 Monte Carlo histogram (real champion dist, client-side sampling 1→16→500→10k) + finale scaffold. Clean build 0 warnings; both routes prerender. **Scroll-trigger not yet eyeballed (needs a browser).** Next: N.B data export.
- **Batches N.B + N.C ✓.** Files: `v2/eval_export.py`, `web/scripts/build_narrative.py`, `web/static/data/{eval.json,narrative.json}`, `src/lib/components/{MathPill.svelte,Calibration.svelte}`, full rewrite of `historia/+page.svelte`. All 3 acts guided (steps + morphing visuals), 3 math pills, finale podium, rail tracking. Real numbers: 3-way Spain/France/England, RPS M3 0.165<M2 0.166<Elo 0.175, calibration on diagonal. Clean build 0 warnings; all act content in prerendered HTML.
- **Batches N.D + N.E ✓ — NARRATIVE SITE COMPLETE.** Files: `src/lib/components/narrative/{DiceRoller,MatchupExplorer,CoverageSlider}.svelte`, `web/scripts/build_journey.py`, `web/static/the-journey.html`, `src/routes/la-caceria/{+page.svelte,+page.js}`, autoplay+sandboxes in `historia/+page.svelte`, reduced-motion in `Scrolly.svelte`, `tau_by_coverage` in eval_export/narrative.json. 3 sandboxes (dice/explorer/coverage), text-only autoplay, unlisted Hunt page (THE_JOURNEY.md rendered). Clean build 0 warnings; 3 pages prerender. **Still worth a browser eyeball of scroll + sandbox interactions before deploy.**
