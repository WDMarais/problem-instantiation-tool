"""
Parallelogram angle-chases — three reason-bearing variants.

First consumer of render/geometry.py (GeometryFigure). Each problem gives one
angle of parallelogram ABCD and asks for another, with the reason supplied in the
worked steps (the mini-proof). The verifiable output is the single angle value;
the diagram is display-only.

Variants:
  parallelogram_cointerior — given A, find adjacent B.  B = 180 - A
                             reason: co-interior angles; AD ∥ BC
  parallelogram_opposite   — given A, find opposite C.  C = A
                             reason: opposite angles of a parallelogram
  parallelogram_alternate  — diagonal AC drawn; given D^C^A, find B^A^C  (= it)
                             reason: alternate angles ("Z"); AB ∥ DC

`angle_a_deg` is carried purely for drawing (the interior angle drawn at vertex A);
the relationships hold for any parallelogram, so the figure need not be to scale.
"""

from __future__ import annotations

import math
import random

import sympy

from problem_instantiation_tool.schemas import Problem


# Givens are arbitrary integer degrees (no "nice" multiples needed — the answers
# 180−A, A, =given are integer for any integer input). Bands avoid near-90°
# (looks like a rectangle) and the thin extremes.
def _given_adjacent(rng: random.Random) -> int:
    """An angle at A: acute or obtuse, 50/50, so the co-interior subtraction lands
    on either side of 90°."""
    if rng.random() < 0.5:
        return rng.randint(28, 78)
    return rng.randint(102, 148)


def _random_pose(rng: random.Random) -> dict:
    """A similarity transform (plain data; the template builds the Pose). Pure
    visual variety — rotation/scale/reflection preserve angles, so the answer and
    the drawn angle values are unaffected."""
    return {
        "rotate_deg": round(rng.uniform(0, 360), 1),
        "scale": round(rng.uniform(0.72, 1.0), 3),
        "reflect": rng.random() < 0.5,
    }


def _shape(rng: random.Random) -> dict:
    """Intrinsic parallelogram proportions — varied for shape variety."""
    return {
        "base": round(rng.uniform(3.6, 4.8), 2),
        "side": round(rng.uniform(2.2, 3.0), 2),
    }


def _gen_cointerior(rng: random.Random) -> dict:
    given = _given_adjacent(rng)
    return {
        "given_deg": given,
        "angle_a_deg": given,  # given is the angle at A; kept to-scale
        "pose": _random_pose(rng),
        **_shape(rng),
        "answer": sympy.Integer(180 - given),
    }


def _gen_opposite(rng: random.Random) -> dict:
    given = _given_adjacent(rng)
    return {
        "given_deg": given,
        "angle_a_deg": given,
        "pose": _random_pose(rng),
        **_shape(rng),
        "answer": sympy.Integer(given),
    }


def _gen_alternate(rng: random.Random) -> dict:
    given = rng.randint(22, 60)
    # Construct to-scale: pick an obtuse interior angle at A, then solve the side
    # length so the diagonal AC subtends exactly `given` at A (= B^A^C). Both
    # alternate marks (B^A^C and D^C^A) then equal `given` in the drawing.
    # NB: a true acute angle here can *look* smaller than it is — the acute-angle
    # underestimation illusion — but it is geometrically exact (verified in Inkscape).
    theta_a = rng.randint(100, 126)
    base = rng.uniform(3.6, 4.6)
    t = math.tan(math.radians(given))
    th = math.radians(theta_a)
    side = t * base / (math.sin(th) - t * math.cos(th))  # > 0 for obtuse theta_a
    return {
        "given_deg": given,
        "angle_a_deg": theta_a,
        "base": round(base, 2),
        "side": round(side, 2),
        "pose": _random_pose(rng),
        "answer": sympy.Integer(given),
    }


parallelogram_cointerior = Problem(
    id="parallelogram_cointerior",
    type_id="parallelogram_angles",
    name="Find an adjacent angle of a parallelogram (co-interior angles)",
    artifact_type="practice",
    problem_spec=_gen_cointerior,
    verifier_spec=[
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "answer"}
    ],
)

parallelogram_opposite = Problem(
    id="parallelogram_opposite",
    type_id="parallelogram_angles",
    name="Find the opposite angle of a parallelogram (opposite angles equal)",
    artifact_type="practice",
    problem_spec=_gen_opposite,
    verifier_spec=[
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "answer"}
    ],
)

parallelogram_alternate = Problem(
    id="parallelogram_alternate",
    type_id="parallelogram_angles",
    name="Find an alternate angle across a parallelogram diagonal (Z-angles)",
    artifact_type="practice",
    problem_spec=_gen_alternate,
    verifier_spec=[
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "answer"}
    ],
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    problems = {
        p.id: p
        for p in [
            parallelogram_cointerior,
            parallelogram_opposite,
            parallelogram_alternate,
        ]
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
        print(f"=== {pid} ===  given={p['given_deg']}°  answer={canon}°")
        show("correct", inst, canon)
        show("wrong  ", inst, int(canon) + 5)
        print()
