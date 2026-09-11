"""
Acquisition-sheet print — ``content.renderers.a4``.

Each sheet is two fixed-size A4 pages (worked examples, then own work). What
these tests pin:

- a print comes out as exactly those two sheets: each ``.page`` is a full 297mm
  tall, so any page margin Chrome adds on top pushes it onto a second sheet and
  the printout doubles to four pages, one of them blank;
- everything fits: a ``.page`` clips its overflow, so too many problems (or maths
  too big) would silently lose the bottom of the page, and an over-wide
  expression would run into the next column.
"""

from __future__ import annotations

import html
import importlib
import json
import re
import shutil

import pytest

from content.renderers.a4 import build_html
from content.renderers.katex_static import _deno_bin
from worksheets.generate import _find_chrome, html_to_pdf, run_chrome
from worksheets.paper import _pdf_pages

_SHEETS = [
    "func_eval",
    "func_inverse",
    "linear_balance",
    "linear_collect",
    "linear_divide",
    "linear_multiply",
    "linear_shift",
    "linear_shift_divide",
    "linear_shift_multiply",
    "linear_shift_xdenom",
    "linear_xdenom",
]


def _have_print_tools() -> bool:
    try:
        _deno_bin()
    except RuntimeError:
        return False
    return bool(_find_chrome() and shutil.which("pdfinfo"))


def _sheet_html(name: str, seed: int) -> str:
    make_sheet = importlib.import_module(f"content.generators.{name}").make_sheet
    return build_html(make_sheet(seed=seed))


@pytest.mark.skipif(not _have_print_tools(), reason="needs Deno + Chrome + pdfinfo")
@pytest.mark.parametrize("name", _SHEETS)
def test_sheet_prints_on_two_a4_pages(tmp_path, name):
    page = tmp_path / f"{name}.html"
    page.write_text(_sheet_html(name, seed=1), encoding="utf-8")
    pdf = tmp_path / f"{name}.pdf"
    html_to_pdf(page, pdf)
    assert _pdf_pages(pdf) == 2


# Clipped pages, and blocks with anything visible past their right edge. KaTeX's
# visually-hidden MathML copy reports phantom boxes, so it's skipped.
_PROBE_JS = """
<script>
addEventListener('load', () => document.fonts.ready.then(() => {
  const hits = [];
  document.querySelectorAll('.page').forEach((p, i) => {
    const over = p.scrollHeight - p.clientHeight;
    if (over > 1) hits.push('page ' + (i + 1) + ' clipped by '
      + (over * 25.4 / 96).toFixed(1) + 'mm');
  });
  document.querySelectorAll(
    '.worked-ex, .collapsed-ex, .practice-item, .answer-entry'
  ).forEach(block => {
    const edge = block.getBoundingClientRect().right;
    let right = edge;
    block.querySelectorAll('*').forEach(e => {
      if (e.closest('.katex-mathml') || e.ownerSVGElement) return;
      const r = e.getBoundingClientRect();
      if (r.width && r.right > right) right = r.right;
    });
    if (right > edge + 0.5) hits.push(block.className + ' +'
      + ((right - edge) * 25.4 / 96).toFixed(1) + 'mm: '
      + block.textContent.replace(/\\s+/g, ' ').slice(0, 40));
  });
  const pre = document.createElement('pre');
  pre.id = 'FIT';
  pre.textContent = JSON.stringify(hits);
  document.body.append(pre);
}));
</script>
"""


def _misfits(tmp_path, page_html: str) -> list[str]:
    page = tmp_path / "fit.html"
    page.write_text(page_html.replace("</body>", _PROBE_JS + "</body>"), "utf-8")
    dom = run_chrome(
        ["--virtual-time-budget=5000", "--dump-dom", page.as_uri()],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    m = re.search(r'<pre id="FIT">(.*?)</pre>', dom, re.S)
    if m is None:
        raise RuntimeError("the fit probe never reported — did the page load?")
    return json.loads(html.unescape(m.group(1)))


@pytest.mark.skipif(not _have_print_tools(), reason="needs Deno + Chrome + pdfinfo")
@pytest.mark.parametrize("name", _SHEETS)
@pytest.mark.parametrize("seed", [1, 2, 3])
def test_sheet_content_fits_its_pages(tmp_path, name, seed):
    assert _misfits(tmp_path, _sheet_html(name, seed)) == []
