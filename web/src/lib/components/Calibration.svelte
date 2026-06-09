<script>
  // Reliability diagram for Act 3: predicted probability (x) vs observed frequency (y).
  // A model on the dashed diagonal is perfectly calibrated ("when it says 70%, it happens 70%").
  let { points = [], size = 300 } = $props();
  const pad = 34;
  const x = (p) => pad + p * (size - 2 * pad);
  const y = (f) => size - pad - f * (size - 2 * pad);
  const path = $derived(points.map((pt, i) => `${i ? 'L' : 'M'}${x(pt.p).toFixed(1)},${y(pt.freq).toFixed(1)}`).join(' '));
</script>

<svg viewBox="0 0 {size} {size}" class="calib" role="img" aria-label="Diagrama de calibración: predicho contra real">
  <rect x={pad} y={pad} width={size - 2 * pad} height={size - 2 * pad} class="frame" />
  <line x1={pad} y1={size - pad} x2={size - pad} y2={pad} class="diag" />
  <path d={path} class="curve" />
  {#each points as pt}<circle cx={x(pt.p)} cy={y(pt.freq)} r="3.2" class="dot" />{/each}
  <text x={size / 2} y={size - 8} class="ax">predicho →</text>
  <text x="12" y={size / 2} class="ax" transform="rotate(-90 12 {size / 2})">real →</text>
  <text x={size - pad} y={pad - 8} class="leg">calibración perfecta ⟍</text>
</svg>

<style>
  .calib { width: 100%; max-width: 320px; }
  .frame { fill: #0b1220; stroke: #1e293b; stroke-width: 1; }
  .diag { stroke: #475569; stroke-dasharray: 4 4; stroke-width: 1; }
  .curve { fill: none; stroke: #22c55e; stroke-width: 2.5; stroke-linejoin: round; }
  .dot { fill: #22c55e; }
  .ax { fill: #64748b; font-size: 11px; text-anchor: middle; }
  .leg { fill: #475569; font-size: 9px; text-anchor: end; }
</style>
