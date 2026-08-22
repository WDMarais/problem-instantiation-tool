"""
Functions & Graphs — ``hyperbola_from_graph``.

Determine the equation of a rectangular hyperbola from a sketch that labels its
two asymptotes (``x = -p``, ``y = q``) and one point ``(x0, y0)`` on the curve.
The student reads the asymptotes to write ``y = a/(x + p) + q`` with unknown
``a``, substitutes the point to solve ``a = (y0 - q)(x0 + p)``, and states the
equation. Graded on the full expression (``symbolic_equality``, 3 marks: form,
solve a, state).

**Forward read-off, so wire-only (no F1 gate).** The asymptotes fix ``p`` and
``q``; the labelled point fixes ``a``. Because the point never sits on an
asymptote (``x0 != -p`` and ``y0 != q`` by construction), ``a`` is always
recoverable and no draw is ill-posed — gating would be tautological (sharpened
F1 rule: forward read-off → wire-only). Same class as ``parabola_from_graph``.

The point is built from integer offsets ``d = x0 + p`` and ``k = y0 - q`` with
``a = d·k``, so every labelled coordinate is a clean lattice point.

Display-only (see ``render/DESIGN.md``): the generator bakes the whole equation;
the sketch is drawn *from* the baked asymptotes, coefficient and point.
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

_x = sympy.Symbol("x")


def _gen(rng: random.Random) -> dict:
    # Asymptotes off the axes (p, q != 0) so each dashed line is distinct from an
    # axis — a legibility constraint on the sketch, not an answer-band limit.
    p = rng.choice([-3, -2, -1, 1, 2, 3])
    q = rng.choice([-3, -2, -1, 1, 2, 3])

    # The labelled point sits at offset (d, k) from the asymptote intersection
    # (-p, q): x0 = d - p, y0 = k + q, and a = d·k. d, k nonzero ⇒ the point is
    # never on an asymptote and a != 0, so a is always recoverable.
    d = rng.choice([-3, -2, -1, 1, 2, 3])
    k = rng.choice([-3, -2, -1, 1, 2, 3])
    a = d * k
    x0, y0 = d - p, k + q

    answer = a / (_x + p) + q  # y = a/(x + p) + q

    return {
        "a": a,
        "p": p,
        "q": q,
        "point_x": x0,
        "point_y": y0,
        "answer": answer,  # graded by symbolic_equality
    }


hyperbola_from_graph = Problem(
    id="hyperbola_from_graph",
    type_id="hyperbola_from_graph",
    name="Determine the equation of a hyperbola from its sketch (asymptotes + point)",
    artifact_type="practice",
    problem_spec=_gen,
    verifier_spec={
        "kind": "symbolic_equality",
        "marks_possible": 3,  # read asymptotes + solve for a + state equation
        "param_key": "answer",
    },
    corpus_anchor=CorpusAnchor(
        paper="2025 May/June P1",
        question="4.3",  # determine-the-equation (hyperbola) item
        marks=3,
    ),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(
        registry=InMemoryRegistry({hyperbola_from_graph.id: hyperbola_from_graph})
    )

    def show(label, inst, expr):
        attempt = SolutionAttempt(steps=[SubmittedStep(expr)])
        r = inst.verifier.rate(attempt)
        print(f"  {label}: {r.marks_awarded}/{r.marks_possible}  ok={r.is_correct}")

    for seed in (1, 7, 13):
        inst = engine.instantiate(hyperbola_from_graph.id, seed=seed)
        pm = inst.params
        print(f"=== seed {seed} ===")
        print(
            f"  asymptotes x={-pm['p']}, y={pm['q']}   a={pm['a']}   "
            f"point ({pm['point_x']}, {pm['point_y']})"
        )
        print(f"  answer: y = {sympy.latex(pm['answer'])}")
        show("Correct        ", inst, pm["answer"])
        # equivalent single-fraction form must also grade full marks
        show("Combined form  ", inst, sympy.together(pm["answer"]))
        # forgot to solve a (left a = 1): correct only when a really is 1
        show("Assumed a = 1  ", inst, 1 / (_x + pm["p"]) + pm["q"])
