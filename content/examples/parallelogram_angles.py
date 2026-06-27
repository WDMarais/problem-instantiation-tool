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

import random

import sympy

from problem_instantiation_tool.schemas import Problem

# "Nice" givens. Acute and obtuse both allowed for the A-vertex variants so the
# co-interior subtraction lands on the other side of 90° about half the time.
_GIVEN_ADJ = [35, 40, 50, 55, 65, 70, 75, 105, 110, 115, 125, 130]
# Alternate-angle givens are the acute angle between a side and the diagonal.
_GIVEN_ALT = [25, 30, 35, 40, 45, 50, 55]


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
    given = rng.choice(_GIVEN_ADJ)
    return {
        "given_deg": given,
        "angle_a_deg": given,  # given is the angle at A; kept to-scale
        "pose": _random_pose(rng),
        **_shape(rng),
        "answer": sympy.Integer(180 - given),
    }


def _gen_opposite(rng: random.Random) -> dict:
    given = rng.choice(_GIVEN_ADJ)
    return {
        "given_deg": given,
        "angle_a_deg": given,
        "pose": _random_pose(rng),
        **_shape(rng),
        "answer": sympy.Integer(given),
    }


def _gen_alternate(rng: random.Random) -> dict:
    given = rng.choice(_GIVEN_ALT)
    return {
        "given_deg": given,
        "angle_a_deg": 68,  # fixed pleasant shear; diagram not to scale
        "pose": _random_pose(rng),
        **_shape(rng),
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
