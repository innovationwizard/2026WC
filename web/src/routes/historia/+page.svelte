<script>
  // Narrative scrollytelling — /historia. Self-narrating 3-act story of the WC2026 model.
  // Real data only (matches.json + narrative.json). See NARRATIVE_BUILD_PROGRESS.md.
  import { onMount } from 'svelte';
  import Scrolly from '$lib/components/Scrolly.svelte';
  import MathPill from '$lib/components/MathPill.svelte';
  import Calibration from '$lib/components/Calibration.svelte';
  import DiceRoller from '$lib/components/narrative/DiceRoller.svelte';
  import MatchupExplorer from '$lib/components/narrative/MatchupExplorer.svelte';
  import CoverageSlider from '$lib/components/narrative/CoverageSlider.svelte';
  import { teamShort, teamFlag } from '$lib/teams.js';

  let { data } = $props();

  // ── ACT 1 · Azar — Monte Carlo champion histogram (real dist, client-side sampling) ──
  const allTeams = $derived(data.knockout.map((t) => ({ team: t.team, p: t.champion })));
  const total = $derived(allTeams.reduce((s, t) => s + t.p, 0) || 1);
  const display = $derived([...allTeams].sort((a, b) => b.p - a.p).slice(0, 8).map((t) => t.team));
  function mulberry32(a) {
    return function () {
      a |= 0; a = (a + 0x6d2b79f5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function simulate(teams, tot, N) {
    const r = mulberry32(42), c = {};
    for (let i = 0; i < N; i++) {
      let x = r() * tot, acc = 0, pick = teams.at(-1).team;
      for (const t of teams) { acc += t.p; if (x <= acc) { pick = t.team; break; } }
      c[pick] = (c[pick] || 0) + 1;
    }
    return c;
  }
  const NS = [1, 16, 500, 10000];
  const act1 = [
    { text: 'La máquina arranca sabiendo una sola cosa con certeza: las reglas. 48 equipos, 104 partidos, un formato.' },
    { text: 'Pero es ciega. No distingue a España de Arabia Saudita. Lo único que sabe hacer es tirar los dados.' },
    { text: 'Entonces juega el torneo completo, una y otra vez. Cada simulación corona a un campeón distinto.' },
    { text: 'Apile diez mil torneos y emerge una forma: una distribución. Ancha, honesta, todavía sin saber de fútbol.' },
  ];
  let a1 = $state(0);
  const simN = $derived(NS[Math.min(a1, NS.length - 1)]);
  const sim = $derived(simulate(allTeams, total, simN));
  const leader = $derived(Object.entries(sim).sort((x, y) => y[1] - x[1])[0]?.[0]);

  // ── ACT 2 · Red Neuronal — independent agreement + measured skill ──
  const c3 = $derived(data.narrative.champion_3way ?? []);
  const rps = $derived(data.narrative.backtest?.rps ?? {});
  const nBacktest = $derived(data.narrative.backtest?.n_matches ?? 1267);
  const maxC = $derived(Math.max(0.01, ...c3.map((t) => Math.max(t.M1, t.M2))));
  const act2 = [
    { mode: 'champ', text: 'Ahora le damos ojos. Una red neuronal aprende de 48 variables por equipo: forma, fuerza, valor del plantel, historia.' },
    { mode: 'champ', text: 'Construida desde cero, sin decirle qué responder, llega sola al mismo podio que Opta y las casas de apuestas: España y Francia arriba, Inglaterra cerca.' },
    { mode: 'rps', text: 'Pero, ¿acierta o solo suena bien? La única prueba honesta: predecir partidos que el modelo nunca vio.' },
    { mode: 'rps', text: 'Su error —el RPS, donde más bajo es mejor— le gana al Elo puro en 1 267 partidos de prueba. No es opinión; es un cálculo matemático estricto.' },
  ];
  let a2 = $state(0);
  const a2mode = $derived(act2[Math.min(a2, act2.length - 1)].mode);
  const rpsBar = (v) => Math.max(4, ((0.18 - v) / (0.18 - 0.16)) * 100); // longer = lower error = better (zoomed 0.16–0.18)

  // ── ACT 3 · Conjunto — honest uncertainty ──
  const calib = $derived(data.narrative.calibration ?? []);
  const setOf = (n) => data.matches.find((m) => m.predictions.M3?.set?.length === n);
  const confExamples = $derived([setOf(1), setOf(2), setOf(3)].filter(Boolean));
  const setLabel = (m) => {
    const s = m.predictions.M3.set;
    if (s.length === 3) return 'cualquier resultado';
    const name = (o) => (o === 'home' ? teamShort(m.home) : o === 'away' ? teamShort(m.away) : 'Empate');
    return s.map(name).join(' o ');
  };
  const act3 = [
    { mode: 'set', text: 'El modelo más sofisticado no es el que más afirma, sino el que sabe lo que NO sabe y lo reconoce con transparencia.' },
    { mode: 'set', text: 'Predicción conformal: en lugar de un número solo, un conjunto de resultados plausibles con cobertura garantizada. Cuanto más confiable es la predicción, más pequeño es el conjunto.' },
    { mode: 'calib', text: '¿Y está bien calibrado? Cuando dice 70%, ¿ocurre el 70%? La curva cae sobre la diagonal: sí.' },
    { mode: 'calib', text: 'Una verdad incómoda para el final: una curva más angosta NO sería un mejor modelo. El fútbol es así de impredecible. La honestidad ES la sofisticación.' },
  ];
  let a3 = $state(0);
  const a3mode = $derived(act3[Math.min(a3, act3.length - 1)].mode);

  // ── Finale: the honest leaderboard (real champion odds) ──
  const podium = $derived([...data.knockout].sort((a, b) => b.champion - a.champion).slice(0, 5));

  // ── Progress-rail tracking + text-only autoplay ──
  let currentAct = $state(0);
  let playing = $state(false);
  let raf;
  function tick() {
    if (!playing) return;
    window.scrollBy(0, 1.4); // ~84 px/s — reading cadence; hands-off for the video / a cold link
    if (window.scrollY + window.innerHeight >= document.body.scrollHeight - 2) { playing = false; return; }
    raf = requestAnimationFrame(tick);
  }
  function togglePlay() {
    playing = !playing;
    if (playing) raf = requestAnimationFrame(tick); else cancelAnimationFrame(raf);
  }
  onMount(() => {
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (e.isIntersecting) currentAct = +(e.target.getAttribute('data-act') || 0);
        }
      },
      { rootMargin: '-45% 0px -45% 0px' }
    );
    document.querySelectorAll('[data-act]').forEach((s) => io.observe(s));
    const pause = () => { if (playing) { playing = false; cancelAnimationFrame(raf); } };
    window.addEventListener('wheel', pause, { passive: true });
    window.addEventListener('touchstart', pause, { passive: true });
    return () => { io.disconnect(); window.removeEventListener('wheel', pause); window.removeEventListener('touchstart', pause); };
  });
</script>

<svelte:head>
  <title>¿Quién gana el Mundial? · Cómo se construye una predicción</title>
</svelte:head>

<nav class="rail" aria-hidden="true">
  <span class:on={currentAct === 1}>01 · Azar</span>
  <span class:on={currentAct === 2}>02 · Red Neuronal</span>
  <span class:on={currentAct === 3}>03 · Conjunto</span>
</nav>

<button class="autoplay" onclick={togglePlay} aria-pressed={playing}>
  {playing ? '⏸ Pausar' : '▶ Reproducir solo'}
</button>

<main class="historia">
  <section class="hero" data-act="0">
    <p class="kicker">Mundial 2026</p>
    <h1>¿Quién gana<br />el Mundial?</h1>
    <p class="sub">Y, sobre todo, ¿<em>cómo</em> podría usted saberlo?</p>
    <div class="scroll-cue" aria-hidden="true">
      <svg viewBox="0 0 24 24" width="40" height="40" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9l6 6 6-6" /></svg>
    </div>
  </section>

  <!-- ════ ACT 1 ════ -->
  <section class="act" data-act="1">
    <header class="act-head"><p class="phase">Modelo 1 · Azar</p><h2>La máquina ciega</h2></header>
    <Scrolly steps={act1} bind:active={a1}>
      {#snippet visual()}
        <div class="sim">
          <div class="sim-head">{simN.toLocaleString('es')} {simN === 1 ? 'torneo simulado' : 'torneos simulados'}</div>
          <div class="bars">
            {#each display as team}
              {@const pct = (sim[team] || 0) / simN}
              <div class="bar-row">
                <span class="bt"><span class="flag">{teamFlag(team)}</span>{teamShort(team)}</span>
                <span class="track"><span class="fill slate" style="width:{Math.max(pct * 100, 0)}%"></span></span>
                <span class="bp">{(pct * 100).toFixed(pct < 0.1 ? 1 : 0)}%</span>
              </div>
            {/each}
          </div>
          {#if simN <= 16 && leader}<p class="cap">Esta vez ganó: <b>{teamShort(leader)}</b></p>{/if}
        </div>
      {/snippet}
      {#snippet stepBody(step)}{step.text}{/snippet}
    </Scrolly>
    <div class="sandbox"><p class="sand-label">🎲 Tírelo usted</p><DiceRoller matches={data.matches} /></div>
    <MathPill>
      <p><b>Modelo 1 (Azar).</b> Cada partido: los goles son <span class="f">G<sub>A</sub> ~ Poisson(λ<sub>A</sub>)</span>, <span class="f">G<sub>B</sub> ~ Poisson(λ<sub>B</sub>)</span>, independientes. Los <span class="f">λ</span> vienen del Elo: <span class="f">p<sub>A</sub> = (1 + 10<sup>−(E<sub>A</sub>−E<sub>B</sub>)/400</sup>)<sup>−1</sup></span>, <span class="f">λ<sub>A</sub> = ḡ·(0,5 + p<sub>A</sub>)</span>, con <span class="f">ḡ = 1,35</span>. Monte Carlo: se simula el torneo <span class="f">N = 10 000</span> veces; <span class="f">P(campeón) = victorias ⁄ N</span>. La incertidumbre ancha no es un defecto: es la varianza de Poisson más el azar del cuadro.</p>
    </MathPill>
  </section>

  <!-- ════ ACT 2 ════ -->
  <section class="act" data-act="2">
    <header class="act-head"><p class="phase">Modelo 2 · Red Neuronal</p><h2>Ahora puede ver</h2></header>
    <Scrolly steps={act2} bind:active={a2}>
      {#snippet visual()}
        {#if a2mode === 'champ'}
          <div class="sim">
            <div class="sim-head">Probabilidad de campeón</div>
            <div class="legend"><span class="k slate"></span>Elo (M1) <span class="k blue"></span>Red (M2)</div>
            <div class="bars">
              {#each c3.slice(0, 6) as t}
                <div class="bar2">
                  <span class="bt">{teamShort(t.team)}</span>
                  <div class="stack">
                    <span class="track"><span class="fill slate" style="width:{(t.M1 / maxC) * 100}%"></span></span>
                    <span class="track"><span class="fill blue" style="width:{(t.M2 / maxC) * 100}%"></span></span>
                  </div>
                  <span class="bp">{Math.round(t.M2 * 100)}%</span>
                </div>
              {/each}
            </div>
          </div>
        {:else}
          <div class="sim">
            <div class="sim-head">Error de predicción · RPS <span class="muted">(más bajo = mejor)</span></div>
            <div class="bars">
              {#each [['M1', 'Elo', 'slate'], ['M2', 'Red neuronal', 'blue'], ['M3', 'Conjunto', 'green']] as [k, name, col]}
                <div class="bar-row rps">
                  <span class="bt">{name}</span>
                  <span class="track"><span class="fill {col}" style="width:{rpsBar(rps[k] ?? 0.18)}%"></span></span>
                  <span class="bp">{(rps[k] ?? 0).toFixed(3)}</span>
                </div>
              {/each}
            </div>
            <p class="cap">{nBacktest.toLocaleString('es')} partidos que el modelo nunca vio · eje ampliado 0,16–0,18</p>
          </div>
        {/if}
      {/snippet}
      {#snippet stepBody(step)}{step.text}{/snippet}
    </Scrolly>
    <div class="sandbox"><p class="sand-label">Explore cualquier partido</p><MatchupExplorer matches={data.matches} /></div>
    <MathPill>
      <p><b>Modelo 2 (Red Neuronal).</b> Regresión de Poisson neuronal: la red predice <span class="f">λ = softplus(f<sub>θ</sub>(x))</span> desde 48 variables, entrenada con la log-verosimilitud de Poisson <span class="f">ℒ = λ − y·log λ</span>. <i>Ensemble</i> de <span class="f">M = 50</span> redes: <span class="f">λ̄ = (1⁄M) Σ<sub>m</sub> λ<sup>(m)</sup></span> (cancela el ruido de entrenamiento). Resultado por convolución: <span class="f">P(local) = Σ<sub>i&gt;j</sub> P(G<sub>A</sub>=i)·P(G<sub>B</sub>=j)</span>. Validación fuera de muestra con el RPS <span class="f">= (1⁄(r−1)) Σ<sub>i</sub> (Σ<sub>j≤i</sub>(p<sub>j</sub>−o<sub>j</sub>))²</span>: <b>0,162</b> contra <b>0,175</b> del Elo en {nBacktest.toLocaleString('es')} partidos no vistos.</p>
    </MathPill>
  </section>

  <!-- ════ ACT 3 ════ -->
  <section class="act" data-act="3">
    <header class="act-head"><p class="phase">Modelo 3 · Conjunto</p><h2>Y sabe lo que no sabe</h2></header>
    <Scrolly steps={act3} bind:active={a3}>
      {#snippet visual()}
        {#if a3mode === 'set'}
          <div class="sim">
            <div class="sim-head">Conjuntos plausibles · 80% de confianza</div>
            <div class="sets">
              {#each confExamples as m}
                <div class="set-row">
                  <span class="match">{teamShort(m.home)} vs {teamShort(m.away)}</span>
                  <span class="set" class:wide={m.predictions.M3.set.length === 3}>{setLabel(m)}</span>
                </div>
              {/each}
            </div>
            <p class="cap">Un favorito claro deja un solo resultado; un partido parejo, los tres.</p>
          </div>
        {:else}
          <div class="sim calib-wrap">
            <Calibration points={calib} />
            <p class="cap">Cuando el modelo dice <b>p</b>, ocurre ≈ <b>p</b>. La curva (verde) sigue la diagonal.</p>
          </div>
        {/if}
      {/snippet}
      {#snippet stepBody(step)}{step.text}{/snippet}
    </Scrolly>
    <div class="sandbox"><p class="sand-label">¿Qué tan seguro debería estar?</p><CoverageSlider matches={data.matches} tau={data.narrative.tau_by_coverage ?? {}} /></div>
    <MathPill>
      <p><b>Modelo 3 (Conjunto).</b> Mezcla de dos familias: <span class="f">λ<sub>M3</sub> = w·λ<sub>red</sub> + (1−w)·λ<sub>gbt</sub></span>, con <span class="f">w = 0,5</span> elegido por <i>backtest</i> (RPS 0,162, gana a ambas). Predicción <i>conformal</i> (LAC): con scores de no-conformidad <span class="f">s<sub>i</sub> = 1 − p<sub>i</sub>[real]</span> en calibración, el conjunto <span class="f">{'{'} o : p<sub>o</sub> ≥ 1 − q̂ {'}'}</span> tiene cobertura <span class="f">≥ 1 − α</span> garantizada (solo asume intercambiabilidad). La banda del campeón es <i>bootstrap</i> sobre las simulaciones — no puede llegar a ser una garantía, porque <span class="f">n = 1</span>.</p>
    </MathPill>
  </section>

  <!-- ════ FINALE ════ -->
  <section class="finale" data-act="3">
    <p class="phase">El veredicto honesto</p>
    <h2>Quién gana el Mundial</h2>
    <ol class="podium">
      {#each podium as t, i}
        <li><span class="rk">{i + 1}</span><span class="pteam"><span class="flag">{teamFlag(t.team)}</span>{teamShort(t.team)}</span><span class="pp">{(t.champion * 100).toFixed(1)}%</span></li>
      {/each}
    </ol>
    <p class="closing">Ningún número fue ingresado a mano ni sesgado a la fuerza. <br /> Cada cifra se obtuvo entrenando los modelos con datos históricos crudos y comprobando en partidos que el modelo nunca vio.</p>
    <a class="cta" href="/">Ver el marcador en vivo →</a>
  </section>
</main>

<style>
  :global(body) { margin: 0; background: #0a0e17; }
  .historia { color: #e2e8f0; font-family: 'Segoe UI', system-ui, sans-serif; }

  .rail { position: fixed; top: var(--banner-h); left: 0; right: 0; z-index: 10; display: flex; gap: 1.25rem; justify-content: center; padding: 0.5rem; font-size: 0.72rem; letter-spacing: 0.05em; background: #0a0e17cc; backdrop-filter: blur(6px); border-bottom: 1px solid #1e293b; color: #475569; }
  .rail .on { color: #d4af37; }

  .autoplay { position: fixed; bottom: 1.25rem; right: 1.25rem; z-index: 11; background: #111827cc; backdrop-filter: blur(6px); border: 1px solid #334155; color: #e2e8f0; padding: 0.5rem 0.9rem; border-radius: 999px; cursor: pointer; font-family: inherit; font-size: 0.8rem; font-weight: 600; }
  .autoplay:hover { border-color: #d4af37; }

  .hero { position: relative; box-sizing: border-box; height: calc(100vh - var(--banner-h)); height: calc(100svh - var(--banner-h)); display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; gap: 0.6rem; padding: 1rem 2rem 11vh; }
  .kicker { color: #d4af37; letter-spacing: 0.2em; text-transform: uppercase; font-size: 0.8rem; margin: 0; }
  h1 { font-size: clamp(2.6rem, 9vw, 5.5rem); line-height: 1.03; margin: 0.4rem 0 0; font-weight: 800; letter-spacing: -0.02em; }
  .sub { font-size: clamp(1.1rem, 3vw, 1.6rem); color: #94a3b8; margin: 0.6rem 0 0; }
  .sub em { color: #e2e8f0; font-style: italic; }
  .scroll-cue { position: absolute; bottom: 1.6rem; color: #475569; line-height: 0; animation: cue 2.2s ease-in-out infinite; }
  @keyframes cue {
    0%, 100% { opacity: 0.3; transform: translateY(0); filter: drop-shadow(0 0 0 rgba(212, 175, 55, 0)); }
    50% { opacity: 0.85; transform: translateY(5px); filter: drop-shadow(0 0 7px rgba(212, 175, 55, 0.5)); }
  }
  @media (prefers-reduced-motion: reduce) { .scroll-cue { animation: none; opacity: 0.5; } }

  .act { max-width: 1100px; margin: 0 auto; padding: 0 1.25rem 2rem; }
  .act-head { padding: 4rem 0 0; }
  .phase { color: #64748b; letter-spacing: 0.15em; text-transform: uppercase; font-size: 0.75rem; margin: 0; }
  .act-head h2 { font-size: clamp(1.8rem, 5vw, 3rem); margin: 0.3rem 0 0; }

  .sim { width: 100%; max-width: 470px; }
  .sim-head { color: #d4af37; font-variant-numeric: tabular-nums; font-size: 0.95rem; margin-bottom: 0.9rem; text-align: center; }
  .sim-head .muted { color: #64748b; font-size: 0.8rem; }
  .legend { display: flex; gap: 0.75rem; justify-content: center; font-size: 0.72rem; color: #94a3b8; margin-bottom: 0.7rem; }
  .k { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 0.25rem; vertical-align: middle; }
  .bars { display: flex; flex-direction: column; gap: 0.45rem; }
  .bar-row { display: grid; grid-template-columns: 7.5rem 1fr 2.8rem; align-items: center; gap: 0.5rem; font-size: 0.85rem; }
  .bar-row.rps { grid-template-columns: 6.5rem 1fr 3rem; }
  .bar2 { display: grid; grid-template-columns: 5rem 1fr 2.6rem; align-items: center; gap: 0.5rem; font-size: 0.85rem; }
  .stack { display: flex; flex-direction: column; gap: 3px; }
  .bt { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: #cbd5e1; }
  .flag { margin-right: 0.3rem; }
  .track { height: 12px; background: #0f172a; border-radius: 3px; overflow: hidden; }
  .bar2 .track { height: 9px; }
  .fill { display: block; height: 100%; border-radius: 3px; transition: width 0.5s ease; }
  .fill.slate { background: #64748b; } .fill.blue { background: #3b82f6; } .fill.green { background: #22c55e; }
  .k.slate { background: #64748b; } .k.blue { background: #3b82f6; }
  .bp { text-align: right; font-variant-numeric: tabular-nums; color: #94a3b8; }
  .cap { text-align: center; color: #94a3b8; margin-top: 0.9rem; font-size: 0.85rem; }
  .cap b { color: #e2e8f0; }

  .sets { display: flex; flex-direction: column; gap: 0.6rem; }
  .set-row { display: flex; justify-content: space-between; align-items: center; gap: 1rem; background: #0f172a; border-left: 3px solid #22c55e; border-radius: 4px; padding: 0.55rem 0.8rem; }
  .match { color: #cbd5e1; font-size: 0.9rem; }
  .set { color: #22c55e; font-weight: 600; font-size: 0.9rem; text-align: right; }
  .set.wide { color: #94a3b8; font-weight: 400; font-style: italic; }
  .calib-wrap { display: flex; flex-direction: column; align-items: center; }

  .sandbox { max-width: 520px; margin: 1.5rem auto 0; padding: 1.25rem; background: #0d1424; border: 1px solid #1e293b; border-radius: 10px; }
  .sand-label { text-align: center; color: #d4af37; font-size: 0.8rem; letter-spacing: 0.05em; margin: 0 0 0.9rem; }

  .finale { min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; gap: 0.5rem; padding: 2rem; max-width: 620px; margin: 0 auto; }
  .finale h2 { font-size: clamp(1.8rem, 5vw, 3rem); margin: 0.2rem 0 1rem; }
  .podium { list-style: none; padding: 0; margin: 0; width: 100%; max-width: 360px; display: flex; flex-direction: column; gap: 0.4rem; }
  .podium li { display: grid; grid-template-columns: 1.5rem 1fr auto; align-items: center; gap: 0.6rem; background: #111827; border: 1px solid #1e293b; border-radius: 6px; padding: 0.5rem 0.8rem; }
  .podium .rk { color: #d4af37; font-weight: 700; }
  .pteam { text-align: left; font-weight: 600; }
  .pp { color: #d4af37; font-variant-numeric: tabular-nums; font-weight: 700; }
  .closing { color: #94a3b8; margin-top: 1.5rem; line-height: 1.55; }
  .cta { margin-top: 1rem; color: #3b82f6; text-decoration: none; font-weight: 600; }
  .cta:hover { text-decoration: underline; }
</style>
