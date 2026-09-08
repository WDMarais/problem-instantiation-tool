"""
Tangent-chord angle-chase — tan-chord + central angle, with reasons.

Second Euclidean circle-theorem consumer of render/geometry.py, and the first to
use a tangent (the ``tangent_point`` helper). O is the centre; A, B, C lie on the
circle and a tangent touches at A. The *given* is the tangent-chord angle between
the tangent and chord AB; the student chases two more, each a two-column
statement/reason:

  10.1  AĈB  (C in the alternate segment)  = t    reason: tan-chord angle
  10.2  AÔB  (central angle on chord AB)    = 2t   reason: ∠ at centre = 2 × ∠ at circ.

Sibling of ``circle_geometry_angle_chase`` (same compound shape, distinct first
theorem). Giving the tangent-chord angle makes 10.1 a single clean theorem (the
tan-chord angle equals the inscribed angle in the alternate segment), and 10.2 the
centre-is-twice rule — no two-valid-reasons ambiguity for the closed reason-set.

**Faithful, not merely schematic.** A is placed at the bottom of the circle so the
tangent (⟂ the vertical radius OA) is horizontal; B is at central angle 2t from A,
which makes chord AB rise at exactly t above the tangent — so the *drawn*
tangent-chord angle equals t, AĈB from the alternate arc equals t, and AÔB equals
2t, all in the actual drawing. The pose only spins the whole figure for variety.

**Reason grading.** Each part is DBE two-column: 1 mark value + 1 mark reason
(``value_and_reason``, partial credit). ``TANGENT_CHORD_REASONS`` holds the two used
theorems plus three real circle theorems as load-bearing distractors.
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import Problem

# Canonical circle-theorem id → accepted student phrasings (matched after NFC +
# lowercase + whitespace normalisation). The first two are the answers; the rest are
# valid theorems that are *wrong here* — distractors that keep the reason mark honest.
TANGENT_CHORD_REASONS: dict[str, list[str]] = {
    "tan_chord": [
        "tan-chord angle",
        "tangent-chord angle",
        "angle between tangent and chord",
        "tan chord",
        "angle between a tangent and a chord",
        "tangent chord angle",
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
    "same_segment": [
        "angles in the same segment",
        "∠s in the same segment",
        "same segment",
    ],
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
}


def _verifier_spec() -> list[dict]:
    """Two DBE two-column parts: value (1) + reason (1) each, partial credit."""
    return [
        {
            "kind": "value_and_reason",
            "marks_possible": 2,
            "value_key": "answer_inscribed",
            "value_kind": "symbolic_equality",
            "reason_key": "reason_inscribed",
            "reason_set": TANGENT_CHORD_REASONS,
            "normalize": ["whitespace"],
        },
        {
            "kind": "value_and_reason",
            "marks_possible": 2,
            "value_key": "answer_central",
            "value_kind": "symbolic_equality",
            "reason_key": "reason_central",
            "reason_set": TANGENT_CHORD_REASONS,
            "normalize": ["whitespace"],
        },
    ]


# Point letters by role: (contact A, chord end B, inscribed C, tangent-ray end M).
# O is always the centre. O/I excluded (read as 0/1); exam-plausible runs.
_VERTEX_NAMINGS: tuple[tuple[str, str, str, str], ...] = (
    ("A", "B", "C", "T"),
    ("P", "Q", "R", "S"),
    ("K", "L", "M", "N"),
    ("D", "E", "F", "G"),
    ("R", "S", "T", "U"),
)


def _generate(rng: random.Random) -> dict:
    t = rng.randint(26, 48)  # tan-chord angle; central = 2t ∈ [52,96] (exam range)
    a, b, cc, m = rng.choice(_VERTEX_NAMINGS)

    # True angular positions (layout degrees, y-up, CCW). A (the contact) sits at the
    # bottom (270°) so the tangent is horizontal; B is 2t further round, so the minor
    # arc AB subtends 2t at O and chord AB rises exactly t above the tangent. C is on
    # the major (alternate) arc, offset past B's antipode (90+2t) by a margin so no
    # chord CA/CB is a diameter through O (same clutter guard as the same-segment
    # archetype). Then the drawn tan-chord angle = AĈB = t and AÔB = 2t.
    margin = 14.0
    pos = {
        "A": 270.0,
        "B": (270 + 2 * t) % 360,
        "C": (90 + 2 * t + margin + rng.uniform(0, 18)) % 360,
    }
    return {
        "t": t,
        "central_deg": 2 * t,
        "contact_deg": 270.0,  # A, so the scene builder knows where the tangent touches
        "labels": {"O": "O", "A": a, "B": b, "C": cc, "M": m},
        "pos": pos,
        "pose": {
            "rotate_deg": round(rng.uniform(0, 360), 1),
            "scale": round(rng.uniform(0.78, 1.0), 3),
            "reflect": rng.random() < 0.5,
        },
        "answer_inscribed": sympy.Integer(t),
        "reason_inscribed": "tan_chord",
        "answer_central": sympy.Integer(2 * t),
        "reason_central": "centre_double_circumference",
    }


problem = Problem(
    id="tangent_chord_angle_chase",
    type_id="circle_geometry",
    name="Tangent-chord angle-chase: alternate-segment angle, then central",
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
        "tan_chord": "tan-chord angle",
        "centre_double_circumference": "angle at centre = 2 × angle at circumference",
    }
    for seed in (1, 7, 42):
        inst = engine.instantiate(problem.id, seed=seed)
        p = inst.params
        print(
            f"=== seed {seed} ===  given tan-chord = {p['t']}°  "
            f"→ AĈB = {p['answer_inscribed']}°, AÔB = {p['answer_central']}°"
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
        # tan-chord part should lose only its reason mark (semantic_error).
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
