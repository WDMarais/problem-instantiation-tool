"""
Static KaTeX rendering — turn ``$…$`` / ``$$…$$`` math into pre-rendered HTML
so a sheet is fully self-contained (no CDN, no client-side JS, no external
fonts). This is what makes the printable / emailable artifact robust offline.

All KaTeX work is delegated to ``tools/katex/prerender.ts`` (run under Deno),
which is the single place that touches KaTeX — pinned in ``tools/katex/deno.json``
as ``npm:katex@0.16.11``. Nothing is vendored or committed; Deno resolves the
pinned package into a gitignored ``node_modules`` on first run.

Two entry points:

- :func:`inline_style` — the KaTeX stylesheet with every font embedded as a
  base64 ``woff2`` data URI, wrapped in ``<style>``. Drop into ``<head>`` in
  place of the CDN ``<link>``/``<script>`` block.
- :func:`prerender_body` — replace each math span in a body HTML string with
  static KaTeX markup, rendered in one Deno call.

A tex string that fails to parse raises :class:`KatexRenderError` — the build
is loud rather than silently shipping a broken glyph (project house rule).
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from functools import lru_cache
from html import unescape as _unescape
from pathlib import Path

_TOOL = Path(__file__).resolve().parents[2] / "tools" / "katex"
_CONFIG = _TOOL / "deno.json"
_SCRIPT = _TOOL / "prerender.ts"

# One combined pass: ``$$…$$`` (display, group 1) or ``$…$`` (inline, group 2).
# Display is tried first so a display span is never mis-split as two inline ones.
_MATH = re.compile(r"\$\$(.+?)\$\$|\$(.+?)\$", re.DOTALL)


class KatexRenderError(RuntimeError):
    """A math span failed to render under the pinned KaTeX."""


@lru_cache(maxsize=1)
def _deno_bin() -> str:
    exe = shutil.which("deno") or str(Path.home() / ".deno" / "bin" / "deno")
    if not Path(exe).exists():
        raise RuntimeError(
            "deno not found — install it (https://deno.land) to render sheets; "
            "the static KaTeX pipeline runs under Deno (see tools/katex/)."
        )
    return exe


def _deno(mode: str, stdin: str | None = None) -> str:
    proc = subprocess.run(
        [_deno_bin(), "run", "-A", "--config", str(_CONFIG), str(_SCRIPT), mode],
        input=stdin,
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout


@lru_cache(maxsize=1)
def inline_style() -> str:
    """The KaTeX CSS with fonts inlined as base64 woff2, as a ``<style>`` tag."""
    return _deno("style")


def prerender_body(html: str) -> str:
    """Replace every ``$…$`` / ``$$…$$`` span in *html* with static KaTeX.

    Math is collected in document order, rendered in one Deno call, then
    substituted back. KaTeX output contains no ``$``, so the display pass never
    collides with the inline pass.
    """
    jobs: list[dict] = []

    def _collect(m: re.Match[str]) -> str:
        # Content is authored with HTML-escaped math bodies (``<``/``>``/``&`` →
        # entities, so a raw ``<`` isn't eaten by the HTML parser). KaTeX wants the
        # real characters (``<`` is a relation, ``&`` an array separator), so decode
        # the entities back before rendering. KaTeX's own output is proper HTML.
        if m.group(1) is not None:
            jobs.append({"tex": _unescape(m.group(1)), "display": True})
        else:
            jobs.append({"tex": _unescape(m.group(2)), "display": False})
        return m.group(0)

    _MATH.sub(_collect, html)
    if not jobs:
        return html

    rendered = json.loads(_deno("render", stdin=json.dumps(jobs)))
    for job, out in zip(jobs, rendered):
        if out.startswith("KaTeX FAIL:"):
            raise KatexRenderError(f"{out}  (tex: {job['tex']!r})")

    it = iter(rendered)
    return _MATH.sub(lambda _m: next(it), html)
