#!/usr/bin/env python3
"""
Acquisition sheet: ax = b (divide both sides).

Prerequisites: linear_balance.py (x±a=0), linear_shift.py (x±a=b).

Usage:
    .venv/bin/python content/examples/linear_divide.py
    .venv/bin/python content/examples/linear_divide.py --seed 42 --kinds integer fraction
"""

from __future__ import annotations

import argparse
from pathlib import Path

from content.generators import Kind
from content.generators.linear_divide import make_sheet
from content.renderers.a4 import build_html

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Generate ax=b divide-both-sides sheet.")
    ap.add_argument("--output", default="linear_divide.html")
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
