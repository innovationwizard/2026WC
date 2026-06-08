# WC2026 — Self-Narrating Website: Storytelling UI Design & Research

**Date:** 2026-06-08
**Status:** Research + design. Targets a future **v2/v3 presentation layer**; does not touch the locked `v1.0-baseline`. The current `generate_html.py` (one static page) is the thing we're outgrowing.
**The brief (verbatim intent):** the project now has *"3 different depth rounds AT LEAST,"* so it needs *"a full website, no longer a standalone page,"* one that can *"tell the story itself, even (or as close as possible to) without me telling the narrative with my talking head."*

**The single hardest requirement, stated plainly:** the site must **narrate itself.** Most "data sites" assume a human voice-over fills the gaps. Ours can't. So every design choice below is judged against one test: *if Jorge says nothing, does the story still land?*

---

## 0. The core idea (if you read nothing else)

Build the site as **three "martini glasses" in a row** — one per model — connected by transitions, riding on a **sticky-stepper scrollytelling** spine.

- **Martini glass** (Segel & Heer's most-blended genre): each model's section starts *author-driven* (a narrow, guided path of scroll-steps that tell the story for you) and then *opens* into a *reader-driven* sandbox (play with the model yourself). Guided first so a passive viewer gets the whole narrative; open after so a curious one can explore. This is the structure that lets the site work **with or without** you talking.
- **Sticky-stepper:** a visualization pins to one side of the screen; short narrative blocks scroll past on the other; each block ("step") updates the pinned visual. **The steps are the script.** This is how the page narrates — the scroll *is* the pacing, the text *is* the voice-over.
- **The emotional arc** (from the v2 roadmap): **Certainty → Intelligence → Honesty.** Model 1 shows the machine is blind; Model 2 gives it sight; Model 3 gives it the humility to say how much it still can't see. That arc is the spine the whole site hangs on.

---

## 0.5 The model lineup (locked 2026-06-08)

The site compares **three distinct in-house models plus the betting market** — four lines on every match and on the running scoreboard:

| Line | Name | What it is | Role · arc |
|---|---|---|---|
| **M1** | Modelo 1 — Azar | Monte Carlo over the Elo/historical baseline (existing `EloBaselineModel`) | blind-chance foil · **Certeza** |
| **M2** | Modelo 2 — Red Neuronal | the from-scratch ANN (Dixon-Coles + bivariate Poisson — P2/P5), **no external odds** | the "I built it myself" pure model · **Inteligencia** |
| **M3** | Modelo 3 — Conjunto | market-anchored **ensemble** (ANN + GBT + market — P7/P4) **with conformal intervals (P12)** | max-accuracy + honest uncertainty · **Honestidad** |
| **Mercado** | Mercado | betting-market implied probabilities (Polymarket / Bet365 …) | the external yardstick to beat |

What this locks:
- **M3 is a *distinct* point-forecaster, not "M2 + intervals."** The three models produce three genuinely different scorelines and three different accuracy scores; conformal intervals are M3's *uncertainty feature* layered on its own ensemble forecast.
- **Pure-vs-anchored is resolved by having both:** M2 pure (no odds — the from-scratch brag), M3 market-anchored (max accuracy). Narrative = "my pure net, my best blended model, and the raw market — watch them race."
- **Mercado is a pick, not a scoreline.** Markets price 1X2 outcomes, not exact scores. So Mercado shows its implied favorite + probability (e.g. `Mercado ⟶ España 58%`), graded on **outcome only** — M1/M2/M3 can earn the exact-score ⭐; **Mercado cannot**.

---

## 1. Research — how the best in the world do it

### 1.1 The scrollytelling canon
- **NYT "Snow Fall" (2012)** invented the form — pinned media + scrolling narrative held readers ~12 min, 3.5M views/week. It proved a webpage can hold a long story without a presenter.
- **The Pudding** is the gold standard for *data* scrollytelling and literally authors the tooling (**scrollama.js**, IntersectionObserver-based, performant). Their lesson: **let the data carry the weight; restraint beats spectacle** — not every section needs motion.
- **Five recognized techniques** (Newsroom scrollytelling vocabulary): graphic sequences, animated transitions, panning/zooming, scrolling-through-movies, and auto-playing animated content. We'll use the first two and the last heavily.
  Sources: [Snow Fall / scrollytelling examples (Shorthand)](https://shorthand.com/the-craft/scrollytelling-examples/index.html), [The Pudding — how to implement scrollytelling](https://pudding.cool/process/how-to-implement-scrollytelling/), [Scrolling into the Newsroom (vocabulary)](https://benjamins.com/catalog/idj.22005.oes).

### 1.2 Segel & Heer — *Narrative Visualization* (2010), the framework
The canonical paper (≈2,100 citations) defines three genres on an author-driven ↔ reader-driven axis:
- **Martini Glass** — guided intro, then open exploration. *(our per-model structure)*
- **Interactive Slideshow** — author guidance with interaction inside each step.
- **Drill-Down Story** — a theme the reader navigates by picking cases. *(our Modelo-2 matchup explorer)*
The finding that matters: **the best stories blend author guidance with reader freedom.** Pure-guided is a video; pure-open is a tool nobody understands. The blend is the craft.
Source: [Segel & Heer, *Narrative Visualization* (Stanford vis)](http://vis.stanford.edu/files/2010-Narrative-InfoVis.pdf).

### 1.3 Distill.pub & explorable explanations — teaching by play
Distill's principle: integrate **explanation + data + interactive visualization** so the reader changes parameters and *immediately sees what happens* — building understanding dynamically instead of consuming it passively. Nicky Case's **Explorable Explanations** movement adds the pacing rule: **introduce the "sandbox" gradually — shallow end first, then deeper.** Bartosz Ciechanowski's pieces (Lights & Shadows, etc.) show the long-form ceiling: embedded micro-simulations the reader *operates*. For us this means each model's interactive should **start on rails and earn its freedom.**
Sources: [Distill](https://distill.pub/), [Nicky Case — Explorable Explanations](https://blog.ncase.me/explorable-explanations/), [Andy Matuschak — Explorable explanations notes](https://notes.andymatuschak.org/Explorable_explanations).

### 1.4 Uncertainty visualization — the secret weapon for Models 1 & 3
- **Hypothetical Outcome Plots (HOPs):** instead of a static error bar, **animate through equally-likely outcomes.** Untrained viewers judge uncertainty *far* more accurately from animated HOPs than from static aggregate plots. This is *exactly* our Monte Carlo — "watch a different tournament each time" IS a HOP.
- **Quantile dotplots / Plinko** (NYT election-needle lineage): discrete dots beat smooth density curves for lay legibility and honesty — people count dots, they misread shaded areas. Election forecasts also showed these visuals *move emotions and trust* — powerful, handle with care.
- **Claus Wilke, *Fundamentals of Data Visualization* — "Visualizing Uncertainty":** the reference for doing it without lying.
Sources: [HOPs — Experiencing the Uncertain (UW IDL)](https://medium.com/hci-design-at-uw/hypothetical-outcomes-plots-experiencing-the-uncertain-b9ea60d7c740), [Wilke — Visualizing uncertainty](https://clauswilke.com/dataviz/visualizing-uncertainty.html).

### 1.5 Monte Carlo, made watchable
The **MCMC Interactive Gallery** (chi-feng) is the reference feel: samples *accumulate into a histogram in real time*, with toggles for proposals/targets/samples. The pedagogy literature is blunt: sampling is hard to explain in words and **animation is the best route** — let people *watch the randomness*.
Source: [MCMC Interactive Gallery](https://chi-feng.github.io/mcmc-demo/app.html).

### 1.6 The current bar
The **Information is Beautiful Awards 2025** (≈1,000 entries, judged on beauty + storytelling + impact + innovation) is the level to benchmark against if this becomes the "international authority" video's companion site.
Source: [IIB Awards 2025 winners](https://informationisbeautiful.net/2025/information-is-beautiful-awards-winners/).

---

## 2. Governing design principles (the rubric every screen must pass)

1. **The step text is the narrator.** Write each scroll-step as a sentence you'd *say*. If it reads like a caption, rewrite it until it reads like narration.
2. **One idea per step.** Progressive disclosure. Never show full complexity at once — reveal it as the reader scrolls into it.
3. **Every visual self-labels its punchline.** Direct labeling, inline annotations, callout arrows. No chart should depend on "as I'll explain." The "so what" is always on screen.
4. **Show, then let play** (martini glass). Guided narrative first; sandbox after; sandbox starts on rails.
5. **Make uncertainty felt, not stated.** Animate outcomes (HOPs), count dots (quantile dotplots) — don't just draw a band and assert it.
6. **Restraint over spectacle.** Motion is punctuation, not wallpaper. If an animation doesn't carry meaning, cut it.
7. **Honest by construction.** The site's *content* is humility (Model 3); its *form* must match — no fake precision, no narrowing-for-drama (see §4.3).
8. **Degrade gracefully.** Mobile = vertical, simplified visuals, fewer simultaneous layers. Respect `prefers-reduced-motion`. Works without a presenter *and* without a fast machine.

---

## 3. Site architecture (the shell)

```
┌──────────────────────────────────────────────────────────────┐
│  HERO  — poses the question, promises the 3 models            │
│         "¿Quién gana el Mundial 2026? — ¿y cómo lo sabría?"  │
│         subtle animated bracket/field; one CTA: ▼ scroll      │
├──────────────────────────────────────────────────────────────┤
│  STICKY PROGRESS RAIL (persists):  ① Certeza ─ ② Inteligencia │
│                                    ─ ③ Honestidad             │
├──────────────────────────────────────────────────────────────┤
│  MODELO 1  (martini glass: guided scrolly → sandbox)          │
│  ── transition ──                                             │
│  MODELO 2  (martini glass: guided scrolly → matchup explorer) │
│  ── transition ──                                             │
│  MODELO 3  (martini glass: guided scrolly → confidence sandbox)│
├──────────────────────────────────────────────────────────────┤
│  FINALE — honest leaderboard + the one-line thesis +          │
│           methodology/credits + "play it again / autoplay"    │
└──────────────────────────────────────────────────────────────┘
```

**Reusable sticky-stepper unit** (every model's section is built from this):
```
┌───────────────────────────┬──────────────────────────────┐
│                           │  ┌────────────────────────┐  │
│     STICKY VISUAL          │  │ step ①  (narration)    │  │
│     (pinned; re-renders    │  └────────────────────────┘  │
│      when active step       │  ┌────────────────────────┐  │
│      changes)              │  │ step ②  ◀ ACTIVE       │  │
│   [ chart / sim / bracket ]│  └────────────────────────┘  │
│                           │  ┌────────────────────────┐  │
│   ▸ inline annotation      │  │ step ③                 │  │
│                           │  └────────────────────────┘  │
└───────────────────────────┴──────────────────────────────┘
   (mobile: visual pins to TOP, text scrolls beneath)
```

**Brand continuity:** keep the v1 palette (dark `#0a0e17`, gold `#d4af37` champion, silver, accent blue) so the site reads as the same project, leveled up. **Language: Spanish** (the office + the friend's audience), with an EN toggle as a stretch.

---

## 4. Per-model UI design

### 4.1 MODELO 1 — "La Máquina de Azar" (Certainty / Stochastic Baseline)
**Story job:** kill the idea that a prediction is *a single answer*. A tournament is a probability machine; chance alone is wide and blind. Plants the seed Model 2 pays off.

**Sticky-stepper sequence** (the pinned visual evolves down the column):
```
 step 1  "Un partido no es una predicción.        VISUAL: one match card.
          Es un dado, lanzado 104 veces."        λ_A=1.9  λ_B=1.1  → 2–1
 step 2  "El mismo partido, otra noche…"          HOP: same λ's, re-sampled
          (scroll re-rolls the score live)         each scroll → 1–1, 0–2, 3–1…
 step 3  "Multiplíquelo por todo el torneo."        VISUAL: one full 104-match
          (one bracket fills via simulation)        bracket animates to a champion
 step 4  "Córralo otra vez. Otro campeón."         bracket re-runs → different winner
 step 5  "Ahora córralo 10,000 veces."             HISTOGRAM builds live, bars rising,
          counter ticks 1→10,000                    champion distribution emerges WIDE
 step 6  "Nadie es destino. Esto es lo que          final wide distribution, annotated:
          el puro azar 'sabe'."                      "blind to who's actually good"
```
**Key techniques:** HOPs (steps 2,4 = *feel* the variance), MCMC-gallery accumulation (step 5 = *watch* 10k pile up). This is the most viscerally convincing screen on the site — people *get* Monte Carlo by watching it, never by hearing it defined.

**Sandbox (martini opens):** a "🎲 Tírelo usted" panel — pick any matchup, hit a button, watch N simulations stack into a scoreline distribution; a slider for N (10 → 10,000) so they feel the law of large numbers. Starts pre-loaded with one matchup (on rails), then frees up.

**Transition to M2:** the wide distribution literally *can't tell Spain from Saudi Arabia* — freeze on that and hand off: *"El azar conoce las reglas. No conoce a los equipos. Vamos a enseñarle."*

---

### 4.2 MODELO 2 — "La Red Aprende" (Intelligence / the ANN + the disagreement)
**Story job:** show what the neural net *adds* — learned attack/defense from 47 features — and stage the **honest, braggable centerpiece: where the ANN disagrees with the markets, and why.** This is where v1's Spain-outlier becomes a *feature of the talk*, not a bug to hide.

**Sticky-stepper sequence:**
```
 step 1  "El azar era ciego. 47 variables le dan ojos."   VISUAL: 47 feature chips
                                                            flow into a network diagram
 step 2  "La red aprende a atacar y defender."             network lights up input→
          (highlight top features as bars grow)             hidden→ λ; elo_diff,
                                                            recent-form bars rise
 step 3  "Para España vs Uruguay, así nace el λ."          one matchup → λ_A, λ_B,
                                                            scoreline probability grid
 step 4  "Pero el azar puro mentía en los 0-0 y 1-0.       Dixon-Coles: independent vs
          La corrección de correlación."                    correlated scoreline grid
                                                            (low-score cells re-weighted)
 step 5  "Ahora la parte interesante:                       SLOPE CHART — 3 columns:
          ¿en qué NO coincidimos con el mundo?"             ANN | Elo | Mercado, lines
                                                            connecting each team's odds
 step 6  "El mundo entero pone a España arriba.             spotlight Spain's line
          Nuestra red, sexta. ¿Genialidad o error?"         diving from top to 6th;
                                                            annotation invites judgment
```
**The slope chart (step 5–6) is the signature visual of the whole site.** Three vertical axes — *Nuestra Red · Elo · Consenso del Mercado* — each team a connecting line. Agreement = flat lines; disagreement = steep crossings. Spain's plunge and Brazil's climb are *immediately* visible. This is the intellectually honest move from the roadmap: don't bury the outlier — **frame it as the question the rest of the model answers.**

**Sandbox (drill-down genre):** **"Explorador de Partidos"** — pick any two of the 48 teams → λ's, the scoreline grid, W/D/L, *and* the three-model comparison for that matchup, plus the feature contributions that drove it (provenance: "*why*, not just *what*"). This is the part technical colleagues will play with for ten minutes.

**Transition to M3:** the ANN is confident — *too* confident? *"Tenemos respuestas. Pero, ¿qué tan seguros deberíamos estar? La parte más sofisticada del modelo no es la respuesta — es saber cuánto no sabe."*

---

### 4.3 MODELO 3 — "Honestidad con Garantía" (Honesty / market-anchored ensemble + Conformal)
**Story job:** the climax is **not a sharper answer — it's a calibrated, partly-guaranteed one.** Conformal intervals at the match level (rigorous); labeled simulation bands at the tournament level (honest). And explicitly debunk the "fancier math = more certain" lie.

**Sticky-stepper sequence:**
```
 step 1  "Lo más sofisticado no es la respuesta.           VISUAL: a single match
          Es saber cuánto no se sabe — y probarlo."           prediction with a fuzzy band
 step 2  "Conformal prediction: separa datos,               split train/calibration;
          mide errores, garantiza cobertura."                nonconformity scores pile up;
                                                            95% interval snaps into place
 step 3  "España vs Uruguay: 58% — con intervalo            quantile DOTPLOT of the
          [52%, 64%] garantizado al 95%."                    match outcome (count the dots)
 step 4  "⚠️ Cuidado con la mentira bonita."                SIDE BY SIDE: Gemini's
          (debunk the narrowing graphs)                      shrinking-σ curves  vs  the
                                                            truth — football stays wide
 step 5  "2022: Arabia venció a Argentina.                  upset reel; the distribution
          Marruecos, semis. El fútbol no se                  REFUSES to narrow
          vuelve más cierto porque su matemática mejoró."
 step 6  "Campeón: España 14% — banda de simulación         champion leaderboard with
          12–16% (NO es garantía de cobertura)."             LABELED bootstrap bands,
                                                            honestly distinguished
 step 7  "Cuando digo 70%, ¿pasa el 70% de las veces?"      RELIABILITY DIAGRAM from the
                                                            backtest — calibration curve
                                                            hugging the diagonal
```
**The honesty principle, made visual (step 4–5):** put Gemini's misleading "uncertainty shrinks at each model" curves *next to* the truth and let the contrast do the talking — *"A tighter curve isn't a better model. It's an overconfident one."* This is the most defensible slide on the site and the one a mathematician will respect. (Note the deliberate framing from the roadmap: conformal "guarantee" lives **only** at match level; the champion band is **labeled simulation spread**, never "guaranteed" — n=1.)

**Sandbox:** **"¿Qué tan seguro debería estar?"** — a coverage slider (80% ↔ 99%); watch every interval widen as you demand more certainty. The lesson lands physically: *more guarantee = wider band. There is no free lunch.*

**Finale:** resolve the arc on one screen — the honest champion leaderboard (odds + labeled intervals), the reliability curve as the "trust badge," and the thesis line: ***"Cuando difiero del mercado, el backtest se ganó el derecho."*** Then methodology/credits, and a **"▶ Reproducir solo / Autoplay"** button (see §5).

---

## 5. The "no talking head" playbook (making it narrate itself)

This is the heart of the brief. Concrete mechanisms, in priority order:

1. **Script-grade step text.** The scroll-steps above are written as *spoken* lines, not captions. They are the narration. Tighten every one until it could be read aloud verbatim.
2. **Scroll = pacing.** Animations trigger on scroll position (scrollama/IntersectionObserver), so the *reader's* scroll advances the story at their pace — the page never waits for a presenter.
3. **Self-labeling visuals.** Every chart states its punchline on the chart (annotation layer), so a muted, autoplaying screen still communicates.
4. **An explicit Autoplay mode.** A "▶ Reproducir solo" toggle that auto-scrolls at a reading cadence and (optionally) plays a voice track. Two ways to get the voice:
   - record Jorge once (best — his authority, reusable in the video), or
   - TTS narration generated from the step text (zero-effort, good enough for a hands-off kiosk/link).
   This is what makes the *same site* serve (a) a live talk where Jorge clicks, (b) a hands-off video, and (c) a link someone opens cold — without rebuilding anything.
5. **Martini glass guarantees a complete passive story.** Because the guided spine is self-contained, a viewer who never touches a control still gets beginning → middle → end. Interactivity is dessert, not the meal.
6. **A persistent "you are here" rail** (Certeza · Inteligencia · Honestidad) so a viewer dropped mid-scroll always knows the act they're in.

---

## 6. Recommended tech stack & data flow

| Layer | Recommendation | Why |
|---|---|---|
| Framework | **SvelteKit** (locked 2026-06-08) | Svelte is the data-journalism default (Pudding/NYT/Guardian); compiles away to tiny JS — ideal for many small interactive viz. Pudding ships a Svelte scrollytelling starter. scrollama + D3 sit on top (framework-agnostic). |
| Scroll engine | **scrollama.js** (IntersectionObserver) | The Pudding's own lib; performant, the field standard. |
| Dataviz | **D3** (+ optional layout helpers) | Full control for bespoke sims, slope charts, dotplots, reliability diagrams. |
| Motion | D3 transitions + **GSAP ScrollTrigger** or native CSS scroll-driven animations | Punctuation, used with restraint. |
| Data | **Static JSON baked from the Python pipeline** (`predictions.json` + new sim/backtest exports) | Ties back to the earlier Postgres conversation: still **no DB needed** — the site is a static front-end over pre-computed JSON. |
| Hosting | **Vercel** — `@sveltejs/adapter-vercel`, **Project Root Directory = `web`** (no need to move the app to repo root). All routes `prerender=true` → fully static output (+1 harmless fallback fn). | Cheap, fast, linkable, zero ops; zero-config deploy. |

**Data flow (baseline-safe):** the Python model (v2, branched off `v1.0-baseline`) emits JSON → the SvelteKit site reads it at build time → static deploy. The website is a *new* artifact; it reads the model's output and never modifies baseline code.

---

## 7. Build steps — honest about the June 11 reality

This is a **long-term / "international authority" video** artifact, **not** something that ships by the June 11 kickoff. Sequencing once we start:
- **Step A — Skeleton & spine:** the shell, sticky-stepper engine, progress rail, hero, finale; one model wired end-to-end (M1) against real JSON. Proves the pattern.
- **Step B — The three guided narratives:** M1, M2, M3 sticky sequences with their signature visuals (Monte Carlo accumulation, the 3-way slope chart, conformal dotplot + reliability diagram).
- **Step C — The sandboxes:** the three interactive "martini" tails (dice roller, matchup explorer, confidence slider).
- **Step D — Self-narration polish:** autoplay mode, optional voice track, mobile degradation, `prefers-reduced-motion`, accessibility pass.
- Depends on the model work (P0→P3 in the roadmap) for real conformal/backtest data; the site can be built against v1 outputs first and upgraded as v2 data lands.

### 7.1 The Context/Calendar page is baked in — and it ships *first*
The narrative site is long-term/video. **The Context page is the exception that wants to be live for the tournament**, so it gets its own front-loaded track:
- **Why first:** it's *separable* — it needs only the fixture list (already in `results.csv`), per-match model predictions (v1 `predictions.json` already holds group-stage match numbers), and a results feed. It does **not** depend on the scrollytelling engine or the finished v2 model. And it's the **only piece with a real-time reason to exist by June 11** — the running accuracy scoreboard and the "predictions meet reality" rows only come alive *during* play. A polished narrative video can wait; **the live scoreboard cannot — every day it's down is a day of drama lost.**
- **The running accuracy scoreboard is a headline feature, not a detail** — it is the live embodiment of the whole thesis (the backtest, dramatized match by match).
- **Context build track:**
  - **Step A′ (can start first):** the 3-state match-row atom + date-grouped `Lista` + group A–L filter + the two single-day cards (Recientes/Próximos) + the running accuracy scoreboard, wired to `results.csv` fixtures and `predictions.json`. Shippable as a standalone page before the narrative exists.
  - **Step B′:** results ingestion as a *deliberate* update (per P0 tripwire / P13) so rows flip to *finalizado* with ✓/✗ as matches play; add `Grupos` + `Llaves` views.
  - **Step C′:** RPS/calibration panel, expand-row detail, mobile polish.
- **Data nuance to plan for:** the **72 group-stage matches have predictions now**; **knockout predictions are conditional** — they only materialize once the participants are known, so the page generates each knockout match's three predictions *as teams qualify* (which is itself a natural use of P13 dynamic updating). Design the row to show "Predicción pendiente — equipos por definir" until then.
- **Operational requirement for "live":** a results feed (manual entry, or a scores API/scrape) plus a deploy that refreshes daily. Cheap, but it must exist for the scoreboard to update.
- Still gated on a go-ahead (we remain planning-only); but when building starts, **the Context page is the highest-ROI first ship** because of its tournament-timed value.

---

## 8. Open decisions (need your call before/at build time)
1. **Stack:** SvelteKit (my rec) vs React/Next — depends on who maintains it and your comfort.
2. **Autoplay voice:** your recorded narration (best, reusable for the video) vs TTS (free, hands-off) vs text-only.
3. **Scope vs deadline:** confirm this is the video/long-term track (not a June-11 deliverable), so we don't starve the model work that *is* deadline-bound.
4. **Language:** Spanish-first confirmed? EN toggle now or later?
5. **Presenter mode:** do you still click through live, or is fully-autonomous the primary mode? (Design supports both; this just sets which we polish first.)

---

## 9. Sources
- The Pudding — How to implement scrollytelling — https://pudding.cool/process/how-to-implement-scrollytelling/
- Shorthand — Scrollytelling examples (Snow Fall lineage) — https://shorthand.com/the-craft/scrollytelling-examples/index.html
- Scrolling into the Newsroom (scrollytelling technique vocabulary) — https://benjamins.com/catalog/idj.22005.oes
- Segel & Heer — Narrative Visualization: Telling Stories with Data (2010) — http://vis.stanford.edu/files/2010-Narrative-InfoVis.pdf
- Distill — interactive ML journal — https://distill.pub/
- Nicky Case — Explorable Explanations — https://blog.ncase.me/explorable-explanations/
- Andy Matuschak — Explorable explanations (notes) — https://notes.andymatuschak.org/Explorable_explanations
- HOPs — Hypothetical Outcome Plots (UW Interactive Data Lab) — https://medium.com/hci-design-at-uw/hypothetical-outcomes-plots-experiencing-the-uncertain-b9ea60d7c740
- Claus Wilke — Fundamentals of Data Visualization, Visualizing Uncertainty — https://clauswilke.com/dataviz/visualizing-uncertainty.html
- MCMC Interactive Gallery (chi-feng) — https://chi-feng.github.io/mcmc-demo/app.html
- Information is Beautiful Awards 2025 — https://informationisbeautiful.net/2025/information-is-beautiful-awards-winners/

---
---

# 10. CONTEXT PAGE — Calendar & Results Hub (added 2026-06-08)

A **second page**, distinct from the 3-model scrollytelling narrative: the reference/"context" surface where a viewer checks fixtures, reads each match's **three model-predictions clearly labeled**, and — as the tournament unfolds — watches those predictions meet reality. Framed right, this page is the most compelling thing on the whole site: **the scoreboard of the models against the real world — the reputation test playing out live, match by match.** (All UI copy below is LatAm Spanish, *usted* — see [[spanish-usted-standard]].)

## 10.1 Research takeaways (sources at end of section)
- **The universal pattern is a date-grouped fixture list**, not a calendar grid. FIFA/BBC/Sky present "day-by-day breakdown of all 104 matches"; FotMob/Sofascore let you "tap a date or use nav buttons to move through the schedule."
- **FotMob = the clean-minimal UI benchmark**; **Sofascore = data depth** (expandable detail).
- **One match-card component must handle three states** — pre-match, live, post-match (Sportmonks). That single component is the atom of this page.
- **FiveThirtyEight forecast-tracking lesson:** calibration is the headline ("when we say 70%, does it happen 70%?"), the page is "updated the minute every match ends," and the move is *show the prediction, then compare it to the outcome.* That is exactly this page's job.

## 10.2 The big decision — how to display the full calendar
**Recommendation: a date-grouped vertical list (sticky day headers) + filters + jump-to-date — as the default**, with Bracket and Group-Table as complementary toggles.

| Option | Verdict | Why |
|---|---|---|
| **Date-grouped list** (sticky day headers) | ✓ **default** | chronological, scannable, mobile-native, the field standard; handles uneven match cadence gracefully |
| Month-grid calendar | ✗ | 4 matches/day in groups then sparse knockouts → unreadable cells; bad on mobile; *this is the instinct to resist* |
| Bracket / llaves | ✓ *secondary* | superb for the knockout stage (R32→Final), useless for 12 parallel groups → offer as a **Llaves** view toggle |
| Big sortable table | ~ *optional* | great for desktop power users, poor on mobile → offer as a dense "Tabla" view |

So: **three views, one default.** `[ Lista ]  [ Grupos ]  [ Llaves ]` — Lista selected.

## 10.3 Page layout (wireframe)
```
┌──────────────────────────────────────────────────────────────────┐
│  Contexto — Calendario y Predicciones         [Lista][Grupos][Llaves]│
├────────────────────────────────┬─────────────────────────────────┤
│  RECIENTES                      │  PRÓXIMOS                       │
│  (último día YA jugado)         │  (siguiente día por jugarse)    │
│  Mar 13 jun                     │  Mié 14 jun                     │
│  ┌────────── match row ───────┐ │  ┌────────── match row ───────┐ │
│  │ Brasil 2–1 Marruecos       │ │  │ España  vs  Uruguay        │ │
│  │ M1 ✓  M2 ✓  M3 ✗           │ │  │ M1 · M2 · M3 (predicciones)│ │
│  └────────────────────────────┘ │  └────────────────────────────┘ │
│  …todos los partidos del día…   │  …todos los partidos del día…   │
├────────────────────────────────┴─────────────────────────────────┤
│  Filtros:  Grupo [Todos ▾ A B C D … L]   Fase [▾]   Equipo [🔍]   │
│  Aciertos·RPS:  M1 6/12·.224  M2 8/12·.198  M3 9/12·.191  Mercado 8/12·.20 │
├──────────────────────────────────────────────────────────────────┤
│  CALENDARIO COMPLETO                                              │
│  ══ Mié 11 jun ══════════════════════════════ (sticky header)     │
│     match row    match row                                        │
│  ══ Jue 12 jun ══════════════════════════════                     │
│     match row    match row    match row                           │
│   … (Toque una fecha o desplácese; «Ir a hoy» fija el día actual) │
└──────────────────────────────────────────────────────────────────┘
```
"Recientes" and "Próximos" are **single-day** cards (per the brief): each shows *all* matches of that one day, not a rolling multi-day list.

## 10.4 The match-row component — the atom (3 states)
**Upcoming (por jugarse):** show the three predictions, clearly labeled.
```
┌──────────────────────────────────────────────────────────────────┐
│ 15:00   🇪🇸 España        vs        Uruguay 🇺🇾   · Grupo H · Por jugarse│
│ Predicción  M1 1–1 · M2 2–1 · M3 2–1 · Mercado España 58%    Esp–Uru │
└──────────────────────────────────────────────────────────────────┘
   M1 = Azar · M2 = Red Neuronal (pura) · M3 = Conjunto (ensemble+conformal) · Mercado = apuestas
```
**Finished (finalizado):** the actual result joins the three predictions, each marked acierto/fallo.
```
┌──────────────────────────────────────────────────────────────────┐
│ 🇪🇸 España   2 – 1   Uruguay 🇺🇾                · Grupo H · Finalizado │
│ M1 1–1✗ · M2 2–1✓⭐ · M3 2–1✓⭐ · Mercado Esp✓   Marcador 2–1·Esp │
└──────────────────────────────────────────────────────────────────┘
```
**Live (en vivo):** live score + a pulsing dot; predictions stay visible, ✓/✗ resolve at full time.
**Expand on click** (Sofascore-style progressive disclosure): full W/D/L probabilities per model, the λ expected-scoreline, M3's conformal interval, and a one-line "why" (top features) — so the row is glanceable but drillable.

## 10.5 Showing three predictions + the result clearly (the core comparison)
- **A fixed "prediction strip"** of four labeled cells (M1/M2/M3 + Mercado), color-keyed to the models used everywhere else on the site (M1/M2/M3 keep one consistent color each; Mercado a neutral/grey). Labels always visible — never make the viewer guess which value is which model.
- **Per-model verdict** once played: a quiet ✓ (acierto, *outcome* correct) / ✗ (fallo) on each cell — green/red, subtle (restraint) — **plus a ⭐ when the exact scoreline is matched** (badge label: "Marcador exacto").
- **The running accuracy scoreboard** (top of the calendar; season-long version in the finale) shows **two metrics, clearly labeled, in a deliberate visual hierarchy:** **hit-rate in full-contrast color** (the headline — `M2 8/12 aciertos`, the gripping batting average) and **RPS muted/secondary** (`RPS 0.198`, the rigorous proof for the technical eye), with an exact-score tally alongside (`2 exactos`). **Four lines compete — M1 / M2 / M3 / Mercado** (Mercado is outcome-graded only, never earns ⭐). This is the honest, on-brand payoff — the audience *watches the pure net (M2) and the ensemble (M3) beat (or lose to) blind chance and the bookmakers in real time*, dramatizing the whole thesis (the backtest, live). Early on, tag it "(muestra pequeña)" — both metrics are noisy under ~20 matches.
- **The predicted value in-row is each model's most-likely SCORELINE** — the *modal* exact score from that model's goal distribution, **not rounded λ** (rounding overstates: λ=1.8 has modal count 1, not 2). Full W/D/L probabilities, λ, and M3's interval move to the expand. **Correctness for the scoreboard is graded on the outcome (1/X/2)** so a near-miss (predicted 2–1, actual 3–1) still counts as an acierto; an exact-scoreline hit additionally earns the ⭐ badge.

## 10.6 Filters & views
- **Group filter A–L** (the brief's requirement) as a chip row; **Fase** dropdown (Grupos / Dieciseisavos / Octavos / Cuartos / Semis / Final); **Equipo** search to follow one nation.
- **Views:** *Lista* (default date-grouped), *Grupos* (12 standings tables with predicted vs actual position), *Llaves* (knockout bracket, lit up as results land).

## 10.7 Data source & the honesty hook (ties back to the model)
The fixtures already exist in `results.csv` — they're literally **the 72 unscored future-dated rows the Dirty George audit found**. As matches are played, their results fill in. That makes this page the **deliberate-update surface** for P13 (dynamic Bayesian updating), and the P0 leakage tripwire is what guarantees a result only enters the *model* on purpose, never silently. **The calendar page and the integrity layer are the same data flow** — which is a genuinely elegant story to tell: "the page you watch fill in is the same pipe that updates the model, and here's the guard that keeps yesterday's results from contaminating tomorrow's prediction."

## 10.8 Mobile
Single column; the two top cards stack (Próximos first — it's the forward-looking one); the prediction strip wraps to a compact M1/M2/M3 row under the teams; sticky date headers; filters collapse into a sheet. `prefers-reduced-motion` respected.

## 10.9 Decisions (resolved 2026-06-08)
- **In-row predicted value → predicted SCORELINE** (modal exact score per model; e.g. `M1 1–1 · M2 2–1 · M3 2–1`). Scoreboard grades on outcome (1/X/2); exact-scoreline hits earn a ⭐ badge. **Mercado** shows its implied pick + % (not a scoreline) and is outcome-graded only (no ⭐). Full probabilities / λ / P3 interval live in the expand. *Impl note:* use the modal scoreline of the joint goal distribution, not rounded λ.
- **Accuracy scoreboard → BOTH metrics, clearly labeled, with hierarchy:** hit-rate in **full-contrast color** (headline) + RPS **muted** (secondary proof), with an exact-score tally. Tag "(muestra pequeña)" under ~20 matches.
- **"Recientes" = the most recent single day with ≥1 *finished* match** (date-labeled); **"Próximos" = the next single day with ≥1 *unplayed* match.** On a busy match day both may point to today.

## 10.10 Sources (this section)
- FIFA — Scores & Fixtures, WC 2026 — https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/scores-fixtures
- Sky Sports — WC 2026 day-by-day, all 104 matches — https://www.skysports.com/football/news/11095/13481245/world-cup-2026-fixture-schedule-and-uk-kick-off-times-day-by-day-breakdown-of-all-104-matches-including-england-scotland
- Sportmonks — Knockout match centres: UX patterns — https://www.sportmonks.com/blogs/knockout-match-centres-best-ux-patterns-data-requirements/
- FiveThirtyEight — Checking our work (forecast tracking) — https://projects.fivethirtyeight.com/checking-our-work/
- FotMob (UI benchmark) — https://www.fotmob.com/  ·  Sofascore (data depth) — https://www.sofascore.com/
