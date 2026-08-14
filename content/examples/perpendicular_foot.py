"""
Analytic geometry (straight line), archetype 7 — ``perpendicular_foot``.

Given a point P and a line L: Ax + By + C = 0, find the coordinates of the
**foot of the perpendicular** F — the point on L nearest P, where PF ⊥ L.

The method: L has gradient −A/B, so the perpendicular from P has gradient B/A;
write that perpendicular line through P and intersect it with L. Two coordinates,
graded independently (1 mark each) — a sign slip on the perpendicular gradient
costs the coordinate it corrupts, not both.

**Construction** is backward from the answer, the house pattern: choose the foot
F = (fx, fy) with integer coordinates and an oblique line L through it (integer
A, B, reduced, B > 0), then step off P along the *normal* direction (A, B) by an
integer multiple. PF is then parallel to the normal by construction, so F is
genuinely the foot and is never solved for in the generator — which is what makes
the test's own two-line intersection an independent oracle. Both A and B are
non-zero (a vertical or horizontal L would make the −1/m step degenerate), and
the multiple is non-zero so P never lands on L. |PF| = |t|·√(A²+B²) is an honest
surd, but only the (integer) foot is graded here.
"""

from __future__ import annotations

import math
import random

import sympy

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

_x, _y = sympy.symbols("x y")


def _gen(rng: random.Random) -> dict:
    while True:
        a = rng.randint(-5, 5)
        b = rng.randint(-5, 5)
        if a == 0 or b == 0:  # need a genuinely oblique line (finite, non-zero m)
            continue
        g = math.gcd(a, b)
        a, b = a // g, b // g
        if b < 0:  # normalise to B > 0
            a, b = -a, -b
        break

    fx = rng.randint(-6, 6)
    fy = rng.randint(-6, 6)
    c = -(a * fx + b * fy)  # C makes L pass through the foot

    t = rng.choice([-3, -2, -1, 1, 2, 3])  # non-zero: P is off the line
    px = fx + t * a  # step along the normal (A, B)
    py = fy + t * b

    gradient = sympy.Rational(-a, b)
    line_expr = a * _x + b * _y + c

    return {
        "A": a,
        "B": b,
        "C": c,
        "px": px,
        "py": py,
        "foot_x": fx,
        "foot_y": fy,
        "gradient": gradient,
        "line_latex": rf"{sympy.latex(line_expr)} = 0",
        "point_latex": rf"P({px},\,{py})",
    }


perpendicular_foot = Problem(
    id="perpendicular_foot",
    type_id="perpendicular_foot",
    name="Foot of the perpendicular from a point to a line",
    artifact_type="practice",
    problem_spec=_gen,
    verifier_spec=[
        {"kind": "numeric_equality", "marks_possible": 1, "param_key": "foot_x"},
        {"kind": "numeric_equality", "marks_possible": 1, "param_key": "foot_y"},
    ],
    corpus_anchor=CorpusAnchor(
        paper="2025 Nov P2",
        question="3.6",  # "perp-foot" — part of the 7-mark 3.3–3.6 straight-line block
        # standalone sub-part mark not isolated in our provenance notes → left unset
    ),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(
        registry=InMemoryRegistry({perpendicular_foot.id: perpendicular_foot})
    )

    def show(label, inst, *answers):
        attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
        r = inst.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  "
            f"is_correct={r.is_correct}"
        )

    for seed in range(4):
        inst = engine.instantiate(perpendicular_foot.id, seed=seed)
        p = inst.params
        print(f"=== seed {seed} ===")
        print(
            f"  L: {p['line_latex']}   P=({p['px']},{p['py']})  ->  "
            f"F=({p['foot_x']},{p['foot_y']})"
        )
        show("foot F        ", inst, p["foot_x"], p["foot_y"])
        # reflection of P in L is 2F − P — a classic confusion with the foot
        show(
            "reflection of P",
            inst,
            2 * p["foot_x"] - p["px"],
            2 * p["foot_y"] - p["py"],
        )
