<script>
  // "La cacería" — the bug-hunt story (THE_JOURNEY.md). UNLISTED: no link points here.
  let { data } = $props();
</script>

<svelte:head>
  <title>La cacería · Mundial 2026</title>
  <meta name="robots" content="noindex" />
</svelte:head>

<article class="journey">
  {@html data.html}
</article>

<style>
  :global(body) { margin: 0; background: #0a0e17; }
  .journey {
    color: #cbd5e1; font-family: Georgia, 'Times New Roman', serif;
    max-width: 720px; margin: 0 auto; padding: 4rem 1.5rem 6rem; line-height: 1.75;
  }
  .journey :global(h1) { color: #d4af37; font-size: clamp(2rem, 6vw, 3rem); line-height: 1.1; margin: 0 0 1.5rem; font-family: 'Segoe UI', system-ui, sans-serif; }
  .journey :global(h2) { color: #e2e8f0; font-size: 1.5rem; margin: 3rem 0 0.75rem; padding-top: 1.5rem; border-top: 1px solid #1e293b; font-family: 'Segoe UI', system-ui, sans-serif; }
  .journey :global(p) { margin: 0 0 1.1rem; }
  .journey :global(strong) { color: #e2e8f0; }
  .journey :global(em) { color: #cbd5e1; }
  .journey :global(a) { color: #3b82f6; }
  .journey :global(hr) { border: none; border-top: 1px solid #1e293b; margin: 2rem 0; }
  .journey :global(blockquote) { margin: 1.5rem 0; padding: 0.75rem 1.25rem; border-left: 3px solid #d4af37; background: #0d1424; color: #e2e8f0; border-radius: 0 6px 6px 0; }
  .journey :global(code) { font-family: 'SF Mono', Menlo, monospace; font-size: 0.85em; background: #0f172a; color: #93c5fd; padding: 0.1em 0.35em; border-radius: 4px; }
  .journey :global(ul) { padding-left: 1.25rem; }
  .journey :global(li) { margin: 0.35rem 0; }
  .journey :global(table) { width: 100%; border-collapse: collapse; margin: 1.5rem 0; font-family: 'Segoe UI', system-ui, sans-serif; font-size: 0.9rem; }
  .journey :global(th), .journey :global(td) { border: 1px solid #1e293b; padding: 0.45rem 0.7rem; text-align: left; }
  .journey :global(th) { background: #0f172a; color: #d4af37; }
  .journey :global(td) { color: #cbd5e1; }
</style>
