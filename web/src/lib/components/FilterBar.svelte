<script>
  let { group = $bindable('Todos'), query = $bindable(''), groups } = $props();
  const chips = ['Todos', ...groups];
</script>

<div class="bar">
  <div class="chips">
    {#each chips as g}
      <button class="chip" class:active={group === g} onclick={() => (group = g)}>
        {g === 'Todos' ? 'Todos' : g}
      </button>
    {/each}
  </div>
  <input class="search" type="search" placeholder="Buscar selección…" bind:value={query} />
</div>

<style>
  .bar {
    display: flex;
    gap: 0.6rem;
    align-items: center;
    flex-wrap: wrap;
    margin: 0 0 0.6rem;
  }
  .chips { display: flex; gap: 0.25rem; flex-wrap: wrap; }
  .chip {
    background: #0f172a;
    border: 1px solid #1e293b;
    color: #94a3b8;
    border-radius: 999px;
    padding: 0.2rem 0.6rem;
    font-size: 0.78rem;
    cursor: pointer;
    font-weight: 600;
    min-width: 1.9rem;
  }
  .chip:hover { border-color: #334155; color: #e2e8f0; }
  .chip.active { background: #3b82f6; border-color: #3b82f6; color: #fff; }
  .search {
    flex: 1 1 160px;
    background: #0f172a;
    border: 1px solid #1e293b;
    color: #e2e8f0;
    border-radius: 6px;
    padding: 0.3rem 0.6rem;
    font-size: 0.82rem;
    min-width: 140px;
  }
  .search::placeholder { color: #475569; }
</style>
