<script>
  import { scoreboard, SCOREBOARD_LINES, LINE_LABELS, LINE_COLORS, PINNACLE_NOTE } from '$lib/grade.js';

  let { matches } = $props();
  const sb = scoreboard(matches);
  const anyPlayed = SCOREBOARD_LINES.some((l) => sb[l].jugados > 0);
  const maxPlayed = Math.max(0, ...SCOREBOARD_LINES.map((l) => sb[l].jugados));
  const smallSample = anyPlayed && maxPlayed < 20;
  // Best (lowest) RPS + log-loss across lines, to highlight the leader.
  const bestRps = Math.min(...SCOREBOARD_LINES.map((l) => sb[l].rps ?? Infinity));
  const bestLl = Math.min(...SCOREBOARD_LINES.map((l) => sb[l].logloss ?? Infinity));
  const NOTE = { M3_frozen: 'M3 congelado antes del torneo (predicción pre-torneo). Sirve de referencia: ¿ayuda actualizar el modelo con los resultados del torneo?' };
</script>

<section class="board">
  <h2>Tablero de aciertos {#if smallSample}<span class="tag">(muestra pequeña)</span>{/if}</h2>
  {#if !anyPlayed}
    <p class="empty">Se activa cuando se jueguen los primeros partidos. Por ahora muestra los pronósticos de cada modelo en el calendario.</p>
  {/if}
  <div class="lines">
    {#each SCOREBOARD_LINES as l}
      {@const s = sb[l]}
      <div class="line" style="--c:{LINE_COLORS[l]}">
        <span class="name" title={l === 'Mercado' ? PINNACLE_NOTE : (NOTE[l] ?? null)}>{LINE_LABELS[l]}</span>
        <span class="hit">{s.aciertos}/{s.jugados}<small> aciertos</small></span>
        <span class="pct">{s.jugados ? `${Math.round((s.aciertos / s.jugados) * 100)}%` : '—'}</span>
        <span class="rps" class:best={s.rps != null && s.rps === bestRps}>{s.rps != null ? `RPS ${s.rps.toFixed(3)}` : 'RPS —'}</span>
        <span class="ll" class:best={s.logloss != null && s.logloss === bestLl}>{s.logloss != null ? `log ${s.logloss.toFixed(3)}` : 'log —'}</span>
        <span class="ex">{s.exactos != null ? `${s.exactos} exactos` : '— exactos'}</span>
      </div>
    {/each}
  </div>
  <p class="foot">RPS y <span title="Puntaje logarítmico / ignorancia: −log₂ p(resultado). Más bajo = mejor. Regla de puntuación más estricta que RPS.">log</span> (menor = mejor) contra el resultado real. <b>M3₀</b> = modelo congelado pre-torneo (referencia).</p>
</section>

<style>
  .board { background: #111827; border: 1px solid #1e293b; border-radius: 8px; padding: 0.9rem 1rem; margin: 0 0 1.25rem; }
  h2 { font-size: 0.95rem; color: #e2e8f0; margin: 0 0 0.6rem; }
  .tag { color: #64748b; font-size: 0.7rem; font-weight: 400; }
  .empty { color: #64748b; font-size: 0.78rem; margin: 0 0 0.6rem; }
  .lines { display: grid; gap: 0.3rem; }
  .line {
    display: grid;
    grid-template-columns: 5.5rem auto 1fr auto auto auto;
    gap: 0.6rem;
    align-items: baseline;
    border-left: 3px solid var(--c);
    padding: 0.25rem 0 0.25rem 0.6rem;
  }
  .name { color: var(--c); font-weight: 700; font-size: 0.85rem; }
  .hit { color: #e2e8f0; font-weight: 700; font-size: 1rem; font-variant-numeric: tabular-nums; } /* headline, full contrast */
  .hit small { color: #64748b; font-weight: 400; font-size: 0.7rem; }
  .pct { color: var(--c); font-weight: 700; font-size: 1rem; font-variant-numeric: tabular-nums; } /* % aciertos, model-colored */
  .rps, .ll { color: #64748b; font-size: 0.78rem; font-variant-numeric: tabular-nums; }        /* muted, secondary */
  .rps.best, .ll.best { color: #facc15; font-weight: 700; }                                     /* leader on that metric */
  .ex { color: #94a3b8; font-size: 0.75rem; }
  .foot { color: #64748b; font-size: 0.68rem; margin: 0.55rem 0 0; }
  .foot b { color: #4d7c5f; }
  @media (max-width: 520px) {
    .line { grid-template-columns: 4.5rem auto 1fr auto; }
    .ex, .ll { display: none; }
  }
</style>
