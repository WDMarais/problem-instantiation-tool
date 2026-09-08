"""
Cyclic-quad angle-chase archetype (P2 Q11): opposite angle + exterior angle.

A single compound problem with two ``value_and_reason`` sub-steps sharing one
circle figure (a cyclic quadrilateral ABCD with side BC produced to E):

  step 0  BĈD = 180 - a  (opposite angles of a cyclic quad)
  step 1  DĈE = a        (exterior angle of a cyclic quad = interior opposite)

Covered here: the generator emits the expected canonical reasons and the
supplementary / exterior relations; the given angle varies across seeds; the
two-part grading has teeth (partial credit isolates the value and reason marks);
and — the property that makes this archetype honest — the *drawn* figure is
faithful (the given ∠DAB, the interior BĈD and the exterior DĈE all equal their
baked values in the actual geometry). Render-level circle invariants live in
test_geometry_circle.py.
"""

from __future__ import annotations

import math
import random

from content.examples.cyclic_quad_opposite_angles import (
    CYCLIC_QUAD_REASONS,
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
    "opp_angles_cyclic_quad": "opp ∠s of cyclic quad",
    "ext_angle_cyclic_quad": "ext ∠ of cyclic quad",
}


def _engine() -> Engine:
    return Engine(registry=InMemoryRegistry({problem.id: problem}))


def _all_correct_steps(inst) -> list[dict]:
    return [
        {"value": cn["value"], "reason": _SURFACE[cn["reason"]]}
        for cn in inst.verifier.canonicals
    ]


# ── generator: the two theorems and the supplementary / exterior relations ───────


def test_canonicals_are_opposite_then_exterior():
    inst = _engine().instantiate(problem.id, seed=1)
    c0, c1 = inst.verifier.canonicals
    assert c0["reason"] == "opp_angles_cyclic_quad"
    assert c1["reason"] == "ext_angle_cyclic_quad"
    assert c0["reason"] in CYCLIC_QUAD_REASONS
    assert c1["reason"] in CYCLIC_QUAD_REASONS


def test_opposite_is_supplement_and_exterior_equals_given():
    for seed in range(12):
        p = _generate(random.Random(seed))
        a = p["a"]
        assert int(p["answer_opposite"]) == 180 - a  # BĈD supplements ∠A
        assert int(p["answer_exterior"]) == a  # DĈE = interior opposite ∠A


def test_given_angle_varies_across_seeds():
    givens = {_generate(random.Random(seed))["a"] for seed in range(30)}
    assert len(givens) >= 6  # not a constant figure
    assert all(55 <= a <= 80 for a in givens)  # exam-range acute given angle


# ── faithful geometry: the drawn angles equal the baked values ───────────────────


def _pt(deg):
    p = circle_point("_", 0.0, 0.0, 1.0, deg)
    return p.x, p.y


def _angle_at(vertex, p, q) -> float:
    """Interior angle p–vertex–q in degrees, from layout coordinates."""
    ux, uy = p[0] - vertex[0], p[1] - vertex[1]
    vx, vy = q[0] - vertex[0], q[1] - vertex[1]
    cos = (ux * vx + uy * vy) / (math.hypot(ux, uy) * math.hypot(vx, vy))
    return math.degrees(math.acos(max(-1.0, min(1.0, cos))))


def test_figure_is_faithful_given_opposite_and_exterior():
    # The archetype's claim: not schematic. Reconstruct the vertices (and E on BC
    # produced) from the generator's angular positions and confirm the drawn ∠DAB,
    # the interior BĈD and the exterior DĈE each equal their baked answer.
    for seed in range(40):
        p = _generate(random.Random(seed))
        a = p["a"]
        pos = p["pos"]
        A, B, C, D = (_pt(pos[k]) for k in ("A", "B", "C", "D"))
        ux, uy = C[0] - B[0], C[1] - B[1]
        n = math.hypot(ux, uy) or 1.0
        E = (C[0] + ux / n * 0.55, C[1] + uy / n * 0.55)  # BC produced beyond C
        assert math.isclose(_angle_at(A, D, B), a, abs_tol=1e-6)  # given ∠DAB
        assert math.isclose(_angle_at(C, B, D), 180 - a, abs_tol=1e-6)  # BĈD
        assert math.isclose(_angle_at(C, D, E), a, abs_tol=1e-6)  # DĈE


# ── grading teeth: value and reason marks move independently ─────────────────────


def test_all_correct_scores_full():
    inst = _engine().instantiate(problem.id, seed=7)
    r = inst.verifier.rate(
        SolutionAttempt(steps=[SubmittedStep(s) for s in _all_correct_steps(inst)])
    )
    assert r.marks_awarded == 4 and r.marks_possible == 4 and r.is_correct


def test_one_reason_for_all_loses_only_the_mis_cited_reason_mark():
    # right values everywhere, but both parts cite opposite-angles — the exterior
    # part must keep its value mark and lose just its reason mark.
    inst = _engine().instantiate(problem.id, seed=7)
    both_opp = [
        {"value": cn["value"], "reason": _SURFACE["opp_angles_cyclic_quad"]}
        for cn in inst.verifier.canonicals
    ]
    r = inst.verifier.rate(SolutionAttempt(steps=[SubmittedStep(s) for s in both_opp]))
    assert r.marks_awarded == 3  # 4 − the one wrong reason
    assert r.steps[0].mistake_type == MistakeType.correct  # opposite part fully right
    assert r.steps[1].mistake_type == MistakeType.semantic_error  # exterior reason


def test_wrong_value_keeps_the_reason_mark():
    inst = _engine().instantiate(problem.id, seed=7)
    steps = _all_correct_steps(inst)
    steps[0]["value"] = int(inst.verifier.canonicals[0]["value"]) + 5  # miscompute BĈD
    r = inst.verifier.rate(SolutionAttempt(steps=[SubmittedStep(s) for s in steps]))
    assert r.marks_awarded == 3  # lost only the opposite-angle value mark
    assert r.steps[0].mistake_type == MistakeType.computation_error


def test_reason_outside_the_set_is_rejected_not_fuzzy_matched():
    inst = _engine().instantiate(problem.id, seed=7)
    steps = _all_correct_steps(inst)
    steps[1]["reason"] = "because it looks the same"  # not a theorem in the set
    r = inst.verifier.rate(SolutionAttempt(steps=[SubmittedStep(s) for s in steps]))
    assert r.marks_awarded == 3  # exterior value kept, its reason rejected
    assert r.steps[1].mistake_type == MistakeType.semantic_error


# ── the shared figure is present ─────────────────────────────────────────────────


def test_template_emits_a_circle_figure():
    from worksheets.generate import template_cyclic_quad_opposite_angles

    card = template_cyclic_quad_opposite_angles(_generate(random.Random(3)))
    assert 'fill="none"' in card.graph_svg  # the circle outline (an unfilled ring)
    assert len(card.subparts) == 2
    assert sum(sp.auto_marks for sp in card.subparts) == 4
