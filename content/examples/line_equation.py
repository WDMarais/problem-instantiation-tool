"""
Analytic geometry (straight line), archetype 2 — ``line_equation``.

Given a line L defined by two points, and a separate point P, find the equation
of the line through P that is either **parallel** or **perpendicular** to L.

Two skills compose here:
  1. the gradient of the required line — for a parallel line it equals L's
     gradient m; for a perpendicular line it is the negative reciprocal −1/m
     (the m₁·m₂ = −1 condition). This is the distinctive step and is graded on
     its own (1 mark).
  2. the full equation y = (gradient)·x + c, with c fixed by substituting P
     (2 marks) — the same value-of-c-from-a-point step as a tangent line.

Grading the required gradient separately means a student who uses the parallel
gradient when perpendicular was asked (or forgets the negative reciprocal) loses
that mark cleanly, rather than it being hidden inside a wrong final equation.

**Construction** is backward: pick L by two integer points (neither horizontal
nor vertical, so both parallel and perpendicular gradients are finite and
non-zero), pick the relation and the point P, then set c = y_P − gradient·x_P so
the line passes exactly through P. Gradients and intercepts are left as exact
rationals — no cosmetic rounding.
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

_x = sympy.Symbol("x")


def _gen(rng: random.Random) -> dict:
    while True:
        gx1, gy1 = rng.randint(-8, 8), rng.randint(-8, 8)
        gx2, gy2 = rng.randint(-8, 8), rng.randint(-8, 8)
        if gx1 == gx2 or gy1 == gy2:
            continue  # vertical or horizontal L: a reciprocal gradient degenerates
        break

    given_gradient = sympy.Rational(gy2 - gy1, gx2 - gx1)
    relation = rng.choice(["parallel", "perpendicular"])
    if relation == "parallel":
        gradient = given_gradient
    else:
        gradient = -1 / given_gradient

    px, py = rng.randint(-8, 8), rng.randint(-8, 8)
    c = sympy.Rational(py) - gradient * px
    equation_rhs = gradient * _x + c

    return {
        "gx1": gx1,
        "gy1": gy1,
        "gx2": gx2,
        "gy2": gy2,
        "px": px,
        "py": py,
        "relation": relation,
        "given_gradient": given_gradient,
        "required_gradient": gradient,
        "c": c,
        "equation_rhs": equation_rhs,
        "given_line_latex": rf"({gx1},\,{gy1})\text{{ and }}({gx2},\,{gy2})",
        "point_latex": rf"({px},\,{py})",
        "equation_latex": rf"y = {sympy.latex(equation_rhs)}",
    }


line_equation = Problem(
    id="line_equation",
    type_id="line_equation",
    name="Equation of a line through a point, parallel/perpendicular to another",
    artifact_type="practice",
    problem_spec=_gen,
    verifier_spec=[
        {
            "kind": "symbolic_equality",
            "marks_possible": 1,
            "param_key": "required_gradient",
        },
        {
            "kind": "symbolic_equality",
            "marks_possible": 2,
            "param_key": "equation_rhs",
        },
    ],
    corpus_anchor=CorpusAnchor(
        paper="2023 Nov P2",
        question="3.5",
        marks=3,
    ),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(registry=InMemoryRegistry({line_equation.id: line_equation}))

    def show(label, inst, *answers):
        attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
        r = inst.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  "
            f"is_correct={r.is_correct}"
        )

    for seed in range(4):
        inst = engine.instantiate(line_equation.id, seed=seed)
        p = inst.params
        print(f"=== seed {seed} ({p['relation']}) ===")
        print(f"  L through {p['given_line_latex']}  m_L={p['given_gradient']}")
        print(f"  P={p['point_latex']}  ->  {p['equation_latex']}")
        show("both correct   ", inst, p["required_gradient"], p["equation_rhs"])
        # the parallel/perpendicular confusion: the negative-reciprocal gradient
        confused = -1 / p["required_gradient"]
        show("wrong relation ", inst, confused, confused * _x + p["c"])
