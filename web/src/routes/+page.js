// Load the static match data at prerender time.
export async function load({ fetch }) {
  const res = await fetch('/data/matches.json');
  const j = await res.json();
  return { matches: j.matches, teams: j.teams, meta: j.meta };
}
