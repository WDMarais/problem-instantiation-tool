"""
Cyclic-quadrilateral angle-chase — opposite angles, then the exterior angle.

Third Euclidean circle-theorem consumer of render/geometry.py. A, B, C, D lie in
order on a circle (a cyclic quadrilateral) and side BC is *produced* to E. The
*given* is the interior angle at A; the student chases two more, each a two-column
statement/reason, using two DISTINCT cyclic-quad theorems:

  11.1  BĈD  (interior, opposite A)      = 180 - a   reason: opp ∠s of cyclic quad
  11.2  DĈE  (exterior, on BC produced)  = a         reason: ext ∠ of cyclic quad

Sibling of ``circle_geometry_angle_chase`` and ``tangent_chord_angle_chase`` (same
compound shape, distinct theorems). Pairing opposite-angles with the exterior-angle
theorem gives two different reasons AND two distinct values (180-a and a) from the
one given, so neither the value nor the reason facet is a give-away — and the
closed reason-set has exactly one right theorem per part.

**Faithful, not merely schematic.** The four vertices sit at true angular
positions chosen so the inscribed angle DÂB equals a (the arc BCD it subtends is
2a), which forces BĈD = 180 - a in the actual drawing (A and C are on opposite
arcs of chord BD). E is placed exactly collinear on BC produced, so DĈE is the
true supplement of BĈD and equals a. The pose only spins the whole figure.

**Reason grading.** Each part is DBE two-column: 1 mark value + 1 mark reason
(``value_and_reason``, partial credit). ``CYCLIC_QUAD_REASONS`` holds the two used
theorems plus three real circle theorems as load-bearing distractors.
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import Problem

# Canonical circle-theorem id → accepted student phrasings (matched after NFC +
# lowercase + whitespace normalisation). The first two are the answers; the rest are
# valid theorems that are *wrong here* — distractors that keep the reason mark honest.
CYCLIC_QUAD_REASONS: dict[str, list[str]] = {
    "opp_angles_cyclic_quad": [
        "opposite angles of a cyclic quadrilateral",
        "opposite angles of a cyclic quad",
        "opp angles of a cyclic quad",
        "opp ∠s of cyclic quad",
        "opp ∠s of a cyclic quad",
        "opposite angles of cyclic quad",
        "opp ∠s cyclic quad",
    ],
    "ext_angle_cyclic_quad": [
        "exterior angle of a cyclic quadrilateral",
        "exterior angle of a cyclic quad",
        "exterior angle of cyclic quad",
        "ext angle of cyclic quad",
        "ext ∠ of cyclic quad",
        "ext ∠ of a cyclic quad",
        "exterior angle of a cyclic quad = interior opposite angle",
        "ext ∠ cyclic quad",
    ],
    # ── load-bearing distractors: real circle theorems, wrong for these parts ──
    "same_segment": [
        "angles in the same segment",
        "∠s in the same segment",
        "same segment",
    ],
    "centre_double_circumference": [
        "angle at centre = 2 × angle at circumference",
        "∠ at centre = 2 × ∠ at circumference",
        "angle at centre",
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
            "value_key": "answer_opposite",
            "value_kind": "symbolic_equality",
            "reason_key": "reason_opposite",
            "reason_set": CYCLIC_QUAD_REASONS,
            "normalize": ["whitespace"],
        },
        {
            "kind": "value_and_reason",
            "marks_possible": 2,
            "value_key": "answer_exterior",
            "value_kind": "symbolic_equality",
            "reason_key": "reason_exterior",
            "reason_set": CYCLIC_QUAD_REASONS,
            "normalize": ["whitespace"],
        },
    ]


# Point letters by role: (vertex A given, B, C where the angles sit, D, exterior E).
# O/I excluded (read as 0/1); the four vertices go A→B→C→D around the circle.
_VERTEX_NAMINGS: tuple[tuple[str, str, str, str, str], ...] = (
    ("A", "B", "C", "D", "E"),
    ("P", "Q", "R", "S", "T"),
    ("K", "L", "M", "N", "T"),
    ("D", "E", "F", "G", "H"),
    ("W", "X", "Y", "Z", "V"),
)


def _generate(rng: random.Random) -> dict:
    a = rng.randint(55, 80)  # given interior ∠A (∠DAB), acute; 180-a ∈ [100,125]
    aa, bb, cc, dd, ee = rng.choice(_VERTEX_NAMINGS)

    # True angular positions (layout degrees, y-up, CCW), vertices in order A→B→C→D.
    # ∠DAB is inscribed on chord BD and subtends arc B→C→D = arc_BC + arc_CD, so we
    # set arc_BC + arc_CD = 2a to make the drawn ∠A exactly a. The remaining arcs
    # (AB, DA) share 360 - 2a. Jitter varies the quad's shape without touching ∠A;
    # every arc stays ≳ 40° so no two vertices crowd.
    j1 = rng.uniform(-14, 14)
    j2 = rng.uniform(-22, 22)
    arc_ab = (180 - a) + j2
    arc_bc = a + j1
    arc_cd = a - j1
    pos_a = 90.0
    pos_b = (pos_a + arc_ab) % 360
    pos_c = (pos_b + arc_bc) % 360
    pos_d = (pos_c + arc_cd) % 360
    pos = {"A": pos_a, "B": pos_b, "C": pos_c, "D": pos_d}

    return {
        "a": a,
        "given_deg": a,
        "labels": {"A": aa, "B": bb, "C": cc, "D": dd, "E": ee},
        "pos": pos,
        "pose": {
            "rotate_deg": round(rng.uniform(0, 360), 1),
            "scale": round(rng.uniform(0.78, 1.0), 3),
            "reflect": rng.random() < 0.5,
        },
        "answer_opposite": sympy.Integer(180 - a),
        "reason_opposite": "opp_angles_cyclic_quad",
        "answer_exterior": sympy.Integer(a),
        "reason_exterior": "ext_angle_cyclic_quad",
    }


problem = Problem(
    id="cyclic_quad_opposite_angles",
    type_id="circle_geometry",
    name="Cyclic-quad angle-chase: opposite angle, then exterior angle",
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
        "opp_angles_cyclic_quad": "opp ∠s of cyclic quad",
        "ext_angle_cyclic_quad": "ext ∠ of cyclic quad",
    }
    for seed in (1, 7, 42):
        inst = engine.instantiate(problem.id, seed=seed)
        p = inst.params
        print(
            f"=== seed {seed} ===  given ∠A = {p['a']}°  "
            f"→ BĈD = {p['answer_opposite']}°, DĈE = {p['answer_exterior']}°"
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
        # both parts cite opposite-angles — the exterior part should lose only its
        # reason mark (semantic_error), keeping its value mark.
        swapped = inst.verifier.rate(
            SolutionAttempt(
                steps=[
                    SubmittedStep(
                        {
                            "value": cn["value"],
                            "reason": _SURFACE["opp_angles_cyclic_quad"],
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
