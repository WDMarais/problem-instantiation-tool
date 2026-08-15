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

**Reason grading (the Tier-3 pilot).** Each variant grades as DBE two-column
statement/reason: 1 mark for the angle value, 1 mark for citing the correct
theorem (``value_and_reason``, partial credit). The generator emits the canonical
reason *id*; the student's phrasing is matched by alias against the closed
``PARALLELOGRAM_REASONS`` set — the other two reasons in that set are the
load-bearing distractors, so a student who names the wrong (but plausible)
theorem keeps the value mark and loses the reason mark (``semantic_error``).
"""

from __future__ import annotations

import math
import random

import sympy

from problem_instantiation_tool.schemas import Problem

# Closed reason-set for the parallelogram configuration: canonical theorem id →
# accepted student surface phrasings (matched after NFC + lowercase + whitespace
# normalisation). Holding all three reasons in one set makes each a load-bearing
# distractor for the others — a student can't win the reason mark by always
# writing the same theorem. v1 grades the theorem name only; the parallel-lines
# citation ("; AD ∥ BC") is accepted but not required (spec scope cut §5.1).
PARALLELOGRAM_REASONS: dict[str, list[str]] = {
    "opp_angles_parallelogram": [
        "opposite angles of a parallelogram",
        "opp angles of a parallelogram",
        "opp angles of a parm",
        "opp ∠s of parm",
        "opposite angles of parm",
        "opposite angles parallelogram",
    ],
    "cointerior_angles": [
        "co-interior angles",
        "cointerior angles",
        "co-int angles",
        "coint angles",
        "co-interior angles; ad ∥ bc",
        "allied angles",
    ],
    "alternate_angles": [
        "alternate angles",
        "alt angles",
        "z angles",
        "alternate angles; ab ∥ dc",
    ],
}


def _value_and_reason_spec(reason_set: dict) -> list[dict]:
    """The shared two-column S/R verifier: 1 mark value + 1 mark reason."""
    return [
        {
            "kind": "value_and_reason",
            "marks_possible": 2,
            "value_key": "answer",
            "value_kind": "symbolic_equality",
            "reason_key": "reason",
            "reason_set": reason_set,
            "normalize": ["whitespace"],
        }
    ]


# Givens are arbitrary integer degrees (no "nice" multiples needed — the answers
# 180−A, A, =given are integer for any integer input). Bands avoid near-90°
# (looks like a rectangle) and the thin extremes.
def _given_adjacent(rng: random.Random) -> int:
    """An angle at A: acute or obtuse, 50/50, so the co-interior subtraction lands
    on either side of 90°."""
    if rng.random() < 0.5:
        return rng.randint(28, 78)
    return rng.randint(102, 148)


# Vertex namings for the figure/prose. The geometry is fixed by the *roles*
# A→B→C→D (anticlockwise); these are only the letters shown to the student, so a
# fixed "ABCD" can't become a notational crutch. Each entry lists four distinct
# letters in role order (role A first — the given-angle vertex). Kept to
# consecutive, exam-plausible runs; O/I excluded (read as 0/1).
_VERTEX_NAMINGS: tuple[tuple[str, str, str, str], ...] = (
    ("A", "B", "C", "D"),
    ("P", "Q", "R", "S"),
    ("K", "L", "M", "N"),
    ("D", "E", "F", "G"),
    ("W", "X", "Y", "Z"),
    ("Q", "R", "S", "T"),
    ("E", "F", "G", "H"),
    ("T", "U", "V", "W"),
)


def _vertex_labels(rng: random.Random) -> dict[str, str]:
    """A role→letter naming for one parallelogram, chosen from the exam-plausible
    pool. Pure display: rotation/reflection of the *letters*, never the shape."""
    a, b, c, d = rng.choice(_VERTEX_NAMINGS)
    return {"A": a, "B": b, "C": c, "D": d}


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
        "labels": _vertex_labels(rng),
        "answer": sympy.Integer(180 - given),
        "reason": "cointerior_angles",
    }


def _gen_opposite(rng: random.Random) -> dict:
    given = _given_adjacent(rng)
    return {
        "given_deg": given,
        "angle_a_deg": given,
        "pose": _random_pose(rng),
        **_shape(rng),
        "labels": _vertex_labels(rng),
        "answer": sympy.Integer(given),
        "reason": "opp_angles_parallelogram",
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
        "labels": _vertex_labels(rng),
        "answer": sympy.Integer(given),
        "reason": "alternate_angles",
    }


parallelogram_cointerior = Problem(
    id="parallelogram_cointerior",
    type_id="parallelogram_angles",
    name="Find an adjacent angle of a parallelogram (co-interior angles)",
    artifact_type="practice",
    problem_spec=_gen_cointerior,
    verifier_spec=_value_and_reason_spec(PARALLELOGRAM_REASONS),
)

parallelogram_opposite = Problem(
    id="parallelogram_opposite",
    type_id="parallelogram_angles",
    name="Find the opposite angle of a parallelogram (opposite angles equal)",
    artifact_type="practice",
    problem_spec=_gen_opposite,
    verifier_spec=_value_and_reason_spec(PARALLELOGRAM_REASONS),
)

parallelogram_alternate = Problem(
    id="parallelogram_alternate",
    type_id="parallelogram_angles",
    name="Find an alternate angle across a parallelogram diagonal (Z-angles)",
    artifact_type="practice",
    problem_spec=_gen_alternate,
    verifier_spec=_value_and_reason_spec(PARALLELOGRAM_REASONS),
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

    # one accepted surface phrasing per canonical reason id, for the demo
    _SURFACE = {
        "cointerior_angles": "co-interior angles",
        "opp_angles_parallelogram": "opposite angles of a parallelogram",
        "alternate_angles": "alternate angles",
    }

    def show(label, instance, value, reason):
        attempt = SolutionAttempt(
            steps=[SubmittedStep({"value": value, "reason": reason})]
        )
        r = instance.verifier.rate(attempt)
        mt = r.steps[0].mistake_type.name
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  "
            f"ok={r.is_correct}  [{mt}]"
        )

    for pid in problems:
        inst = engine.instantiate(pid, seed=7)
        p = inst.params
        canon = inst.verifier.canonicals[0]
        val, good_reason = canon["value"], _SURFACE[canon["reason"]]
        print(f"=== {pid} ===  given={p['given_deg']}°  answer={val}°")
        show("value ✓ reason ✓", inst, val, good_reason)
        show("value ✓ reason ✗", inst, val, "vertically opposite angles")
        show("value ✗ reason ✓", inst, int(val) + 5, good_reason)
        print()
