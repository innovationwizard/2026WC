<script>
  import MatchRow from '$lib/components/MatchRow.svelte';
  import Scoreboard from '$lib/components/Scoreboard.svelte';
  import Cards from '$lib/components/Cards.svelte';
  import FilterBar from '$lib/components/FilterBar.svelte';
  import Grupos from '$lib/components/Grupos.svelte';
  import Llaves from '$lib/components/Llaves.svelte';
  import { groupByDate, fmtDay } from '$lib/calendar.js';
  import { teamFull, teamShort } from '$lib/teams.js';

  let { data } = $props();
  const { matches, meta, groups, knockout } = data;

  let view = $state('lista');

  const groupsList = [...new Set(matches.map((m) => m.group).filter(Boolean))].sort();
  let group = $state('Todos');
  let query = $state('');

  // Filters apply to the calendar list only; scoreboard stays global.
  const filtered = $derived(
    matches.filter((m) => {
      if (group !== 'Todos' && m.group !== group) return false;
      const q = query.trim().toLowerCase();
      if (q) {
        const hay = [teamFull(m.home), teamShort(m.home), m.home, teamFull(m.away), teamShort(m.away), m.away]
          .join(' ').toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    })
  );
  const days = $derived(groupByDate(filtered));
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
    <span class="leg" title="Además de generar pronósticos, emite un juicio crítico acerca de la calidad y de la validez de sus propios pronósticos."><b style="color:#22c55e">M3</b> IA con Criterio</span>
    <span class="leg"><b style="color:#94a3b8">Mercado</b></span>
  </p>

  <a class="story-link" href="/historia">▶ Ver la historia — cómo se construye una predicción, del azar a la red neuronal →</a>

  <Scoreboard {matches} />

  <nav class="tabs">
    <button class:active={view === 'lista'} onclick={() => (view = 'lista')}>Lista</button>
    <button class:active={view === 'grupos'} onclick={() => (view = 'grupos')}>Grupos</button>
    <button class:active={view === 'llaves'} onclick={() => (view = 'llaves')}>Llaves</button>
  </nav>

  {#if view === 'lista'}
    <Cards {matches} />
    <section class="calendar">
      <h2 class="section-title">
        Calendario completo
        {#if filtered.length !== matches.length}<span class="count">· {filtered.length} de {matches.length}</span>{/if}
      </h2>
      <FilterBar bind:group bind:query groups={groupsList} />
      {#if days.length === 0}
        <p class="empty">Sin resultados para este filtro.</p>
      {/if}
      {#each days as [date, dayMatches]}
        <h3 class="day">{fmtDay(date)}</h3>
        {#each dayMatches as m (m.id)}
          <MatchRow match={m} />
        {/each}
      {/each}
    </section>
  {:else if view === 'grupos'}
    <Grupos {groups} />
  {:else}
    <Llaves {knockout} />
  {/if}
</main>

<style>
  :global(body) {
    margin: 0;
    background: #0a0e17;
    color: #e2e8f0;
    font-family: 'Segoe UI', system-ui, sans-serif;
    line-height: 1.5;
  }
  main { max-width: 900px; margin: 0 auto; padding: 1.5rem 1rem 4rem; }
  h1 { color: #d4af37; font-size: 1.6rem; margin: 0 0 0.25rem; }
  .sub { color: #64748b; font-size: 0.8rem; margin: 0 0 1.25rem; }
  .leg { margin-right: 0.7rem; white-space: nowrap; }

  .story-link {
    display: inline-block; margin: 0 0 1.25rem;
    color: #9eff1f; text-decoration: none; font-weight: 600; font-size: 0.9rem;
    border: 1px solid #1e3a1e; background: #0d1f0d; border-radius: 999px; padding: 0.45rem 1rem;
  }
  .story-link:hover { border-color: #9eff1f; }

  .tabs { display: flex; gap: 0.25rem; margin: 0 0 1.25rem; background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 0.25rem; width: fit-content; }
  .tabs button { background: none; border: none; color: #94a3b8; font-weight: 600; font-size: 0.85rem; padding: 0.35rem 0.9rem; border-radius: 6px; cursor: pointer; }
  .tabs button:hover { color: #e2e8f0; }
  .tabs button.active { background: #3b82f6; color: #fff; }

  .section-title { color: #3b82f6; font-size: 1.1rem; border-bottom: 2px solid #1e293b; padding-bottom: 0.4rem; margin: 0 0 0.5rem; }
  .count { color: #64748b; font-size: 0.8rem; font-weight: 400; }
  .empty { color: #64748b; font-size: 0.85rem; padding: 1rem 0; }
  .day {
    position: sticky; top: var(--banner-h); background: #0a0e17; color: #94a3b8;
    font-size: 0.85rem; padding: 0.5rem 0 0.3rem; margin: 1.2rem 0 0.2rem;
    border-bottom: 1px solid #1e293b; z-index: 1;
  }
</style>
