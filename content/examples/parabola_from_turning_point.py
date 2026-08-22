"""
Functions & Graphs — ``parabola_from_turning_point``.

Determine the equation of a parabola from a sketch that labels its **turning
point** ``(p, q)`` and its y-intercept ``(0, c)`` (the other major CAPS P1
determine-the-equation archetype; cf. ``parabola_from_graph``, which instead
labels the two x-intercepts). The student writes the vertex form
``a(x - p)^2 + q``, uses the y-intercept to pin the leading coefficient ``a``,
and expands. Graded on the expanded polynomial (``symbolic_equality``, 3 marks:
vertex form, solve a, expand).

**Forward read-off, so wire-only (no F1 gate).** The equation is fully pinned by
the labelled turning point and y-intercept. Because the vertex is off the y-axis
(``p != 0``) the y-intercept ``a·p² + q`` differs from ``q`` by ``a·p² != 0``, so
``a = (c - q) / p²`` is always recoverable and no draw makes the ask ill-posed —
gating would be tautological (sharpened F1 rule: forward read-off → wire-only).
Same class as ``parabola_from_graph`` and ``trig_graph_amplitude``.

Display-only (see ``render/DESIGN.md``): the generator bakes the whole equation;
the sketch is drawn *from* the baked vertex and coefficient, never measured.
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

_x = sympy.Symbol("x")


def _gen(rng: random.Random) -> dict:
    # p != 0 keeps the turning point off the y-axis, so the y-intercept
    # (a·p² + q) differs from q and `a` is always recoverable. Small |p|, |q|
    # keep the sketch window legible (a real viewport constraint).
    p = rng.choice([-3, -2, -1, 1, 2, 3])
    q = rng.choice([-4, -3, -2, -1, 1, 2, 3, 4])

    # a = 1 stays in play: the memo always runs the coefficient-pinning step
    # (f(0) = a·p² + q ⟹ a = …), so a = 1 is a value the student verifies from
    # the y-intercept, never one assumed by reading the vertex. Keeping it in also
    # stops the leading coefficient from silently signalling "never 1".
    a = rng.choice([-3, -2, -1, 1, 2, 3])

    answer = sympy.expand(a * (_x - p) ** 2 + q)
    y_intercept = a * p * p + q  # f(0), the coefficient-pinning point

    return {
        "a": a,
        "vertex_x": p,
        "vertex_y": q,
        "y_intercept": y_intercept,
        "answer": answer,  # expanded ax² + bx + c, graded by symbolic_equality
    }


parabola_from_turning_point = Problem(
    id="parabola_from_turning_point",
    type_id="parabola_from_turning_point",
    name="Determine the equation of a parabola from its sketch (turning point given)",
    artifact_type="practice",
    problem_spec=_gen,
    verifier_spec={
        "kind": "symbolic_equality",
        "marks_possible": 3,  # vertex form + solve for a + expand
        "param_key": "answer",
    },
    corpus_anchor=CorpusAnchor(
        paper="2025 May/June P1",
        question="4.2",  # determine-the-equation (turning-point form) item
        marks=3,
    ),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(
        registry=InMemoryRegistry(
            {parabola_from_turning_point.id: parabola_from_turning_point}
        )
    )

    def show(label, inst, *answers):
        attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
        r = inst.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  "
            f"is_correct={r.is_correct}"
        )

    for seed in (1, 7, 13):
        inst = engine.instantiate(parabola_from_turning_point.id, seed=seed)
        pm = inst.params
        print(f"=== seed {seed} ===")
        print(
            f"  vertex ({pm['vertex_x']}, {pm['vertex_y']})   a={pm['a']}   "
            f"y-int={pm['y_intercept']}"
        )
        print(f"  answer: f(x) = {sympy.latex(pm['answer'])}")
        show("Correct        ", inst, pm["answer"])
        show(
            "Forgot a (a=1) ",
            inst,
            sympy.expand((_x - pm["vertex_x"]) ** 2 + pm["vertex_y"]),
        )
