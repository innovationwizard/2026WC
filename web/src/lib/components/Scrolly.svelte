<script>
  // Sticky-stepper engine — the core scrollytelling mechanic.
  // A pinned visual stays on screen while narrated text steps scroll past; each step,
  // as it reaches center, sets `active` so the visual can morph. Scroll = the play button.
  //
  // Usage:
  //   <Scrolly {steps} bind:active {visual} {stepBody} />
  //   {#snippet visual(active)} ...reacts to active... {/snippet}
  //   {#snippet stepBody(step, i)} <p>{step.text}</p> {/snippet}
  import scrollama from 'scrollama';
  import { onMount } from 'svelte';

  let { steps = [], active = $bindable(0), visual, stepBody, offset = 0.6 } = $props();

  let container;

  onMount(() => {
    const scroller = scrollama();
    scroller
      .setup({ step: container.querySelectorAll('.step'), offset, progress: false })
      .onStepEnter(({ index }) => { active = index; });
    const onResize = () => scroller.resize();
    window.addEventListener('resize', onResize);
    return () => { scroller.destroy(); window.removeEventListener('resize', onResize); };
  });
</script>

<div class="scrolly" bind:this={container}>
  <div class="sticky">
    {@render visual(active)}
  </div>
  <div class="steps">
    {#each steps as step, i}
      <div class="step" class:on={i === active}>
        <div class="card">{@render stepBody(step, i)}</div>
      </div>
    {/each}
  </div>
</div>

<style>
  .scrolly { position: relative; display: grid; grid-template-columns: 1.1fr 0.9fr; gap: 2rem; }
  .sticky {
    position: sticky; top: 0; height: 100vh;
    display: flex; align-items: center; justify-content: center;
    grid-column: 1; /* visual on the left */
  }
  .steps { grid-column: 2; }
  .step {
    min-height: 85vh; display: flex; align-items: center;
    opacity: 0.25; transition: opacity 0.35s ease;
  }
  .step.on { opacity: 1; }
  .step:first-child { min-height: 60vh; }
  .step:last-child { min-height: 70vh; }
  .card {
    background: #111827cc; border: 1px solid #1e293b; border-left: 3px solid #d4af37;
    border-radius: 8px; padding: 1.1rem 1.25rem; backdrop-filter: blur(4px);
    font-size: 1.05rem; line-height: 1.5; color: #e2e8f0;
  }

  /* Phones: visual pins to the TOP, steps scroll underneath it. */
  @media (max-width: 800px) {
    .scrolly { grid-template-columns: 1fr; gap: 0; }
    .sticky { grid-column: 1; height: 56vh; top: 0; z-index: 2; background: #0a0e17; }
    .steps { grid-column: 1; }
    .step { min-height: 70vh; }
    .card { font-size: 1rem; }
  }
</style>
