"""
The ``value_and_reason`` compound step — DBE two-column (statement/reason)
marking. A geometry angle-chase scores value + reason: the right angle with no
cited theorem is the classic "knows the number, not the why" case and must lose
the reason mark (and, fused, the whole mark). The reason is graded by closed-set
alias membership — never NLP — so a phrasing outside the curated list is wrong.
"""

import pytest

from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.exceptions import CanonicalResolutionError
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import (
    MistakeType,
    Problem,
    SolutionAttempt,
    SubmittedStep,
)

REASONS = {
    "opp_angles": [
        "opposite angles of a parallelogram",
        "opp angles of a parm",
        "opp ∠s of parm",
    ],
    "cointerior": ["co-interior angles", "cointerior angles"],
    "alternate": ["alternate angles", "alt angles", "z angles"],
}


def _problem(pid, value, reason_id, spec_extra=None):
    spec = {
        "kind": "value_and_reason",
        "marks_possible": 2,
        "value_key": "answer",
        "reason_key": "reason",
        "reason_set": REASONS,
        "normalize": ["whitespace"],
    }
    spec.update(spec_extra or {})
    return Problem(
        id=pid,
        type_id=pid,
        name=pid,
        artifact_type="practice",
        problem_spec=lambda rng: {"answer": value, "reason": reason_id},
        verifier_spec=[spec],
    )


def _rate(problem, value, reason):
    eng = Engine(registry=InMemoryRegistry({problem.id: problem}))
    inst = eng.instantiate(problem.id, seed=0)
    attempt = SolutionAttempt(steps=[SubmittedStep({"value": value, "reason": reason})])
    return inst.verifier.rate(attempt)


# --- partial credit (S/R marking): the four quadrants -----------------------


def test_value_and_reason_both_correct_scores_full():
    prob = _problem("vr_full", 118, "opp_angles")
    r = _rate(prob, 118, "opposite angles of a parallelogram")
    assert r.marks_awarded == 2 and r.is_correct
    assert r.steps[0].mistake_type == MistakeType.correct


def test_value_right_reason_wrong_is_semantic_error_keeps_value_mark():
    # right number, but a *distractor* theorem from the same set → the S/R signal
    prob = _problem("vr_sem", 118, "opp_angles")
    r = _rate(prob, 118, "co-interior angles")
    assert r.marks_awarded == 1 and not r.is_correct
    assert r.steps[0].mistake_type == MistakeType.semantic_error


def test_value_wrong_reason_right_is_computation_error_keeps_reason_mark():
    prob = _problem("vr_comp", 118, "opp_angles")
    r = _rate(prob, 117, "opposite angles of a parallelogram")
    assert r.marks_awarded == 1 and not r.is_correct
    assert r.steps[0].mistake_type == MistakeType.computation_error


def test_both_wrong_scores_zero():
    prob = _problem("vr_zero", 118, "opp_angles")
    r = _rate(prob, 117, "alternate angles")
    assert r.marks_awarded == 0
    assert r.steps[0].mistake_type == MistakeType.computation_error


# --- the reason set is closed, matched by alias after normalization ----------


def test_alias_phrasing_is_accepted():
    prob = _problem("vr_alias", 118, "opp_angles")
    for alias in ("opp angles of a parm", "opp ∠s of parm"):
        assert _rate(prob, 118, alias).marks_awarded == 2, alias


def test_case_and_whitespace_are_normalized():
    prob = _problem("vr_norm", 118, "opp_angles")
    assert (
        _rate(prob, 118, "  Opposite   Angles of a Parallelogram ").marks_awarded == 2
    )


def test_a_phrasing_outside_the_set_is_wrong_not_fuzzy_matched():
    # close but not an enumerated alias → wrong; proves it is closed, not fuzzy
    prob = _problem("vr_closed", 118, "opp_angles")
    r = _rate(prob, 118, "opposite angles because it's a parallelogram shape")
    assert r.marks_awarded == 1  # value kept, reason rejected
    assert r.steps[0].mistake_type == MistakeType.semantic_error


# --- fused (all-or-nothing) marking -----------------------------------------


def test_fused_requires_both_facets_for_any_mark():
    prob = _problem("vr_fused", 118, "opp_angles", {"partial_credit": False})
    assert _rate(prob, 118, "opposite angles of a parallelogram").marks_awarded == 2
    # value right, reason wrong → the DBE "unjustified answer earns nothing"
    fused = _rate(prob, 118, "alternate angles")
    assert fused.marks_awarded == 0
    assert fused.steps[0].mistake_type == MistakeType.semantic_error


# --- authoring guards fire at instantiation, not silently -------------------


def test_reason_id_not_in_set_raises_at_instantiation():
    prob = _problem("vr_badid", 118, "not_a_real_reason_id")
    eng = Engine(registry=InMemoryRegistry({prob.id: prob}))
    with pytest.raises(CanonicalResolutionError):
        eng.instantiate(prob.id, seed=0)


def test_missing_reason_set_raises_at_instantiation():
    prob = _problem("vr_noset", 118, "opp_angles", {"reason_set": None})
    eng = Engine(registry=InMemoryRegistry({prob.id: prob}))
    with pytest.raises(CanonicalResolutionError):
        eng.instantiate(prob.id, seed=0)


def test_non_dict_attempt_is_rejected():
    from problem_instantiation_tool.exceptions import AttemptValidationError

    prob = _problem("vr_baddict", 118, "opp_angles")
    eng = Engine(registry=InMemoryRegistry({prob.id: prob}))
    inst = eng.instantiate(prob.id, seed=0)
    attempt = SolutionAttempt(steps=[SubmittedStep(118)])  # bare value, no reason
    with pytest.raises(AttemptValidationError):
        inst.verifier.rate(attempt)
