"""
Circle angle-chase archetype (P2 Q9): central-angle + same-segment, with reasons.

A single compound problem with two ``value_and_reason`` sub-steps sharing one
circle figure:

  step 0  AD̂B = c   (same segment as the given AĈB)
  step 1  AÔB = 2c  (∠ at centre = 2 × ∠ at circumference)

Covered here: the generator emits the expected canonical reasons and the
central-is-twice relation; the given angle varies across seeds; the two-part
grading has teeth (partial credit isolates the value and reason marks); and the
placement keeps every chord clear of a diameter through O (the clutter fix). The
render-level circle invariants live in test_geometry_circle.py.
"""

from __future__ import annotations

import random

from content.examples.circle_geometry_angle_chase import (
    CIRCLE_ANGLE_REASONS,
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

# canonical reason id -> one accepted student surface phrasing
_SURFACE = {
    "same_segment": "angles in the same segment",
    "centre_double_circumference": "angle at centre = 2 × angle at circumference",
}


def _engine() -> Engine:
    return Engine(registry=InMemoryRegistry({problem.id: problem}))


def _rate(steps: list[dict], seed: int = 7):
    inst = _engine().instantiate(problem.id, seed=seed)
    attempt = SolutionAttempt(steps=[SubmittedStep(s) for s in steps])
    return inst.verifier.rate(attempt), inst


def _all_correct_steps(inst) -> list[dict]:
    return [
        {"value": cn["value"], "reason": _SURFACE[cn["reason"]]}
        for cn in inst.verifier.canonicals
    ]


# ── generator: the two theorems and the central-is-twice relation ────────────────


def test_canonicals_are_same_segment_then_central_double():
    inst = _engine().instantiate(problem.id, seed=1)
    c0, c1 = inst.verifier.canonicals
    assert c0["reason"] == "same_segment"
    assert c1["reason"] == "centre_double_circumference"
    assert c0["reason"] in CIRCLE_ANGLE_REASONS
    assert c1["reason"] in CIRCLE_ANGLE_REASONS


def test_same_segment_equals_given_and_central_is_twice():
    for seed in range(12):
        p = _generate(random.Random(seed))
        c = p["c"]
        assert int(p["answer_same_seg"]) == c  # AD̂B = AĈB (same segment)
        assert int(p["answer_central"]) == 2 * c  # AÔB = 2 × AĈB (centre)
        assert p["central_deg"] == 2 * c


def test_given_angle_varies_across_seeds():
    givens = {_generate(random.Random(seed))["c"] for seed in range(30)}
    assert len(givens) >= 6  # not a constant figure
    assert all(24 <= c <= 50 for c in givens)  # exam-range inscribed angle


# ── placement: no chord to A or B is a diameter through O (the clutter fix) ───────


def test_C_and_D_stay_clear_of_the_antipodes_of_A_and_B():
    # A, B sit at 270∓c, so their antipodes are at 90±c. A chord from C (or D) to A
    # or B becomes a diameter through the centre exactly when the circumference point
    # lands on an antipode — that was the seed-1 clutter. Placement must keep a margin.
    for seed in range(60):
        p = _generate(random.Random(seed))
        c = p["c"]
        antipodes = (90 + c, 90 - c)
        for pt in ("C", "D"):
            gap = min(abs(p["pos"][pt] - anti) for anti in antipodes)
            assert gap >= 12.0, f"seed {seed}: {pt} within {gap:.1f}° of a diameter"


# ── grading teeth: value and reason marks move independently ─────────────────────


def test_all_correct_scores_full():
    inst = _engine().instantiate(problem.id, seed=7)
    r = inst.verifier.rate(
        SolutionAttempt(steps=[SubmittedStep(s) for s in _all_correct_steps(inst)])
    )
    assert r.marks_awarded == 4 and r.marks_possible == 4 and r.is_correct


def test_one_reason_for_all_loses_only_the_mis_cited_reason_mark():
    # right values everywhere, but both parts cite the centre-double theorem — the
    # same-segment part must keep its value mark and lose just its reason mark.
    inst = _engine().instantiate(problem.id, seed=7)
    both_central = [
        {"value": cn["value"], "reason": _SURFACE["centre_double_circumference"]}
        for cn in inst.verifier.canonicals
    ]
    r = inst.verifier.rate(
        SolutionAttempt(steps=[SubmittedStep(s) for s in both_central])
    )
    assert r.marks_awarded == 3  # 4 − the one wrong reason
    assert r.steps[0].mistake_type == MistakeType.semantic_error  # same-segment reason
    assert r.steps[1].mistake_type == MistakeType.correct  # central part fully right


def test_wrong_value_keeps_the_reason_mark():
    inst = _engine().instantiate(problem.id, seed=7)
    steps = _all_correct_steps(inst)
    steps[0]["value"] = int(inst.verifier.canonicals[0]["value"]) + 5  # miscompute AD̂B
    r = inst.verifier.rate(SolutionAttempt(steps=[SubmittedStep(s) for s in steps]))
    assert r.marks_awarded == 3  # lost only the same-segment value mark
    assert r.steps[0].mistake_type == MistakeType.computation_error


def test_reason_outside_the_set_is_rejected_not_fuzzy_matched():
    inst = _engine().instantiate(problem.id, seed=7)
    steps = _all_correct_steps(inst)
    steps[1]["reason"] = "because the arc looks bigger"  # not a theorem in the set
    r = inst.verifier.rate(SolutionAttempt(steps=[SubmittedStep(s) for s in steps]))
    assert r.marks_awarded == 3  # central value kept, its reason rejected
    assert r.steps[1].mistake_type == MistakeType.semantic_error


# ── the shared figure is present ─────────────────────────────────────────────────


def test_template_emits_a_circle_figure():
    from worksheets.generate import template_circle_geometry_angle_chase

    card = template_circle_geometry_angle_chase(_generate(random.Random(3)))
    assert 'fill="none"' in card.graph_svg  # the circle outline (an unfilled ring)
    assert len(card.subparts) == 2
    assert sum(sp.auto_marks for sp in card.subparts) == 4
