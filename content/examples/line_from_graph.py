"""
Functions & Graphs — ``line_from_graph``.

Determine the equation of a straight line from a sketch that labels two points on
it. The student reads the gradient ``m = (y2 - y1)/(x2 - x1)`` off the two points,
substitutes one point to pin the y-intercept ``c``, then states ``y = mx + c``.
Graded on the full expression (``symbolic_equality``, 3 marks: gradient, sub, form).

**Forward read-off, so wire-only (no F1 gate).** Two labelled points with distinct
x fix a unique non-vertical line; ``m != 0`` keeps it genuinely sloped and the two
points off the y-axis mean the student computes ``c`` (it is not just handed over
as a y-intercept). No draw is ill-posed, so gating would be tautological (sharpened
F1 rule: forward read-off → wire-only). Same class as ``hyperbola_from_graph`` and
``exponential_from_graph``.

Display-only (see ``render/DESIGN.md``): the generator bakes the whole equation;
the sketch is drawn *from* the baked gradient, intercept and points.
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

_x = sympy.Symbol("x")


def _gen(rng: random.Random) -> dict:
    # m != 0: a genuinely sloped line. c != 0 keeps the y-intercept off the origin
    # (a distinct labelled tick). Two distinct integer xs, both off the y-axis, so
    # the student must actually solve for c rather than read it straight off.
    m = rng.choice([-3, -2, -1, 1, 2, 3])
    c = rng.choice([-4, -3, -2, -1, 1, 2, 3, 4])
    x1, x2 = sorted(rng.sample([-3, -2, -1, 1, 2, 3], 2))

    y1, y2 = m * x1 + c, m * x2 + c  # lattice points (m, x integer ⇒ y integer)

    answer = m * _x + c  # y = mx + c

    return {
        "m": m,
        "c": c,
        "point1_x": x1,
        "point1_y": y1,
        "point2_x": x2,
        "point2_y": y2,
        "answer": answer,  # graded by symbolic_equality
    }


line_from_graph = Problem(
    id="line_from_graph",
    type_id="line_from_graph",
    name="Determine the equation of a straight line from its graph",
    artifact_type="practice",
    problem_spec=_gen,
    verifier_spec={
        "kind": "symbolic_equality",
        "marks_possible": 3,  # gradient (m) + substitute for c + state the form
        "param_key": "answer",
    },
    corpus_anchor=CorpusAnchor(
        paper="2025 May/June P1",
        question="4.1",  # determine-the-equation (straight line) item
        marks=3,
    ),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(registry=InMemoryRegistry({line_from_graph.id: line_from_graph}))

    def show(label, inst, expr):
        attempt = SolutionAttempt(steps=[SubmittedStep(expr)])
        r = inst.verifier.rate(attempt)
        print(f"  {label}: {r.marks_awarded}/{r.marks_possible}  ok={r.is_correct}")

    for seed in (1, 7, 13):
        inst = engine.instantiate(line_from_graph.id, seed=seed)
        pm = inst.params
        print(f"=== seed {seed} ===")
        print(
            f"  m={pm['m']} c={pm['c']}   "
            f"({pm['point1_x']},{pm['point1_y']})  ({pm['point2_x']},{pm['point2_y']})"
        )
        print(f"  answer: y = {sympy.latex(pm['answer'])}")
        show("Correct         ", inst, pm["answer"])
        # sign-flipped gradient through point 1: never the baked line (m != 0)
        wrong = -pm["m"] * _x + (pm["point1_y"] + pm["m"] * pm["point1_x"])
        show("Flipped gradient", inst, wrong)
