#!/usr/bin/env python3
"""
sync_results_to_corpus.py — feed the played World Cup finals into the TRAINING corpus.

The models train on results.csv, where the 2026 WC finals sit as NA (group) or are
absent (knockouts). Live results live only in results_live.csv (display). This script
carries the finals into results.csv so that compute_elo — which ALREADY uses K=60 for
'FIFA World Cup' — updates team strengths, and the rolling-form features absorb them.

Discipline (project ETL rules):
  • Content-based matching (unordered team pair within 2026 WC rows), never row position.
  • Idempotent: a group row already scored is left alone; a KO row already present is not
    duplicated. Safe to re-run after each round.
  • Uses the recorded 90-MINUTE score (a penalty tie stays a draw — matches how Elo should
    treat shootouts; decision D1).
  • Dry-run by default; --apply gates the write. Never fails silently — unmatched rows are
    reported, not dropped.

  python web/scripts/sync_results_to_corpus.py            # dry-run: report only
  python web/scripts/sync_results_to_corpus.py --apply     # write results.csv
"""
import os, csv, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
CORPUS = os.path.join(ROOT, 'results.csv')
RESULTS_LIVE = os.path.join(ROOT, 'web', 'data', 'results_live.csv')
KO_FIXTURES = os.path.join(ROOT, 'web', 'data', 'knockout_fixtures.csv')
WC = 'FIFA World Cup'


def load_live():
    """{id: {home, away, hs, as}} for finalized rows (both scores present)."""
    out = {}
    with open(RESULTS_LIVE, newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            hs, a_s = (r.get('home_score') or '').strip(), (r.get('away_score') or '').strip()
            if hs == '' or a_s == '':
                continue
            out[r['id']] = {'home': r['home'], 'away': r['away'], 'hs': int(hs), 'as': int(a_s)}
    return out


def load_ko_dates():
    """{id: {date, home, away}} from the discovered knockout fixtures."""
    out = {}
    if os.path.exists(KO_FIXTURES):
        with open(KO_FIXTURES, newline='', encoding='utf-8') as f:
            for r in csv.DictReader(f):
                out[r['id']] = {'date': r['date'], 'home': r['home'], 'away': r['away']}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--apply', action='store_true', help="write results.csv (default: dry-run)")
    args = ap.parse_args()

    with open(CORPUS, newline='', encoding='utf-8') as f:
        rd = csv.DictReader(f)
        fields = list(rd.fieldnames)
        rows = list(rd)

    # Index 2026 WC rows by unordered team pair (for group fill + KO dup-check).
    wc2026 = {}
    for row in rows:
        if row['tournament'] == WC and (row['date'] or '').startswith('2026'):
            wc2026.setdefault(frozenset((row['home_team'], row['away_team'])), []).append(row)

    live = load_live()
    ko_dates = load_ko_dates()

    filled, already, appended, dup, flags = [], 0, [], 0, []

    for mid, r in sorted(live.items()):
        pair = frozenset((r['home'], r['away']))
        is_ko = mid.startswith('P')

        if not is_ko:
            # GROUP: fill the matching NA row in the corpus (oriented to that row).
            candidates = [x for x in wc2026.get(pair, []) if x['home_score'] in ('NA', '', None)]
            scored = [x for x in wc2026.get(pair, []) if x['home_score'] not in ('NA', '', None)]
            if not candidates and scored:
                already += 1
                continue
            if not candidates:
                flags.append(f"GROUP {mid} {r['home']} vs {r['away']}: no matching 2026 WC NA row")
                continue
            if len(candidates) > 1:
                flags.append(f"GROUP {mid} {r['home']} vs {r['away']}: {len(candidates)} ambiguous rows")
                continue
            row = candidates[0]
            if row['home_team'] == r['home']:
                hs, a_s = r['hs'], r['as']
            else:  # corpus row orientation is reversed → swap
                hs, a_s = r['as'], r['hs']
            filled.append((row, str(hs), str(a_s), r['home'], r['away'], r['hs'], r['as']))
        else:
            # KO: append a new WC row (idempotent — skip if already present for that pair/date).
            fx = ko_dates.get(mid)
            if not fx:
                flags.append(f"KO {mid} {r['home']} vs {r['away']}: no date in knockout_fixtures.csv")
                continue
            if any(x['date'] == fx['date'] for x in wc2026.get(pair, [])):
                dup += 1
                continue
            appended.append({
                'date': fx['date'], 'home_team': r['home'], 'away_team': r['away'],
                'home_score': str(r['hs']), 'away_score': str(r['as']),
                'tournament': WC, 'city': '', 'country': '', 'neutral': 'TRUE',
            })

    # ── Report ──
    print(f"GROUP: {len(filled)} to fill · {already} already scored")
    for row, hs, a_s, lh, la, ohs, oas in filled[:6]:
        print(f"    {row['date']} {row['home_team']} {hs}-{a_s} {row['away_team']}  (from {lh} {ohs}-{oas} {la})")
    if len(filled) > 6:
        print(f"    … +{len(filled)-6} more")
    print(f"KNOCKOUT: {len(appended)} to append · {dup} already present")
    for a in appended:
        print(f"    {a['date']} {a['home_team']} {a['home_score']}-{a['away_score']} {a['away_team']} (WC, K=60)")
    if flags:
        print("⚠ FLAGS (not synced, review):")
        for fl in flags:
            print("   -", fl)

    if not args.apply:
        print("\n(dry-run — use --apply to write results.csv)")
        return

    # ── Apply ──
    for row, hs, a_s, *_ in filled:
        row['home_score'], row['away_score'] = hs, a_s
    rows.extend(appended)
    with open(CORPUS, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)
    print(f"\n✓ wrote {CORPUS}: filled {len(filled)} group + appended {len(appended)} knockout rows")


if __name__ == '__main__':
    main()
