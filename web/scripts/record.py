#!/usr/bin/env python3
"""
record.py — one-command result/odds entry for the live scoreboard.
No spreadsheet. Edits the CSV(s) and regenerates matches.json in one shot.

  python web/scripts/record.py gA-01 2 0                      # result: home 2, away 0
  python web/scripts/record.py gA-01 --odds 1.40 4.50 7.00    # bookmaker 1X2 odds (home/draw/away)
  python web/scripts/record.py gA-01 2 0 --odds 1.40 4.50 7.00
  python web/scripts/record.py gA-01 --clear                 # undo (blank a match's result+odds)
  python web/scripts/record.py --find Spain                  # look up match ids for a team
  python web/scripts/record.py --list                        # all matches + what's recorded

Then just:  git add -A && git commit -m "resultados" && git push
"""
import sys, os, csv, argparse, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
RESULTS = os.path.join(ROOT, 'web', 'data', 'results_live.csv')
MARKET = os.path.join(ROOT, 'web', 'data', 'market_odds.csv')
EXPORTER = os.path.join(HERE, 'build_matches.py')


def load(path):
    with open(path, newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    with open(path, newline='', encoding='utf-8') as f:
        fields = next(csv.reader(f))
    return rows, fields


def save(path, rows, fields):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)


def by_id(rows, mid):
    return next((r for r in rows if r['id'] == mid), None)


def ensure_templates():
    """The exporter creates results_live.csv / market_odds.csv if missing."""
    if not (os.path.exists(RESULTS) and os.path.exists(MARKET)):
        subprocess.run([sys.executable, EXPORTER], check=True, capture_output=True)


def regenerate():
    print("Regenerating matches.json …")
    res = subprocess.run([sys.executable, EXPORTER], capture_output=True, text=True)
    if res.returncode != 0:
        print("  ⚠ exporter failed:\n", res.stderr); sys.exit(1)
    for line in res.stdout.splitlines():
        if line.startswith('matches:'):
            print("  " + line.strip())


def main():
    ap = argparse.ArgumentParser(description="Record a match result / odds and rebuild the site data.")
    ap.add_argument('id', nargs='?', help="match id, e.g. gA-01 (use --find / --list to look up)")
    ap.add_argument('home_score', nargs='?', type=int)
    ap.add_argument('away_score', nargs='?', type=int)
    ap.add_argument('--odds', nargs=3, type=float, metavar=('H', 'X', 'A'), help="decimal 1X2 odds")
    ap.add_argument('--clear', action='store_true', help="blank this match's result + odds")
    ap.add_argument('--find', metavar='TEAM', help="list match ids involving a team")
    ap.add_argument('--list', action='store_true', help="list all matches + status")
    args = ap.parse_args()

    ensure_templates()
    results, rfields = load(RESULTS)

    if args.list or args.find:
        market, _ = load(MARKET)
        odds_ids = {r['id'] for r in market if (r.get('odd_1') or '').strip()}
        q = (args.find or '').lower()
        shown = 0
        for r in results:
            if q and q not in r['home'].lower() and q not in r['away'].lower():
                continue
            done = '✓' if (r.get('home_score') or '').strip() != '' else ' '
            od = 'odds' if r['id'] in odds_ids else '    '
            print(f"  [{done}] {od}  {r['id']:7s}  {r['home']} vs {r['away']}")
            shown += 1
        if not shown:
            print("  (no matches)" + (f" for '{args.find}'" if args.find else ""))
        return

    if not args.id:
        ap.print_help(); return
    row = by_id(results, args.id)
    if row is None:
        print(f"✗ no match with id '{args.id}'.  Try:  record.py --find <team>"); sys.exit(1)

    changed = False

    if args.clear:
        row['home_score'] = row['away_score'] = ''
        save(RESULTS, results, rfields)
        market, mfields = load(MARKET)
        mrow = by_id(market, args.id)
        if mrow:
            mrow['odd_1'] = mrow['odd_X'] = mrow['odd_2'] = ''
            save(MARKET, market, mfields)
        print(f"✓ cleared {args.id} ({row['home']} vs {row['away']})")
        changed = True
    else:
        if args.home_score is not None and args.away_score is not None:
            if args.home_score < 0 or args.away_score < 0:
                print("✗ scores must be ≥ 0"); sys.exit(1)
            row['home_score'], row['away_score'] = str(args.home_score), str(args.away_score)
            save(RESULTS, results, rfields)
            print(f"✓ result:  {row['home']} {args.home_score}–{args.away_score} {row['away']}")
            changed = True
        if args.odds:
            if any(o <= 1.0 for o in args.odds):
                print("✗ decimal odds must be > 1.0"); sys.exit(1)
            market, mfields = load(MARKET)
            mrow = by_id(market, args.id)
            mrow['odd_1'], mrow['odd_X'], mrow['odd_2'] = (f"{o:g}" for o in args.odds)
            save(MARKET, market, mfields)
            print(f"✓ odds:    {row['home']} {args.odds[0]} / empate {args.odds[1]} / {row['away']} {args.odds[2]}")
            changed = True

    if not changed:
        print("Nothing to record. Give a score:  record.py <id> <home> <away>   and/or  --odds H X A")
        return
    regenerate()
    print('\nDone. Now:  git add -A && git commit -m "resultados" && git push')


if __name__ == '__main__':
    main()
