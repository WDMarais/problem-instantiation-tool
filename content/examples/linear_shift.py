#!/usr/bin/env python3
"""
Dense worked-example sheet: x ± a = b (non-zero RHS).

Prerequisites: linear_balance.py (x±a=0) — student can already do x ± a = 0.

New challenge: the RHS is not zero, so subtracting a leaves b on the right
(not 0). The student must carry b through: x + a = b → x = b − a.

Important cases covered:
  - b < a: result is negative — students often panic here
  - negative b: x − a = −c is common in practice
  - fraction arithmetic: result requires adding/subtracting fractions

Usage:
    .venv/bin/python content/examples/linear_shift.py
    .venv/bin/python content/examples/linear_shift.py --output shift.html
"""

from __future__ import annotations

import argparse
from pathlib import Path

from content.renderers.a4 import build_html
from content.sheet import CollapsedEx, PracticeEx, SheetData, ThreeStep

_DATA = SheetData(
    title="x ± a = b  —  Non-Zero Right-Hand Side",
    caption=(
        "The 3 does not simply disappear from the left and reappear as $-3$ on the right. "
        "You subtract 3 from both sides: on the left it cancels to zero; "
        "on the right, 7 becomes $7 - 3 = 4$. "
        "The right-hand side is always affected too."
    ),
    output_name="linear_shift.html",
    detailed=[
        ThreeStep(r"x + 3 = 7", r"x + 3 - 3 = 7 - 3", r"x = 4"),
        ThreeStep(r"x - 5 = 2", r"x - 5 + 5 = 2 + 5", r"x = 7"),
        ThreeStep(r"x + 8 = 3", r"x + 8 - 8 = 3 - 8", r"x = -5"),
        ThreeStep(r"x - 2 = -6", r"x - 2 + 2 = -6 + 2", r"x = -4"),
        ThreeStep(
            r"x + \tfrac{1}{2} = \tfrac{3}{4}",
            r"x + \tfrac{1}{2} - \tfrac{1}{2} = \tfrac{3}{4} - \tfrac{1}{2}",
            r"x = \tfrac{1}{4}",
        ),
        ThreeStep(
            r"x - \tfrac{1}{3} = \tfrac{1}{6}",
            r"x - \tfrac{1}{3} + \tfrac{1}{3} = \tfrac{1}{6} + \tfrac{1}{3}",
            r"x = \tfrac{1}{2}",
        ),
        ThreeStep(r"x + a = b", r"x + a - a = b - a", r"x = b - a"),
        ThreeStep(r"x - p = q", r"x - p + p = q + p", r"x = p + q"),
    ],
    collapsed=[
        CollapsedEx(r"x + 4 = 9", r"x = 5"),
        CollapsedEx(r"x - 3 = 8", r"x = 11"),
        CollapsedEx(r"x + 7 = 2", r"x = -5"),
        CollapsedEx(r"x - 6 = -2", r"x = 4"),
        CollapsedEx(r"x + 10 = 4", r"x = -6"),
        CollapsedEx(r"x - 9 = -5", r"x = 4"),
        CollapsedEx(r"x + \tfrac{1}{4} = \tfrac{3}{4}", r"x = \tfrac{1}{2}"),
        CollapsedEx(r"x - \tfrac{2}{3} = \tfrac{1}{3}", r"x = 1"),
        CollapsedEx(r"x + a = b", r"x = b - a"),
        CollapsedEx(r"x - m = n", r"x = m + n"),
        CollapsedEx(r"x + p = q", r"x = q - p"),
        CollapsedEx(r"x - r = s", r"x = r + s"),
    ],
    practice=[
        PracticeEx(r"x + 5 = 9", r"x = 4"),
        PracticeEx(r"x - 3 = 7", None),
        PracticeEx(r"x + 6 = 2", r"x = -4"),
        PracticeEx(r"x - 4 = -1", None),
        PracticeEx(r"x + 9 = 4", r"x = -5"),
        PracticeEx(r"x - 8 = 5", None),
        PracticeEx(r"x + \tfrac{1}{2} = \tfrac{3}{2}", r"x = 1"),
        PracticeEx(r"x - \tfrac{1}{4} = \tfrac{3}{4}", None),
        PracticeEx(r"x + \tfrac{2}{3} = \tfrac{1}{3}", r"x = -\tfrac{1}{3}"),
        PracticeEx(r"x - \tfrac{1}{6} = \tfrac{5}{6}", None),
        PracticeEx(r"x + a = 2b", r"x = 2b - a"),
        PracticeEx(r"x - m = n + 1", None),
        PracticeEx(r"x + p = q", r"x = q - p"),
        PracticeEx(r"x - r = s", None),
        PracticeEx(r"x + 7 = -3", r"x = -10"),
        PracticeEx(r"x - k = j", None),
    ],
)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Generate x±a=b non-zero RHS sheet.")
    ap.add_argument("--output", default=_DATA.output_name)
    args = ap.parse_args()
    Path(args.output).write_text(build_html(_DATA), encoding="utf-8")
    print(f"Wrote → {args.output}")
