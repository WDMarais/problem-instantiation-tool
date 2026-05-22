"""
Quadratics tutorial worksheet: scaffolded skill chain, pedagogical order.

Problems appear in skill-chain order — no shuffle. Each section drills one
link before the next, so a student can see exactly where the chain breaks.

Skill chain:
  1  zero_product_atomic      (×3)  sign-flip rule — single factor
  2  zero_product_standard    (×2)  zero-product rule — two factors
  3  factorise_constraints    (×2)  read mn and m+n from x² + bx + c
  4  factorise_sign_case      (×1)  MCQ: sign case for m and n
  5  factorise_enumerate      (×2)  enumerate factor pairs → find m, n
  6  monic_factorise          (×3)  integrate all: factorise + solve

Usage (from project root):
    .venv/bin/python content/examples/quadratics_tutorial.py
    .venv/bin/python content/examples/quadratics_tutorial.py --seed 3 --output quad_tut.html
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from worksheets.generate import PROBLEMS, REGISTRY, _generate_cards, build_html

TUTORIAL_SEQUENCE: list[tuple[str, int]] = [
    ("zero_product_atomic", 3),
    ("zero_product_standard", 2),
    ("factorise_constraints", 2),
    ("factorise_sign_case", 1),
    ("factorise_enumerate", 2),
    ("monic_factorise", 3),
]


def build_tutorial(
    seed: int | None = None,
    title: str = "Quadratics: Skill by Skill",
) -> str:
    engine = Engine(registry=InMemoryRegistry(REGISTRY))
    rng = random.Random(seed)
    cards = []
    for prob_id, count in TUTORIAL_SEQUENCE:
        entry = PROBLEMS[prob_id]
        # detail="full" for all (long_count == count): tutorial favours full worked steps
        cards.extend(_generate_cards(engine, entry, rng, count, count))
    # No shuffle — preserve pedagogical order
    return build_html(title, cards, per_page=3)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Generate a quadratics tutorial worksheet."
    )
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--title", default="Quadratics: Skill by Skill")
    ap.add_argument("--output", default="quadratics_tutorial.html")
    args = ap.parse_args()

    html = build_tutorial(seed=args.seed, title=args.title)
    Path(args.output).write_text(html, encoding="utf-8")
    total = sum(c for _, c in TUTORIAL_SEQUENCE)
    print(f"Wrote {total} problems → {args.output}")
