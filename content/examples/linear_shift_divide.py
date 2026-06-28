#!/usr/bin/env python3
"""
Acquisition sheet: ax ± b = 0 (shift then divide).

Prerequisites: linear_balance.py (x±a=0), linear_divide.py (ax=b).

Usage:
    .venv/bin/python content/examples/linear_shift_divide.py
    .venv/bin/python content/examples/linear_shift_divide.py --seed 42
        --kinds integer fraction
"""

from __future__ import annotations

import argparse
from pathlib import Path

from content.generators import Kind
from content.generators.linear_shift_divide import make_sheet
from content.renderers.a4 import build_html

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Generate ax±b=0 shift-then-divide sheet.")
    ap.add_argument("--output", default="linear_shift_divide.html")
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
