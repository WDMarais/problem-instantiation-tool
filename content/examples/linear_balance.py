#!/usr/bin/env python3
"""
Dense worked-example sheet: x ± a = 0 (zero RHS, balance method).

Prerequisites: none — this is the entry point for linear equation solving.

Usage:
    .venv/bin/python content/examples/linear_balance.py
    .venv/bin/python content/examples/linear_balance.py --output balance.html
"""

from __future__ import annotations

import argparse
from pathlib import Path

from content.renderers.a4 import build_html
from content.sheet import CollapsedEx, PracticeEx, SheetData, ThreeStep

_DATA = SheetData(
    title="x ± a = 0  —  Balance Method",
    caption=(
        "Principle: we add or subtract the same value on both sides to keep the "
        "equation balanced."
    ),
    output_name="linear_balance.html",
    detailed=[
        ThreeStep(r"x - 5 = 0", r"x - 5 + 5 = 0 + 5", r"x = 5"),
        ThreeStep(r"x + 6 = 0", r"x + 6 - 6 = 0 - 6", r"x = -6"),
        ThreeStep(r"x - 12 = 0", r"x - 12 + 12 = 0 + 12", r"x = 12"),
        ThreeStep(r"x + 8 = 0", r"x + 8 - 8 = 0 - 8", r"x = -8"),
        ThreeStep(
            r"x - \tfrac{1}{2} = 0",
            r"x - \tfrac{1}{2} + \tfrac{1}{2} = 0 + \tfrac{1}{2}",
            r"x = \tfrac{1}{2}",
        ),
        ThreeStep(
            r"x + \tfrac{3}{4} = 0",
            r"x + \tfrac{3}{4} - \tfrac{3}{4} = 0 - \tfrac{3}{4}",
            r"x = -\tfrac{3}{4}",
        ),
        ThreeStep(r"x - p = 0", r"x - p + p = 0 + p", r"x = p"),
        ThreeStep(r"x + k = 0", r"x + k - k = 0 - k", r"x = -k"),
    ],
    collapsed=[
        CollapsedEx(r"x - 3 = 0", r"x = 3"),
        CollapsedEx(r"x + 7 = 0", r"x = -7"),
        CollapsedEx(r"x + 2 = 0", r"x = -2"),
        CollapsedEx(r"x - 9 = 0", r"x = 9"),
        CollapsedEx(r"x - \tfrac{1}{3} = 0", r"x = \tfrac{1}{3}"),
        CollapsedEx(r"x + \tfrac{2}{5} = 0", r"x = -\tfrac{2}{5}"),
        CollapsedEx(r"x - \tfrac{5}{6} = 0", r"x = \tfrac{5}{6}"),
        CollapsedEx(r"x + \tfrac{1}{4} = 0", r"x = -\tfrac{1}{4}"),
        CollapsedEx(r"x - m = 0", r"x = m"),
        CollapsedEx(r"x + n = 0", r"x = -n"),
        CollapsedEx(r"x - \alpha = 0", r"x = \alpha"),
        CollapsedEx(r"x + q = 0", r"x = -q"),
    ],
    practice=[
        PracticeEx(r"x - 4 = 0", r"x = 4"),
        PracticeEx(r"x + 3 = 0", None),
        PracticeEx(r"x + 8 = 0", r"x = -8"),
        PracticeEx(r"x - 1 = 0", None),
        PracticeEx(r"x - 7 = 0", r"x = 7"),
        PracticeEx(r"x + 5 = 0", None),
        PracticeEx(r"x + \tfrac{1}{2} = 0", r"x = -\tfrac{1}{2}"),
        PracticeEx(r"x - \tfrac{3}{4} = 0", None),
        PracticeEx(r"x - \tfrac{2}{3} = 0", r"x = \tfrac{2}{3}"),
        PracticeEx(r"x + \tfrac{5}{8} = 0", None),
        PracticeEx(r"x - r = 0", r"x = r"),
        PracticeEx(r"x + t = 0", None),
        PracticeEx(r"x + \beta = 0", r"x = -\beta"),
        PracticeEx(r"x - \lambda = 0", None),
        PracticeEx(r"x + 11 = 0", r"x = -11"),
        PracticeEx(r"x - \tfrac{2}{5} = 0", None),
    ],
)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Generate x±a=0 balance method sheet.")
    ap.add_argument("--output", default=_DATA.output_name)
    args = ap.parse_args()
    Path(args.output).write_text(build_html(_DATA), encoding="utf-8")
    print(f"Wrote → {args.output}")
