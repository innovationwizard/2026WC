<script>
  // El veredicto — /veredicto. Self-narrating epilogue: across the full World Cup, how
  // did the AI models stack up against Pinnacle (the sharpest market)? Same scrollytelling
  // spine as /historia (Scrolly sticky-stepper). Real data only: the calibration scoreboard
  // is computed live from matches.json via grade.js; ROI is the tournament-complete
  // backtest (backtest_edge.py). See FINDINGS_adaptive_forecasting.md.
  import Scrolly from '$lib/components/Scrolly.svelte';
  import { scoreboard } from '$lib/grade.js';
  import { teamShort, teamFlag } from '$lib/teams.js';

  let { data } = $props();

  // ── Real scoreboard, computed from baked data (freeze-at-kickoff, out-of-sample) ──
  const sb = $derived(scoreboard(data.matches));
  const nPlayed = $derived(data.matches.filter((m) => m.status === 'finalizado' && m.result).length);

  const COL = { M1: '#64748b', M2: '#3b82f6', M3: '#22c55e', Mercado: '#d4af37', M3_frozen: '#4d7c5f' };
  const NAME = { M1: 'M1 · Azar/Elo', M2: 'M2 · Red Neuronal', M3: 'M3 · IA con Criterio', Mercado: 'Pinnacle', M3_frozen: 'M3 pre-torneo' };
  const BOARD = ['Mercado', 'M2', 'M3', 'M1']; // best → worst, the four canonical lines

  const pct = (l) => (sb[l].jugados ? sb[l].aciertos / sb[l].jugados : 0);
  const pctBar = (p) => Math.max(3, Math.min(100, ((p - 0.55) / 0.15) * 100)); // window 55–70%
  const rpsBar = (v) => Math.max(3, Math.min(100, ((0.175 - v) / 0.05) * 100)); // window .125–.175, lower=better

  // Betting ROI vs Pinnacle over all 104 matches (backtest_edge.py, τ=0 best-case).
  const ROI = { M1: -55, M2: -57, M3: -47 };
  const roiBar = (r) => Math.min(100, (Math.abs(r) / 62) * 100);

  // Champion, derived from the real final (P104).
  const finalMatch = $derived(data.matches.find((m) => m.id === 'P104'));
  const champion = $derived(finalMatch?.result?.advances ?? 'Spain');

  // ── ACT 1 · Calibration ──
  const act1 = [
    { mode: 'pct', text: 'Terminó el Mundial. Durante todo el torneo, cuatro modelos pronosticaron cada partido y compitieron, uno por uno, contra la línea de cierre de Pinnacle — el mercado de apuestas más afilado del mundo.' },
    { mode: 'pct', text: 'La regla fue estricta: cada pronóstico se congeló al inicio del partido y nunca se recalculó. Sin trampa de retrospectiva. Esto es rendimiento real fuera de muestra.' },
    { mode: 'pct', text: '¿Quién acertó más partidos? Pinnacle acertó el 68%. El mejor modelo llegó al 65%. Buenos — pero segundos.' },
    { mode: 'rps', text: 'Y en calibración —el RPS, donde más bajo es mejor— Pinnacle quedó solo adelante. La IA acierta 2 de cada 3; el mercado, casi 7 de cada 10, y con la probabilidad mejor afinada.' },
  ];
  let a1 = $state(0);
  const a1mode = $derived(act1[Math.min(a1, act1.length - 1)].mode);

  // ── ACT 2 · Betting edge ──
  const act2 = [
    { text: '¿Y si uno apostara los “valores” que el modelo cree ver en las cuotas de Pinnacle?' },
    { text: 'Habría perdido cerca de la mitad del dinero. Apostar al azar solo pierde la comisión (~6%); estos modelos pierden ~50%.' },
    { text: 'Lo demoledor: mientras más seguro estaba el modelo, más perdía. Donde más difería del mercado, más se equivocaba. Su error está alineado con equivocarse — no con detectar precios mal puestos.' },
  ];
  let a2 = $state(0);

  // ── ACT 3 · Did updating help? + verdict ──
  const act3 = [
    { text: '¿Sirvió que el modelo aprendiera de los propios resultados del Mundial, ronda a ronda?' },
    { text: 'No. El modelo actualizado con el torneo empató —apenas peor— con el modelo congelado antes del primer partido. Unos 100 partidos casi no mueven a un modelo entrenado con ~49 000.' },
    { text: 'El veredicto, medido sin engaños: la IA es buena, pero segunda. El mercado más afilado del mundo todavía le gana — en precisión, en calibración y en ganancia.' },
  ];
  let a3 = $state(0);
</script>

<main class="veredicto">
  <section class="hero">
    <p class="kicker">El veredicto final · Mundial 2026</p>
    <h1>¿Le ganó la IA a Pinnacle?</h1>
    <p class="sub">{nPlayed} partidos, medidos sin trampa. La respuesta honesta: <em>todavía no.</em></p>
    <div class="scroll-cue" aria-hidden="true">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>
    </div>
  </section>

  <!-- ════ ACT 1 · Calibración ════ -->
  <section class="act">
    <header class="act-head"><p class="phase">El marcador · {nPlayed} partidos</p><h2>Buena, pero segunda</h2></header>
    <Scrolly steps={act1} bind:active={a1}>
      {#snippet visual()}
        <div class="sim">
          {#if a1mode === 'pct'}
            <div class="sim-head">Aciertos <span class="muted">(% de partidos · ventana 55–70)</span></div>
            <div class="bars">
              {#each BOARD as l}
                <div class="bar-row" class:win={l === 'Mercado'}>
                  <span class="bt" style="color:{COL[l]}">{NAME[l]}</span>
                  <span class="track"><span class="fill" style="width:{pctBar(pct(l))}%; background:{COL[l]}"></span></span>
                  <span class="bp">{Math.round(pct(l) * 100)}%</span>
                </div>
              {/each}
            </div>
            <p class="cap">Pinnacle acierta más partidos que cualquier modelo.</p>
          {:else}
            <div class="sim-head">Error de predicción · RPS <span class="muted">(más bajo = mejor)</span></div>
            <div class="bars">
              {#each BOARD as l}
                <div class="bar-row rps" class:win={l === 'Mercado'}>
                  <span class="bt" style="color:{COL[l]}">{NAME[l]}</span>
                  <span class="track"><span class="fill" style="width:{rpsBar(sb[l].rps ?? 0.175)}%; background:{COL[l]}"></span></span>
                  <span class="bp">{(sb[l].rps ?? 0).toFixed(3)}</span>
                </div>
              {/each}
            </div>
            <p class="cap">Barra más larga = menor error. Pinnacle queda solo adelante.</p>
          {/if}
        </div>
      {/snippet}
      {#snippet stepBody(step)}{step.text}{/snippet}
    </Scrolly>
  </section>

  <!-- ════ ACT 2 · Apuestas ════ -->
  <section class="act">
    <header class="act-head"><p class="phase">¿Y apostando?</p><h2>Peor: pierde la mitad</h2></header>
    <Scrolly steps={act2} bind:active={a2}>
      {#snippet visual()}
        <div class="sim">
          <div class="sim-head">Rendimiento apostando contra Pinnacle <span class="muted">(ROI)</span></div>
          <div class="roi">
            {#each ['M1', 'M2', 'M3'] as l}
              <div class="roi-row">
                <span class="bt" style="color:{COL[l]}">{NAME[l]}</span>
                <span class="track roi-track"><span class="fill roi-fill" style="width:{roiBar(ROI[l])}%"></span></span>
                <span class="bp neg">{ROI[l]}%</span>
              </div>
            {/each}
          </div>
          <p class="zero">│ 0% = el mercado (cuota justa). Al azar se pierde solo el ~6% de comisión.</p>
        </div>
      {/snippet}
      {#snippet stepBody(step)}{step.text}{/snippet}
    </Scrolly>
  </section>

  <!-- ════ ACT 3 · ¿Ayudó actualizar? + veredicto ════ -->
  <section class="act">
    <header class="act-head"><p class="phase">¿Sirvió aprender del torneo?</p><h2>Tampoco</h2></header>
    <Scrolly steps={act3} bind:active={a3}>
      {#snippet visual()}
        <div class="sim">
          <div class="sim-head">RPS · actualizado vs. congelado <span class="muted">(más bajo = mejor)</span></div>
          <div class="bars">
            {#each [['M3', 'M3 · actualizado con el torneo'], ['M3_frozen', 'M3 · congelado pre-torneo']] as [l, name]}
              <div class="bar-row rps">
                <span class="bt" style="color:{COL[l]}">{name}</span>
                <span class="track"><span class="fill" style="width:{rpsBar(sb[l].rps ?? 0.175)}%; background:{COL[l]}"></span></span>
                <span class="bp">{(sb[l].rps ?? 0).toFixed(3)}</span>
              </div>
            {/each}
          </div>
          <p class="cap">Prácticamente idénticos. Aprender del torneo no movió la aguja.</p>
        </div>
      {/snippet}
      {#snippet stepBody(step)}{step.text}{/snippet}
    </Scrolly>
  </section>

  <!-- ════ FINALE ════ -->
  <section class="finale">
    <p class="phase">Campeón del Mundo 2026</p>
    <div class="champ"><span class="flag">{teamFlag(champion)}</span>{teamShort(champion)}</div>
    {#if finalMatch?.result}
      <p class="fscore">Final: {teamShort(finalMatch.home)} {finalMatch.result.home}–{finalMatch.result.away} {teamShort(finalMatch.away)}
        <span class="muted">(90′) · avanzó {teamShort(champion)}</span></p>
    {/if}
    <p class="closing">Lo valioso no fue ganarle al mercado. Fue <b>medirlo sin engañarnos</b> — y poder decir, con honestidad, que todavía no.</p>
    <a class="cta" href="/">Ver el marcador en vivo →</a>
  </section>
</main>

<style>
  :global(body) { margin: 0; background: #0a0e17; }
  .veredicto { color: #e2e8f0; font-family: 'Segoe UI', system-ui, sans-serif; }

  .hero { position: relative; box-sizing: border-box; height: calc(100vh - var(--banner-h, 0px)); height: calc(100svh - var(--banner-h, 0px)); display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; gap: 0.6rem; padding: 1rem 2rem 11vh; }
  .kicker { color: #d4af37; letter-spacing: 0.2em; text-transform: uppercase; font-size: 0.8rem; margin: 0; }
  h1 { font-size: clamp(2.6rem, 9vw, 5.5rem); line-height: 1.03; margin: 0.4rem 0 0; font-weight: 800; letter-spacing: -0.02em; text-wrap: balance; }
  .sub { font-size: clamp(1.1rem, 3vw, 1.6rem); color: #94a3b8; margin: 0.6rem 0 0; }
  .sub em { color: #d4af37; font-style: italic; }
  .scroll-cue { position: absolute; bottom: 1.6rem; color: #475569; animation: cue 2.2s ease-in-out infinite; }
  @keyframes cue { 0%, 100% { opacity: 0.3; transform: translateY(0); } 50% { opacity: 0.85; transform: translateY(5px); } }
  @media (prefers-reduced-motion: reduce) { .scroll-cue { animation: none; opacity: 0.5; } }

  .act { max-width: 1100px; margin: 0 auto; padding: 0 1.25rem 2rem; }
  .act-head { padding: 4rem 0 0; }
  .phase { color: #64748b; letter-spacing: 0.15em; text-transform: uppercase; font-size: 0.75rem; margin: 0; }
  .act-head h2 { font-size: clamp(1.8rem, 5vw, 3rem); margin: 0.3rem 0 0; }

  .sim { width: 100%; max-width: 480px; }
  .sim-head { color: #d4af37; font-variant-numeric: tabular-nums; font-size: 0.95rem; margin-bottom: 0.9rem; text-align: center; }
  .sim-head .muted { color: #64748b; font-size: 0.8rem; }
  .bars, .roi { display: flex; flex-direction: column; gap: 0.5rem; }
  .bar-row { display: grid; grid-template-columns: 9rem 1fr 3rem; align-items: center; gap: 0.5rem; font-size: 0.85rem; }
  .bar-row.rps { grid-template-columns: 11rem 1fr 3.2rem; }
  .roi-row { display: grid; grid-template-columns: 9rem 1fr 3rem; align-items: center; gap: 0.5rem; font-size: 0.85rem; }
  .bt { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-weight: 600; }
  .flag { margin-right: 0.3rem; }
  .track { height: 12px; background: #0f172a; border-radius: 3px; overflow: hidden; }
  .fill { display: block; height: 100%; border-radius: 3px; transition: width 0.6s cubic-bezier(.2,.7,.2,1); }
  .bp { text-align: right; font-variant-numeric: tabular-nums; color: #94a3b8; }
  .bp.neg { color: #f4756b; font-weight: 600; }
  .cap { text-align: center; color: #94a3b8; margin-top: 0.9rem; font-size: 0.85rem; }
  .win .bt { color: #d4af37 !important; }

  /* ROI bars grow from a gold "market = 0%" baseline, red into loss */
  .roi-track { position: relative; height: 16px; }
  .roi-track::before { content: ""; position: absolute; left: 0; top: -3px; bottom: -3px; width: 2px; background: #d4af37; }
  .roi-fill { background: linear-gradient(90deg, #b23b33, #f4756b); }
  .zero { text-align: center; color: #d4af37; font-size: 0.78rem; margin-top: 0.9rem; font-variant-numeric: tabular-nums; }

  .finale { min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; gap: 0.4rem; padding: 2rem; max-width: 620px; margin: 0 auto; }
  .champ { font-size: clamp(2.4rem, 8vw, 4rem); font-weight: 800; color: #d4af37; letter-spacing: -0.01em; margin: 0.4rem 0 0; }
  .fscore { color: #94a3b8; font-variant-numeric: tabular-nums; margin: 0.3rem 0 0; }
  .fscore .muted { color: #64748b; }
  .closing { color: #94a3b8; margin-top: 1.8rem; line-height: 1.6; }
  .closing b { color: #e2e8f0; }
  .cta { margin-top: 1.2rem; color: #3b82f6; text-decoration: none; font-weight: 600; }
  .cta:hover { text-decoration: underline; }
</style>
