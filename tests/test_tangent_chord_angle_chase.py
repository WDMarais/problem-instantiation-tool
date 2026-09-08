"""
Tangent-chord angle-chase archetype (P2 Q10): tan-chord + central, with reasons.

A single compound problem with two ``value_and_reason`` sub-steps sharing one
circle figure and a tangent at the contact point A:

  step 0  AĈB = t   (tan-chord angle; C in the alternate segment)
  step 1  AÔB = 2t  (∠ at centre = 2 × ∠ at circumference)

Covered here: the generator emits the expected canonical reasons and the
central-is-twice relation; the given angle varies across seeds; the two-part
grading has teeth (partial credit isolates the value and reason marks); the
placement keeps C off a diameter through O; and — the property that makes this
archetype honest — the *drawn* figure is faithful (the tangent-chord angle, the
inscribed AĈB and the central AÔB all equal their baked values in the actual
geometry). The render-level circle/tangent invariants live in
test_geometry_circle.py.
"""

from __future__ import annotations

import math
import random

from content.examples.tangent_chord_angle_chase import (
    TANGENT_CHORD_REASONS,
    _generate,
    problem,
)
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import (
    MistakeType,
    SolutionAttempt,
    SubmittedStep,
)
from render.geometry import circle_point

# canonical reason id -> one accepted student surface phrasing
_SURFACE = {
    "tan_chord": "tan-chord angle",
    "centre_double_circumference": "angle at centre = 2 × angle at circumference",
}


def _engine() -> Engine:
    return Engine(registry=InMemoryRegistry({problem.id: problem}))


def _all_correct_steps(inst) -> list[dict]:
    return [
        {"value": cn["value"], "reason": _SURFACE[cn["reason"]]}
        for cn in inst.verifier.canonicals
    ]


# ── generator: the two theorems and the central-is-twice relation ────────────────


def test_canonicals_are_tan_chord_then_central_double():
    inst = _engine().instantiate(problem.id, seed=1)
    c0, c1 = inst.verifier.canonicals
    assert c0["reason"] == "tan_chord"
    assert c1["reason"] == "centre_double_circumference"
    assert c0["reason"] in TANGENT_CHORD_REASONS
    assert c1["reason"] in TANGENT_CHORD_REASONS


def test_inscribed_equals_given_and_central_is_twice():
    for seed in range(12):
        p = _generate(random.Random(seed))
        t = p["t"]
        assert int(p["answer_inscribed"]) == t  # AĈB = tan-chord angle
        assert int(p["answer_central"]) == 2 * t  # AÔB = 2 × AĈB (centre)
        assert p["central_deg"] == 2 * t


def test_given_angle_varies_across_seeds():
    givens = {_generate(random.Random(seed))["t"] for seed in range(30)}
    assert len(givens) >= 6  # not a constant figure
    assert all(26 <= t <= 48 for t in givens)  # exam-range tan-chord angle


# ── faithful geometry: the drawn angles equal the baked values ───────────────────


def _pt(cx, cy, deg):
    p = circle_point("_", cx, cy, 1.0, deg)
    return p.x, p.y


def _angle_at(vertex, p, q) -> float:
    """Interior angle p–vertex–q in degrees, from layout coordinates."""
    ux, uy = p[0] - vertex[0], p[1] - vertex[1]
    vx, vy = q[0] - vertex[0], q[1] - vertex[1]
    cos = (ux * vx + uy * vy) / (math.hypot(ux, uy) * math.hypot(vx, vy))
    return math.degrees(math.acos(max(-1.0, min(1.0, cos))))


def test_figure_is_faithful_tan_chord_inscribed_and_central():
    # The whole claim of the archetype: not schematic. Reconstruct A, B, C from the
    # generator's own angular positions and confirm the drawn tan-chord angle, the
    # inscribed AĈB and the central AÔB each equal the baked answer.
    for seed in range(40):
        p = _generate(random.Random(seed))
        t = p["t"]
        o = (0.0, 0.0)
        a = _pt(0, 0, p["pos"]["A"])
        b = _pt(0, 0, p["pos"]["B"])
        c = _pt(0, 0, p["pos"]["C"])
        # tangent direction at A = radius OA rotated 90°
        rad = math.radians(p["pos"]["A"])
        tangent = (a[0] - math.sin(rad), a[1] + math.cos(rad))  # a + tangent unit
        assert math.isclose(_angle_at(a, tangent, b), t, abs_tol=1e-6)  # tan-chord
        assert math.isclose(_angle_at(c, a, b), t, abs_tol=1e-6)  # inscribed AĈB
        assert math.isclose(_angle_at(o, a, b), 2 * t, abs_tol=1e-6)  # central AÔB


# ── placement: C stays off a diameter through O (the clutter guard) ───────────────


def test_C_stays_clear_of_the_antipodes_of_A_and_B():
    # A sits at 270 and B at 270+2t, so their antipodes are at 90 and 90+2t. A chord
    # from C to A or B becomes a diameter through the centre exactly when C lands on an
    # antipode — the same clutter the same-segment archetype guards against.
    for seed in range(60):
        p = _generate(random.Random(seed))
        t = p["t"]
        antipodes = (90.0, (90 + 2 * t) % 360)
        c = p["pos"]["C"] % 360
        gap = min(min(abs(c - anti), 360 - abs(c - anti)) for anti in antipodes)
        assert gap >= 12.0, f"seed {seed}: C within {gap:.1f}° of a diameter"


# ── grading teeth: value and reason marks move independently ─────────────────────


def test_all_correct_scores_full():
    inst = _engine().instantiate(problem.id, seed=7)
    r = inst.verifier.rate(
        SolutionAttempt(steps=[SubmittedStep(s) for s in _all_correct_steps(inst)])
    )
    assert r.marks_awarded == 4 and r.marks_possible == 4 and r.is_correct


def test_one_reason_for_all_loses_only_the_mis_cited_reason_mark():
    # right values everywhere, but both parts cite the centre-double theorem — the
    # tan-chord part must keep its value mark and lose just its reason mark.
    inst = _engine().instantiate(problem.id, seed=7)
    both_central = [
        {"value": cn["value"], "reason": _SURFACE["centre_double_circumference"]}
        for cn in inst.verifier.canonicals
    ]
    r = inst.verifier.rate(
        SolutionAttempt(steps=[SubmittedStep(s) for s in both_central])
    )
    assert r.marks_awarded == 3  # 4 − the one wrong reason
    assert r.steps[0].mistake_type == MistakeType.semantic_error  # tan-chord reason
    assert r.steps[1].mistake_type == MistakeType.correct  # central part fully right


def test_wrong_value_keeps_the_reason_mark():
    inst = _engine().instantiate(problem.id, seed=7)
    steps = _all_correct_steps(inst)
    steps[0]["value"] = int(inst.verifier.canonicals[0]["value"]) + 5  # miscompute AĈB
    r = inst.verifier.rate(SolutionAttempt(steps=[SubmittedStep(s) for s in steps]))
    assert r.marks_awarded == 3  # lost only the tan-chord value mark
    assert r.steps[0].mistake_type == MistakeType.computation_error


def test_reason_outside_the_set_is_rejected_not_fuzzy_matched():
    inst = _engine().instantiate(problem.id, seed=7)
    steps = _all_correct_steps(inst)
    steps[1]["reason"] = "because the arc looks bigger"  # not a theorem in the set
    r = inst.verifier.rate(SolutionAttempt(steps=[SubmittedStep(s) for s in steps]))
    assert r.marks_awarded == 3  # central value kept, its reason rejected
    assert r.steps[1].mistake_type == MistakeType.semantic_error


# ── the shared figure (with a tangent) is present ────────────────────────────────


def test_template_emits_a_circle_figure_with_a_tangent():
    from worksheets.generate import template_tangent_chord_angle_chase

    card = template_tangent_chord_angle_chase(_generate(random.Random(3)))
    assert 'fill="none"' in card.graph_svg  # the circle outline (an unfilled ring)
    assert len(card.subparts) == 2
    assert sum(sp.auto_marks for sp in card.subparts) == 4
