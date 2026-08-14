"""
Analytic geometry (circle), archetype 5 — ``circle_tangent``.

A circle has centre C(h, k) and P(px, py) lies on it. Find the equation of the
**tangent to the circle at P**. The tangent is perpendicular to the radius CP,
so its gradient is the negative reciprocal of the radius gradient:
    m_radius = (py − k)/(px − h),   m_tangent = −(px − h)/(py − k),
and the tangent passes through P.

The distinctive step is the radius-then-perpendicular gradient, so it is graded
on its own (1 mark); the full equation y = m·x + c, with c fixed by P, is the
remaining 2 marks — the same 1+2 split as an ordinary line/tangent.

**Construction** is backward: pick an integer centre and an integer offset
(dx, dy) with both components non-zero (so the radius is neither horizontal nor
vertical and the tangent gradient is finite and non-zero); P = C + (dx, dy).
The tangent gradient is the exact rational −dx/dy and the intercept follows from
P — no rounding.
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

_x = sympy.Symbol("x")


def _gen(rng: random.Random) -> dict:
    h = rng.randint(-6, 6)
    k = rng.randint(-6, 6)
    dx = rng.choice([-6, -5, -4, -3, -2, -1, 1, 2, 3, 4, 5, 6])
    dy = rng.choice([-6, -5, -4, -3, -2, -1, 1, 2, 3, 4, 5, 6])
    px, py = h + dx, k + dy

    radius_gradient = sympy.Rational(dy, dx)
    tangent_gradient = -sympy.Rational(dx, dy)
    c = sympy.Rational(py) - tangent_gradient * px
    tangent_rhs = tangent_gradient * _x + c
    radius_sq = dx * dx + dy * dy

    return {
        "h": h,
        "k": k,
        "px": px,
        "py": py,
        "radius_sq": radius_sq,
        "radius_gradient": radius_gradient,
        "tangent_gradient": tangent_gradient,
        "c": c,
        "tangent_rhs": tangent_rhs,
        "centre_latex": rf"C({h},\,{k})",
        "point_latex": rf"P({px},\,{py})",
        "tangent_latex": rf"y = {sympy.latex(tangent_rhs)}",
    }


circle_tangent = Problem(
    id="circle_tangent",
    type_id="circle_tangent",
    name="Equation of the tangent to a circle at a point on it",
    artifact_type="practice",
    problem_spec=_gen,
    verifier_spec=[
        {
            "kind": "symbolic_equality",
            "marks_possible": 1,
            "param_key": "tangent_gradient",
        },
        {"kind": "symbolic_equality", "marks_possible": 2, "param_key": "tangent_rhs"},
    ],
    corpus_anchor=CorpusAnchor(
        paper="2024 Nov P2",
        question="4.1–4.5",  # tangent part of the 17-mark circle block
        # standalone sub-part mark not in our provenance notes → left unset
    ),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(registry=InMemoryRegistry({circle_tangent.id: circle_tangent}))

    def show(label, inst, *answers):
        attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
        r = inst.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  "
            f"is_correct={r.is_correct}"
        )

    for seed in range(4):
        inst = engine.instantiate(circle_tangent.id, seed=seed)
        p = inst.params
        print(f"=== seed {seed} ===")
        print(
            f"  centre {p['centre_latex']}  point {p['point_latex']}  ->  "
            f"{p['tangent_latex']}"
        )
        show("both correct   ", inst, p["tangent_gradient"], p["tangent_rhs"])
        # using the radius gradient (forgot the perpendicular) — classic error
        wrong_rhs = p["radius_gradient"] * _x + (
            p["py"] - p["radius_gradient"] * p["px"]
        )
        show("used radius grad", inst, p["radius_gradient"], wrong_rhs)
