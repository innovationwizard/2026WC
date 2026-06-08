# Live results — updating the scoreboard during the tournament

`results_live.csv` holds the **actual scores**. Edit it as matches play; everything else cascades. No server, no cron, no database — just a CSV and one build command.

## Each match day
1. Open **`results_live.csv`**. Find the match (by team names) and fill in `home_score` and `away_score`.
2. Regenerate the site data:
   ```
   .venv/bin/python web/scripts/build_matches.py
   ```
3. Commit + push:
   ```
   git add -A && git commit -m "results: <fecha>" && git push
   ```
4. Vercel redeploys automatically → the calendar rows flip to *Finalizado*, the ✓/✗/⭐ appear, and the **Tablero de aciertos** updates live.

## Notes
- Fill **only** the two score columns; leave a match blank until it's played.
- `home`/`away` are canonical (English/CSV) names; the UI shows Spanish.
- This file is deliberately **separate** from the locked root `results.csv` and from `predictions.json` — so the model's predictions stay a true *pre-match* forecast (no leakage), and the baseline stays frozen.
- The exporter **never overwrites your filled scores**; on re-run it preserves edits and only appends new fixtures (e.g. knockout matches) if missing.
- Knockout fixtures aren't in the data yet (teams TBD) — they'll be added as the bracket resolves.
