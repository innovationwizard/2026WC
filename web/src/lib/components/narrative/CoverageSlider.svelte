<script>
  // Act 3 sandbox: demand more confidence → the conformal set widens. No free lunch.
  // Uses the held-out-validated τ per coverage level (tau_by_coverage from narrative.json).
  import { teamShort } from '$lib/teams.js';
  let { matches, tau } = $props();

  const covs = $derived(Object.keys(tau).map(Number).sort((a, b) => a - b));
  let ci = $state(0);
  const cov = $derived(covs.length ? covs[Math.min(ci, covs.length - 1)] : 0.8);
  const t = $derived(tau[String(cov)] ?? 0.236);

  // A fixture that's interesting at the low end (a 2-way set), else any with M3.
  const sample = $derived(
    matches.find((m) => m.predictions.M3?.set?.length === 2) || matches.find((m) => m.predictions.M3)
  );

  function setAt(m, thr) {
    const p = m.predictions.M3.probs;
    const order = ['home', 'draw', 'away'];
    const s = order.filter((o) => p[o] >= thr);
    return s.length ? s : [order.reduce((a, b) => (p[a] >= p[b] ? a : b))];
  }
  const curSet = $derived(sample ? setAt(sample, t) : []);
  const label = (o, m) => (o === 'home' ? teamShort(m.home) : o === 'away' ? teamShort(m.away) : 'Empate');
</script>

{#if sample}
  <div class="cov">
    <div class="match">{teamShort(sample.home)} vs {teamShort(sample.away)}</div>
    <input type="range" min="0" max={Math.max(0, covs.length - 1)} step="1" bind:value={ci} aria-label="Nivel de confianza" />
    <div class="lab">Confianza exigida: <b>{Math.round(cov * 100)}%</b></div>
    <div class="outcomes">
      {#each ['home', 'draw', 'away'] as o}
        <span class="oc" class:inset={curSet.includes(o)}>{label(o, sample)}</span>
      {/each}
    </div>
    <p class="cap">Más confianza ⇒ conjunto más ancho. No hay almuerzo gratis: la honestidad cuesta precisión.</p>
  </div>
{/if}

<style>
  .cov { width: 100%; max-width: 420px; margin: 0 auto; text-align: center; }
  .match { color: #cbd5e1; font-weight: 600; margin-bottom: 0.9rem; }
  input[type='range'] { width: 100%; accent-color: #22c55e; }
  .lab { color: #94a3b8; font-size: 0.9rem; margin: 0.5rem 0 0.9rem; }
  .lab b { color: #22c55e; font-variant-numeric: tabular-nums; }
  .outcomes { display: flex; gap: 0.5rem; justify-content: center; }
  .oc { flex: 1; padding: 0.5rem 0.3rem; border-radius: 6px; background: #0f172a; border: 1px solid #1e293b; color: #475569; font-size: 0.85rem; text-decoration: line-through; transition: all 0.2s; }
  .oc.inset { color: #e2e8f0; border-color: #22c55e; background: #14241c; text-decoration: none; }
  .cap { color: #94a3b8; font-size: 0.82rem; margin-top: 1rem; line-height: 1.5; }
</style>
