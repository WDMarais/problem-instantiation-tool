"""
Reason-grading for the parallelogram angle-chases (the value_and_reason pilot).

The label/template variety lives in test_parallelogram_labels.py; this file
covers the new S/R marking: each variant grades the angle value and the cited
theorem jointly, with the other two theorems as load-bearing distractors.
"""

from __future__ import annotations

import pytest

from content.examples.parallelogram_angles import (
    PARALLELOGRAM_REASONS,
    parallelogram_alternate,
    parallelogram_cointerior,
    parallelogram_opposite,
)
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import (
    MistakeType,
    SolutionAttempt,
    SubmittedStep,
)

# problem → (its canonical reason id, one accepted surface, a distractor surface)
_CASES = [
    (
        parallelogram_cointerior,
        "cointerior_angles",
        "co-interior angles",
        "alternate angles",
    ),
    (
        parallelogram_opposite,
        "opp_angles_parallelogram",
        "opposite angles of a parallelogram",
        "co-interior angles",
    ),
    (
        parallelogram_alternate,
        "alternate_angles",
        "alt angles",
        "opposite angles of a parallelogram",
    ),
]
_IDS = [c[0].id for c in _CASES]


def _engine(problem):
    return Engine(registry=InMemoryRegistry({problem.id: problem}))


def _rate(problem, value, reason, seed=7):
    inst = _engine(problem).instantiate(problem.id, seed=seed)
    val = inst.verifier.canonicals[0]["value"] if value is None else value
    attempt = SolutionAttempt(steps=[SubmittedStep({"value": val, "reason": reason})])
    return inst.verifier.rate(attempt), inst


@pytest.mark.parametrize("problem,rid,good,distractor", _CASES, ids=_IDS)
def test_generator_emits_the_expected_canonical_reason(problem, rid, good, distractor):
    inst = _engine(problem).instantiate(problem.id, seed=1)
    assert inst.params["reason"] == rid
    assert inst.verifier.canonicals[0]["reason"] == rid
    assert rid in PARALLELOGRAM_REASONS


@pytest.mark.parametrize("problem,rid,good,distractor", _CASES, ids=_IDS)
def test_correct_value_and_reason_scores_full(problem, rid, good, distractor):
    r, _ = _rate(problem, None, good)
    assert r.marks_awarded == 2 and r.is_correct
    assert r.steps[0].mistake_type == MistakeType.correct


@pytest.mark.parametrize("problem,rid,good,distractor", _CASES, ids=_IDS)
def test_right_angle_distractor_reason_keeps_value_loses_reason(
    problem, rid, good, distractor
):
    # a *plausible* wrong theorem from the same set — the comprehension-edge signal
    r, _ = _rate(problem, None, distractor)
    assert r.marks_awarded == 1 and not r.is_correct
    assert r.steps[0].mistake_type == MistakeType.semantic_error


@pytest.mark.parametrize("problem,rid,good,distractor", _CASES, ids=_IDS)
def test_wrong_angle_right_reason_keeps_reason_mark(problem, rid, good, distractor):
    inst = _engine(problem).instantiate(problem.id, seed=7)
    wrong = int(inst.verifier.canonicals[0]["value"]) + 7
    r, _ = _rate(problem, wrong, good)
    assert r.marks_awarded == 1 and not r.is_correct
    assert r.steps[0].mistake_type == MistakeType.computation_error


@pytest.mark.parametrize("problem,rid,good,distractor", _CASES, ids=_IDS)
def test_reason_outside_the_set_is_wrong(problem, rid, good, distractor):
    r, _ = _rate(problem, None, "because the diagram looks like it")
    assert r.marks_awarded == 1  # value kept, reason rejected (not fuzzy-matched)
    assert r.steps[0].mistake_type == MistakeType.semantic_error
