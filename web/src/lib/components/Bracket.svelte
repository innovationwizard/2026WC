<script>
  import { tick } from 'svelte';
  import { teamShort, teamFlag, teamFull, teamCode } from '$lib/teams.js';
  import { buildBracket, groupStandings, R32, ROUNDS } from '$lib/bracket.js';

  let { matches } = $props();
  const { resolved } = buildBracket(matches);
  const GS = groupStandings(matches);
  const S = (id) => resolved[id];

  const fmtDate = (iso) => {
    const [, mo, d] = iso.split('-');
    return `${+d}/${+mo}`;
  };

  // Screen (vertical): every round in left-to-right columns, all 16 R32 ties stacked.
  const COLS = [
    { key: 'r32', label: 'Dieciseisavos', ids: R32.map((t) => t.id) },
    { key: 'r16', label: 'Octavos', ids: ROUNDS.r16.map((t) => t.id) },
    { key: 'qf', label: 'Cuartos', ids: ROUNDS.qf.map((t) => t.id) },
    { key: 'sf', label: 'Semifinales', ids: ROUNDS.sf.map((t) => t.id) },
    { key: 'f', label: 'Final', ids: [ROUNDS.final.id] },
  ];

  // Print (horizontal mirror): left half flows right to the final, right half flows left.
  const L = {
    r32: ['P74', 'P77', 'P73', 'P75', 'P83', 'P84', 'P81', 'P82'],
    r16: ['P89', 'P90', 'P93', 'P94'], qf: ['P97', 'P98'], sf: ['P101'],
  };
  const R = {
    r32: ['P76', 'P78', 'P79', 'P80', 'P86', 'P88', 'P85', 'P87'],
    r16: ['P91', 'P92', 'P95', 'P96'], qf: ['P99', 'P100'], sf: ['P102'],
  };

  // Two print modes share one window.print(); a class flag picks which sheet shows.
  let mode = $state('plain');
  const printSheet = async (m) => { mode = m; await tick(); window.print(); };

  // Move both print sheets to direct children of <body> so we can display:none the
  // rest of the page when printing (removes it from flow → no trailing blank pages).
  function portal(node) {
    document.body.appendChild(node);
    return { destroy() { node.remove(); } };
  }
</script>

<!-- Reusable team slot: a locked team, or a blank placeholder (flag box + underline). -->
{#snippet teamSlot(team, label, align)}
  <div class="slot {align}" class:filled={!!team}>
    {#if team}
      <span class="flag" title={teamFull(team)}>{teamFlag(team)}</span>
      <span class="nm">{teamShort(team)}</span>
    {:else}
      <span class="flag box" aria-hidden="true"></span>
      <span class="nm line"><span class="hint">{label}</span></span>
    {/if}
  </div>
{/snippet}

{#snippet tie(id, align = 'l')}
  {@const s = S(id)}
  <div class="tie" class:done={s.teamA && s.teamB}>
    {#if s.date}<span class="when">{fmtDate(s.date)} · {s.time}</span>{/if}
    {@render teamSlot(s.teamA, s.labelA, align)}
    {@render teamSlot(s.teamB, s.labelB, align)}
  </div>
{/snippet}

<!-- Compact group table (Pos · flag · code · Pts), one referenced group. `hi` = the
     slot's position (1 or 2) emphasized so the reader sees that pair's candidate. -->
{#snippet groupMini(g, hi)}
  {@const gs = GS[g]}
  <table class="gt">
    <caption>Grupo {g}</caption>
    <tbody>
      {#each gs.rows as r, i}
        <tr class="p{i + 1}" class:hi={i + 1 === hi}>
          <td class="pos">{i + 1}</td>
          <td class="fl">{teamFlag(r.team)}</td>
          <td class="cd">{teamCode(r.team)}</td>
          <td class="pt">{r.pts}</td>
        </tr>
      {/each}
    </tbody>
  </table>
{/snippet}

<!-- Third-place slot: the current 3rd-placed team of each group in the combo. -->
{#snippet thirdsList(combo)}
  <table class="gt thirds">
    <caption>3.º de {combo.join('·')}</caption>
    <tbody>
      {#each combo as g}
        {@const r = GS[g].rows[2]}
        <tr class="p3">
          <td class="pos">{g}</td>
          <td class="fl">{teamFlag(r.team)}</td>
          <td class="cd">{teamCode(r.team)}</td>
          <td class="pt">{r.pts}</td>
        </tr>
      {/each}
    </tbody>
  </table>
{/snippet}

{#snippet annot(feed)}
  {#if feed.third}{@render thirdsList(feed.third)}{:else}{@render groupMini(feed.group, feed.pos)}{/if}
{/snippet}

<!-- R32 tie WITH its group tables attached (for the "con grupos" sheet). -->
{#snippet gtie(id, align)}
  {@const s = S(id)}
  <div class="gtie" class:l={align === 'l'} class:r={align === 'r'}>
    <div class="tie" class:done={s.teamA && s.teamB}>
      {#if s.date}<span class="when">{fmtDate(s.date)} · {s.time}</span>{/if}
      {@render teamSlot(s.teamA, s.labelA, align)}
      {@render teamSlot(s.teamB, s.labelB, align)}
    </div>
    <div class="gtables">
      {@render annot(s.a)}
      {@render annot(s.b)}
    </div>
  </div>
{/snippet}

<!-- ════════ Toolbar ════════ -->
<div class="bar">
  <p class="lead">
    Cuadro determinista: una selección aparece solo cuando tiene <b>asegurada</b> esa
    posición exacta; lo demás queda en blanco para llenar a mano.
  </p>
  <div class="btns">
    <button class="export" onclick={() => printSheet('plain')}>🖨️ Imprimir</button>
    <button class="export" onclick={() => printSheet('groups')}>🖨️ Imprimir con grupos</button>
  </div>
</div>

<!-- ════════ Screen: vertical bracket, all ties from the left ════════ -->
<div class="screen">
  <div class="grid">
    {#each COLS as col}
      <div class="col">
        <h4>{col.label}</h4>
        <div class="ties">
          {#each col.ids as id}{@render tie(id, 'l')}{/each}
        </div>
      </div>
    {/each}
  </div>
</div>

<!-- ════════ Print sheet A: plain mirrored bracket (letter landscape) ════════ -->
<div class="print-sheet plain" class:active={mode === 'plain'} use:portal>
  <h1 class="title">QUINIELA GRUPO ORIÓN</h1>
  <div class="mirror">
    <div class="half">
      <div class="pcol">{#each L.r32 as id}{@render tie(id, 'l')}{/each}</div>
      <div class="pcol">{#each L.r16 as id}{@render tie(id, 'l')}{/each}</div>
      <div class="pcol">{#each L.qf as id}{@render tie(id, 'l')}{/each}</div>
      <div class="pcol">{#each L.sf as id}{@render tie(id, 'l')}{/each}</div>
    </div>
    <div class="center">
      <span class="clabel">FINAL</span>
      {@render tie(ROUNDS.final.id, 'c')}
      <span class="clabel third">3.º puesto</span>
      {@render tie(ROUNDS.third.id, 'c')}
    </div>
    <div class="half right">
      <div class="pcol">{#each R.sf as id}{@render tie(id, 'r')}{/each}</div>
      <div class="pcol">{#each R.qf as id}{@render tie(id, 'r')}{/each}</div>
      <div class="pcol">{#each R.r16 as id}{@render tie(id, 'r')}{/each}</div>
      <div class="pcol">{#each R.r32 as id}{@render tie(id, 'r')}{/each}</div>
    </div>
  </div>
  <p class="foot">Copa Mundial de la FIFA 2026 · puedelaiaganarquinielas.com</p>
</div>

<!-- ════════ Print sheet B: with group tables next to each dieciseisavos (8.5×13) ════════ -->
<div class="print-sheet groups" class:active={mode === 'groups'} use:portal>
  <h1 class="title">QUINIELA GRUPO ORIÓN</h1>
  <div class="mirror">
    <div class="half">
      <div class="pcol gcol">{#each L.r32 as id}{@render gtie(id, 'l')}{/each}</div>
      <div class="pcol">{#each L.r16 as id}{@render tie(id, 'l')}{/each}</div>
      <div class="pcol">{#each L.qf as id}{@render tie(id, 'l')}{/each}</div>
      <div class="pcol">{#each L.sf as id}{@render tie(id, 'l')}{/each}</div>
    </div>
    <div class="center">
      <span class="clabel">FINAL</span>
      {@render tie(ROUNDS.final.id, 'c')}
      <span class="clabel third">3.º puesto</span>
      {@render tie(ROUNDS.third.id, 'c')}
    </div>
    <div class="half right">
      <div class="pcol">{#each R.sf as id}{@render tie(id, 'r')}{/each}</div>
      <div class="pcol">{#each R.qf as id}{@render tie(id, 'r')}{/each}</div>
      <div class="pcol">{#each R.r16 as id}{@render tie(id, 'r')}{/each}</div>
      <div class="pcol gcol">{#each R.r32 as id}{@render gtie(id, 'r')}{/each}</div>
    </div>
  </div>
  <p class="foot">Tablas de grupos provisionales · Copa Mundial de la FIFA 2026 · puedelaiaganarquinielas.com</p>
</div>

<style>
  .bar { display: flex; justify-content: space-between; align-items: center; gap: 1rem; flex-wrap: wrap; margin: 0 0 1rem; }
  .lead { color: #94a3b8; font-size: 0.8rem; margin: 0; max-width: 42ch; }
  .lead b { color: #e2e8f0; }
  .btns { display: flex; gap: 0.5rem; flex-wrap: wrap; }
  .export {
    background: #001f54; color: #fff; border: 1px solid #1d3a6e; border-radius: 6px;
    padding: 0.5rem 0.9rem; font: inherit; font-weight: 600; font-size: 0.85rem; cursor: pointer; white-space: nowrap;
  }
  .export:hover { background: #062a6b; }

  /* ── Screen vertical bracket ── */
  .screen { overflow-x: auto; padding-bottom: 0.5rem; }
  .grid { display: flex; gap: 1.1rem; min-width: max-content; }
  .col { display: flex; flex-direction: column; }
  .col h4 { color: #64748b; font-size: 0.64rem; text-transform: uppercase; letter-spacing: 0.05em; margin: 0 0 0.5rem; text-align: center; }
  .ties { display: flex; flex-direction: column; justify-content: space-around; flex: 1; gap: 0.45rem; }

  .tie {
    position: relative; background: #0f172a; border: 1px solid #1e293b; border-radius: 6px;
    padding: 0.3rem 0.4rem; width: 9.4rem; display: flex; flex-direction: column; gap: 0.2rem;
  }
  .tie.done { border-color: #2f4d34; }
  .when { font-size: 0.55rem; color: #475569; font-variant-numeric: tabular-nums; }

  .slot { display: flex; align-items: center; gap: 0.35rem; min-height: 1.25rem; }
  .slot.r { flex-direction: row-reverse; text-align: right; }
  .flag { font-size: 0.95rem; line-height: 1; flex: none; }
  .flag.box { width: 0.95rem; height: 0.7rem; border: 1px solid #334155; border-radius: 2px; }
  .nm { font-size: 0.74rem; color: #cbd5e1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex: 1; }
  .slot.filled .nm { color: #e2e8f0; font-weight: 600; }
  .nm.line { border-bottom: 1px solid #334155; min-height: 0.95rem; display: flex; align-items: flex-end; }
  .hint { font-size: 0.58rem; color: #475569; font-weight: 400; }

  /* group tables: hidden off-print */
  .gt { display: none; }

  /* ── Print: shared ── */
  .print-sheet { display: none; }

  @media print {
    :global(body > *:not(.active)) { display: none !important; }
    :global(html), :global(body) { background: #fff !important; margin: 0 !important; }
    .print-sheet.active { display: block; width: 100%; color: #0f172a; }
    .plain { page: carta; }
    .groups { page: grupos; }
    @page carta  { size: letter landscape; margin: 0.5cm; }
    @page grupos { size: 13in 8.5in; margin: 0.4cm; }   /* su papel 8.5×13, apaisado */

    .title { text-align: center; color: #001f54; font-weight: 800; font-size: 20pt; letter-spacing: 0.04em; margin: 0 0 0.15cm; }
    .mirror { display: flex; align-items: stretch; justify-content: center; gap: 0.15cm; }
    .half { display: flex; flex: 1; gap: 0.15cm; }
    .pcol { display: flex; flex-direction: column; justify-content: space-around; flex: 1; gap: 0.1cm; }
    .center { display: flex; flex-direction: column; justify-content: center; align-items: center; gap: 0.15cm; flex: 0 0 2.2cm; }
    .clabel { font-size: 8pt; font-weight: 700; color: #001f54; letter-spacing: 0.05em; }
    .clabel.third { color: #64748b; font-weight: 600; margin-top: 0.3cm; }

    .print-sheet .tie { background: #fff; border: 1px solid #94a3b8; border-radius: 3px; width: auto; padding: 2pt 3pt; }
    .print-sheet .tie.done { border-color: #001f54; }
    .print-sheet .when { color: #94a3b8; font-size: 5pt; }
    .print-sheet .nm { color: #0f172a; font-size: 7pt; }
    .print-sheet .slot.filled .nm { color: #001f54; }
    .print-sheet .flag.box { border-color: #94a3b8; }
    .print-sheet .nm.line { border-bottom: 1px solid #94a3b8; }
    .print-sheet .hint { color: #94a3b8; font-size: 5pt; }
    .foot { text-align: center; color: #94a3b8; font-size: 6pt; margin: 0.15cm 0 0; }

    /* Group tables sit on the EXTERIOR side of each tie (consume width, not height,
       so the column no longer overflows onto a 2nd page). */
    .groups .gcol { flex: 2.7; }
    .print-sheet .gtie { display: flex; align-items: center; gap: 4pt; }
    .print-sheet .gtie.l { flex-direction: row-reverse; }   /* tablas al exterior izquierdo */
    .print-sheet .gtie.r { flex-direction: row; }            /* tablas al exterior derecho */
    .print-sheet .gtie > .tie { flex: 1 1 auto; }
    .gtables { display: flex; flex-direction: column; gap: 2pt; }
    .gt { display: table; border-collapse: collapse; font-size: 5pt; line-height: 1.15; }
    .gt caption { caption-side: top; text-align: left; font-weight: 700; font-size: 5pt; color: #001f54; padding-bottom: 0.5pt; white-space: nowrap; }
    .gt td { padding: 0 1.5pt; white-space: nowrap; }
    .gt .pos { color: #94a3b8; }
    .gt .cd { font-weight: 600; }
    .gt .pt { font-weight: 700; text-align: right; }
    .gt tr.p1, .gt tr.p2 { color: #15803d; }           /* clasifican */
    .gt tr.p3 { color: #b45309; }                        /* tercero */
    .gt tr.p4 { color: #94a3b8; }                        /* eliminado */
    .gt tr.hi td { background: #eef4ff; }                /* casilla de esta llave */
    .gt.thirds caption { color: #b45309; }
    .gt.thirds .pos { color: #b45309; font-weight: 700; }
  }
</style>
