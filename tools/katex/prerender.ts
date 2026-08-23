// Static KaTeX rendering for the self-contained sheet pipeline.
//
// KaTeX is pinned in deno.json (npm:katex@0.16.11); this script is the only
// thing that touches it. Two modes:
//
//   deno run -A --config tools/katex/deno.json tools/katex/prerender.ts style
//       → prints the KaTeX stylesheet with every font inlined as a base64
//         woff2 data URI, wrapped in a <style> tag.
//
//   deno run ... prerender.ts render   (JSON [{tex, display}] on stdin)
//       → prints the rendered-HTML array (order preserved). A tex that fails
//         comes back as a "KaTeX FAIL:" marker so the Python caller can raise.
//
// createRequire resolves a real filesystem path into the Deno-materialised
// node_modules, so the CSS + fonts read with plain Deno.readFile — no unstable
// import attributes, no vendored assets.

import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import katex from "katex";

const require = createRequire(import.meta.url);
const distDir = dirname(require.resolve("katex"));

// woff2 first, then the woff/ttf alternatives up to ; or } — keep only woff2.
const FONT_SRC = /src:url\(fonts\/([^)]+\.woff2)\)\s*format\("woff2"\)[^;}]*/g;

function toBase64(bytes: Uint8Array): string {
  let bin = "";
  for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
  return btoa(bin);
}

async function emitStyle(): Promise<string> {
  const css = await Deno.readTextFile(join(distDir, "katex.min.css"));
  const names = new Set<string>();
  for (const m of css.matchAll(FONT_SRC)) names.add(m[1]);
  const b64 = new Map<string, string>();
  for (const name of names) {
    b64.set(name, toBase64(await Deno.readFile(join(distDir, "fonts", name))));
  }
  const inlined = css.replace(
    FONT_SRC,
    (_full, name) => `src:url(data:font/woff2;base64,${b64.get(name)}) format("woff2")`,
  );
  return `<style>${inlined}</style>`;
}

function renderJobs(jobs: { tex: string; display: boolean }[]): string[] {
  return jobs.map((j) => {
    try {
      return katex.renderToString(j.tex, {
        throwOnError: true,
        displayMode: j.display,
      });
    } catch (e) {
      return `KaTeX FAIL: ${j.tex} :: ${(e as Error).message}`;
    }
  });
}

const mode = Deno.args[0];
const enc = new TextEncoder();
if (mode === "style") {
  await Deno.stdout.write(enc.encode(await emitStyle()));
} else if (mode === "render") {
  const input = await new Response(Deno.stdin.readable).text();
  await Deno.stdout.write(enc.encode(JSON.stringify(renderJobs(JSON.parse(input)))));
} else {
  console.error("usage: prerender.ts style|render");
  Deno.exit(2);
}
