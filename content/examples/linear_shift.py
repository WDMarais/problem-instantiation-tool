#!/usr/bin/env python3
"""
Acquisition sheet: x ± a = b (non-zero RHS).

Prerequisites: linear_balance.py (x±a=0).

Usage:
    .venv/bin/python content/examples/linear_shift.py
    .venv/bin/python content/examples/linear_shift.py --output shift.html
    .venv/bin/python content/examples/linear_shift.py --seed 42 --kinds integer fraction
"""

from __future__ import annotations

import argparse
from pathlib import Path

from content.generators import Kind
from content.generators.linear_shift import make_sheet
from content.renderers.a4 import build_html

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Generate x±a=b non-zero RHS sheet.")
    ap.add_argument("--output", default="linear_shift.html")
    ap.add_argument(
        "--seed", type=int, default=None, help="RNG seed for reproducibility"
    )
    ap.add_argument(
        "--kinds",
        nargs="+",
        choices=["integer", "fraction", "symbol"],
        default=None,
        metavar="KIND",
        help="Problem kinds to include (default: all three)",
    )
    args = ap.parse_args()

    kinds = frozenset(Kind(k) for k in args.kinds) if args.kinds else frozenset(Kind)
    sheet = make_sheet(kinds, seed=args.seed)
    Path(args.output).write_text(build_html(sheet), encoding="utf-8")
    print(f"Wrote → {args.output}")
