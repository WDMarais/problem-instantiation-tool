#!/usr/bin/env python3
"""
Dense worked-example sheet: a/x = b (x in the denominator).

Key move: multiply both sides by x. x clears from the denominator,
leaving a = bx — then divide (the known x/a=b form).

Four steps (not three): equation → ×x on both sides → a=bx (intermediate) → result.
The intermediate step is styled lighter — it's a known form, not a new idea.

Prerequisites: linear_multiply.py (x/a=b) — student has already multiplied
both sides by p, r, m; x follows the same rule.

Usage:
    .venv/bin/python content/examples/linear_xdenom.py
    .venv/bin/python content/examples/linear_xdenom.py --output xdenom.html
"""

from __future__ import annotations

import argparse
from pathlib import Path

from content.renderers.a4 import build_html
from content.sheet import CollapsedEx, FourStep, PracticeEx, SheetData

_DATA = SheetData(
    title="a / x = b  —  Multiply Both Sides by x",
    caption=(
        "In the previous sheet you multiplied both sides by p, r, m — x follows the same rule. "
        "Multiplying by x clears it from the denominator, leaving a = bx. "
        "You then solve that as before: divide both sides by b."
    ),
    output_name="linear_xdenom.html",
    detailed=[
        FourStep(
            r"\tfrac{5}{x} = 2",
            r"\tfrac{5}{x} \times x = 2 \times x",
            r"5 = 2x",
            r"x = \tfrac{5}{2}",
        ),
        FourStep(
            r"\tfrac{6}{x} = 3",
            r"\tfrac{6}{x} \times x = 3 \times x",
            r"6 = 3x",
            r"x = 2",
        ),
        FourStep(
            r"\tfrac{6}{x} = \tfrac{3}{4}",
            r"\tfrac{6}{x} \times x = \tfrac{3}{4} \times x",
            r"6 = \tfrac{3x}{4}",
            r"x = 8",
        ),
        FourStep(
            r"\tfrac{1}{x} = \tfrac{1}{5}",
            r"\tfrac{1}{x} \times x = \tfrac{1}{5} \times x",
            r"1 = \tfrac{x}{5}",
            r"x = 5",
        ),
        FourStep(
            r"\tfrac{a}{x} = b",
            r"\tfrac{a}{x} \times x = b \times x",
            r"a = bx",
            r"x = \tfrac{a}{b}",
        ),
        FourStep(
            r"\tfrac{p}{x} = \tfrac{q}{r}",
            r"\tfrac{p}{x} \times x = \tfrac{q}{r} \times x",
            r"p = \tfrac{qx}{r}",
            r"x = \tfrac{pr}{q}",
        ),
    ],
    collapsed=[
        CollapsedEx(r"\tfrac{4}{x} = 2", r"x = 2"),
        CollapsedEx(r"\tfrac{9}{x} = 3", r"x = 3"),
        CollapsedEx(r"\tfrac{7}{x} = 2", r"x = \tfrac{7}{2}"),
        CollapsedEx(r"\tfrac{8}{x} = 5", r"x = \tfrac{8}{5}"),
        CollapsedEx(r"\tfrac{2}{x} = \tfrac{1}{3}", r"x = 6"),
        CollapsedEx(r"\tfrac{5}{x} = \tfrac{2}{3}", r"x = \tfrac{15}{2}"),
        CollapsedEx(r"\tfrac{k}{x} = m", r"x = \tfrac{k}{m}"),
        CollapsedEx(r"\tfrac{a}{x} = \tfrac{1}{b}", r"x = ab"),
        CollapsedEx(r"\tfrac{c}{x} = \tfrac{d}{e}", r"x = \tfrac{ce}{d}"),
        CollapsedEx(r"\tfrac{n}{x} = n", r"x = 1"),
        CollapsedEx(r"\tfrac{p}{x} = \tfrac{p}{q}", r"x = q"),
        CollapsedEx(r"\tfrac{ab}{x} = c", r"x = \tfrac{ab}{c}"),
    ],
    practice=[
        PracticeEx(r"\tfrac{4}{x} = 2", r"x = 2"),
        PracticeEx(r"\tfrac{10}{x} = 5", None),
        PracticeEx(r"\tfrac{7}{x} = 3", r"x = \tfrac{7}{3}"),
        PracticeEx(r"\tfrac{9}{x} = 6", None),
        PracticeEx(r"\tfrac{5}{x} = \tfrac{1}{2}", r"x = 10"),
        PracticeEx(r"\tfrac{3}{x} = \tfrac{3}{4}", None),
        PracticeEx(r"\tfrac{a}{x} = 5", r"x = \tfrac{a}{5}"),
        PracticeEx(r"\tfrac{k}{x} = m", None),
        PracticeEx(r"\tfrac{p}{x} = \tfrac{1}{q}", r"x = pq"),
        PracticeEx(r"\tfrac{c}{x} = \tfrac{d}{e}", None),
        PracticeEx(r"\tfrac{6}{x} = \tfrac{3}{4}", r"x = 8"),
        PracticeEx(r"\tfrac{n}{x} = n", None),
        PracticeEx(r"\tfrac{1}{x} = \tfrac{1}{7}", r"x = 7"),
        PracticeEx(r"\tfrac{r}{x} = \tfrac{s}{t}", None),
        PracticeEx(r"\tfrac{8}{x} = 5", r"x = \tfrac{8}{5}"),
        PracticeEx(r"\tfrac{ab}{x} = c", None),
    ],
)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Generate a/x=b worked-example sheet.")
    ap.add_argument("--output", default=_DATA.output_name)
    args = ap.parse_args()
    Path(args.output).write_text(build_html(_DATA), encoding="utf-8")
    print(f"Wrote → {args.output}")
