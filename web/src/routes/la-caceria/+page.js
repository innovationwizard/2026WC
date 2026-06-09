// The Hunt — renders THE_JOURNEY.md (converted to an HTML fragment at build time).
export async function load({ fetch }) {
  const html = await fetch('/the-journey.html').then((r) => r.text());
  return { html };
}
