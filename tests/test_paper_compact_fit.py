"""
Compact print fit — ``worksheets.paper``.

Chrome's print silently scales the whole page down when any element is wider than
the text column, so one over-wide display block shrinks every page of that paper
without a word. These tests lay the compact student copy out at the A5 text-column
width and fail, naming the slot, if anything sticks out.

The layout is screen media, not print: headless Chrome can only dump a screen
layout. So the print rules (base + compact) are unwrapped from their ``@media print``
blocks and applied directly, with the body pinned to the column width.
"""

from __future__ import annotations

import html
import json
import re
import subprocess

import pytest

from content.renderers.katex_static import _deno_bin
from worksheets.generate import _find_chrome
from worksheets.paper import (
    _COMPACT_MARGINS_MM,
    _COMPACT_PAGE_WIDTH_MM,
    _PAPER_CSS,
    PAPERS,
    _compact_print_css,
    _html_document,
    _paper_body,
    build_paper,
)

# page width minus the right (notes) and left margins
_COLUMN_MM = _COMPACT_PAGE_WIDTH_MM - _COMPACT_MARGINS_MM[1] - _COMPACT_MARGINS_MM[3]

# Per block, the furthest right edge of anything visible, past the column edge.
# KaTeX's visually-hidden MathML copy and the inner parts of SVGs (clipped stretchy
# glyphs) report huge phantom boxes, so they're skipped; an SVG's root still counts.
_PROBE_JS = """
<script>
addEventListener('load', () => document.fonts.ready.then(() => {
  const W = document.body.getBoundingClientRect().right;
  const hits = [];
  document.querySelectorAll('.paper-header, .q-head, .slot').forEach(block => {
    let right = W;
    block.querySelectorAll('*').forEach(e => {
      if (e.closest('.katex-mathml') || e.ownerSVGElement) return;
      const r = e.getBoundingClientRect();
      if (r.width && r.right > right) right = r.right;
    });
    if (right > W + 0.5) {
      const num = block.querySelector('.slot-num');
      const where = num ? num.textContent
        : block.classList.contains('slot') ? 'stem of ' + block.closest('section').id
        : block.className;
      hits.push(where + ' +' + ((right - W) * 25.4 / 96).toFixed(1) + 'mm');
    }
  });
  const pre = document.createElement('pre');
  pre.id = 'FIT';
  pre.textContent = JSON.stringify(hits);
  document.body.append(pre);
}));
</script>
"""


def _have_tools() -> bool:
    try:
        _deno_bin()
    except RuntimeError:
        return False
    return _find_chrome() is not None


_needs_tools = pytest.mark.skipif(not _have_tools(), reason="needs Deno + Chrome")


def _print_rules(css: str) -> str:
    """The contents of every ``@media print { … }`` block in *css*, unwrapped."""
    out: list[str] = []
    i = 0
    while (start := css.find("@media print", i)) != -1:
        j = css.index("{", start) + 1
        body_start, depth = j, 1
        while depth:
            depth += {"{": 1, "}": -1}.get(css[j], 0)
            j += 1
        out.append(css[body_start : j - 1])
        i = j
    return "\n".join(out)


def _overflows(tmp_path, body: str, compact_css: str) -> list[str]:
    """Lay *body* out at the compact column width; the blocks that overflow it,
    as ``"<slot> +<mm>"``."""
    css = (
        _print_rules(_PAPER_CSS)
        + _print_rules(compact_css)
        + f"body {{ width: {_COLUMN_MM}mm; }}"
    )
    page = tmp_path / "fit.html"
    page.write_text(
        _html_document("fit probe", body, script=_PROBE_JS, extra_css=css),
        encoding="utf-8",
    )
    dom = subprocess.run(
        [
            _find_chrome(),
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            "--virtual-time-budget=5000",
            "--dump-dom",
            page.as_uri(),
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    m = re.search(r'<pre id="FIT">(.*?)</pre>', dom, re.S)
    if m is None:
        raise RuntimeError("the fit probe never reported — did the page load?")
    return json.loads(html.unescape(m.group(1)))


@_needs_tools
@pytest.mark.parametrize("paper", ["2025_mj_p1", "2025_mj_p2"])
# P2 seeds 4, 5 and 58 draw three-factor 5.2 quotients, the widest seen
@pytest.mark.parametrize("seed", [1, 4, 5, 58])
def test_compact_student_copy_fits_the_a5_column(tmp_path, paper, seed):
    spec = PAPERS[paper]
    body = _paper_body(spec, build_paper(spec, seed=seed), seed=seed)
    hits = _overflows(tmp_path, body, _compact_print_css(seed))
    assert hits == [], f"wider than the {_COLUMN_MM}mm column: {hits}"


@_needs_tools
def test_probe_catches_an_over_wide_display(tmp_path):
    wide = " + ".join(f"x_{{{i}}}" for i in range(40))
    body = (
        '<div class="doc"><div class="slot"><span class="slot-num">9.9</span>'
        f'<div class="slot-content"><div class="slot-eq">$${wide}$$</div></div>'
        "</div></div>"
    )
    hits = _overflows(tmp_path, body, _compact_print_css(1))
    assert len(hits) == 1 and hits[0].startswith("9.9 +")
