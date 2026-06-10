<script>
  import { teamFull, teamShort, teamFlag } from '$lib/teams.js';
  import { LINES, LINE_COLORS, LINE_NAMES, verdictFor } from '$lib/grade.js';
  import ScoreMatrix from './ScoreMatrix.svelte';

  let { match } = $props();
  let open = $state(false);
  let active = $state('M2'); // which model's distribution the matrix shows

  const finished = $derived(match.status === 'finalizado' && match.result);

  function cellText(line, p) {
    if (!p) return '—';
    if (line === 'Mercado') {
      const pct = p.probs ? Math.round((p.probs[p.pick] ?? 0) * 100) : null;
      const who = p.pick === 'draw' ? 'X'
        : teamShort(p.pick === 'home' ? match.home : match.away);
      return pct != null ? `${who} ${pct}%` : who;
    }
    return `${p.home}–${p.away}`;
  }

  function mark(line, p) {
    if (!finished || !p) return '';
    const v = verdictFor(line, p, match.result);
    if (!v) return '';
    return v.acierto ? (v.exacto ? '✓⭐' : '✓') : '✗';
  }

  const pct = (x) => Math.round((x ?? 0) * 100);
  // M3 conformal set → Spanish ("México o Empate"); whole set means no outcome ruled out.
  const setLabel = (set) => {
    if (!set || !set.length) return '';
    if (set.length === 3) return 'cualquier resultado';
    const name = (o) => (o === 'home' ? teamShort(match.home) : o === 'away' ? teamShort(match.away) : 'Empate');
    return set.map(name).join(' o ');
  };
  const statusLabel = { por_jugarse: 'Por jugarse', en_vivo: 'En vivo', finalizado: 'Finalizado' };
</script>

<details class="row" class:finished bind:open>
  <summary>
    <div class="top">
      <div class="teams">
        <span class="team" title={teamFull(match.home)}>
          <span class="flag">{teamFlag(match.home)}</span>{teamShort(match.home)}
        </span>
        {#if finished}
          <span class="score">{match.result.home}–{match.result.away}</span>
        {:else}
          <span class="vs">vs</span>
        {/if}
        <span class="team away" title={teamFull(match.away)}>
          <span class="flag">{teamFlag(match.away)}</span>{teamShort(match.away)}
        </span>
      </div>
      <div class="meta">
        {#if match.group}<span class="grp">Grupo {match.group}</span>{/if}
        <span class="status status-{match.status}">{statusLabel[match.status]}</span>
        <span class="chev" aria-hidden="true">▸</span>
      </div>
    </div>

    <div class="strip">
      {#each LINES as line}
        {@const p = match.predictions[line]}
        {#if line !== 'Mercado' && p?.lambda}
          <button type="button" class="cell ix" class:on={open && active === line} style="--c:{LINE_COLORS[line]}"
            onclick={(e) => { e.stopPropagation(); active = line; open = true; }}
            title="Ver la distribución de marcadores">
            <span class="lbl">{line}</span>
            <span class="val">{cellText(line, p)}</span>
            {#if finished}<span class="mk">{mark(line, p)}</span>{/if}
          </button>
        {:else}
          <div class="cell" class:muted={!p} style="--c:{LINE_COLORS[line]}">
            <span class="lbl">{line}</span>
            <span class="val">{cellText(line, p)}</span>
            {#if finished}<span class="mk">{mark(line, p)}</span>{/if}
          </div>
        {/if}
      {/each}
    </div>
  </summary>

  <!-- Detail: scoreline distribution (matrix) + per-model W/D/L bars -->
  <div class="detail">
    {#if match.predictions.M2?.lambda}
      <ScoreMatrix {match} bind:active />
    {/if}
    {#each LINES as line}
      {@const p = match.predictions[line]}
      <div class="dline" style="--c:{LINE_COLORS[line]}">
        <div class="dhead"><b class="dlbl">{line}</b> <span class="dname">{LINE_NAMES[line]}</span></div>
        {#if p && p.probs}
          <div class="wdl" aria-hidden="true">
            <span class="seg h" style="width:{pct(p.probs.home)}%"></span>
            <span class="seg d" style="width:{pct(p.probs.draw)}%"></span>
            <span class="seg a" style="width:{pct(p.probs.away)}%"></span>
          </div>
          <div class="dmeta">
            <span>L {pct(p.probs.home)}% · E {pct(p.probs.draw)}% · V {pct(p.probs.away)}%</span>
            {#if p.lambda}<span class="xg">xG {p.lambda.home}–{p.lambda.away}</span>{/if}
            {#if line === 'Mercado'}<span class="xg">favorito: {p.pick === 'draw' ? 'empate' : teamShort(p.pick === 'home' ? match.home : match.away)}</span>{/if}
            {#if line === 'M3' && p.set}<span class="conf" title="Resultados que el modelo NO descarta con {pct(p.coverage)}% de confianza (predicción conformal)">{pct(p.coverage)}% conf: {setLabel(p.set)}</span>{/if}
          </div>
        {:else}
          <span class="pend">— pendiente</span>
        {/if}
      </div>
    {/each}
  </div>
</details>

<style>
  .row {
    background: #111827;
    border: 1px solid #1e293b;
    border-radius: 8px;
    padding: 0.6rem 0.75rem;
    margin: 0.4rem 0;
  }
  summary { cursor: pointer; list-style: none; }
  summary::-webkit-details-marker { display: none; }
  .top { display: flex; justify-content: space-between; align-items: baseline; gap: 0.5rem; flex-wrap: wrap; }
  .teams { display: flex; align-items: baseline; gap: 0.5rem; font-size: 0.95rem; }
  .team { font-weight: 600; white-space: nowrap; }
  .team.away { color: #cbd5e1; }
  .flag { margin-right: 0.3rem; }
  .vs { color: #64748b; font-size: 0.8rem; }
  .score { color: #d4af37; font-weight: 700; font-variant-numeric: tabular-nums; white-space: nowrap; }
  .meta { display: flex; gap: 0.5rem; align-items: center; font-size: 0.7rem; }
  .grp { color: #64748b; }
  .status { text-transform: uppercase; letter-spacing: 0.03em; }
  .status-por_jugarse { color: #64748b; }
  .status-en_vivo { color: #ef4444; }
  .status-finalizado { color: #22c55e; }
  .chev { color: #475569; transition: transform 0.15s; display: inline-block; }
  details[open] .chev { transform: rotate(90deg); }

  .strip { display: flex; gap: 0.4rem; margin-top: 0.5rem; flex-wrap: wrap; }
  .cell {
    flex: 1 1 0; min-width: 92px;
    border-left: 3px solid var(--c);
    background: #0f172a; border-radius: 4px;
    padding: 0.25rem 0.45rem;
    display: flex; flex-direction: column; gap: 0.05rem;
  }
  .cell.muted { opacity: 0.45; }
  button.cell { border: none; border-left: 3px solid var(--c); cursor: pointer; font: inherit; text-align: left; color: inherit; }
  button.cell:hover { background: #162133; }
  .cell.on { background: color-mix(in srgb, var(--c) 16%, #0f172a); }
  .lbl { font-size: 0.62rem; color: var(--c); font-weight: 700; letter-spacing: 0.04em; }
  .val { font-size: 0.85rem; font-variant-numeric: tabular-nums; white-space: nowrap; }
  .mk { font-size: 0.75rem; }

  .detail { margin-top: 0.6rem; padding-top: 0.5rem; border-top: 1px solid #1e293b; display: grid; gap: 0.5rem; }
  .dline { border-left: 3px solid var(--c); padding-left: 0.5rem; }
  .dhead { font-size: 0.72rem; }
  .dlbl { color: var(--c); }
  .dname { color: #94a3b8; }
  .wdl { display: flex; height: 7px; border-radius: 3px; overflow: hidden; margin: 0.25rem 0; background: #0f172a; }
  .seg.h { background: #38bdf8; }
  .seg.d { background: #475569; }
  .seg.a { background: #fb923c; }
  .dmeta { display: flex; gap: 0.75rem; flex-wrap: wrap; font-size: 0.72rem; color: #94a3b8; font-variant-numeric: tabular-nums; }
  .xg { color: #64748b; }
  .conf { color: #22c55e; font-variant-numeric: tabular-nums; }
  .pend { font-size: 0.72rem; color: #475569; }

  /* Phones: 4-line strip becomes an even 2×2 grid (no ragged wrap). */
  @media (max-width: 480px) {
    .strip { display: grid; grid-template-columns: 1fr 1fr; }
    .cell { min-width: 0; }
    .teams { font-size: 0.88rem; }
    .meta { font-size: 0.65rem; }
  }
</style>
