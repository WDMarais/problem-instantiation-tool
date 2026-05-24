#!/usr/bin/env python3
"""
Acquisition sheet: a/x ± b = 0 (shift, multiply by x, divide).

Prerequisites: linear_balance.py (x±a=0), linear_xdenom.py (a/x=b).

Usage:
    .venv/bin/python content/examples/linear_shift_xdenom.py
    .venv/bin/python content/examples/linear_shift_xdenom.py --seed 42 --kinds integer fraction
"""

from __future__ import annotations

import argparse
from pathlib import Path

from content.generators import Kind
from content.generators.linear_shift_xdenom import make_sheet
from content.renderers.a4 import build_html

if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Generate a/x±b=0 shift-multiply-divide sheet."
    )
    ap.add_argument("--output", default="linear_shift_xdenom.html")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument(
        "--kinds",
        nargs="+",
        choices=["integer", "fraction", "symbol"],
        default=None,
        metavar="KIND",
    )
    args = ap.parse_args()

    kinds = frozenset(Kind(k) for k in args.kinds) if args.kinds else frozenset(Kind)
    sheet = make_sheet(kinds, seed=args.seed)
    Path(args.output).write_text(build_html(sheet), encoding="utf-8")
    print(f"Wrote → {args.output}")
