// Load the static match + standings data at prerender time.
export async function load({ fetch }) {
  const res = await fetch('/data/matches.json');
  const j = await res.json();
  return { matches: j.matches, meta: j.meta, groups: j.groups, knockout: j.knockout };
}
