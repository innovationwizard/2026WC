# M3 — Player-State Variable Group: Plan & Progress

**Status:** BUILD COMPLETE (B1–B6). Suspension effect derived & validated, but the RPS gate said DO NOT SHIP into λ (see VERDICT below). Live collector still shipped.
**Last updated:** 2026-06-26

## ⬛ FINAL VERDICT (B6 gate, 2026-06-26)
Built the full pipeline (290-match API-Football corpus → deterministic suspension labels at 100% cross-check → as-of-date weights → empirical-Bayes Poisson GLM). The suspension effect is **real and robust**: `b_susp = -0.078`, bootstrap 95% CI [-0.130, -0.022] (excludes 0), stable in leave-one-tournament-out across all 6 editions, and survives a knockout-stage confounder check. Downweight = `exp(b_susp·w)` (≈×0.984 at w=0.2).
**BUT the leave-one-tournament-out match-outcome RPS gate is NOT significant:** ΔRPS=+0.000039 (direction correct — the downweight helps), 95% CI [-0.000009, +0.000092], DM p=0.137, only 16/290 matches affected. The effect is too small (~1–3% on λ) and too rare to move W/D/L prediction.
**Decision: do NOT wire into production λ.** Keep all machinery (`v2/m3/`) dormant; re-run the gate after the 2026 group stage adds ~30–40 suspension events. The bulletproof discipline held — no taste-based number shipped, no effect asserted beyond what the data supports. Build details + resume protocol in [`M3_BUILD_PLAN.md`](M3_BUILD_PLAN.md) / [`M3_BUILD_PROGRESS.md`](M3_BUILD_PROGRESS.md).

## DECISIONS (locked)
- **Scope (decided 2026-06-26):** Ship **TWO** snapshot effects by the ~June 27 deadline — **suspension** and **yellow card**. Both reconstruct cleanly as-of-date (pure functions of completed prior matches), so the gate is fully leakage-free with no proxy.
  - **DEFERRED to post-group-stage** (bring into scope when the group stage completes): **(1) availability** — injury / announced-not-playing — dropped now because there's no retroactive as-of-date feed (the did-not-appear proxy is undesirable); **(2) form trend** — needs per-match time series, ~3 games too thin.
- **Q2 (backtest methodology, decided 2026-06-26):** **Point-in-time rebuild.** Build player-state *as of each matchday* and backtest leakage-free against actual results. Implementation reality: the ESPN data is already **per-match**, so we do NOT re-hit ESPN once per matchday — we collect every per-match player record **once** (each tagged with its match date), then derive each snapshot by **date-filtering** (state-as-of-date D = aggregate only matches with date < D). One collection pass → N point-in-time snapshots.
  - **Clean to reconstruct as-of-date:** cards / suspension accrual, goals/assists/shots totals, concentration. (All are functions of completed prior matches.)
  - **(Former wrinkle now out of scope):** the did-not-appear proxy was only needed for availability, which is deferred. With scope = suspension + yellow only, every signal reconstructs cleanly from completed prior matches — no proxy, no self-reference.
- **Q3 (downweight magnitudes, decided 2026-06-26):** **Build & ship BOTH tiers at once** — source a historical football corpus now and fit a **partial-pooling / Bayesian model** so the downweight bounds are **data-derived (credible intervals), never hand-set.** No coefficient comes from football taste. Techniques: shrinkage chosen by CV + structural `weight` cap + bootstrap/DM-test gate, with the historical corpus supplying the prior.
  - **Tradeoff Jorge accepted:** correctness over the ~June 27 deadline. Sourcing + cleaning a historical corpus is real ETL work (cross-project wisdom: always dirtier/longer than expected), so the group-stage deadline likely slips. The alternative (ship Tier A on time, Tier B after) was declined in favor of shipping both together.
  - **Critical path is now SOURCING, not modeling.** First action = hands-on inspection of candidate historical sources before any parser is written.

## Corpus data spec (what the historical model needs, per match-team)
To estimate "effect of a key player's absence on team expected goals," each historical match needs:
- **Match result** (goals for/against) — the target.
- **Per-player contribution** (goals, assists, minutes) over PRIOR matches in that competition → to compute each player's `weight` as-of-date (same definition the collector uses now).
- **Lineups / availability** — who started / was available per match (to detect a key player's absence).
- **Suspension events** — player available-but-ruled-out by card accumulation. ← **hardest field to source historically; the make-or-break.**
- **Competition + date** — to scope as-of-date aggregation and to weight WC/international data above club data.

## Sourcing assessment (recon 2026-06-26)
**Governing finding:** a *labeled* suspension ("missed match N because of cards") is machine-readable in only ONE free place — **Transfermarkt `/ausfaelle/spieler/{id}`** — or via **paid API-Football** (`reason="Suspended"/"Red Card"`). All other sources (StatsBomb, ESPN, FBref, Kaggle, Wikipedia) give only card events + lineups → suspension must be INFERRED, which silently conflates suspension/injury/rotation/benching. ⇒ architecture is forced **two-source**.

**RESOLVED 2026-06-26 by live probe → SINGLE SOURCE: API-Football Pro.** (Probe scripts: `scratchpad/af_probe.py`, `af_probe2.py`.)
- **Probe finding:** API-Football's editorial injury/suspension LABEL is NOT available for historical international tournaments — `coverage.injuries=False` for WC 2018/2022, Euro 2020/2024, Copa 2021/2024, and `/injuries?league=1&season=2022` returns 0 rows.
- **But the spine IS fully present** (verified on WC2022 Korea–Ghana, fixture 855757): card events (yellow/red + player + team + minute), lineups (startXI **and** full 15-man bench → true absence is observable, beating StatsBomb's appeared-only limit), and per-player stats (minutes, goals, assists, rating). All in ONE ID space, all target tournaments, under Pro.
- **Key reframing — suspension is DERIVED, not labeled.** A card suspension is deterministic (2 yellows pre-semifinal, or a red → banned next match, by published FIFA rule). We have the card events + the rules, so we derive bans ourselves — MORE bulletproof than any editorial label, and the next match's full squad confirms the absence. The recon's "rule engine as cross-check" is promoted to PRIMARY signal.
- **Consequences:** (1) **StatsBomb dropped entirely** (and its non-commercial license concern). (2) **Cross-source name+DOB join — the #1 Dirty George risk — ELIMINATED.** (3) `injuries=False` only costs historical injury/announced-out labels, which are already DEFERRED out of scope → no deadline impact. For LIVE 2026, separately check whether the 2026 WC season has `injuries=True` when availability comes into scope.
- **Data-cleaning note (Dirty George):** player stat fields come back `null` when zero (e.g. `goals.total=None` for a non-scorer) — coalesce None→0 on ingest.
- **Cross-source join is the hard part:** StatsBomb / ESPN / Transfermarkt / API-Football use non-aligned player IDs → crosswalk on **name + birthdate + nationality, never name alone**.
- **Rule-engine cross-check:** re-implement the disciplinary rules (WC: 2 yellows = 1-game ban, yellows wiped after QF, red = ban) to CROSS-CHECK overlay labels and flag disagreements — never trust either side silently.

**MVP corpus:** the ~320 StatsBomb international matches + Transfermarkt-labeled suspensions for those squads. Yield ≈ **60–120 labeled suspension events** (thin but workable for partial pooling). Enrich the general "key player out" prior with injury/rotation absences from the same spine (hundreds of events), with suspension as the labeled subset.

**Effort: multi-day ETL.** Easy part = StatsBomb pull. Hard part = minutes computation, cross-source name+DOB join, Transfermarkt parse, "X games missed" → specific-fixture mapping, rule-engine validation.

**Dirty George traps flagged by recon:**
1. **Silent zero-suspension trap** — `felipeall/transfermarkt-api` scrapes injuries-only; Kaggle dcaribou export has cards but NO suspension table. Reusing either yields zero suspensions silently. Parse `ausfaelle` BY CONTENT; emit a flag when a player has cards but zero absence rows.
2. **"Did not play" ≠ "suspended"** on any inference-only source.
3. **Name-matching across 4 ID spaces** → name+DOB+nationality.
4. **Soft fixture mapping** — Transfermarkt gives games-count + date window, not fixture IDs.
5. **Source brittleness** — FBref jails bots / dropped xG (Jan 2026); ESPN pre-2014 patchy; dcaribou lost a whole season once. Build anomaly flags.

**Licensing notes (must respect — site is live/public):**
- **StatsBomb Open Data = non-commercial user agreement, no redistribution, logo attribution.** OK as a TRAINING input (we derive a prior coefficient, not republish their data); do NOT expose their raw data on the site; show attribution.
- **Transfermarkt** = copyrighted + EU sui-generis DB right; ToS restricts bulk scraping. Scrape narrowly (only the squads we need), rate-limit politely.
- **API-Football** = paid; storage/caching OK, reselling raw API banned, no betting/fantasy rights (we use only suspension/injury, not odds → consistent with the project's "sin cuotas" mode).

**Calibration flags from recon (verify before depending):** (1) API-Football's exact `reason`/`type` value list came from 3rd-party output + client structs, not vendor docs (Cloudflare-blocked) — confirm with one live call. (2) Transfermarkt historical depth for 2018 — confirm before committing it as the backtest overlay.
**Owner brief (verbatim):** see `~/.claude/projects/<2026wc>/memory/m3-player-state-variables.md`
**Discipline:** strict-math. Any new feature must be **backtest-gated (improve held-out RPS)** before it ships — exactly like the home-advantage feature was. This is a NEW M3 variable group, not the locked baseline.

> Jorge's request (2026-06-25), to implement by end of group phase (~2026-06-27):
> - Weight how key each player has demonstrated to be in the groups phase.
> - Key player injured? → must affect forecasted values.
> - Key player announced not playing next match? → must affect forecasted values.
> - Key player has a yellow card? → could affect forecasted values.
> - Key player performance increasing/decreasing (through matches / within a match)? → should affect forecasted values.

---

## Architecture / data flow

```
ESPN match-summary endpoint
        │  (player_state.py — DONE)
        ▼
v2/output/player_state.json   ← per-team player state
        │  (M3 adjustment layer — TODO)
        ▼
λ multiplier per team per fixture  (availability / concentration / form)
        │  gate: m3 backtest must improve RPS
        ▼
feature_engine.py / main.py  (only if gate passes)
```

---

## Step 0 — Collector  ✅ DONE (committed `be7743f`)

`v2/player_state.py` → `v2/output/player_state.json`.

**Verified output shape** (top-level dict keyed by canonical team name):

```jsonc
"Mexico": {
  "concentration_top3": 0.537,        // share of output in top-3 players
  "key_players": [
    {
      "name": "Julián Quiñones", "pos": "LF",
      "goals": 2, "assists": 0, "yellows": 0, "reds": 0,
      "shots": 10, "sot": 4, "saves": 0,
      "starts": 3, "apps": 3,
      "contribution": 2.0,            // goal+assist-based contribution
      "weight": 0.211                 // normalized key-ness within team
    },
    ...
  ]
}
```

Handles: confirmed-lineup absences (reason-agnostic), card-sanction double-check, ESPN→canonical team alias map.

**Caveat (Dirty George):** `pos: "SUB"` appears for some high-weight players (e.g. Raúl Jiménez) — position is unreliable; do NOT use `pos` to gate logic. Trust counting stats + weight.

---

## Step 0.5 — API-Football coverage probe  ✅ DONE (2026-06-26)
Result: SINGLE SOURCE = API-Football Pro; suspensions DERIVED from card events + disciplinary rules (the `/injuries` label is absent for history but unneeded). StatsBomb dropped, cross-source join eliminated. See "Sourcing assessment" above for full findings.

## Step 0.6 — Disciplinary rule engine  ☐ TODO (now PRIMARY suspension signal, not a cross-check)
Deterministic ban derivation from card events. Must encode the real FIFA tournament rules carefully (Dirty George — the nuances are where this breaks):
- [ ] 2 yellows in separate matches → 1-match ban.
- [ ] Yellow-card accumulation is WIPED after the quarter-finals (so a single yellow carried into the semis does not risk a final ban). Verify exact wipe point per tournament/edition — it has changed historically.
- [ ] Straight red → ≥1-match ban (length can vary by offence; start with 1, flag multi-match reds).
- [ ] Output per (player, upcoming fixture): banned = True/False, with the triggering cards as provenance.
- [ ] CROSS-CHECK against observed absence (player banned by rule AND absent from the next match's full squad). Flag disagreements; never drop silently.

## Step 1 — Inspect `player_state.json` in depth  ☐ TODO (do before writing consumer code)

Before any λ math: eyeball the real distribution, not a sample.
- [ ] How many teams present vs. teams in `matches.json`? Any missing / unmatched (alias gaps)?
- [ ] Range of `concentration_top3` across teams — is it discriminating?
- [ ] Are `weight`s normalized per-team (sum ≈ 1)? Confirm.
- [ ] Suspension signal: which players actually carry red/yellow-accumulation risk right now?
- [ ] Absence data: where does "announced not playing" live in the JSON, and is it populated for upcoming fixtures? (The brief needs forward-looking availability, not just historical.)

## Step 2 — Define the λ-adjustment function  ☐ TODO

A pure, testable function: `adjust_lambda(team, base_lambda, player_state, availability) -> lambda'`.
IN-SCOPE signals → effects (each must earn its place via Step 4):
- [ ] **Suspension**: a key player (weight w) ruled out by accumulated cards (red, or yellow-accumulation threshold) → scale team λ down by a function of w. Deterministic and reconstructable as-of-date → strongest in-scope signal.
- [ ] **Yellow card** on a key player (not yet suspended) → small downweight (caution risk / sit-out risk), per brief "could affect".
- [ ] **Concentration**: high `concentration_top3` → team more fragile to a key suspension (interacts with the suspension term, not standalone).

DEFERRED (bring in when group stage completes):
- [ ] ~~**Availability** (injury / announced-not-playing)~~ → no retroactive as-of-date feed; did-not-appear proxy undesirable.
- [ ] ~~**Form trend** (increasing/decreasing)~~ → needs per-match time series; ~3 games too thin.
Keep it ONE multiplier with transparent components; no scattered inline tweaks.

## Step 3 — Wire a backtest harness for the feature  ☐ TODO

Reuse the pattern in `v2/m3_backtest.py` (trains net+GBT on train split, sweeps, reports held-out RPS via `wdl`/`rps`/`CUTOFF`).
- [ ] Build an ablation: baseline λ vs. player-state-adjusted λ on the held-out split.
- [ ] **Point-in-time (Q2 decision):** restructure the collector to emit per-match player records tagged with match date, then build a `state_as_of(date)` aggregator (matches strictly before `date`). Backtest predicts each historical fixture using only its as-of-date snapshot → no leakage.
- [ ] Availability proxy in backtest = did-not-appear in that match's lineup (see Q2 wrinkle); cards/suspension reconstruct cleanly from prior matches.

## Step 4 — Gate & decide  ☐ TODO

- [ ] Run ablation. Ship ONLY if held-out RPS improves (Δ meaningful, not noise — consider `dm_test.py` for significance).
- [ ] If it doesn't improve: keep collector as data, do NOT wire into production λ. Record the negative result here.

## Step 5 — Integrate (only if Step 4 passes)  ☐ TODO

- [ ] Hook `adjust_lambda` into `feature_engine.py` / `main.py` λ path.
- [ ] Surface provenance on the site if it changes published numbers (formal usted Spanish).
- [ ] Update memory `m3-player-state-variables.md` with the outcome.

---

## Open questions for Jorge
1. **Form trend** needs within-match / across-match time series — collector currently aggregates totals. Build the time series now, or defer form to post-group-phase and ship availability+suspension first?
2. **Backtest methodology**: we only have current-state player data. OK to gate on a forward holdout (upcoming knockout fixtures) rather than a true historical point-in-time backtest?
3. Magnitude philosophy: let the backtest fit the downweight coefficients, or cap them by hand to avoid overfitting on a tiny sample?
