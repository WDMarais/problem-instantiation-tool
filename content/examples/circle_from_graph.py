"""
Analytic Geometry — ``circle_from_graph``.

Determine the equation of a circle from a sketch that labels its centre ``(a, b)``
and one point ``(x0, y0)`` on it. The student reads the centre off the sketch,
computes ``r^2 = (x0 - a)^2 + (y0 - b)^2`` (the distance formula, squared, so no
surd is needed), and states ``(x - a)^2 + (y - b)^2 = r^2``. Graded on the equation
written as its "= 0" side (``symbolic_equality``, 3 marks: centre, r², form).

**Forward read-off, so wire-only (no F1 gate).** A centre and one point on the
circle fix it uniquely; the point sits at a nonzero integer offset from the centre,
so ``r^2 > 0`` and the radius is a genuine solve. No draw is ill-posed, so gating
would be tautological (sharpened F1 rule: forward read-off → wire-only). Same class
as the four function determine-the-equation items.

Display-only (see ``render/DESIGN.md``): the generator bakes the whole equation;
the sketch is drawn *from* the baked centre, radius and point.
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

_x, _y = sympy.symbols("x y")


def _gen(rng: random.Random) -> dict:
    # centre off both axes (a distinct labelled point); the point sits a nonzero
    # integer offset away, so r² = dx² + dy² is a positive integer (no surd in the
    # stated equation — the radius solve stays exact).
    a = rng.choice([-2, -1, 1, 2])
    b = rng.choice([-2, -1, 1, 2])
    dx = rng.choice([-3, -2, -1, 1, 2, 3])
    dy = rng.choice([-3, -2, -1, 1, 2, 3])

    x0, y0 = a + dx, b + dy
    r2 = dx * dx + dy * dy  # radius squared (integer)

    answer = (_x - a) ** 2 + (_y - b) ** 2 - r2  # "= 0" side of the equation

    return {
        "a": a,
        "b": b,
        "radius_sq": r2,
        "point_x": x0,
        "point_y": y0,
        "answer": answer,  # graded by symbolic_equality
    }


circle_from_graph = Problem(
    id="circle_from_graph",
    type_id="circle_from_graph",
    name="Determine the equation of a circle from its graph",
    artifact_type="practice",
    problem_spec=_gen,
    verifier_spec={
        "kind": "symbolic_equality",
        "marks_possible": 3,  # read centre (a, b) + compute r² + state the form
        "param_key": "answer",
    },
    corpus_anchor=CorpusAnchor(
        paper="2025 May/June P2",
        question="3.1",  # determine-the-equation (circle) item
        marks=3,
    ),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(
        registry=InMemoryRegistry({circle_from_graph.id: circle_from_graph})
    )

    def show(label, inst, expr):
        attempt = SolutionAttempt(steps=[SubmittedStep(expr)])
        r = inst.verifier.rate(attempt)
        print(f"  {label}: {r.marks_awarded}/{r.marks_possible}  ok={r.is_correct}")

    for seed in (1, 7, 13):
        inst = engine.instantiate(circle_from_graph.id, seed=seed)
        pm = inst.params
        print(f"=== seed {seed} ===")
        print(
            f"  centre ({pm['a']},{pm['b']})  r²={pm['radius_sq']}   "
            f"point ({pm['point_x']},{pm['point_y']})"
        )
        print(f"  answer (= 0): {sympy.latex(pm['answer'])}")
        show("Correct        ", inst, pm["answer"])
        # expanded form: symbolic_equality should still accept it
        show("Expanded       ", inst, sympy.expand(pm["answer"]))
        # forgot to subtract r² (left the '= 0' side as the raw squares)
        forgot = (_x - pm["a"]) ** 2 + (_y - pm["b"]) ** 2
        show("Forgot r²      ", inst, forgot)
