// El veredicto — reads the same real baked data as the rest of the site (matches.json).
// The whole final scoreboard is computed client-side from it (grade.js), so nothing is
// hand-entered here. ROI figures are the tournament-complete backtest_edge.py output.
export async function load({ fetch }) {
  const m = await fetch('/data/matches.json').then((r) => r.json());
  return { matches: m.matches, knockout: m.knockout };
}
