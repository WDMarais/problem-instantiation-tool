"""
Mixed half-exam: Gr10 quadratics + trig graph properties.

Compose by listing (problem_id, count) pairs in EXAM_MIX.
Problems are shuffled so same-type questions don't cluster.

Usage (from project root):
    .venv/bin/python content/examples/exam.py
    .venv/bin/python content/examples/exam.py --seed 7 --output revision.html
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

# ── exam composition ──────────────────────────────────────────────────────────

EXAM_MIX: list[tuple[str, int]] = [
    ("monic_factorise", 2),
    ("factorise_enumerate", 1),
    ("zero_product_standard", 2),
    ("trig_graph_range", 2),
    ("trig_graph_decreasing", 2),
    # trig_graph_solve omitted: R-form needs scaffolded decomposition first
    # (see memory: project-backlog-rethink-curriculum-pathing)
]

# ── generation ────────────────────────────────────────────────────────────────


def build_exam(seed: int | None = None, title: str = "Gr10 Practice Exam") -> str:
    engine = Engine(registry=InMemoryRegistry(REGISTRY))
    rng = random.Random(seed)
    cards = []
    for prob_id, count in EXAM_MIX:
        entry = PROBLEMS[prob_id]
        cards.extend(_generate_cards(engine, entry, rng, count, count))
    rng.shuffle(cards)
    return build_html(title, cards, per_page=2)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Generate a mixed Gr10 practice exam.")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--title", default="Gr10 Practice Exam")
    ap.add_argument("--output", default="exam.html")
    args = ap.parse_args()

    html = build_exam(seed=args.seed, title=args.title)
    Path(args.output).write_text(html, encoding="utf-8")
    total = sum(c for _, c in EXAM_MIX)
    print(f"Wrote {total} problems → {args.output}")
