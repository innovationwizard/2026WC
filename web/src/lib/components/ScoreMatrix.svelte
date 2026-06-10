<script>
  // Correct-score distribution for a match: the independent-Poisson outer product of the
  // two λ's (already in matches.json). Hero = heatmap (home rows × away cols, 0–4 + ≥5),
  // summary band = W/D/L + top-4 scores (also the mobile/screen-reader view). M1/M2/M3 tabs.
  import { teamShort } from '$lib/teams.js';
  import { LINE_COLORS, LINE_NAMES } from '$lib/grade.js';

  let { match, active = $bindable('M2') } = $props();

  const MODELS = ['M1', 'M2', 'M3'];
  const MAXG = 5; // cells 0..4, then a "≥5" bucket folds the tail (keeps mass = 1)

  function poisVec(l) {
    const v = []; let term = Math.exp(-l), acc = 0;
    for (let k = 0; k < MAXG; k++) { v.push(term); acc += term; term = (term * l) / (k + 1); }
    v.push(Math.max(0, 1 - acc));
    return v;
  }

  const pred = $derived(match.predictions[active]);
  const lh = $derived(pred?.lambda?.home ?? 0);
  const la = $derived(pred?.lambda?.away ?? 0);
  const matrix = $derived(poisVec(lh).map((ph) => poisVec(la).map((pa) => ph * pa)));
  const maxCell = $derived(Math.max(0.0001, ...matrix.flat()));
  const modal = $derived.by(() => {
    let mi = 0, mj = 0, m = -1;
    matrix.forEach((row, i) => row.forEach((p, j) => { if (p > m) { m = p; mi = i; mj = j; } }));
    return `${mi}-${mj}`;
  });
  const wdl = $derived.by(() => {
    let w = 0, d = 0, l = 0;
    matrix.forEach((row, i) => row.forEach((p, j) => { if (i > j) w += p; else if (i === j) d += p; else l += p; }));
    return { w, d, l };
  });
  const top = $derived.by(() => {
    const c = [];
    matrix.forEach((row, i) => row.forEach((p, j) => c.push([p, i, j])));
    return c.sort((a, b) => b[0] - a[0]).slice(0, 4);
  });

  const lbl = (i) => (i < MAXG ? String(i) : `≥${MAXG}`);
  const score = (i, j) => `${lbl(i)}-${lbl(j)}`;
  const setLabel = (s) => {
    if (!s) return '';
    if (s.length === 3) return 'cualquier resultado';
    const n = (o) => (o === 'home' ? teamShort(match.home) : o === 'away' ? teamShort(match.away) : 'Empate');
    return s.map(n).join(' o ');
  };
</script>

<div class="sm" style="--c:{LINE_COLORS[active]}">
  <div class="tabs">
    {#each MODELS as m}
      <button class:on={active === m} style="--mc:{LINE_COLORS[m]}" onclick={() => (active = m)}>{m}</button>
    {/each}
    <span class="tname">{LINE_NAMES[active]}</span>
  </div>

  <p class="orient">Probabilidad de cada marcador exacto · <b>{teamShort(match.home)} ↓</b> contra <b>{teamShort(match.away)} →</b></p>

  <div class="grid-wrap">
    <table class="grid">
      <tbody>
        <tr><td class="corner"></td>{#each Array(MAXG + 1) as _, j}<th class="gh">{lbl(j)}</th>{/each}</tr>
        {#each matrix as row, i}
          <tr>
            <th class="gh">{lbl(i)}</th>
            {#each row as p, j}
              <td class:mode={`${i}-${j}` === modal}
                  style="background:color-mix(in srgb, var(--c) {Math.round((p / maxCell) * 88)}%, #0b1220)"
                  title="{score(i, j)} · {(p * 100).toFixed(1)}%"
                  aria-label="{teamShort(match.home)} {lbl(i)}, {teamShort(match.away)} {lbl(j)}: {(p * 100).toFixed(1)}%">
                {p >= 0.005 ? Math.round(p * 100) : ''}
              </td>
            {/each}
          </tr>
        {/each}
      </tbody>
    </table>
  </div>

  <div class="band">
    <div class="wdl">Local <b>{Math.round(wdl.w * 100)}%</b> · Empate <b>{Math.round(wdl.d * 100)}%</b> · Visitante <b>{Math.round(wdl.l * 100)}%</b></div>
    <div class="tops">Más probables: {#each top as [p, i, j], k}<span class="ts">{score(i, j)} {Math.round(p * 100)}%</span>{#if k < top.length - 1}<i> · </i>{/if}{/each}</div>
    {#if active === 'M3' && pred?.set}
      <div class="conf">{Math.round((pred.coverage ?? 0.8) * 100)}% de confianza: <b>{setLabel(pred.set)}</b></div>
    {/if}
  </div>

  <p class="foot">Poisson independiente. Probamos la dependencia de marcadores bajos (Dixon-Coles): ρ̂ = −0,06, no significativa (p = 0,15).</p>
</div>

<style>
  .sm { background: #0b1220; border: 1px solid #1e293b; border-radius: 8px; padding: 0.7rem 0.8rem; }
  .tabs { display: flex; align-items: center; gap: 0.35rem; margin-bottom: 0.5rem; }
  .tabs button { background: #0f172a; border: 1px solid #1e293b; color: #94a3b8; font: 700 0.72rem/1 inherit; padding: 0.25rem 0.6rem; border-radius: 999px; cursor: pointer; }
  .tabs button.on { color: #fff; border-color: var(--mc); background: color-mix(in srgb, var(--mc) 25%, #0f172a); }
  .tname { color: #94a3b8; font-size: 0.75rem; margin-left: 0.25rem; }
  .orient { color: #94a3b8; font-size: 0.72rem; margin: 0 0 0.5rem; }
  .orient b { color: #cbd5e1; }

  .grid-wrap { overflow-x: auto; }
  .grid { border-collapse: collapse; font-variant-numeric: tabular-nums; }
  .grid th, .grid td { width: 2rem; height: 1.55rem; text-align: center; font-size: 0.72rem; }
  .gh { color: #64748b; font-weight: 700; }
  .corner { width: 2rem; }
  .grid td { color: #e2e8f0; border: 1px solid #0a0e17; border-radius: 2px; }
  .grid td.mode { outline: 2px solid var(--c); outline-offset: -2px; font-weight: 800; }

  .band { margin-top: 0.6rem; font-size: 0.8rem; color: #cbd5e1; display: grid; gap: 0.25rem; }
  .wdl b { color: #e2e8f0; }
  .tops { color: #94a3b8; }
  .tops .ts { color: #cbd5e1; }
  .tops i { color: #475569; font-style: normal; }
  .conf { color: #22c55e; }
  .conf b { color: #e2e8f0; }
  .foot { color: #475569; font-size: 0.68rem; margin: 0.6rem 0 0; line-height: 1.4; }

  /* Phones: drop the grid, keep the band (W/D/L + top scores) as the distribution view. */
  @media (max-width: 460px) {
    .grid-wrap, .orient { display: none; }
  }
</style>
