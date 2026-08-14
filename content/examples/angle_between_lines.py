"""
Analytic geometry (straight line), archetype 3 — ``angle_between_lines``.

Given two non-parallel lines AB and CD (each by two points), find the acute
angle between them. The taught method goes through the inclinations: find θ₁ and
θ₂ (tan θ = gradient, with the obtuse adjustment for a negative gradient), then
the angle between the lines is the acute value obtained from their difference —
|θ₁ − θ₂|, folded into (0°, 90°] by taking 180° − it when the raw difference is
obtuse.

So the three marks are graded as the two inclinations (1 each) plus the combined
angle (1). Grading the inclinations separately keeps the method visible: the
final acute angle alone would hide whether a student found the constituent
inclinations or guessed.

The angle is irrational in degrees; the memo rounds to two decimals, so every
step is ``numeric_equality`` with a small absolute tolerance.

**Construction** draws two non-vertical lines (so both inclinations come from a
finite gradient) with distinct gradients (non-parallel, so the angle is
non-zero). Perpendicular pairs are allowed — they give the clean 90° answer. No
cosmetic clamping of the gradients.
"""

from __future__ import annotations

import math
import random

import sympy

from problem_instantiation_tool.schemas import CorpusAnchor, Problem


def _inclination(m: float) -> float:
    theta = math.degrees(math.atan(m))
    return theta + 180 if theta < 0 else theta


def _gen(rng: random.Random) -> dict:
    while True:
        ax, ay = rng.randint(-8, 8), rng.randint(-8, 8)
        bx, by = rng.randint(-8, 8), rng.randint(-8, 8)
        cx, cy = rng.randint(-8, 8), rng.randint(-8, 8)
        dx, dy = rng.randint(-8, 8), rng.randint(-8, 8)
        if ax == bx or cx == dx:
            continue  # a vertical line — inclination not from a finite gradient
        m1 = sympy.Rational(by - ay, bx - ax)
        m2 = sympy.Rational(dy - cy, dx - cx)
        if m1 == m2:
            continue  # parallel — no angle between them
        break

    theta1 = _inclination(float(m1))
    theta2 = _inclination(float(m2))
    raw = abs(theta1 - theta2)
    angle_between = raw if raw <= 90 else 180 - raw

    return {
        "ax": ax,
        "ay": ay,
        "bx": bx,
        "by": by,
        "cx": cx,
        "cy": cy,
        "dx": dx,
        "dy": dy,
        "m1": m1,
        "m2": m2,
        "theta1": round(theta1, 2),
        "theta2": round(theta2, 2),
        "angle_between": round(angle_between, 2),
        "line_ab_latex": rf"A({ax},\,{ay})\text{{ and }}B({bx},\,{by})",
        "line_cd_latex": rf"C({cx},\,{cy})\text{{ and }}D({dx},\,{dy})",
    }


angle_between_lines = Problem(
    id="angle_between_lines",
    type_id="angle_between_lines",
    name="Acute angle between two lines via their inclinations",
    artifact_type="practice",
    problem_spec=_gen,
    verifier_spec=[
        {
            "kind": "numeric_equality",
            "marks_possible": 1,
            "param_key": "theta1",
            "tolerance": 0.05,
        },
        {
            "kind": "numeric_equality",
            "marks_possible": 1,
            "param_key": "theta2",
            "tolerance": 0.05,
        },
        {
            "kind": "numeric_equality",
            "marks_possible": 1,
            "param_key": "angle_between",
            "tolerance": 0.05,
        },
    ],
    corpus_anchor=CorpusAnchor(
        paper="2023 Nov P2",
        question="3.4",
        marks=3,
    ),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(
        registry=InMemoryRegistry({angle_between_lines.id: angle_between_lines})
    )

    def show(label, inst, *answers):
        attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
        r = inst.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  "
            f"is_correct={r.is_correct}"
        )

    for seed in range(4):
        inst = engine.instantiate(angle_between_lines.id, seed=seed)
        p = inst.params
        print(f"=== seed {seed} ===")
        print(
            f"  m1={p['m1']} (θ₁={p['theta1']}°)  m2={p['m2']} (θ₂={p['theta2']}°)  "
            f"angle={p['angle_between']}°"
        )
        show("all correct  ", inst, p["theta1"], p["theta2"], p["angle_between"])
        show("angle wrong  ", inst, p["theta1"], p["theta2"], p["angle_between"] + 20)
