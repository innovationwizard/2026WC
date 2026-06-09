<script>
  // "Ver la mate que hay detrás" — collapsed chevron → text-only math card.
  // Casual viewers skip it; the technical crowd taps. Content passed as children.
  let { children } = $props();
  let open = $state(false);
</script>

<div class="pill-wrap">
  <button class="pill" class:open onclick={() => (open = !open)} aria-expanded={open}>
    <span class="chev" aria-hidden="true">▸</span> Ver la mate que hay detrás
  </button>
  {#if open}
    <div class="card">{@render children()}</div>
  {/if}
</div>

<style>
  .pill-wrap { margin: 1.75rem auto 0; max-width: 640px; text-align: center; }
  .pill {
    display: inline-flex; align-items: center; gap: 0.5rem;
    background: #0f172a; border: 1px solid #1e293b; color: #94a3b8;
    font-size: 0.85rem; padding: 0.5rem 1rem; border-radius: 999px;
    cursor: pointer; font-family: inherit;
  }
  .pill:hover { border-color: #334155; color: #cbd5e1; }
  .chev { display: inline-block; transition: transform 0.2s; }
  .pill.open .chev { transform: rotate(90deg); }
  .card {
    margin-top: 0.7rem; text-align: left;
    background: #0b1220; border: 1px solid #1e293b; border-left: 3px solid #d4af37;
    border-radius: 8px; padding: 1rem 1.15rem;
    font-size: 0.88rem; line-height: 1.65; color: #cbd5e1;
  }
  .card :global(b) { color: #e2e8f0; }
  .card :global(.f) { font-family: 'Cambria Math', Georgia, serif; font-style: italic; color: #e8eefc; white-space: nowrap; }
  .card :global(p) { margin: 0; }
</style>
