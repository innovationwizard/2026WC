// Narrative reads the same real model output as the Context page, plus the
// held-out validation artifacts (RPS + calibration) in narrative.json.
export async function load({ fetch }) {
  const [m, n] = await Promise.all([
    fetch('/data/matches.json').then((r) => r.json()),
    fetch('/data/narrative.json').then((r) => r.json()),
  ]);
  return { knockout: m.knockout, matches: m.matches, narrative: n };
}
