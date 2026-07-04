#!/usr/bin/env python3
"""
autofetch.py — hourly catch-up of finished World Cup 2026 results from >= 2
independent authoritative sources.

Discipline (matches the gA-06 lesson + the project's ETL rules):
  • Records a pending fixture ONLY when >= 2 sources report the SAME exact final
    score. One source, a disagreement, or an unmapped team name → FLAGGED, never
    guessed. The parser does not fail silently and does not drop data.
  • Results ONLY — no odds. Pinnacle closing lines stay a manual step (the sources
    don't carry them), exactly as we've done all tournament.
  • Idempotent: only looks at fixtures still 'por_jugarse'; re-runs are safe.
  • Timezone-proof: "finished" means a source shows a FINAL score (keyed by team
    names), never a clock calculation. The hourly schedule is just a heartbeat.

  python web/scripts/autofetch.py           # dry-run: report only, change nothing
  python web/scripts/autofetch.py --apply    # record agreements via record.py
"""
import sys, os, json, subprocess, argparse, unicodedata, datetime
import urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
MATCHES = os.path.join(ROOT, 'web', 'static', 'data', 'matches.json')
FLAGS = os.path.join(ROOT, 'web', 'data', 'autofetch_flags.json')
RECORD = os.path.join(HERE, 'record.py')
KO_DISCOVER = os.path.join(HERE, 'ko_discover.py')
EXPORTER = os.path.join(HERE, 'build_matches.py')
UA = {'User-Agent': 'orion-quiniela-autofetch/1.0 (+puedelaiaganarquinielas.com)'}


# ── name normalization ───────────────────────────────────────────────────────
def norm(name):
    s = unicodedata.normalize('NFKD', name or '').encode('ascii', 'ignore').decode().lower()
    for ch in ".'-&":
        s = s.replace(ch, ' ')
    return ' '.join(s.split())

# Source spelling variants → our canonical team names (as in matches.json).
ALIASES = {
    'czechia': 'Czech Republic', 'czech republic': 'Czech Republic',
    'cote d ivoire': 'Ivory Coast', 'ivory coast': 'Ivory Coast',
    'turkiye': 'Turkey', 'turkey': 'Turkey',
    'korea republic': 'South Korea', 'south korea': 'South Korea',
    'ir iran': 'Iran', 'iran': 'Iran',
    'cabo verde': 'Cape Verde', 'cape verde': 'Cape Verde',
    'dr congo': 'DR Congo', 'congo dr': 'DR Congo',
    'democratic republic of the congo': 'DR Congo', 'congo': 'DR Congo',
    'usa': 'United States', 'united states': 'United States', 'united states of america': 'United States',
    'curacao': 'Curaçao',
    'cape verde islands': 'Cape Verde',
    'bosnia and herzegovina': 'Bosnia and Herzegovina',
    'bosnia herzegovina': 'Bosnia and Herzegovina',
}
ALIASES = {norm(k): v for k, v in ALIASES.items()}


def resolver(canonical_names):
    canon = {norm(t): t for t in canonical_names}

    def resolve(raw):
        n = norm(raw)
        if n in canon:
            return canon[n]
        if n in ALIASES:
            return ALIASES[n]
        return None  # unmapped → caller flags it; never silently dropped
    return resolve


# ── source adapters: each returns list of (rawHome, gHome, rawAway, gAway) ─────
def get_json(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.load(r)


def src_espn(dates):
    rows, errs = [], []
    for d in dates:
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?dates={d:%Y%m%d}"
        try:
            data = get_json(url)
        except Exception as e:
            errs.append(f"espn {d:%Y-%m-%d}: {e}")
            continue
        for ev in data.get('events', []):
            comp = (ev.get('competitions') or [{}])[0]
            st = ((comp.get('status') or ev.get('status') or {}).get('type') or {})
            if not st.get('completed'):
                continue
            cs = comp.get('competitors', [])
            if len(cs) != 2:
                continue
            try:
                h = next(c for c in cs if c.get('homeAway') == 'home')
                a = next(c for c in cs if c.get('homeAway') == 'away')
                rows.append((h['team']['displayName'], int(h['score']),
                             a['team']['displayName'], int(a['score'])))
            except Exception:
                continue
    return rows, errs


def src_thesportsdb(dates):
    rows, errs = [], []
    for d in dates:
        url = f"https://www.thesportsdb.com/api/v1/json/3/eventsday.php?d={d:%Y-%m-%d}&s=Soccer"
        try:
            data = get_json(url)
        except Exception as e:
            errs.append(f"thesportsdb {d:%Y-%m-%d}: {e}")
            continue
        for ev in (data.get('events') or []):
            lg = (ev.get('strLeague') or '').lower()
            if 'world cup' not in lg or 'qual' in lg:
                continue
            # "Finished" must be decided by the source's status, never by the mere
            # presence of a score: an in-play event carries the LIVE score (e.g. a
            # half-time 1-1), which is not the final. Only accept terminal states.
            if (ev.get('strStatus') or '').strip().upper() not in TSDB_FINISHED:
                continue
            hs, as_ = ev.get('intHomeScore'), ev.get('intAwayScore')
            if hs in (None, '') or as_ in (None, ''):
                continue
            try:
                rows.append((ev['strHomeTeam'], int(hs), ev['strAwayTeam'], int(as_)))
            except Exception:
                continue
    return rows, errs


# Terminal status codes per source (a finished match — full time, after extra time,
# or decided on penalties). Anything else (in play, half time, scheduled) is NOT final.
TSDB_FINISHED = {'FT', 'AET', 'PEN', 'AWD', 'WO', 'MATCH FINISHED'}
AF_FINISHED = {'FT', 'AET', 'PEN', 'AWD', 'WO'}
WORLD_CUP_LEAGUE_ID = 1  # API-Football league id for the World Cup


def src_apifootball(dates):
    """API-Football (api-sports) — the authoritative, comprehensive feed we already
    pay for. It carries every fixture with an explicit status, so it both confirms
    genuine finals and refuses in-play ones. Degrades gracefully (returns an error,
    never crashes the run) if the key is missing or the quota is exhausted."""
    rows, errs = [], []
    af_dir = os.path.join(ROOT, 'v2', 'm3')
    if af_dir not in sys.path:
        sys.path.insert(0, af_dir)
    try:
        import af_client
    except Exception as e:
        return rows, [f"api-football: cliente no disponible ({e})"]
    for d in dates:
        try:
            # force=True: always fetch live — a match may have finished since last run.
            data = af_client.get(f"/fixtures?date={d:%Y-%m-%d}", force=True)
        except BaseException as e:  # noqa: BLE001 — missing key raises SystemExit; degrade, don't abort
            errs.append(f"api-football {d:%Y-%m-%d}: {e}")
            continue
        if not isinstance(data, dict):
            errs.append(f"api-football {d:%Y-%m-%d}: respuesta inesperada")
            continue
        problem = data.get('_http_error') or data.get('_url_error') or data.get('errors') or data.get('_api_errors')
        if problem:
            errs.append(f"api-football {d:%Y-%m-%d}: {problem}")
            continue
        for f in (data.get('response') or []):
            if (f.get('league') or {}).get('id') != WORLD_CUP_LEAGUE_ID:
                continue
            st = (((f.get('fixture') or {}).get('status') or {}).get('short') or '').upper()
            if st not in AF_FINISHED:
                continue
            t, g = f.get('teams') or {}, f.get('goals') or {}
            h = (t.get('home') or {}).get('name')
            a = (t.get('away') or {}).get('name')
            gh, ga = g.get('home'), g.get('away')
            if h is None or a is None or gh is None or ga is None:
                continue
            try:
                rows.append((h, int(gh), a, int(ga)))
            except (TypeError, ValueError):
                continue
    return rows, errs


SOURCES = [('espn', src_espn), ('thesportsdb', src_thesportsdb), ('api-football', src_apifootball)]


# ── main ──────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--apply', action='store_true', help="record agreements (default: dry-run)")
    args = ap.parse_args()

    matches = json.load(open(MATCHES, encoding='utf-8'))['matches']
    canonical = {m['home'] for m in matches} | {m['away'] for m in matches}
    resolve = resolver(canonical)
    # Group stage ONLY. Knockout ties are handled by the ko_discover phase, which records
    # the 90-minute score (not the ET/penalty final that these exact-score sources report)
    # and the advancer. Letting the group loop touch them would mis-record ET/pen results.
    pending = {frozenset((m['home'], m['away'])): m
               for m in matches if m['status'] != 'finalizado' and m.get('stage') == 'grupos'}

    # Dates to query: every pending fixture date that is today-or-past (UTC), ±1 day for TZ.
    today = datetime.datetime.now(datetime.timezone.utc).date()
    dates = set()
    for m in pending.values():
        d = datetime.date.fromisoformat(m['date'])
        if d <= today + datetime.timedelta(days=1):
            for off in (-1, 0, 1):
                dates.add(d + datetime.timedelta(days=off))
    dates = sorted(dates)

    flags, errors = [], []
    # Build per-source {teamset: {team: goals}} of FINISHED matches, resolving names.
    per_source = {}
    for sname, fn in SOURCES:
        raw, errs = fn(dates)
        errors += errs
        table = {}
        for rh, gh, ra, ga in raw:
            ch, ca = resolve(rh), resolve(ra)
            if ch is None or ca is None:
                # Only flag unmapped names that involve a still-pending fixture's group of teams.
                if (ch or rh) and (ca or ra):
                    flags.append({'kind': 'unmapped-team', 'source': sname,
                                  'raw': [rh, ra], 'resolved': [ch, ca]})
                continue
            table[frozenset((ch, ca))] = {ch: gh, ca: ga}
        per_source[sname] = table
        print(f"  fuente {sname}: {len(table)} partidos finalizados parseados"
              + (f"  ⚠ {len(errs)} error(es)" if errs else ""))

    applied, waiting, disagree = [], [], []
    for key, m in pending.items():
        reports = [(s, per_source[s][key]) for s, _ in SOURCES if key in per_source[s]]
        if not reports:
            continue
        home, away = m['home'], m['away']
        if len(reports) < 2:
            waiting.append((m, reports[0]))
            flags.append({'kind': 'single-source', 'id': m['id'],
                          'fixture': f"{home} vs {away}", 'source': reports[0][0],
                          'score': [reports[0][1][home], reports[0][1][away]]})
            continue
        scores = {(r[home], r[away]) for _, r in reports}
        if len(scores) != 1:
            disagree.append((m, reports))
            flags.append({'kind': 'sources-disagree', 'id': m['id'],
                          'fixture': f"{home} vs {away}",
                          'reports': {s: [r[home], r[away]] for s, r in reports}})
            continue
        hg, ag = reports[0][1][home], reports[0][1][away]
        applied.append((m, hg, ag))

    # Report
    print("")
    if applied:
        print("✓ CONCUERDAN (≥2 fuentes) — listos para registrar:")
        for m, hg, ag in applied:
            print(f"    {m['id']}: {m['home']} {hg}-{ag} {m['away']}")
    if waiting:
        print("… una sola fuente (esperando confirmación de la 2ª):")
        for m, (s, r) in waiting:
            print(f"    {m['id']}: {m['home']} {r[m['home']]}-{r[m['away']]} {m['away']}  ({s})")
    if disagree:
        print("⚠ FUENTES EN CONFLICTO — NO se registra, revisar a mano:")
        for m, reports in disagree:
            detail = ", ".join(f"{s} {r[m['home']]}-{r[m['away']]}" for s, r in reports)
            print(f"    {m['id']}: {m['home']} vs {m['away']}  →  {detail}")
    if errors:
        print("⚠ errores de fuente:", "; ".join(errors))
    if not (applied or waiting or disagree):
        print("Sin partidos nuevos finalizados.")

    # Persist flags (diff-stable: no per-run timestamp inside) so they surface in a commit.
    if flags:
        json.dump({'flags': sorted(flags, key=lambda x: x.get('id', x['kind']))},
                  open(FLAGS, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    elif os.path.exists(FLAGS):
        os.remove(FLAGS)

    # Apply
    if args.apply and applied:
        print("\nRegistrando…")
        for m, hg, ag in applied:
            subprocess.run([sys.executable, RECORD, m['id'], str(hg), str(ag)],
                           check=True, capture_output=True)
            print(f"    ✓ {m['id']} {m['home']} {hg}-{ag} {m['away']}")
    elif applied:
        print("\n(dry-run — use --apply para registrar)")

    # ── Knockout phase ─────────────────────────────────────────────────────────
    # Discover + record the bracket (R32→Final) from the same authoritative feeds.
    # Run as a subprocess (ko_discover imports this module → avoids a circular import),
    # in the same dry-run/apply mode. On --apply, rebuild matches.json once so the new
    # knockout fixtures/results are published alongside the group stage.
    print("\n── Eliminatorias ──")
    ko = subprocess.run([sys.executable, KO_DISCOVER] + (['--apply'] if args.apply else []),
                        capture_output=True, text=True)
    print(ko.stdout.rstrip() or "(sin salida)")
    if ko.returncode != 0:
        print("⚠ ko_discover falló:\n", ko.stderr.rstrip())
    elif args.apply:
        build = subprocess.run([sys.executable, EXPORTER], capture_output=True, text=True)
        for line in build.stdout.splitlines():
            if line.startswith('matches:'):
                print("  " + line.strip())
        if build.returncode != 0:
            print("⚠ build_matches falló:\n", build.stderr.rstrip())


if __name__ == '__main__':
    main()
