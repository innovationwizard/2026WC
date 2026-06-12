# How to enter results & odds (step by step)

> The simple, no-jargon guide for during the tournament. (Technical version: `README.md` next to this file.)
> **Nothing to do until the tournament starts (June 11).** This is the daily routine once matches begin.

## ⭐ The easy way — one command, no spreadsheet (`record.py`)

You don't have to open any file. From the project folder:

```bash
python web/scripts/record.py gA-01 2 0                    # result: home 2, away 0
python web/scripts/record.py gA-01 --odds 1.40 4.50 7.00  # bookmaker 1X2 odds
python web/scripts/record.py --find Spain                 # find a match's id by team
python web/scripts/record.py --list                       # all matches + what's recorded
python web/scripts/record.py gA-01 --clear                # undo a mistake
```

It edits the CSV **and** rebuilds the site data in one shot. Then just
`git add -A && git commit -m "resultados" && git push`. Don't know the id?
`--find Spain` shows it. **That's the whole job.**

The rest of this file explains the underlying CSVs (in case you ever want to edit by hand).

---

There are two files in this `web/data/` folder. **Open them in Numbers or Excel** (they're spreadsheets — much easier than a text editor).

---

## 📋 File 1 — `results_live.csv` (the scores) — THE IMPORTANT ONE

It looks like this:

| id | home | away | home_score | away_score |
|---|---|---|---|---|
| gA-01 | Mexico | South Africa | *(blank)* | *(blank)* |
| gA-02 | South Korea | Czech Republic | *(blank)* | *(blank)* |

**You only ever touch the last two columns** (`home_score`, `away_score`). Leave `id`, `home`, `away` alone — they're already filled.

**When a match ends**, find its row (by the two team names) and type the goals.
Example — Mexico beats South Africa **2–0**:

| id | home | away | home_score | away_score |
|---|---|---|---|---|
| gA-01 | Mexico | South Africa | **2** | **0** |

Leave every not-yet-played match blank. Save the file.

---

## 💶 File 2 — `market_odds.csv` (the bookies' odds) — OPTIONAL

Feeds the **"Mercado"** line. **You can skip this entirely** — if you do, Mercado just shows "—". Only fill it if you want the "can my models beat the bookies?" comparison.

> **✅ Which odds, and when — the rule (use this every match):**
> Use the **Pinnacle closing line** — the final pre-match odds, just before kick-off. It's the **gold standard**: the sharpest, lowest-margin market estimate, and it's *not* affected by the result (it's pre-match), so it's a fair benchmark.
> - It's available **retroactively** — Oddsportal (and others) **archive closing odds**, so you're *not* racing the clock. Grab it just before kickoff **or** pull it after the match. Either is fine.
> - The only thing to avoid is *in-play* / post-result odds — those aren't pre-match and would cheat the comparison.
> - **Be consistent:** same source (Pinnacle), same moment (closing line), **every** match. That keeps Mercado a clean, comparable benchmark all tournament. (A low overround — ~2–4% — confirms you've got a genuine sharp line.)

| id | home | away | odd_1 | odd_X | odd_2 |
|---|---|---|---|---|---|
| gA-01 | Mexico | South Africa | *(blank)* | *(blank)* | *(blank)* |

Go to any betting site (Bet365…), find the match, copy the **three decimal numbers**:
- **odd_1** = odds the HOME team wins (Mexico) → e.g. `1.40`
- **odd_X** = odds of a DRAW → e.g. `4.50`
- **odd_2** = odds the AWAY team wins (South Africa) → e.g. `7.00`

| id | home | away | odd_1 | odd_X | odd_2 |
|---|---|---|---|---|---|
| gA-01 | Mexico | South Africa | **1.40** | **4.50** | **7.00** |

⚠️ The site must show **"Decimal"** odds (1.40, 2.50…), NOT American (+150) or fractional (5/2). There's usually a settings toggle for it.

---

## ▶️ After editing either file — run ONE command

In the terminal, from the project folder (`2026WC`):
```bash
.venv/bin/python web/scripts/build_matches.py
```
Then push (your usual):
```bash
git add -A && git commit -m "resultados" && git push
```
Vercel rebuilds the site automatically a minute later. The calendar rows flip to **Finalizado**, the ✓/✗/⭐ appear, and the **Tablero de aciertos** updates. ✅

---

## 🗓️ Daily routine in one line
**Type the day's scores into `results_live.csv` → run the build command → push.** That's the whole job. No servers, no database, nothing else.

---

## 🤚 Common questions
- **Which row is which match?** Read the `home` and `away` columns — they show the two teams. Find the row with the two teams that played.
- **I don't see knockout matches.** They appear once the group stage finishes and the teams are known.
- **I made a typo / wrong score.** Just fix the number, re-run the build command, push again. It overwrites cleanly.
- **Do I have to do the odds file?** No. Scores (File 1) are what light up the scoreboard. Odds (File 2) are a bonus.

## 💡 Even easier
The `record.py` helper (top of this file) means you never have to open these spreadsheets at all — `python web/scripts/record.py gA-01 2 0` does the edit + rebuild for you. The CSVs above are just the manual fallback.
