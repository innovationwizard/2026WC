# Scoreline-distribution tooltip — design proposal

> **The mid-level ask:** the calendar currently shows each model's *modal* scoreline (e.g. M2 "1-0").
> The next tier wants to see the **distribution behind that point** — *P(1-0)? P(2-0)? P(3-0)? P(1-2)?* —
> in a tooltip/popover. This doc proposes how to organize and display it.
> Inputs read: `comments/01gemini.md` + the three "Predictive Uncertainty" charts.

---

## 0. The punchline first

The modal scoreline is a **lie of confidence**. For the example match (México vs Sudáfrica), M2's
"1-0" carries only **11.5%** probability — and **1-1 is tied with it at 11.1%**. The whole *point* of
this tooltip is to expose that: the strip shows a single number; the tooltip shows it's the tallest
bar in a wide, flat field. That reinforces the project's honest-uncertainty thesis at the match level,
and it's the 2-D, per-match realization of Gemini's "predictive uncertainty" density curves.

---

## 1. The data reality — we already have everything

Every model emits, per match, two expected-goals rates already in `matches.json`:
`predictions.{M1,M2,M3}.lambda.{home,away}`. Under the model's independent-Poisson assumption, the
**full joint distribution of scorelines is the outer product**:

$$P(\text{home}=i,\ \text{away}=j) \;=\; \mathrm{Pois}(i;\lambda_h)\cdot\mathrm{Pois}(j;\lambda_a)$$

So the entire "correct-score matrix" is **computable client-side in ~15 lines** — no new export, no new
data. The W/D/L the strip already shows are just sums of regions of this same matrix (upper triangle =
home win, diagonal = draw, lower triangle = away win).

**Caveat to state honestly (and an upgrade path):** independence slightly under-weights the very low
scores (0-0, 1-1) — the classic **Dixon-Coles** low-score correction (a single dependence parameter ρ)
fixes this. We can ship independent-Poisson now and add ρ later; the tooltip's structure doesn't change.

---

## 2. Prior art (how the world shows this)

| Form | Who | Strength | Weakness |
|---|---|---|---|
| **Correct-score matrix (heatmap)** | Opta, FiveThirtyEight match pages, bookmakers' "correct score" grid | Shows *every* scoreline's probability at once; structure (win/draw/loss regions) is spatial | Needs a 6×6 grid; tight on mobile |
| **Top-N correct scores (ranked list)** | Bet365 / betting "correct score" market | Dead simple, scannable, mobile-friendly | Only top few; no spatial intuition |
| **Marginal goal bars** (Poisson per team) | xG explainers | Answers "how many will each score" | Doesn't give the *joint* P(i-j) directly |
| **HOPs (animated sampling)** | Hullman/Kale uncertainty viz; our own Act 1 | Visceral for *teaching* variance | Too busy/animated for a hover tooltip |
| **1-D density curve** | Gemini's "Predictive Uncertainty" charts | Elegant for a *single* quantity | A scoreline is 2-D; a curve loses the joint |

**Takeaway:** the **correct-score matrix is the canonical answer** to "what's the probability of each
exact scoreline" — it answers all four of your questions (1-0, 2-0, 3-0, 1-2) as four cells, read at a
glance. The top-N list is its perfect *summary / mobile fallback*. We should use **both**: matrix as the
hero, top-N + W/D/L as the always-visible summary band.

---

## 3. Recommended design — the "correct-score matrix" tooltip

**Trigger (progressive disclosure):** tapping/hovering a model's scoreline strip (the `M2 1-0` chip)
opens the popover **for that model** — the point estimate expands into the distribution it came from.
This mirrors the martini-glass ethos and keeps the default calendar uncluttered.

```
┌────────────────────────────────────────────────────────┐
│  M2 · Red Neuronal        México 1.76 – 0.97 Sudáfrica  │  ← header: model + xG (λ)
│                                                          │
│            Sudáfrica  →                                  │
│           0     1     2     3    4+                       │
│      ┌───────────────────────────────                    │
│   0  │ 6.5   6.3   3.1   1.0   ·    │                     │   shade = P; darker = likelier
│ M 1  │[11.5] 11.1   5.4   1.7   ·    │  ← 1-0 = modo (box) │   diagonal subtly ruled = empates
│ é 2  │11.0   9.8   4.7   1.5   ·    │                     │   ▲ upper-right of diag = visitante
│ x 3  │ 5.9   5.7   2.8   ·     ·    │                     │   ▼ lower-left  = local
│   4+ │  ·     ·     ·     ·     ·    │                     │
│      └───────────────────────────────                    │
│   ↓ México                                               │
│                                                          │
│  Local 56% · Empate 23% · Visitante 21%                  │  ← summary band (region sums)
│  Más probables:  1-0 11% · 1-1 11% · 2-0 10% · 2-1 10%   │  ← top-N (and the mobile fallback)
└────────────────────────────────────────────────────────┘
```

**Why the matrix wins here:** your four questions map to four cells — P(1-0)=11.5 (row 1, col 0),
P(2-0)=10.1 (row 2, col 0), P(3-0)=5.9 (row 3, col 0), P(1-2)=5.4 (row 1, col 2). A vertical scan of
column 0 *is* "1-0 vs 2-0 vs 3-0." Nothing else gives you that comparison in one glance.

**Encoding details**
- **Axes:** home (the strip's left team) on rows, away on columns, 0–5 goals + a `4+`/`5+` bucket so the
  grid stays finite (the tail mass is folded in). Hovering a cell shows its exact % + the scoreline.
- **Color:** a sequential ramp in the **model's hue** (M1 slate, M2 blue, M3 green) so the popover is
  self-identifying. Modal cell gets a bright outline + the % label always on.
- **Regions:** a faint diagonal rule marks draws; optional very-light tint separating the win/loss
  triangles so "who's favored" reads spatially without clutter.
- **Summary band (always visible):** W/D/L (the triangle/diagonal sums) + the **top-4 exact scores**.
  This band is also the **whole tooltip on narrow phones** (the grid collapses to the list under ~360px).

**M3 gets one extra line — the conformal set.** Since M3 already carries its 80% prediction set, add:
`M3 · 80% de confianza: {México o Empate}` under the summary. That's the honest-uncertainty payoff and
ties the per-match tooltip back to Act 3 of the story.

---

## 4. Variants considered → recommendation

1. **Matrix-only.** Densest, but a bare grid intimidates casual viewers and dies on mobile.
2. **Top-N list only.** Friendly, but loses the spatial "1-0 vs 2-0 vs 3-0" comparison and the structure.
3. **★ Matrix + summary band (recommended).** Matrix for the curious, top-N + W/D/L for everyone, list
   as the mobile fallback. Best of both; one component, two densities.
4. **Marginal bars on the axes** (Poisson per team along the grid edges). A tasteful *optional* add to (3)
   — shows each team's goal distribution and visually "explains" the joint as their product. Nice-to-have,
   not essential.

**Recommendation: (3), with (4) as a phase-2 flourish.** Hero = correct-score heatmap; persistent
summary band = W/D/L + top-4; M3 adds the conformal set; the band alone serves mobile.

---

## 5. The example, fully worked (real model output)

México vs Sudáfrica — the four you asked about, plus the structure, **straight from the live λ**:

| | M1 (Azar) | M2 (Red) | M3 (Conjunto) |
|---|---:|---:|---:|
| **P(1-0)** | 12.3% | 11.5% | 12.9% |
| **P(2-0)** | 11.3% | 10.1% | 11.2% |
| **P(3-0)** | 6.9% | 5.9% | 6.5% |
| **P(1-2)** | 4.7% | 5.4% | 4.8% |
| modal score | 1-0 | 1-0 | 1-0 |
| **P(modal)** | **12%** | **11%** | **13%** |
| L / E / V | 60/23/17 | 56/23/21 | 58/23/18 |

The story the tooltip tells itself: *the model "says 1-0," but 1-0 is barely 1-in-8, 1-1 is just as
likely, and a goal-fest 3-0 is a real 6%.* The point estimate is the **mode of a broad field**, and the
three models barely differ on the full distribution — exactly the "honest about uncertainty" message.

---

## 6. Interaction & pedagogy
- **Progressive disclosure:** strip = the point; tooltip = the distribution it summarizes. Tap to open;
  it doesn't crowd the calendar.
- **Hover-a-cell = exact %** — so "what's the probability of 3-1?" is one mouse-over, no list needed.
- **Optional model toggle inside the tooltip** (M1/M2/M3 tabs) so a curious viewer can watch the matrix
  shift between models — the per-match echo of Gemini's round-to-round "uncertainty narrowing."
- **Mercado:** no scoreline (pick-only), so its strip stays non-interactive (or shows just its 1X2 bar).

---

## 7. Implementation notes
- **Compute:** client-side `pois(i,λh)*pois(j,λa)` over a 0..6 grid + a `≥` bucket; W/D/L = region sums;
  top-N = sort the grid. ~30 lines in a `ScoreMatrix.svelte`, fed `lambda.home/away` from `matches.json`.
  **No pipeline/exporter change.**
- **Accessibility:** the grid needs a text equivalent — the top-N + W/D/L band *is* that equivalent
  (screen-reader-friendly); give each cell an `aria-label` ("México 2, Sudáfrica 0 — 10%").
- **Caveat surfaced honestly:** label the popover's basis (independent Poisson). Optional **Dixon-Coles ρ**
  later nudges 0-0/1-1 and would require exporting one ρ (or a small per-λ correction) — structure
  unchanged.
- **Tooltip vs popover:** on touch there's no hover, so implement as a **tap-to-open popover** (a
  `<details>`/dialog), not a pure CSS hover tooltip; desktop can also open on hover.

---

## 8. LOCKED SPEC (decided 2026-06-10)
1. **Surface:** ✅ correct-score **matrix (hero) + summary band** (W/D/L + top-4 scores). Band = mobile fallback.
2. **Grid:** ✅ **0–4 goals + `≥5` bucket** (6×6). Tail folded into the bucket.
3. **Marginal axis bars:** ✅ **skip for v1** (phase-2 flourish).
4. **Model selection:** ✅ **one popover with an M1/M2/M3 toggle** — opens on the chip the reader tapped,
   then flips between models in place. Mercado is pick-only → non-interactive (no scoreline).
5. **Distribution:** ✅ **independent Poisson now** (client-side `Pois(i;λh)·Pois(j;λa)`), kept **identical**
   to the strip/scoreboard W/D/L. Dixon-Coles ρ deferred to a **model-level** change (so all surfaces stay
   consistent), not a tooltip-only hack.

**Inherited details:** M3's tab adds its 80% **conformal set** line; popover is **tap-to-open** (touch has
no hover); each cell gets an `aria-label` and the top-N band is the screen-reader equivalent; popover
labeled "Poisson independiente."

**Build shape:** one self-contained `ScoreMatrix.svelte` (matrix + tabs + summary band), fed
`predictions.{M1,M2,M3}.lambda` from `matches.json`, wired into `MatchRow`'s expanded detail. ~Small,
**no backend/exporter change.**
