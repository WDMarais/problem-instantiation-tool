"""
Analytic geometry (straight line), archetype 1 — ``inclination_angle``.

Given two points A(x₁,y₁), B(x₂,y₂), find the **gradient** of line AB and the
**angle of inclination** θ — the angle the line makes with the positive x-axis,
measured anticlockwise, 0° ≤ θ < 180°.

The gradient is m = (y₂−y₁)/(x₂−x₁) and tan θ = m, so θ = tan⁻¹(m). The
distinctive skill is the **quadrant adjustment**: tan⁻¹ returns a value in
(−90°, 90°), so for a *negative* gradient the calculator angle is negative and
the inclination is the obtuse angle θ = 180° + tan⁻¹(m). A student who reports
the raw (negative or acute) calculator value has the wrong inclination — so the
angle is graded as its own mark, separately from the gradient.

The angle is an irrational number of degrees in general; the memo convention is
to round to two decimals, so the answer is graded with ``numeric_equality`` and a
small absolute tolerance (a student rounding to 1–2 dp lands inside it; a missed
quadrant adjustment does not).

**Construction** just draws two integer lattice points and rejects the two
degenerate lines: vertical (x₁=x₂, gradient undefined) and horizontal (y₁=y₂,
the trivial θ=0). No cosmetic clamping — any integer gradient is fair game, so
the angles are the genuine spread the method produces.
"""

from __future__ import annotations

import math
import random

import sympy

from problem_instantiation_tool.schemas import CorpusAnchor, Problem


def _gen(rng: random.Random) -> dict:
    while True:
        x1, y1 = rng.randint(-8, 8), rng.randint(-8, 8)
        x2, y2 = rng.randint(-8, 8), rng.randint(-8, 8)
        if x1 == x2:  # vertical line — gradient undefined
            continue
        if y1 == y2:  # horizontal line — trivial θ = 0
            continue
        break

    gradient = sympy.Rational(y2 - y1, x2 - x1)
    theta = math.degrees(math.atan(float(gradient)))
    if theta < 0:  # negative gradient ⇒ obtuse inclination
        theta += 180

    return {
        "x1": x1,
        "y1": y1,
        "x2": x2,
        "y2": y2,
        "gradient": gradient,
        "inclination": round(theta, 2),
        "gradient_latex": sympy.latex(gradient),
        "points_latex": rf"A({x1},\,{y1})\text{{ and }}B({x2},\,{y2})",
    }


inclination_angle = Problem(
    id="inclination_angle",
    type_id="inclination_angle",
    name="Gradient and angle of inclination of a line through two points",
    artifact_type="practice",
    problem_spec=_gen,
    verifier_spec=[
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "gradient"},
        {
            "kind": "numeric_equality",
            "marks_possible": 1,
            "param_key": "inclination",
            "tolerance": 0.05,
        },
    ],
    corpus_anchor=CorpusAnchor(
        paper="2023 Nov P2",
        question="3.3",
        marks=2,
    ),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(
        registry=InMemoryRegistry({inclination_angle.id: inclination_angle})
    )

    def show(label, inst, *answers):
        attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
        r = inst.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  "
            f"is_correct={r.is_correct}"
        )

    for seed in range(4):
        inst = engine.instantiate(inclination_angle.id, seed=seed)
        p = inst.params
        print(f"=== seed {seed} ===")
        print(
            f"  A=({p['x1']},{p['y1']})  B=({p['x2']},{p['y2']})  "
            f"m={p['gradient']}  θ={p['inclination']}°"
        )
        show("both correct    ", inst, p["gradient"], p["inclination"])
        show("angle unadjusted", inst, p["gradient"], round(p["inclination"] - 180, 2))
