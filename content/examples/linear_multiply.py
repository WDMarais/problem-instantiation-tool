#!/usr/bin/env python3
"""
Dense worked-example sheet: x/a = b (multiply both sides).

Scaffold: integers → fraction RHS → symbol divisor → symbol fraction
→ general form (ax/b = c/d) previewed in Section B only.

Prerequisites: linear_balance.py (x±a=0).

Usage:
    .venv/bin/python content/examples/linear_multiply.py
    .venv/bin/python content/examples/linear_multiply.py --output multiply.html
"""

from __future__ import annotations

import argparse
from pathlib import Path

from content.renderers.a4 import build_html
from content.sheet import CollapsedEx, PracticeEx, SheetData, ThreeStep

_DATA = SheetData(
    title="x / a = b  —  Multiply Both Sides",
    caption=(
        "Principle: multiply both sides by the same value to keep the equation balanced. "
        "Here we multiply by the denominator under x to leave x on its own."
    ),
    output_name="linear_multiply.html",
    detailed=[
        ThreeStep(
            r"\tfrac{x}{5} = 3",
            r"\tfrac{x}{5} \times 5 = 3 \times 5",
            r"x = 15",
        ),
        ThreeStep(
            r"\tfrac{x}{4} = 8",
            r"\tfrac{x}{4} \times 4 = 8 \times 4",
            r"x = 32",
        ),
        ThreeStep(
            r"\tfrac{x}{2} = \tfrac{3}{4}",
            r"\tfrac{x}{2} \times 2 = \tfrac{3}{4} \times 2",
            r"x = \tfrac{3}{2}",
        ),
        ThreeStep(
            r"\tfrac{x}{3} = \tfrac{1}{6}",
            r"\tfrac{x}{3} \times 3 = \tfrac{1}{6} \times 3",
            r"x = \tfrac{3}{6} = \tfrac{1}{2}",
        ),
        ThreeStep(
            r"\tfrac{x}{p} = q",
            r"\tfrac{x}{p} \times p = q \times p",
            r"x = pq",
        ),
        ThreeStep(
            r"\tfrac{x}{k} = 5",
            r"\tfrac{x}{k} \times k = 5 \times k",
            r"x = 5k",
        ),
        ThreeStep(
            r"\tfrac{x}{r} = \tfrac{1}{s}",
            r"\tfrac{x}{r} \times r = \tfrac{1}{s} \times r",
            r"x = \tfrac{r}{s}",
        ),
        ThreeStep(
            r"\tfrac{x}{m} = \tfrac{n}{t}",
            r"\tfrac{x}{m} \times m = \tfrac{n}{t} \times m",
            r"x = \tfrac{mn}{t}",
        ),
    ],
    collapsed=[
        CollapsedEx(r"\tfrac{x}{7} = 4", r"x = 28"),
        CollapsedEx(r"\tfrac{x}{9} = 3", r"x = 27"),
        CollapsedEx(r"\tfrac{x}{6} = \tfrac{1}{2}", r"x = 3"),
        CollapsedEx(r"\tfrac{x}{5} = \tfrac{2}{3}", r"x = \tfrac{10}{3}"),
        CollapsedEx(r"\tfrac{x}{a} = b", r"x = ab"),
        CollapsedEx(r"\tfrac{x}{n} = 7", r"x = 7n"),
        CollapsedEx(r"\tfrac{x}{c} = \tfrac{d}{e}", r"x = \tfrac{cd}{e}"),
        CollapsedEx(r"\tfrac{x}{p} = \tfrac{1}{q}", r"x = \tfrac{p}{q}"),
        CollapsedEx(r"\tfrac{2x}{3} = 4", r"x = 6"),
        CollapsedEx(r"\tfrac{3x}{5} = 6", r"x = 10"),
        CollapsedEx(r"\tfrac{ax}{b} = c", r"x = \tfrac{bc}{a}"),
        CollapsedEx(r"\tfrac{ax}{b} = \tfrac{c}{d}", r"x = \tfrac{bc}{ad}"),
    ],
    practice=[
        PracticeEx(r"\tfrac{x}{3} = 5", r"x = 15"),
        PracticeEx(r"\tfrac{x}{7} = 4", None),
        PracticeEx(r"\tfrac{x}{2} = \tfrac{1}{4}", r"x = \tfrac{1}{2}"),
        PracticeEx(r"\tfrac{x}{5} = \tfrac{3}{4}", None),
        PracticeEx(r"\tfrac{x}{8} = 3", r"x = 24"),
        PracticeEx(r"\tfrac{x}{6} = \tfrac{2}{3}", None),
        PracticeEx(r"\tfrac{x}{a} = 4", r"x = 4a"),
        PracticeEx(r"\tfrac{x}{n} = m", None),
        PracticeEx(r"\tfrac{x}{k} = \tfrac{1}{j}", r"x = \tfrac{k}{j}"),
        PracticeEx(r"\tfrac{x}{p} = \tfrac{q}{r}", None),
        PracticeEx(r"\tfrac{x}{12} = 7", r"x = 84"),
        PracticeEx(r"\tfrac{x}{a} = \tfrac{b}{c}", None),
        PracticeEx(r"\tfrac{x}{4} = \tfrac{5}{8}", r"x = \tfrac{5}{2}"),
        PracticeEx(r"\tfrac{x}{s} = \tfrac{t}{u}", None),
        PracticeEx(r"\tfrac{x}{11} = 3", r"x = 33"),
        PracticeEx(r"\tfrac{x}{m} = \tfrac{n}{p}", None),
    ],
)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Generate x/a=b multiply-both-sides sheet."
    )
    ap.add_argument("--output", default=_DATA.output_name)
    args = ap.parse_args()
    Path(args.output).write_text(
        build_html(_DATA, section_b_note="last four preview the next sheet"),
        encoding="utf-8",
    )
    print(f"Wrote → {args.output}")
