<script>
  // Global chrome on every page: the sticky brand banner (top) + the attribution footer (bottom).
  let { children } = $props();
</script>

<a class="banner" href="/historia">¿Puede la <strong>IA</strong> ganar quinielas?</a>

{@render children()}

<footer class="site-footer">
  <p>Powered by <span class="aid">Artificial Intelligence Developments</span> © 2026</p>
</footer>

<style>
  /* Inner sticky elements (Context date headers, historia rail) offset below the banner. */
  :global(:root) { --banner-h: 2.1rem; }

  .banner {
    position: sticky; top: 0; z-index: 50; display: block;
    background: #00063d; color: #9eff1f; text-decoration: none;
    text-align: center; font-size: 0.85rem; line-height: 1.25;
    padding: 0.42rem 1rem; font-family: 'Segoe UI', system-ui, sans-serif;
  }
  .banner:hover { background: #00084f; }
  .banner strong { font-weight: 800; }

  .site-footer { border-top: 1px solid #1e293b; padding: 2rem 1rem; }
  .site-footer p {
    text-align: center; margin: 0;
    font-size: 0.72rem; letter-spacing: 0.2em; text-transform: uppercase;
    color: #a3a3a3; font-family: 'Segoe UI', system-ui, sans-serif;
  }
  .aid { color: #dc2626; }
</style>
