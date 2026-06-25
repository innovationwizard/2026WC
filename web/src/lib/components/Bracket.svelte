<script>
  import { teamShort, teamFlag, teamFull } from '$lib/teams.js';
  import { buildBracket, R32, ROUNDS } from '$lib/bracket.js';

  let { matches } = $props();
  const { resolved } = buildBracket(matches);
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
    r16: ['P89', 'P90', 'P93', 'P94'],
    qf: ['P97', 'P98'],
    sf: ['P101'],
  };
  const R = {
    r32: ['P76', 'P78', 'P79', 'P80', 'P86', 'P88', 'P85', 'P87'],
    r16: ['P91', 'P92', 'P95', 'P96'],
    qf: ['P99', 'P100'],
    sf: ['P102'],
  };

  const print = () => window.print();

  // Move the print sheet to a direct child of <body> so that, when printing, we can
  // display:none everything else (removing it from flow → no trailing blank pages).
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

<!-- ════════ Toolbar ════════ -->
<div class="bar">
  <p class="lead">
    Cuadro determinista: una selección aparece solo cuando tiene <b>asegurada</b> esa
    posición exacta; lo demás queda en blanco para llenar a mano.
  </p>
  <button class="export" onclick={print}>🖨️ Imprimir</button>
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

<!-- ════════ Print only: letter-size mirrored sheet ════════ -->
<div class="print-sheet" use:portal>
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

<style>
  .bar { display: flex; justify-content: space-between; align-items: center; gap: 1rem; flex-wrap: wrap; margin: 0 0 1rem; }
  .lead { color: #94a3b8; font-size: 0.8rem; margin: 0; max-width: 46ch; }
  .lead b { color: #e2e8f0; }
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

  /* ── Print sheet (portaled to <body>, hidden on screen) ── */
  .print-sheet { display: none; }

  @media print {
    /* The sheet is now a direct child of <body>; hide every other body child so the
       document collapses to a single landscape page (no trailing blank pages). */
    :global(body > *:not(.print-sheet)) { display: none !important; }
    :global(html), :global(body) { background: #fff !important; margin: 0 !important; }
    .print-sheet { display: block; width: 100%; color: #0f172a; }
    @page { size: letter landscape; margin: 0.5cm; }

    .title { text-align: center; color: #001f54; font-weight: 800; font-size: 20pt; letter-spacing: 0.04em; margin: 0 0 0.2cm; }
    .mirror { display: flex; align-items: stretch; justify-content: center; gap: 0.15cm; }
    .half { display: flex; flex: 1; gap: 0.15cm; }
    .half.right { flex-direction: row; }
    .pcol { display: flex; flex-direction: column; justify-content: space-around; flex: 1; gap: 0.1cm; }
    .center { display: flex; flex-direction: column; justify-content: center; align-items: center; gap: 0.15cm; flex: 0 0 2.4cm; }
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
    .foot { text-align: center; color: #94a3b8; font-size: 6pt; margin: 0.2cm 0 0; }
  }
</style>
