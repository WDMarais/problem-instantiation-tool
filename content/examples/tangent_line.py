"""
Calculus, archetype 3 — ``tangent_line``.

Given a cubic  f(x) = a·x³ + b·x² + c·x + d  and a point on it at  x = x₀, find
the equation of the **tangent** to the curve there. This composes the derivative
rules (archetype 2): the gradient of the tangent is  m = f′(x₀), and the line
through (x₀, f(x₀)) with that gradient is  y = m·x + k  where  k = f(x₀) − m·x₀.

The two things a marker rewards are decomposed:

  1. the **gradient** m = f′(x₀) — a number (``numeric_equality``, 1 mark), and
  2. the **tangent line** y = m·x + k — the right-hand side as an expression
     (``symbolic_equality``, 2 marks), which accepts any equal form the student
     writes (``-x - 2``, ``-(x + 2)``, …).

So a student who differentiates and evaluates the gradient correctly but slips
on the y-intercept arithmetic still earns the gradient mark. Coefficients are
integer and x₀ small, so m, f(x₀) and k are all integers.
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

_x, _y = sympy.symbols("x y")


def _gen(rng: random.Random) -> dict:
    a = rng.choice([-2, -1, 1, 2])  # nonzero → genuinely cubic
    b = rng.randint(-4, 4)
    c = rng.randint(-6, 6)
    d = rng.randint(-6, 6)
    x0 = rng.randint(-3, 3)

    f = a * _x**3 + b * _x**2 + c * _x + d
    gradient = int(sympy.diff(f, _x).subs(_x, x0))
    y0 = int(f.subs(_x, x0))
    k = y0 - gradient * x0
    tangent_rhs = gradient * _x + k

    return {
        "a": a,
        "b": b,
        "c": c,
        "d": d,
        "x0": x0,
        "y0": y0,
        "gradient": gradient,
        "tangent_rhs": tangent_rhs,
        "function_latex": rf"f(x) = {sympy.latex(f)}",
        "point_latex": rf"x = {x0}",
        "tangent_latex": sympy.latex(sympy.Eq(_y, tangent_rhs)),
    }


tangent_line = Problem(
    id="tangent_line",
    type_id="tangent_line",
    name="Find the tangent line to a cubic at a point (gradient via f′, then y=mx+k)",
    artifact_type="practice",
    problem_spec=_gen,
    verifier_spec=[
        {"kind": "numeric_equality", "marks_possible": 1, "param_key": "gradient"},
        {"kind": "symbolic_equality", "marks_possible": 2, "param_key": "tangent_rhs"},
    ],
    corpus_anchor=CorpusAnchor(
        paper="2024 Nov P1",
        question="8.2",
        marks=3,  # gradient f′(x₀) (1) + tangent equation (2)
    ),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(registry=InMemoryRegistry({tangent_line.id: tangent_line}))

    def show(label, inst, *answers):
        attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
        r = inst.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  "
            f"is_correct={r.is_correct}"
        )

    for seed in range(3):
        inst = engine.instantiate(tangent_line.id, seed=seed)
        p = inst.params
        print(f"=== seed {seed} ===")
        print(f"  {p['function_latex']}   at {p['point_latex']}")
        print(f"  tangent: y = {p['tangent_rhs']}   (m = {p['gradient']})")
        show("gradient + line    ", inst, p["gradient"], p["tangent_rhs"])
        show("gradient, bad y-int", inst, p["gradient"], p["tangent_rhs"] + 1)
