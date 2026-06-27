#!/usr/bin/env python3
"""
player_state.py — tournament player-state collector (M3 feature foundation).

Pulls per-player, per-match data from ESPN's match-summary endpoint for every
completed World Cup 2026 fixture and aggregates it into a per-team "player state":
who the load-bearing players are (goal + assist share), how concentrated each
team's output is in a few players, and suspension risk (reds / yellow build-up).

This is DATA COLLECTION only — it does not touch the model. The downstream M3
adjustment layer (scaling λ for availability) will consume v2/output/player_state.json.
It must be backtest-gated before it ships, like the home-advantage feature was.

  python v2/player_state.py            # collect + print report
  python v2/player_state.py --json     # also write v2/output/player_state.json
"""
import os, json, argparse, unicodedata, urllib.request
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
MATCHES = os.path.join(ROOT, 'web', 'static', 'data', 'matches.json')
OUT = os.path.join(HERE, 'output', 'player_state.json')
UA = {'User-Agent': 'orion-player-state/1.0 (+puedelaiaganarquinielas.com)'}


def get(url):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25))


def norm(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()
    for ch in ".'-&":
        s = s.replace(ch, ' ')
    return ' '.join(s.split())

# ESPN team spelling → our canonical name (matches.json).
ALIASES = {norm(k): v for k, v in {
    'Czechia': 'Czech Republic', 'Cote d Ivoire': 'Ivory Coast', 'Turkiye': 'Turkey',
    'Korea Republic': 'South Korea', 'IR Iran': 'Iran', 'Cabo Verde': 'Cape Verde',
    'Congo DR': 'DR Congo', 'Bosnia-Herzegovina': 'Bosnia and Herzegovina',
    'USA': 'United States',
}.items()}


def resolver(canon_names):
    canon = {norm(t): t for t in canon_names}
    def resolve(raw):
        n = norm(raw)
        return canon.get(n) or ALIASES.get(n)
    return resolve


def stat_dict(player):
    return {s.get('name'): s.get('value') for s in (player.get('stats') or [])}


def collect(matches):
    canon = {m['home'] for m in matches} | {m['away'] for m in matches}
    resolve = resolver(canon)
    done = [m for m in matches if m['status'] == 'finalizado']
    dates = sorted({m['date'] for m in done})

    # athlete aggregates keyed by (team, name)
    agg = defaultdict(lambda: {'team': None, 'pos': '', 'goals': 0, 'assists': 0,
                               'yellows': 0, 'reds': 0, 'shots': 0, 'sot': 0,
                               'saves': 0, 'starts': 0, 'apps': 0})
    seen_events, unmapped = set(), set()
    for d in dates:
        sb = get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?dates={d.replace('-','')}")
        for ev in sb.get('events', []):
            comp = ev['competitions'][0]
            if not ((comp.get('status', {}).get('type') or {}).get('completed')):
                continue
            eid = ev['id']
            if eid in seen_events:
                continue
            seen_events.add(eid)
            summ = get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/summary?event={eid}")
            for ros in summ.get('rosters', []):
                team = resolve(ros.get('team', {}).get('displayName', ''))
                if team is None:
                    unmapped.add(ros.get('team', {}).get('displayName', ''))
                    continue
                for pl in ros.get('roster', []):
                    if not pl.get('active') and not pl.get('starter') and not pl.get('subbedIn'):
                        continue
                    st = stat_dict(pl)
                    name = pl.get('athlete', {}).get('displayName', '?')
                    a = agg[(team, name)]
                    a['team'] = team
                    a['pos'] = pl.get('position', {}).get('abbreviation', a['pos'])
                    a['goals'] += int(st.get('totalGoals') or 0)
                    a['assists'] += int(st.get('goalAssists') or 0)
                    a['yellows'] += int(st.get('yellowCards') or 0)
                    a['reds'] += int(st.get('redCards') or 0)
                    a['shots'] += int(st.get('totalShots') or 0)
                    a['sot'] += int(st.get('shotsOnTarget') or 0)
                    a['saves'] += int(st.get('saves') or 0)
                    a['starts'] += 1 if pl.get('starter') else 0
                    a['apps'] += 1 if (st.get('appearances') or pl.get('starter') or pl.get('subbedIn')) else 0
    return agg, len(seen_events), unmapped


def build_state(agg):
    """Per-team: ranked players, output concentration, suspension flags."""
    by_team = defaultdict(list)
    for (team, name), a in agg.items():
        by_team[team].append({'name': name, **{k: a[k] for k in
                              ('pos', 'goals', 'assists', 'yellows', 'reds', 'shots', 'sot', 'saves', 'starts', 'apps')}})
    state = {}
    for team, players in by_team.items():
        for p in players:
            p['contribution'] = p['goals'] + 0.7 * p['assists']        # goal-involvement weight
        players.sort(key=lambda p: (-p['contribution'], -p['goals'], -p['shots']))
        tot = sum(p['contribution'] for p in players) or 1.0
        for p in players:
            p['weight'] = round(p['contribution'] / tot, 3)             # share of team goal involvement
        top3 = sum(p['contribution'] for p in players[:3])
        suspended = [p['name'] for p in players if p['reds'] > 0]       # red → misses next match
        at_risk = [p['name'] for p in players if p['reds'] == 0 and p['yellows'] >= 1 and p['contribution'] > 0]
        state[team] = {
            'concentration_top3': round(top3 / tot, 3),                 # how few players carry the team
            'key_players': [p for p in players if p['contribution'] > 0][:6],
            'suspended_next': suspended,
            'yellow_watch': at_risk,
            'players': players,
        }
    return state


# ── absence detection from confirmed lineups (released ~1h pre-kickoff) ─────────
# The ESPN /injuries feed is empty for this tournament, so instead of guessing the
# REASON (injury vs suspension vs rotation) we read the confirmed matchday squad and
# flag any key player who isn't in it. Reason-agnostic, deterministic: in the XI =
# available, on the bench = partial, not in the squad at all = out.
def confirmed_squad(event_id, resolve):
    s = get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/summary?event={event_id}")
    out = {}
    for ros in s.get('rosters', []):
        team = resolve(ros.get('team', {}).get('displayName', ''))
        if not team:
            continue
        pls = ros.get('roster', [])
        xi = {p.get('athlete', {}).get('displayName') for p in pls if p.get('starter')}
        squad = {p.get('athlete', {}).get('displayName') for p in pls
                 if p.get('active') or p.get('starter') or p.get('subbedIn')}
        out[team] = {'xi': xi, 'squad': squad, 'released': len(xi) >= 11}
    return out


def absences_for_date(date, state, resolve):
    d = date.replace('-', '')
    sb = get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?dates={d}")
    report = []
    for ev in sb.get('events', []):
        for team, sq in confirmed_squad(ev['id'], resolve).items():
            if not sq['released'] or team not in state:
                continue
            # Card-suspension source kept as a cross-check (not discarded).
            susp = set(state[team].get('suspended_next', []))
            watch = set(state[team].get('yellow_watch', []))
            players = []
            for p in state[team]['key_players']:
                if p.get('weight', 0) <= 0:
                    continue
                status = 'XI' if p['name'] in sq['xi'] else ('banca' if p['name'] in sq['squad'] else 'FUERA')
                card = 'roja' if p['name'] in susp else ('amarilla' if p['name'] in watch else None)
                # Reconcile the two sources.
                if status == 'FUERA' and card == 'roja':
                    check = 'confirma (lineup + tarjeta)'
                elif status == 'FUERA':
                    check = 'solo lineup (lesión/rotación?)'
                elif status != 'FUERA' and card == 'roja':
                    check = '⚠ CONFLICTO: en plantel pese a roja'
                elif card == 'amarilla':
                    check = 'amarilla en vigilancia'
                else:
                    check = ''
                players.append({'name': p['name'], 'weight': p['weight'], 'goals': p['goals'],
                                'assists': p['assists'], 'status': status, 'card': card, 'check': check})
            report.append({'match': ev.get('name', ''), 'team': team, 'players': players})
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--json', action='store_true', help="write v2/output/player_state.json")
    ap.add_argument('--absences', metavar='YYYYMMDD', help="flag absent key players for a date's matches (needs --json first)")
    args = ap.parse_args()

    matches = json.load(open(MATCHES, encoding='utf-8'))['matches']
    canon = {m['home'] for m in matches} | {m['away'] for m in matches}
    resolve = resolver(canon)

    # Absence mode: read cached state, check confirmed lineups for a date.
    if args.absences:
        if not os.path.exists(OUT):
            print("Falta el estado. Corre primero:  python v2/player_state.py --json"); return
        state = json.load(open(OUT, encoding='utf-8'))
        rep = absences_for_date(args.absences, state, resolve)
        if not rep:
            print(f"Sin alineaciones confirmadas todavía para {args.absences} (se publican ~1h antes).")
            return
        print(f"Disponibilidad de jugadores clave — {args.absences}:")
        for r in rep:
            print(f"\n  {r['team']}  ({r['match']})")
            for p in r['players']:
                mark = {'XI': '✓ titular', 'banca': '◐ banca', 'FUERA': '✗ FUERA'}[p['status']]
                chk = f"  ·  {p['check']}" if p['check'] else ''
                print(f"    {mark:12} {p['name']:22} peso {p['weight']:.2f}  ({p['goals']}g+{p['assists']}a){chk}")
        return

    agg, n_matches, unmapped = collect(matches)
    state = build_state(agg)

    print(f"Recolectado de {n_matches} partidos · {len(agg)} jugadores · {len(state)} selecciones")
    if unmapped:
        print("⚠ equipos sin mapear:", sorted(unmapped))

    # Report: most goal-dependent teams + their key men, and suspension flags.
    ranked = sorted(state.items(), key=lambda kv: -kv[1]['concentration_top3'])
    print("\nDependencia de pocos jugadores (top-3 sobre la producción del equipo):")
    for team, s in ranked[:8]:
        keys = ", ".join(f"{p['name']} ({p['goals']}g{'+'+str(p['assists'])+'a' if p['assists'] else ''})"
                         for p in s['key_players'][:3])
        print(f"  {team:24} {int(s['concentration_top3']*100):3d}%  ·  {keys}")

    susp = [(t, s) for t, s in state.items() if s['suspended_next'] or s['yellow_watch']]
    print("\nRiesgo de disponibilidad (rojas / amarillas acumuladas):")
    for team, s in sorted(susp):
        bits = []
        if s['suspended_next']:
            bits.append("ROJA→fuera: " + ", ".join(s['suspended_next']))
        if s['yellow_watch']:
            bits.append("amarilla: " + ", ".join(s['yellow_watch'][:4]))
        print(f"  {team:24} {' · '.join(bits)}")

    if args.json:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        json.dump(state, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        print(f"\n✓ escrito {OUT}")


if __name__ == '__main__':
    main()
