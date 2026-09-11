"""
Acquisition-sheet print — ``content.renderers.a4``.

Each sheet is two fixed-size A4 pages (worked examples, then own work). What
these tests pin is that a print comes out as exactly those two sheets: each
``.page`` is a full 297mm tall, so any page margin Chrome adds on top pushes it
onto a second sheet and the printout doubles to four pages, one of them blank.
"""

from __future__ import annotations

import importlib
import shutil

import pytest

from content.renderers.a4 import build_html
from content.renderers.katex_static import _deno_bin
from worksheets.generate import _find_chrome, html_to_pdf
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


@pytest.mark.skipif(not _have_print_tools(), reason="needs Deno + Chrome + pdfinfo")
@pytest.mark.parametrize("name", _SHEETS)
def test_sheet_prints_on_two_a4_pages(tmp_path, name):
    make_sheet = importlib.import_module(f"content.generators.{name}").make_sheet
    page = tmp_path / f"{name}.html"
    page.write_text(build_html(make_sheet(seed=1)), encoding="utf-8")
    pdf = tmp_path / f"{name}.pdf"
    html_to_pdf(page, pdf)
    assert _pdf_pages(pdf) == 2
