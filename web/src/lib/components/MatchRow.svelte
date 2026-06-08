<script>
  import { teamFull, teamShort, teamFlag } from '$lib/teams.js';
  import { LINES, LINE_COLORS, verdictFor } from '$lib/grade.js';

  let { match } = $props();

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

  const statusLabel = { por_jugarse: 'Por jugarse', en_vivo: 'En vivo', finalizado: 'Finalizado' };
</script>

<article class="row" class:finished>
  <header>
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
    </div>
  </header>

  <div class="strip">
    {#each LINES as line}
      {@const p = match.predictions[line]}
      <div class="cell" class:muted={!p} style="--c:{LINE_COLORS[line]}">
        <span class="lbl">{line}</span>
        <span class="val">{cellText(line, p)}</span>
        {#if finished}<span class="mk">{mark(line, p)}</span>{/if}
      </div>
    {/each}
  </div>
</article>

<style>
  .row {
    background: #111827;
    border: 1px solid #1e293b;
    border-radius: 8px;
    padding: 0.6rem 0.75rem;
    margin: 0.4rem 0;
  }
  header { display: flex; justify-content: space-between; align-items: baseline; gap: 0.5rem; flex-wrap: wrap; }
  .teams { display: flex; align-items: baseline; gap: 0.5rem; font-size: 0.95rem; }
  .team { font-weight: 600; white-space: nowrap; }      /* single line, always */
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

  .strip { display: flex; gap: 0.4rem; margin-top: 0.5rem; flex-wrap: wrap; }
  .cell {
    flex: 1 1 0;
    min-width: 92px;
    border-left: 3px solid var(--c);
    background: #0f172a;
    border-radius: 4px;
    padding: 0.25rem 0.45rem;
    display: flex;
    flex-direction: column;
    gap: 0.05rem;
  }
  .cell.muted { opacity: 0.45; }
  .lbl { font-size: 0.62rem; color: var(--c); font-weight: 700; letter-spacing: 0.04em; }
  .val { font-size: 0.85rem; font-variant-numeric: tabular-nums; white-space: nowrap; }
  .mk { font-size: 0.75rem; }
</style>
