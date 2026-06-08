<script>
  import MatchRow from '$lib/components/MatchRow.svelte';
  import Scoreboard from '$lib/components/Scoreboard.svelte';
  import Cards from '$lib/components/Cards.svelte';
  import { groupByDate, fmtDay } from '$lib/calendar.js';

  let { data } = $props();
  const { matches, meta } = data;
  const days = groupByDate(matches);
</script>

<svelte:head>
  <title>Copa Mundial 2026 — Contexto</title>
</svelte:head>

<main>
  <h1>Contexto — Calendario y Predicciones</h1>
  <p class="sub">
    Copa Mundial de la FIFA 2026 · {meta.count} partidos de fase de grupos
    <br />
    <span class="leg"><b style="color:#64748b">M1</b> Azar</span>
    <span class="leg"><b style="color:#3b82f6">M2</b> Red Neuronal</span>
    <span class="leg"><b style="color:#22c55e">M3</b> Conjunto</span>
    <span class="leg"><b style="color:#94a3b8">Mercado</b></span>
  </p>

  <Scoreboard {matches} />
  <Cards {matches} />

  <section class="calendar">
    <h2 class="section-title">Calendario completo</h2>
    {#each days as [date, dayMatches]}
      <h3 class="day">{fmtDay(date)}</h3>
      {#each dayMatches as m (m.id)}
        <MatchRow match={m} />
      {/each}
    {/each}
  </section>
</main>

<style>
  :global(body) {
    margin: 0;
    background: #0a0e17;
    color: #e2e8f0;
    font-family: 'Segoe UI', system-ui, sans-serif;
    line-height: 1.5;
  }
  main { max-width: 760px; margin: 0 auto; padding: 1.5rem 1rem 4rem; }
  h1 { color: #d4af37; font-size: 1.6rem; margin: 0 0 0.25rem; }
  .sub { color: #64748b; font-size: 0.8rem; margin: 0 0 1.25rem; }
  .leg { margin-right: 0.7rem; white-space: nowrap; }
  .section-title { color: #3b82f6; font-size: 1.1rem; border-bottom: 2px solid #1e293b; padding-bottom: 0.4rem; margin: 0 0 0.5rem; }
  .day {
    position: sticky;
    top: 0;
    background: #0a0e17;
    color: #94a3b8;
    font-size: 0.85rem;
    padding: 0.5rem 0 0.3rem;
    margin: 1.2rem 0 0.2rem;
    border-bottom: 1px solid #1e293b;
    z-index: 1;
  }
</style>
