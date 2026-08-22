"""
Functions & Graphs — ``exponential_from_graph``.

Determine the equation of an exponential graph from a sketch that labels its
horizontal asymptote (``y = q``), its y-intercept ``(0, y0)`` and one neighbour
``(1, y1)``. The student reads the asymptote for ``q``, the y-intercept for
``a = y0 - q`` (since ``a·b^0 = a``), and the neighbour for ``b = (y1 - q)/a``,
then states ``y = a·b^x + q``. Graded on the full expression
(``symbolic_equality``, 3 marks: q, a, b).

**Forward read-off, so wire-only (no F1 gate).** The asymptote fixes ``q``; the
y-intercept fixes ``a``; the neighbour fixes ``b``. Because ``a != 0`` the base
``b`` is always recoverable, and ``a != 0`` also keeps the y-intercept off the
asymptote — no draw is ill-posed, so gating would be tautological (sharpened F1
rule: forward read-off → wire-only). Same class as ``hyperbola_from_graph``.

Display-only (see ``render/DESIGN.md``): the generator bakes the whole equation;
the sketch is drawn *from* the baked asymptote, coefficient, base and points.
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

_x = sympy.Symbol("x")


def _gen(rng: random.Random) -> dict:
    # q != 0 keeps the asymptote off the x-axis (a distinct dashed line on the
    # sketch). b in {2, 3}: a genuine growth/decay base, never the constant b = 1.
    a = rng.choice([-3, -2, -1, 1, 2, 3])
    b = rng.choice([2, 3])
    q = rng.choice([-3, -2, -1, 1, 2, 3])

    y0 = a + q  # f(0) = a·b^0 + q = a + q
    y1 = a * b + q  # f(1) = a·b + q

    answer = a * sympy.Integer(b) ** _x + q  # y = a·b^x + q

    return {
        "a": a,
        "b": b,
        "q": q,
        "y_intercept": y0,
        "point_x": 1,
        "point_y": y1,
        "answer": answer,  # graded by symbolic_equality
    }


exponential_from_graph = Problem(
    id="exponential_from_graph",
    type_id="exponential_from_graph",
    name="Determine the equation of an exponential graph from its sketch",
    artifact_type="practice",
    problem_spec=_gen,
    verifier_spec={
        "kind": "symbolic_equality",
        "marks_possible": 3,  # read asymptote (q) + y-intercept (a) + neighbour (b)
        "param_key": "answer",
    },
    corpus_anchor=CorpusAnchor(
        paper="2025 May/June P1",
        question="4.4",  # determine-the-equation (exponential) item
        marks=3,
    ),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(
        registry=InMemoryRegistry({exponential_from_graph.id: exponential_from_graph})
    )

    def show(label, inst, expr):
        attempt = SolutionAttempt(steps=[SubmittedStep(expr)])
        r = inst.verifier.rate(attempt)
        print(f"  {label}: {r.marks_awarded}/{r.marks_possible}  ok={r.is_correct}")

    for seed in (1, 7, 13):
        inst = engine.instantiate(exponential_from_graph.id, seed=seed)
        pm = inst.params
        print(f"=== seed {seed} ===")
        print(
            f"  a={pm['a']} b={pm['b']} q={pm['q']}   "
            f"y-int (0,{pm['y_intercept']})  point (1,{pm['point_y']})"
        )
        print(f"  answer: y = {sympy.latex(pm['answer'])}")
        show("Correct        ", inst, pm["answer"])
        # wrong base (assumed b = 2): correct only when b really is 2
        show("Assumed b = 2  ", inst, pm["a"] * sympy.Integer(2) ** _x + pm["q"])
