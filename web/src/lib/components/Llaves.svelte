<script>
  import { teamFull, teamShort, teamFlag } from '$lib/teams.js';
  let { knockout } = $props();
  const pct = (x) => Math.round((x ?? 0) * 100);
</script>

<p class="note">
  Las predicciones formales se definen al terminar la fase de grupos. <br />Por ahora,
  presentamos la probabilidad de cada selección de alcanzar cada ronda:
</p>

<table class="ko">
  <thead>
    <tr>
      <th>Selección</th><th>Octavos</th><th>Cuartos</th><th>Semis</th><th>Final</th><th>Campeón</th>
    </tr>
  </thead>
  <tbody>
    {#each knockout as t}
      <tr>
        <td class="tname" title={teamFull(t.team)}>
          <span class="flag">{teamFlag(t.team)}</span>{teamShort(t.team)}<span class="g"> ·{t.group}</span>
        </td>
        <td>{pct(t.r16)}%</td>
        <td>{pct(t.qf)}%</td>
        <td>{pct(t.sf)}%</td>
        <td>{pct(t.final)}%</td>
        <td class="champ"><strong>{(t.champion * 100).toFixed(1)}%</strong></td>
      </tr>
    {/each}
  </tbody>
</table>

<style>
  .note { color: #64748b; font-size: 0.8rem; margin: 0 0 0.8rem; }
  .ko { width: 100%; border-collapse: collapse; font-size: 0.82rem; }
  th { color: #64748b; text-align: left; font-weight: 600; text-transform: uppercase; font-size: 0.64rem; padding: 0 0.4rem 0.4rem; }
  th:not(:first-child), td:not(:first-child) { text-align: right; }
  td { padding: 0.35rem 0.4rem; border-top: 1px solid #1e293b; font-variant-numeric: tabular-nums; }
  .tname { font-weight: 600; white-space: nowrap; }
  .flag { margin-right: 0.3rem; }
  .g { color: #475569; font-weight: 400; font-size: 0.72rem; }
  .champ { color: #d4af37; }
  tbody tr:nth-child(-n+3) .champ { font-size: 0.9rem; }
</style>
