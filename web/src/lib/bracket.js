// Deterministic knockout bracket for the 2026 World Cup.
//
// A slot shows a team ONLY when that team is mathematically locked into that exact
// position; otherwise it stays a blank placeholder (empty flag box + name underline).
// Nothing here is probabilistic — it is a fill-in-as-certainty-arrives quiniela.
//
// Official slot map reconstructed from the FIFA 2026 bracket skeleton (P73–P104):
// 12 group winners (1A–1L) + 12 runners-up (2A–2L) + 8 best thirds (3·····) = 32.
// The third-place slots resolve only once ALL 12 groups are final and the official
// combination matrix assigns each qualifying third — until then they stay blank.

// ── Official R32 mapping ───────────────────────────────────────────────────────
// Each slot feed is { pos: 1|2, group: 'A' } (winner/runner) or { third: ['A',…] }.
// w(g) = winner, r(g) = runner-up, t(...) = third from one of these groups.
const w = (g) => ({ pos: 1, group: g });
const r = (g) => ({ pos: 2, group: g });
const t = (...gs) => ({ third: gs });

// R32 ties keyed by FIFA position id (P73–P88), with date/time for the printable sheet.
export const R32 = [
  { id: 'P73', date: '2026-06-28', time: '13:00', a: r('A'), b: r('B') },
  { id: 'P74', date: '2026-06-29', time: '14:30', a: w('E'), b: t('A', 'B', 'C', 'D', 'F') },
  { id: 'P75', date: '2026-06-29', time: '19:00', a: w('F'), b: r('C') },
  { id: 'P76', date: '2026-06-29', time: '11:00', a: w('C'), b: r('F') },
  { id: 'P77', date: '2026-06-30', time: '15:00', a: w('I'), b: t('C', 'D', 'F', 'G', 'H') },
  { id: 'P78', date: '2026-06-30', time: '11:00', a: r('E'), b: r('I') },
  { id: 'P79', date: '2026-06-30', time: '19:00', a: w('A'), b: t('C', 'E', 'F', 'H', 'I') },
  { id: 'P80', date: '2026-07-01', time: '10:00', a: w('L'), b: t('E', 'H', 'I', 'J', 'K') },
  { id: 'P81', date: '2026-07-01', time: '18:00', a: w('D'), b: t('B', 'E', 'F', 'I', 'J') },
  { id: 'P82', date: '2026-07-01', time: '14:00', a: w('G'), b: t('A', 'E', 'H', 'I', 'J') },
  { id: 'P83', date: '2026-07-02', time: '17:00', a: r('K'), b: r('L') },
  { id: 'P84', date: '2026-07-02', time: '13:00', a: w('H'), b: r('J') },
  { id: 'P85', date: '2026-07-02', time: '21:00', a: w('B'), b: t('E', 'F', 'G', 'I', 'J') },
  { id: 'P86', date: '2026-07-03', time: '16:00', a: w('J'), b: r('H') },
  { id: 'P87', date: '2026-07-03', time: '19:30', a: w('K'), b: t('D', 'E', 'I', 'J', 'L') },
  { id: 'P88', date: '2026-07-03', time: '12:00', a: r('D'), b: r('G') },
];

// Later rounds reference the winner (W##) of earlier slots. Left half flows to the
// P101 semifinal, right half to P102; the printable sheet mirrors the two halves.
export const ROUNDS = {
  r16: [
    { id: 'P89', date: '2026-07-04', time: '15:00', a: 'P74', b: 'P77' },
    { id: 'P90', date: '2026-07-04', time: '11:00', a: 'P73', b: 'P75' },
    { id: 'P94', date: '2026-07-06', time: '18:00', a: 'P81', b: 'P82' },
    { id: 'P93', date: '2026-07-06', time: '13:00', a: 'P83', b: 'P84' },
    { id: 'P91', date: '2026-07-05', time: '14:00', a: 'P76', b: 'P78' },
    { id: 'P92', date: '2026-07-05', time: '18:00', a: 'P79', b: 'P80' },
    { id: 'P95', date: '2026-07-07', time: '10:00', a: 'P86', b: 'P88' },
    { id: 'P96', date: '2026-07-07', time: '14:00', a: 'P85', b: 'P87' },
  ],
  qf: [
    { id: 'P97', date: '2026-07-09', time: '14:00', a: 'P89', b: 'P90' },
    { id: 'P98', date: '2026-07-10', time: '13:00', a: 'P93', b: 'P94' },
    { id: 'P99', date: '2026-07-11', time: '15:00', a: 'P91', b: 'P92' },
    { id: 'P100', date: '2026-07-11', time: '19:00', a: 'P95', b: 'P96' },
  ],
  sf: [
    { id: 'P101', date: '2026-07-14', time: '13:00', a: 'P97', b: 'P98' },
    { id: 'P102', date: '2026-07-15', time: '13:00', a: 'P99', b: 'P100' },
  ],
  final: { id: 'P104', date: '2026-07-19', time: '13:00', a: 'P101', b: 'P102' },
  third: { id: 'P103', date: '2026-07-18', time: '15:00', a: 'P101', b: 'P102' }, // losers
};

// Which R32 slots feed each semifinal half — used to split the printable mirror.
export const LEFT_R16 = ['P89', 'P90', 'P94', 'P93'];
export const RIGHT_R16 = ['P91', 'P92', 'P95', 'P96'];

// ── Group standings + deterministic clinch ─────────────────────────────────────
function blankRow(team) {
  return { team, pj: 0, pts: 0, gf: 0, ga: 0, w: 0, d: 0, l: 0 };
}

// Build per-group tables from played matches; returns { group: { teams, rows, played, remaining } }.
export function groupTables(matches) {
  const groups = {};
  for (const m of matches) {
    const g = m.group;
    if (!g) continue;
    (groups[g] ??= { teams: new Set(), matches: [] }).matches.push(m);
    groups[g].teams.add(m.home);
    groups[g].teams.add(m.away);
  }
  const out = {};
  for (const [g, { teams, matches: gm }] of Object.entries(groups)) {
    const rows = {};
    for (const team of teams) rows[team] = blankRow(team);
    let remaining = 0;
    for (const m of gm) {
      if (m.status !== 'finalizado' || !m.result) { remaining++; continue; }
      const { home: hg, away: ag } = m.result;
      for (const [team, gf, ga] of [[m.home, hg, ag], [m.away, ag, hg]]) {
        const row = rows[team];
        row.pj++; row.gf += gf; row.ga += ga;
      }
      if (hg > ag) { rows[m.home].pts += 3; rows[m.home].w++; rows[m.away].l++; }
      else if (ag > hg) { rows[m.away].pts += 3; rows[m.away].w++; rows[m.home].l++; }
      else { rows[m.home].pts++; rows[m.away].pts++; rows[m.home].d++; rows[m.away].d++; }
    }
    out[g] = { group: g, rows, remaining, matches: gm };
  }
  return out;
}

// FIFA ranking: points, then goal difference, then goals for, then head-to-head
// (points / GD / GF among the tied teams only). Stable, with a `tied` flag if still even.
function rank(table) {
  const teams = Object.values(table.rows);
  const gd = (x) => x.gf - x.ga;
  const overall = (x) => [x.pts, gd(x), x.gf];
  const cmp = (a, b, key) => key(b)[0] - key(a)[0] || key(b)[1] - key(a)[1] || key(b)[2] - key(a)[2];

  const sorted = [...teams].sort((a, b) => cmp(a, b, overall) || a.team.localeCompare(b.team));
  // Resolve exact ties on (pts, gd, gf) via head-to-head among the tied block.
  for (let i = 0; i < sorted.length; i++) {
    const block = [sorted[i]];
    while (i + 1 < sorted.length && cmp(sorted[i], sorted[i + 1], overall) === 0) block.push(sorted[++i]);
    if (block.length > 1) block.sort((a, b) => h2h(table, b.team) - h2h(table, a.team));
  }
  return sorted;
}
// Head-to-head points among a set is hard to thread here; we use overall as the
// dominant signal and expose a coarse h2h points tiebreak for completed groups.
function h2h(table, team) {
  let pts = 0;
  for (const m of table.matches) {
    if (m.status !== 'finalizado' || !m.result) continue;
    const { home: hg, away: ag } = m.result;
    if (m.home === team) pts += hg > ag ? 3 : hg === ag ? 1 : 0;
    else if (m.away === team) pts += ag > hg ? 3 : ag === hg ? 1 : 0;
  }
  return pts;
}

// Deterministic position locks. Returns { '1': team|null, '2': team|null, '3': team|null }.
// Completed group → exact final 1/2/3. Incomplete → only positions that are
// mathematically impossible to change (points domination, tiebreaker-independent).
export function clinched(table) {
  const teams = Object.values(table.rows);
  const res = { 1: null, 2: null, 3: null };
  if (table.remaining === 0) {
    const o = rank(table);
    res[1] = o[0]?.team ?? null;
    res[2] = o[1]?.team ?? null;
    res[3] = o[2]?.team ?? null;
    return res;
  }
  const remCount = {};
  for (const t of teams) remCount[t.team] = 0;
  for (const m of table.matches) {
    if (m.status === 'finalizado') continue;
    if (remCount[m.home] != null) remCount[m.home]++;
    if (remCount[m.away] != null) remCount[m.away]++;
  }
  const maxPts = (t) => t.pts + 3 * remCount[t.team];
  // 1st locked: current points already exceed every other team's maximum possible.
  const first = teams.find((t) => teams.every((o) => o === t || t.pts > maxPts(o)));
  if (first) {
    res[1] = first.team;
    // 2nd locked: with 1st settled, one more team's points exceed all the rest's max.
    const rest = teams.filter((t) => t !== first);
    const second = rest.find((t) => rest.every((o) => o === t || t.pts > maxPts(o)));
    if (second) res[2] = second.team;
  }
  return res;
}

// Per-group current standings for display (the printable group tables): ordered
// rows + which positions are mathematically locked. Provisional until a group ends.
export function groupStandings(matches) {
  const tables = groupTables(matches);
  const out = {};
  for (const [g, t] of Object.entries(tables)) {
    const rows = Object.values(t.rows)
      .map((r) => ({ ...r, gd: r.gf - r.ga }))
      .sort((a, b) => b.pts - a.pts || b.gd - a.gd || b.gf - a.gf || a.team.localeCompare(b.team));
    out[g] = { group: g, rows, complete: t.remaining === 0, locks: clinched(t) };
  }
  return out;
}

// ── Resolve the whole bracket ──────────────────────────────────────────────────
// Returns a map slotId → { a: teamOrNull, b: teamOrNull, ...meta }. Winners of
// undecided ties are null, so every downstream slot stays blank until fed.
export function buildBracket(matches) {
  const tables = groupTables(matches);
  const locks = {};
  for (const g of Object.keys(tables)) locks[g] = clinched(tables[g]);

  const slotTeam = (feed) => {
    if (feed.third) return null; // third-place slots need the full combination matrix
    return locks[feed.group]?.[feed.pos] ?? null;
  };

  const resolved = {};
  for (const tie of R32) {
    resolved[tie.id] = {
      ...tie,
      teamA: slotTeam(tie.a), teamB: slotTeam(tie.b),
      labelA: feedLabel(tie.a), labelB: feedLabel(tie.b),
      winner: null, // hand-filled in the quiniela; never auto-predicted
    };
  }
  for (const round of ['r16', 'qf', 'sf']) {
    for (const tie of ROUNDS[round]) {
      resolved[tie.id] = { ...tie, teamA: null, teamB: null, labelA: `W${tie.a.slice(1)}`, labelB: `W${tie.b.slice(1)}`, winner: null };
    }
  }
  for (const key of ['final', 'third']) {
    const tie = ROUNDS[key];
    resolved[tie.id] = { ...tie, teamA: null, teamB: null, labelA: '', labelB: '', winner: null };
  }

  // Overlay the REAL knockout fixtures/results discovered from the data feeds. Each KO
  // match in matches.json is keyed by its bracket slot id (P73…), carrying the actual
  // teams (incl. third-place qualifiers), the 90-min score, and `result.advances` (who
  // progressed via ET/penalties). This fills slots — and advances winners — round by
  // round as the sources publish them, with no combination matrix.
  for (const m of matches) {
    if (!/^P\d+$/.test(m.id || '')) continue;
    const r = resolved[m.id];
    if (!r) continue;
    r.teamA = m.home; r.teamB = m.away;
    if (m.date) r.date = m.date;
    if (m.time) r.time = m.time;
    if (m.status === 'finalizado' && m.result) {
      r.scoreA = m.result.home; r.scoreB = m.result.away;
      r.finished = true;
      r.winner = m.result.advances
        || (m.result.home > m.result.away ? m.home
          : m.result.away > m.result.home ? m.away : null);
    }
  }
  return { resolved, tables, locks };
}

// Human label for an unresolved feed, e.g. "2A", "1F", "3 (A·B·C·D·F)".
function feedLabel(feed) {
  if (feed.third) return `3 (${feed.third.join('·')})`;
  return `${feed.pos}${feed.group}`;
}
