# Data contract — `matches.json`

The Context page reads one static file: `web/static/data/matches.json`, produced by the export script (Batch 1.2) from `results.csv` (fixtures) + v1 `output/predictions.json` (M1/M2). M3 + Mercado are **stubbed** (`null`) until those models exist.

**Design rule:** store *facts*, derive *verdicts*. The JSON holds predictions + results; the UI computes acierto/fallo/⭐ and the scoreboard totals client-side (so adding a played result needs no recomputation in the file).

## Shape

```jsonc
{
  "meta": {
    "generated": "2026-06-08",          // stamped by exporter (passed in; no Date.now)
    "source": "results.csv + output/predictions.json (v1)",
    "models": ["M1", "M2", "M3", "Mercado"],
    "stub": ["M3", "Mercado"]            // lines not yet real
  },
  "teams": {                            // canonical CSV name -> Spanish display
    "Mexico": "México",
    "South Africa": "Sudáfrica"
    // ... full map; see COPY_ES (team names pending native review)
  },
  "matches": [
    {
      "id": "GA-01",                    // stable id: stage/group + index
      "date": "2026-06-11",             // ISO date (local host-city day)
      "time": "18:00",                  // local kickoff, or null if unknown
      "stage": "grupos",                // grupos|dieciseisavos|octavos|cuartos|semifinales|final|tercer_puesto
      "group": "A",                     // letter for group stage; null otherwise
      "home": "Mexico",                 // canonical CSV name (display via teams map)
      "away": "South Africa",
      "status": "por_jugarse",          // por_jugarse|en_vivo|finalizado
      "result": null,                   // when finalizado: { "home": 2, "away": 1, "outcome": "home" }  outcome: home|draw|away
      "predictions": {
        "M1": { "home": 1, "away": 1, "pick": "draw", "probs": { "home": 0.30, "draw": 0.34, "away": 0.36 } },
        "M2": { "home": 2, "away": 1, "pick": "home", "probs": { "home": 0.58, "draw": 0.24, "away": 0.18 } },
        "M3": null,                     // stub: { ...like M2, plus "interval": { "lo": 0.52, "hi": 0.64 } }
        "Mercado": null                 // stub: { "pick": "home", "probs": {...} }  — NO scoreline (markets price 1X2)
      }
    }
    // knockout matches: group=null; home/away may be "Por definir" with predictions=null until teams qualify
  ]
}
```

## Field rules
- **Scoreline lines (M1/M2/M3):** carry integer `home`/`away` (the **modal** scoreline, not rounded λ), a `pick` (home|draw|away derived from the scoreline), and `probs`. M3 additionally carries `interval`.
- **Mercado:** carries `pick` + `probs` only — **no scoreline** (outcome-graded; never earns ⭐).
- **Grading (UI-derived, not stored):**
  - *acierto* (✓) = `prediction.pick === result.outcome`.
  - *Marcador exacto* (⭐, M1/M2/M3 only) = `prediction.home === result.home && prediction.away === result.away`.
- **Scoreboard (UI-derived):** per line, `aciertos = Σ✓`, `jugados = Σ finalizado`, `exactos = Σ⭐`, plus `RPS` (mean ranked-probability score over played matches; needs `probs`).
- **Status transitions:** exporter sets `por_jugarse` for unscored fixtures; the results feed flips to `finalizado` + fills `result`. (`en_vivo` later.)
- **Recientes / Próximos:** Recientes = most recent single `date` with ≥1 `finalizado`; Próximos = next single `date` with ≥1 `por_jugarse`.

## Provenance / integrity (ties to P0)
- The 72 group-stage fixtures already live in `results.csv` (unscored, future-dated). Knockout fixtures fill in as the bracket resolves.
- A result only enters the model pipeline deliberately (P0 leakage tripwire); the Context page's results feed is that deliberate-update surface.

## Standings sections (added 2026-06-08 for Grupos/Llaves views)
- `groups`: `[ { group, teams: [ { team, elo, value, advance, champion, winner, runner } ] } ]` — teams sorted by `advance` desc. **`value` is `null` when squad value is unknown** (e.g. South Africa) — the UI renders "—", never a phantom €0M (Dirty George).
- `knockout`: `[ { team, group, r16, qf, sf, final, champion } ]` — all 48 teams, sorted by `champion` desc (stage-reach probabilities for the Llaves view).
