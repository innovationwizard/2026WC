<script>
  // Act 1 sandbox: pick a real fixture, roll the dice, watch one match produce many
  // different scorelines (genuine Poisson sampling from the match's own λ).
  import { teamShort } from '$lib/teams.js';
  let { matches } = $props();

  const opts = $derived(matches.filter((m) => m.predictions.M2?.lambda));
  let idx = $state(0);
  const m = $derived(opts[idx]);

  let counts = $state({});
  let wdl = $state({ home: 0, draw: 0, away: 0 });
  let total = $state(0);

  function pois(lam) {
    const L = Math.exp(-lam); let k = 0, p = 1;
    do { k++; p *= Math.random(); } while (p > L);
    return k - 1;
  }
  function roll(n) {
    const lh = m.predictions.M2.lambda.home, la = m.predictions.M2.lambda.away;
    const c = { ...counts }, w = { ...wdl };
    for (let i = 0; i < n; i++) {
      const h = Math.min(pois(lh), 7), a = Math.min(pois(la), 7);
      c[`${h}–${a}`] = (c[`${h}–${a}`] || 0) + 1;
      if (h > a) w.home++; else if (h === a) w.draw++; else w.away++;
    }
    counts = c; wdl = w; total += n;
  }
  function reset() { counts = {}; wdl = { home: 0, draw: 0, away: 0 }; total = 0; }

  const topScores = $derived(Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 6));
  const maxN = $derived(Math.max(1, ...Object.values(counts)));
</script>

<div class="dice">
  <div class="controls">
    <select bind:value={idx} onchange={reset} aria-label="Elegir partido">
      {#each opts as o, i}<option value={i}>{teamShort(o.home)} vs {teamShort(o.away)}</option>{/each}
    </select>
    <button onclick={() => roll(1)}>+1</button>
    <button onclick={() => roll(25)}>+25</button>
    <button onclick={() => roll(1000)}>+1000</button>
    <button class="reset" onclick={reset} aria-label="Reiniciar">↺</button>
  </div>

  {#if total > 0}
    <div class="count">{total.toLocaleString('es')} {total === 1 ? 'partido' : 'partidos'}</div>
    <div class="tally">
      <span>{teamShort(m.home)} {Math.round((wdl.home / total) * 100)}%</span>
      <span class="d">Empate {Math.round((wdl.draw / total) * 100)}%</span>
      <span>{teamShort(m.away)} {Math.round((wdl.away / total) * 100)}%</span>
    </div>
    <div class="scores">
      {#each topScores as [k, n]}
        <div class="srow"><span class="sk">{k}</span><span class="strack"><span class="sfill" style="width:{(n / maxN) * 100}%"></span></span><span class="sn">{Math.round((n / total) * 100)}%</span></div>
      {/each}
    </div>
  {:else}
    <p class="hint">Tire los dados: el mismo partido produce marcadores distintos cada vez.</p>
  {/if}
</div>

<style>
  .dice { width: 100%; max-width: 460px; margin: 0 auto; }
  .controls { display: flex; gap: 0.4rem; flex-wrap: wrap; justify-content: center; }
  select { background: #0f172a; color: #e2e8f0; border: 1px solid #1e293b; border-radius: 6px; padding: 0.35rem 0.5rem; font-family: inherit; font-size: 0.85rem; flex: 1 1 11rem; }
  button { background: #1e293b; color: #e2e8f0; border: none; border-radius: 6px; padding: 0.35rem 0.7rem; cursor: pointer; font-family: inherit; font-weight: 600; font-size: 0.85rem; }
  button:hover { background: #334155; }
  button.reset { background: #0f172a; color: #94a3b8; }
  .count { text-align: center; color: #d4af37; font-variant-numeric: tabular-nums; margin: 0.8rem 0 0.5rem; }
  .tally { display: flex; justify-content: space-between; font-size: 0.85rem; color: #cbd5e1; margin-bottom: 0.7rem; }
  .tally .d { color: #94a3b8; }
  .scores { display: flex; flex-direction: column; gap: 0.35rem; }
  .srow { display: grid; grid-template-columns: 2.6rem 1fr 2.4rem; align-items: center; gap: 0.5rem; font-size: 0.82rem; }
  .sk { font-variant-numeric: tabular-nums; color: #cbd5e1; }
  .strack { height: 11px; background: #0f172a; border-radius: 3px; overflow: hidden; }
  .sfill { display: block; height: 100%; background: #64748b; border-radius: 3px; transition: width 0.3s ease; }
  .sn { text-align: right; color: #94a3b8; font-variant-numeric: tabular-nums; }
  .hint { text-align: center; color: #64748b; font-size: 0.85rem; }
</style>
