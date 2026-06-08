<script>
  import MatchRow from './MatchRow.svelte';
  import { recientesDate, proximosDate, matchesOn, fmtDay } from '$lib/calendar.js';

  let { matches } = $props();
  const rDate = recientesDate(matches);
  const pDate = proximosDate(matches);
  const recientes = matchesOn(matches, rDate);
  const proximos = matchesOn(matches, pDate);
</script>

<div class="cards">
  <section class="card">
    <h3>Recientes {#if rDate}<span class="d">· {fmtDay(rDate)}</span>{/if}</h3>
    {#if recientes.length}
      {#each recientes as m (m.id)}<MatchRow match={m} />{/each}
    {:else}
      <p class="empty">Aún no hay partidos jugados.</p>
    {/if}
  </section>

  <section class="card">
    <h3>Próximos {#if pDate}<span class="d">· {fmtDay(pDate)}</span>{/if}</h3>
    {#if proximos.length}
      {#each proximos as m (m.id)}<MatchRow match={m} />{/each}
    {:else}
      <p class="empty">Sin próximos partidos.</p>
    {/if}
  </section>
</div>

<style>
  .cards { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin: 0 0 1.5rem; }
  .card { background: #0d1320; border: 1px solid #1e293b; border-radius: 8px; padding: 0.75rem 0.85rem; }
  h3 { font-size: 0.9rem; color: #94a3b8; margin: 0 0 0.5rem; }
  .d { color: #64748b; font-weight: 400; text-transform: capitalize; }
  .empty { color: #64748b; font-size: 0.78rem; }
  @media (max-width: 640px) {
    .cards { grid-template-columns: 1fr; }
  }
</style>
