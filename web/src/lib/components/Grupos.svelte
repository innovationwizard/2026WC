<script>
  import { teamFull, teamShort, teamFlag } from '$lib/teams.js';
  let { groups } = $props();
  const pct = (x) => Math.round((x ?? 0) * 100);
</script>

<div class="grid">
  {#each groups as g}
    <section class="gcard">
      <h3>Grupo {g.group}</h3>
      <table>
        <thead>
          <tr>
            <th>Selección</th><th>Elo</th>
            <th class="info" title="Valor de mercado del plantel (millones de €, Transfermarkt)">Valor</th>
            <th>Avanza</th><th>Campeón</th>
          </tr>
        </thead>
        <tbody>
          {#each g.teams as t}
            <tr>
              <td class="tname" title={teamFull(t.team)}>
                <span class="flag">{teamFlag(t.team)}</span>{teamShort(t.team)}
              </td>
              <td>{t.elo}</td>
              <td class="val">{t.value != null ? `€${t.value}M` : '—'}</td>
              <td class="adv"><strong>{pct(t.advance)}%</strong></td>
              <td>{(t.champion * 100).toFixed(1)}%</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </section>
  {/each}
</div>

<style>
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1rem; }
  .gcard { background: #111827; border: 1px solid #1e293b; border-radius: 8px; padding: 0.9rem 1rem; }
  h3 { color: #d4af37; font-size: 1rem; margin: 0 0 0.5rem; }
  table { width: 100%; border-collapse: collapse; font-size: 0.8rem; }
  th { color: #64748b; text-align: left; font-weight: 600; text-transform: uppercase; font-size: 0.62rem; padding: 0 0.3rem 0.3rem; }
  th.info { border-bottom: 1px dotted #475569; cursor: help; }
  th:not(:first-child), td:not(:first-child) { text-align: right; }
  td { padding: 0.3rem; border-top: 1px solid #1e293b; font-variant-numeric: tabular-nums; }
  .tname { font-weight: 600; white-space: nowrap; }
  .flag { margin-right: 0.3rem; }
  .val { color: #94a3b8; }
  .adv { color: #22c55e; }
</style>
