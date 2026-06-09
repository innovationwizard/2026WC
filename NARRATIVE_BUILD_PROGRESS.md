# NARRATIVE SITE — BUILD PROGRESS (LIVE TRACKER)

> Separate live tracker for building the **narrative scrollytelling site** (`/historia`).
> Survives context compaction. **Update after EVERY sub-batch.** Fresh context: read this first.
> Spec: `WEBSITE_STORYTELLING_DESIGN.md` (esp. §ADDENDUM 2). Parent: `BUILD_PROGRESS.md`.

---

## ⏩ CURRENT STATE — READ FIRST
- **Goal:** the self-narrating 3-act scroll story (Modelo 1/2/3) at `/historia`, + the unlisted `/la-caceria` (Hunt) page.
- **Last completed:** **Batches N.A + N.B + N.C COMPLETE** — full 3-act narrative live (guided steps + visuals + math pills + finale), clean build 0 warnings.
- **In progress:** Batch N.D (sandboxes) next.
- **NEXT ACTION:** N.D.1 dice roller. NOTE: still verify scroll-trigger + visual morph in `npm run dev` (headless can't test scroll).
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

### Batch N.D — Sandboxes (martini-glass bowls)
- [ ] N.D.1 Act 1 dice roller (pick matchup → stack scorelines; N slider).
- [ ] N.D.2 Act 2 matchup explorer (any two teams → λ, scoreline, 3 lines, features).
- [ ] N.D.3 Act 3 coverage slider (80↔99% → sets widen).

### Batch N.E — Autoplay + Hunt page + polish
- [ ] N.E.1 Autoplay (text-only auto-scroll toggle, reading cadence).
- [ ] N.E.2 Hunt page `/la-caceria` ← render THE_JOURNEY.md (unlisted).
- [ ] N.E.3 Mobile + a11y + `prefers-reduced-motion`.

---

## 🧭 Git checkpoints (Jorge runs)
- [ ] CP after N.A (skeleton + engine + 1 act live)
- [ ] CP after N.C (three acts narrated)
- [ ] CP after N.E (complete)

---

## 📝 PROGRESS LOG (append-only; newest at bottom)
- Plan created. Deps already present (scrollama, d3). Routes pattern: prerender + fetch('/data/*.json'). Starting N.A.1.
- **Batch N.A ✓.** Files: `src/routes/historia/{+page.svelte,+page.js}`, `src/routes/la-caceria/+page.svelte`, `src/lib/components/Scrolly.svelte`. Hero + rail + Act-1 Monte Carlo histogram (real champion dist, client-side sampling 1→16→500→10k) + finale scaffold. Clean build 0 warnings; both routes prerender. **Scroll-trigger not yet eyeballed (needs a browser).** Next: N.B data export.
- **Batches N.B + N.C ✓.** Files: `v2/eval_export.py`, `web/scripts/build_narrative.py`, `web/static/data/{eval.json,narrative.json}`, `src/lib/components/{MathPill.svelte,Calibration.svelte}`, full rewrite of `historia/+page.svelte`. All 3 acts guided (steps + morphing visuals), 3 math pills, finale podium, rail tracking. Real numbers: 3-way Spain/France/England, RPS M3 0.165<M2 0.166<Elo 0.175, calibration on diagonal. Clean build 0 warnings; all act content in prerendered HTML. **Remaining: N.D sandboxes, N.E autoplay+Hunt+polish. STILL need browser eyeball of scroll/morph.**
