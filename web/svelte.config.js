import adapter from '@sveltejs/adapter-vercel';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
  preprocess: vitePreprocess(),
  kit: {
    // Deploy target: Vercel. Every route is prerendered (see +layout.js),
    // so the output is fully static — no serverless functions, cheapest tier.
    // On Vercel: Project → Settings → Root Directory = "web"
    // (no need to move the app to the repo root).
    adapter: adapter()
  }
};

export default config;
