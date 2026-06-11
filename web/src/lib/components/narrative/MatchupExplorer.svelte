<script>
  // Act 2 sandbox: pick any fixture and see the three models side by side — where they
  // agree, where they differ, and the expected goals (λ) the net assigns.
  import { teamShort } from '$lib/teams.js';
  let { matches } = $props();

  const opts = $derived(matches.filter((m) => m.predictions.M2));
  let idx = $state(0);
  const m = $derived(opts[idx]);

  const COL = { M1: '#64748b', M2: '#3b82f6', M3: '#22c55e', Mercado: '#94a3b8' };
  const lines = [['M1', 'Azar'], ['M2', 'Red Neuronal'], ['M3', 'IA con Criterio'], ['Mercado', 'Mercado']];
  const pickName = (mm, p) => (!p ? '—' : p.pick === 'draw' ? 'Empate' : teamShort(p.pick === 'home' ? mm.home : mm.away));
  const setLabel = (mm) => {
    const s = mm.predictions.M3?.set;
    if (!s) return '';
    if (s.length === 3) return 'cualquier resultado';
    const n = (o) => (o === 'home' ? teamShort(mm.home) : o === 'away' ? teamShort(mm.away) : 'Empate');
    return s.map(n).join(' o ');
  };
</script>

<div class="explorer">
  <select bind:value={idx} aria-label="Elegir partido">
    {#each opts as o, i}<option value={i}>{teamShort(o.home)} vs {teamShort(o.away)}</option>{/each}
  </select>

  <div class="lines">
    {#each lines as [k, name]}
      {@const p = m.predictions[k]}
      <div class="line" style="--c:{COL[k]}">
        <span class="lk">{k}</span>
        <span class="ln">{name}</span>
        <span class="lpick">{pickName(m, p)}</span>
        <span class="lprob">{p?.probs ? Math.round(p.probs[p.pick] * 100) + '%' : '—'}</span>
      </div>
    {/each}
  </div>

  {#if m.predictions.M2?.lambda}
    <p class="xg">Goles esperados (red): {teamShort(m.home)} {m.predictions.M2.lambda.home} · {teamShort(m.away)} {m.predictions.M2.lambda.away}</p>
  {/if}
  {#if m.predictions.M3?.set}
    <p class="conf">M3 descarta lo improbable — 80%: <b>{setLabel(m)}</b></p>
  {/if}
</div>

<style>
  .explorer { width: 100%; max-width: 460px; margin: 0 auto; }
  select { width: 100%; background: #0f172a; color: #e2e8f0; border: 1px solid #1e293b; border-radius: 6px; padding: 0.4rem 0.5rem; font-family: inherit; font-size: 0.85rem; margin-bottom: 0.7rem; }
  .lines { display: flex; flex-direction: column; gap: 0.4rem; }
  .line { display: grid; grid-template-columns: 2.2rem 1fr auto 2.6rem; align-items: center; gap: 0.5rem; background: #0f172a; border-left: 3px solid var(--c); border-radius: 4px; padding: 0.4rem 0.6rem; font-size: 0.85rem; }
  .lk { color: var(--c); font-weight: 700; font-size: 0.72rem; }
  .ln { color: #94a3b8; }
  .lpick { color: #e2e8f0; font-weight: 600; text-align: right; }
  .lprob { color: #94a3b8; text-align: right; font-variant-numeric: tabular-nums; }
  .xg { text-align: center; color: #94a3b8; font-size: 0.82rem; margin: 0.8rem 0 0.3rem; }
  .conf { text-align: center; color: #22c55e; font-size: 0.85rem; margin: 0.2rem 0 0; }
  .conf b { color: #e2e8f0; }
</style>
