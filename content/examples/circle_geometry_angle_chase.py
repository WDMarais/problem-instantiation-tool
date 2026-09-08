"""
Circle-geometry angle-chase — central-angle + same-segment, with reasons.

First Euclidean *circle*-theorem consumer of render/geometry.py (the new Circle
primitive). O is the centre; A, B, C, D lie on the circle. One inscribed angle is
given (AĈB = c), and the student chases two more, each a two-column
statement/reason:

  9.1  AD̂B  (D in the same segment as C)   = c    reason: same segment
  9.2  AÔB  (central angle on chord AB)     = 2c   reason: ∠ at centre = 2 × ∠ at circ.

The *given* is an inscribed angle, deliberately, so each ask has exactly one clean
theorem: with no central angle handed to the student, AD̂B can only come from the
same segment, and AÔB can only come from the centre-is-twice rule — no
two-valid-reasons ambiguity for the closed reason-set to mis-grade.

**Faithful, not merely schematic.** Unlike the parallelogram angle-chase (which
needs a Pose similarity to keep drawn angles honest), a circle enforces its own
theorems: the figure places every circumference point at its true angular position
on the real circle, so "central = 2 × inscribed" and "same-segment equal" hold in
the actual drawing. Still display-only — the generator bakes every answer; the pose
only spins the whole figure for variety.

**Reason grading.** Each part is DBE two-column: 1 mark value + 1 mark reason
(``value_and_reason``, partial credit). ``CIRCLE_ANGLE_REASONS`` holds both used
theorems plus three real circle theorems as load-bearing distractors, so a student
can't win the reason mark by writing the same theorem for every part.
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import Problem

# Canonical circle-theorem id → accepted student phrasings (matched after NFC +
# lowercase + whitespace normalisation). The first two are the answers; the rest are
# valid theorems that are *wrong here* — distractors that keep the reason mark honest.
CIRCLE_ANGLE_REASONS: dict[str, list[str]] = {
    "same_segment": [
        "angles in the same segment",
        "∠s in the same segment",
        "angles in same segment",
        "∠s in same segment",
        "same segment",
        "angles subtended by the same arc",
        "angles on the same arc",
        "angles subtended by the same chord",
        "same arc",
    ],
    "centre_double_circumference": [
        "angle at centre = 2 × angle at circumference",
        "angle at the centre is twice the angle at the circumference",
        "angle at centre = 2 angle at circumference",
        "angle at centre = twice angle at circumference",
        "∠ at centre = 2 × ∠ at circumference",
        "∠ at centre = 2∠ at circumference",
        "angle at centre",
    ],
    # ── load-bearing distractors: real circle theorems, wrong for these parts ──
    "opp_angles_cyclic_quad": [
        "opposite angles of a cyclic quadrilateral",
        "opp angles of a cyclic quad",
        "opp ∠s of cyclic quad",
    ],
    "angle_in_semicircle": [
        "angle in a semi-circle",
        "angle in semicircle",
        "∠ in semi-circle",
    ],
    "tan_chord": [
        "tan-chord angle",
        "tangent-chord angle",
        "angle between tangent and chord",
    ],
}


def _verifier_spec() -> list[dict]:
    """Two DBE two-column parts: value (1) + reason (1) each, partial credit."""
    return [
        {
            "kind": "value_and_reason",
            "marks_possible": 2,
            "value_key": "answer_same_seg",
            "value_kind": "symbolic_equality",
            "reason_key": "reason_same_seg",
            "reason_set": CIRCLE_ANGLE_REASONS,
            "normalize": ["whitespace"],
        },
        {
            "kind": "value_and_reason",
            "marks_possible": 2,
            "value_key": "answer_central",
            "value_kind": "symbolic_equality",
            "reason_key": "reason_central",
            "reason_set": CIRCLE_ANGLE_REASONS,
            "normalize": ["whitespace"],
        },
    ]


# Circumference-point letters (role order A→B→C→D). O is always the centre (universal
# convention). Consecutive exam-plausible runs; O/I excluded (read as 0/1).
_VERTEX_NAMINGS: tuple[tuple[str, str, str, str], ...] = (
    ("A", "B", "C", "D"),
    ("P", "Q", "R", "S"),
    ("K", "L", "M", "N"),
    ("D", "E", "F", "G"),
    ("R", "S", "T", "U"),
    ("E", "F", "G", "H"),
)


def _generate(rng: random.Random) -> dict:
    c = rng.randint(24, 50)  # given inscribed ∠; central = 2c ∈ [48,100] (exam range)
    a, b, cc, dd = rng.choice(_VERTEX_NAMINGS)

    # True angular positions on the circle (layout degrees, y-up, CCW). The minor arc
    # AB sits at the bottom, centred on 270°, subtending 2c at O; C and D are on the
    # major arc (top), so AĈB = AD̂B = c and AÔB = 2c hold in the actual drawing.
    #
    # C and D are placed *relative to c* so no chord can become a diameter through O
    # (which would clutter the centre right where the central arc lives). A and B sit
    # at 270∓c, so their antipodes are at 90±c; offsetting C/D from the top by at least
    # (c + margin) keeps every chord to A/B clear of those antipodes. Symmetric offsets
    # also push the two inscribed vertices a clean distance apart (no overlapping
    # triangles), while keeping both on the major arc so each inscribed angle stays c.
    margin = 13.0
    pos = {
        "A": 270 - c,
        "B": 270 + c,
        "C": round(
            90 + c + margin + rng.uniform(0, 20), 1
        ),  # past B's antipode, up-left
        "D": round(
            90 - c - margin - rng.uniform(0, 20), 1
        ),  # past A's antipode, up-right
    }
    return {
        "c": c,
        "central_deg": 2 * c,
        "labels": {"O": "O", "A": a, "B": b, "C": cc, "D": dd},
        "pos": pos,
        "pose": {
            "rotate_deg": round(rng.uniform(0, 360), 1),
            "scale": round(rng.uniform(0.78, 1.0), 3),
            "reflect": rng.random() < 0.5,
        },
        "answer_same_seg": sympy.Integer(c),
        "reason_same_seg": "same_segment",
        "answer_central": sympy.Integer(2 * c),
        "reason_central": "centre_double_circumference",
    }


problem = Problem(
    id="circle_geometry_angle_chase",
    type_id="circle_geometry",
    name="Circle angle-chase: same-segment angle, then central angle (with reasons)",
    artifact_type="practice",
    problem_spec=_generate,
    verifier_spec=_verifier_spec(),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(registry=InMemoryRegistry({problem.id: problem}))
    _SURFACE = {
        "same_segment": "angles in the same segment",
        "centre_double_circumference": "angle at centre = 2 × angle at circumference",
    }
    for seed in (1, 7, 42):
        inst = engine.instantiate(problem.id, seed=seed)
        p = inst.params
        print(
            f"=== seed {seed} ===  given AĈB = {p['c']}°  "
            f"→ AD̂B = {p['answer_same_seg']}°, AÔB = {p['answer_central']}°"
        )
        correct = inst.verifier.rate(
            SolutionAttempt(
                steps=[
                    SubmittedStep(
                        {"value": cn["value"], "reason": _SURFACE[cn["reason"]]}
                    )
                    for cn in inst.verifier.canonicals
                ]
            )
        )
        # right values, but every part cites the same (centre-double) theorem — the
        # same-segment part should lose only its reason mark (semantic_error).
        swapped = inst.verifier.rate(
            SolutionAttempt(
                steps=[
                    SubmittedStep(
                        {
                            "value": cn["value"],
                            "reason": _SURFACE["centre_double_circumference"],
                        }
                    )
                    for cn in inst.verifier.canonicals
                ]
            )
        )
        print(
            f"    all-correct: {correct.marks_awarded}/{correct.marks_possible}"
            f"   one-reason-for-all: {swapped.marks_awarded}/{swapped.marks_possible}"
        )
