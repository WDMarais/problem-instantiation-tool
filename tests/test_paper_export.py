"""
Class-set export — ``worksheets.paper``.

A printed class set is N distinct papers (one per seed) plus their memos. What
makes it usable on paper, and what these tests pin:

- every seeded paper and memo carries a printed **paper ID** (the seed), so a
  student's paper can be matched to its memo and regenerated with ``--seed``;
- the student copy carries no memo and the marker copy no questions;
- in the combined PDFs every paper is padded to an even page count, so a duplex
  print never starts one student's paper on the back of another's.
"""

from __future__ import annotations

import re
import shutil
import subprocess

import pytest

from content.renderers.katex_static import _deno_bin
from worksheets.generate import _find_chrome
from worksheets.paper import (
    PAPERS,
    _masthead_html,
    _memo_body,
    _paper_body,
    _pdf_pages,
    build_paper,
    export_class_set,
)

_P1 = PAPERS["2025_mj_p1"]


# --- printed paper ID --------------------------------------------------------


def test_seeded_masthead_prints_paper_id_and_name_line():
    head = _masthead_html(_P1, seed=7)
    assert "Paper #0007" in head
    assert "Name:" in head


def test_unseeded_masthead_has_no_id():
    assert "Paper #" not in _masthead_html(_P1)


def test_marker_masthead_carries_id_but_no_name_line():
    head = _masthead_html(_P1, seed=7, name_line=False)
    assert "Paper #0007" in head
    assert "Name:" not in head


# --- student copy vs marker copy ---------------------------------------------


def test_student_copy_has_questions_but_no_memo():
    body = _paper_body(_P1, build_paper(_P1, seed=7), seed=7)
    assert 'id="q1"' in body and 'id="q11"' in body
    assert 'id="memo"' not in body
    assert "Paper #0007" in body


def test_marker_copy_has_memo_but_no_questions():
    body = _memo_body(_P1, build_paper(_P1, seed=7), seed=7)
    assert 'id="memo"' in body and "Marking Memorandum" in body
    assert 'id="q1"' not in body
    assert "Paper #0007" in body


# --- class set ---------------------------------------------------------------


def test_class_set_rejects_duplicate_seeds(tmp_path):
    with pytest.raises(ValueError, match="distinct"):
        export_class_set(_P1, [3, 3], tmp_path)


def test_class_set_rejects_empty(tmp_path):
    with pytest.raises(ValueError, match="at least one"):
        export_class_set(_P1, [], tmp_path)


def _have_print_tools() -> bool:
    try:
        _deno_bin()
    except RuntimeError:
        return False
    return bool(_find_chrome() and shutil.which("mutool") and shutil.which("pdfinfo"))


def _repair_warnings(pdf) -> list[str]:
    """Lines where mutool had to repair *pdf* on open (e.g. a broken xref table,
    as pdfunite writes). A print-ready file opens clean."""
    res = subprocess.run(["mutool", "info", str(pdf)], capture_output=True, text=True)
    return [ln for ln in res.stderr.splitlines() if "repair" in ln or "broken" in ln]


@pytest.mark.skipif(
    not _have_print_tools(), reason="needs Deno + Chrome + pdfinfo + mutool"
)
def test_class_set_writes_duplex_safe_combined_pdfs(tmp_path):
    seeds = [3, 4]
    export_class_set(_P1, seeds, tmp_path)
    for kind in ("paper", "memo"):
        singles = [tmp_path / f"{kind}s" / f"{kind}-{s:04d}.pdf" for s in seeds]
        assert all(p.exists() for p in singles)
        padded = sum(n + n % 2 for n in map(_pdf_pages, singles))
        # every paper padded to an even page count → combined = sum of padded
        assert _pdf_pages(tmp_path / f"{kind}s.pdf") == padded
        assert _repair_warnings(tmp_path / f"{kind}s.pdf") == []


def _page_size_name(pdf) -> str:
    """The paper size pdfinfo names for the first page, e.g. ``A5``."""
    out = subprocess.run(
        ["pdfinfo", str(pdf)], capture_output=True, text=True, check=True
    ).stdout
    m = re.search(r"^Page size:.*\((\w+)\)", out, re.MULTILINE)
    return m.group(1) if m else "?"


@pytest.mark.skipif(
    not _have_print_tools(), reason="needs Deno + Chrome + pdfinfo + mutool"
)
def test_compact_class_set_prints_a5_papers_padded_to_whole_sheets(tmp_path):
    seeds = [3, 4]
    export_class_set(_P1, seeds, tmp_path, compact=True)
    papers = [tmp_path / "papers" / f"paper-{s:04d}.pdf" for s in seeds]
    memos = [tmp_path / "memos" / f"memo-{s:04d}.pdf" for s in seeds]
    assert _page_size_name(papers[0]) == "A5"
    assert _page_size_name(memos[0]) == "A4"  # marker copies are unchanged
    # 2 A5 pages per side, duplex → 4 per sheet: each paper pads to a multiple of 4
    padded = sum(n + -n % 4 for n in map(_pdf_pages, papers))
    assert _pdf_pages(tmp_path / "papers.pdf") == padded
    assert _pdf_pages(tmp_path / "memos.pdf") == sum(
        n + n % 2 for n in map(_pdf_pages, memos)
    )
