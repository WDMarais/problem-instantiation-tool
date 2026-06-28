"""
Triangle angle-chases — three reason-bearing variants.

Second consumer of render/geometry.py (GeometryFigure), and a reuse test: it
exercises two primitives the parallelograms never touched — equal-length *ticks*
(isosceles) and a *collinear extended ray* (exterior angle). Each problem gives
angles of triangle ABC and asks for another, the reason supplied in the worked
steps. The verifiable output is the single angle value; the diagram is display-only.

Variants:
  triangle_angle_sum  — given A, B; find C.        C = 180 - A - B
                        reason: angles of a triangle sum to 180°
  triangle_isosceles  — AB = AC (ticks); given base B; find apex A.
                        A = 180 - 2B   reason: base ∠s isosceles equal, then ∠ sum
  triangle_exterior   — AB extended to P; given remote interiors A, C; find ext CBP.
                        ext = A + C    reason: exterior ∠ of a triangle

The construction angles are carried purely for drawing (the figure is built
to-scale so a similarity Pose keeps every drawn angle faithful to its label); the
relationships hold for any triangle, so the figure need not be to scale.
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import Problem


# Givens are arbitrary integer degrees (1° steps). Bands keep all three interior
# angles comfortably non-degenerate and the figure legible.
def _random_pose(rng: random.Random) -> dict:
    """A similarity transform (plain data; the template builds the Pose). Pure
    visual variety — rotation/scale/reflection preserve angles, so the answer and
    the drawn angle values are unaffected."""
    return {
        "rotate_deg": round(rng.uniform(0, 360), 1),
        "scale": round(rng.uniform(0.72, 1.0), 3),
        "reflect": rng.random() < 0.5,
    }


def _gen_angle_sum(rng: random.Random) -> dict:
    alpha = rng.randint(40, 80)  # marked at A
    beta = rng.randint(40, 80)  # marked at B
    # gamma = 180 - alpha - beta lands in [20, 100]; the answer at C.
    return {
        "alpha_deg": alpha,
        "beta_deg": beta,
        "base": round(rng.uniform(3.6, 4.8), 2),
        "pose": _random_pose(rng),
        "answer": sympy.Integer(180 - alpha - beta),
    }


def _gen_isosceles(rng: random.Random) -> dict:
    # AB = AC, apex at A. Give a base angle B; the apex is 180 - 2B.
    base_angle = rng.randint(40, 74)  # apex 180-2B lands in [32, 100]
    apex = 180 - 2 * base_angle
    return {
        "base_angle_deg": base_angle,
        "apex_deg": apex,  # construction angle at A (= the answer)
        "base": round(rng.uniform(3.4, 4.4), 2),
        "pose": _random_pose(rng),
        "answer": sympy.Integer(apex),
    }


def _gen_exterior(rng: random.Random) -> dict:
    # Remote interiors at A and C; exterior at B (angle CBP, AB extended to P).
    alpha = rng.randint(35, 70)  # marked at A
    gamma = rng.randint(35, 70)  # marked at C
    interior_b = 180 - alpha - gamma  # lands in [40, 110]
    return {
        "alpha_deg": alpha,
        "gamma_deg": gamma,
        "interior_b_deg": interior_b,  # construction angle at B
        "base": round(rng.uniform(3.4, 4.2), 2),
        "pose": _random_pose(rng),
        "answer": sympy.Integer(alpha + gamma),
    }


triangle_angle_sum = Problem(
    id="triangle_angle_sum",
    type_id="triangle_angles",
    name="Find the third angle of a triangle (angle sum)",
    artifact_type="practice",
    problem_spec=_gen_angle_sum,
    verifier_spec=[
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "answer"}
    ],
)

triangle_isosceles = Problem(
    id="triangle_isosceles",
    type_id="triangle_angles",
    name="Find the apex angle of an isosceles triangle (base angles equal)",
    artifact_type="practice",
    problem_spec=_gen_isosceles,
    verifier_spec=[
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "answer"}
    ],
)

triangle_exterior = Problem(
    id="triangle_exterior",
    type_id="triangle_angles",
    name="Find the exterior angle of a triangle (exterior angle theorem)",
    artifact_type="practice",
    problem_spec=_gen_exterior,
    verifier_spec=[
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "answer"}
    ],
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    problems = {
        p.id: p for p in [triangle_angle_sum, triangle_isosceles, triangle_exterior]
    }
    engine = Engine(registry=InMemoryRegistry(problems))

    def show(label, instance, *answers):
        attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
        r = instance.verifier.rate(attempt)
        print(f"  {label}: {r.marks_awarded}/{r.marks_possible}  ok={r.is_correct}")

    for pid in problems:
        inst = engine.instantiate(pid, seed=7)
        p = inst.params
        (canon,) = inst.verifier.canonicals
        shown = {k: v for k, v in p.items() if k != "pose"}
        print(f"=== {pid} ===  answer={canon}°  params={shown}")
        show("correct", inst, canon)
        show("wrong  ", inst, int(canon) + 5)
        print()
