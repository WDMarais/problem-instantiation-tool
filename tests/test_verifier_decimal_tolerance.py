"""
symbolic_equality's decimal fallback (generous-by-default numeric acceptance).

A numeric answer graded by ``symbolic_equality`` accepts a calculator decimal
(7.07 for √50) as well as any exact/equivalent surd form — matching how DBE
memos mark a numerically-correct answer. A problem that tests exact/surd form
sets ``require_exact_form`` to opt back into strict grading. Crucially, the
fallback never loosens grading of *expression* answers (m·x + c), which are not
float-able.
"""

import sympy

from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import (
    Problem,
    SolutionAttempt,
    SubmittedStep,
)

_x = sympy.Symbol("x")


def _problem(pid, canonical, spec_extra=None):
    spec = {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "ans"}
    spec.update(spec_extra or {})
    return Problem(
        id=pid,
        type_id=pid,
        name=pid,
        artifact_type="practice",
        problem_spec=lambda rng: {"ans": canonical},
        verifier_spec=[spec],
    )


def _rate(problem, answer):
    eng = Engine(registry=InMemoryRegistry({problem.id: problem}))
    inst = eng.instantiate(problem.id, seed=0)
    attempt = SolutionAttempt(steps=[SubmittedStep(answer)])
    return inst.verifier.rate(attempt)


# --- generous default: surds -----------------------------------------------


def test_surd_accepts_exact_and_equivalent_and_decimal():
    prob = _problem("surd_generous", sympy.sqrt(50))
    for good in ("sqrt(50)", "5*sqrt(2)", "7.07", "7.0710678"):
        assert _rate(prob, good).marks_awarded == 1, good


def test_surd_rejects_a_too_coarse_decimal():
    prob = _problem("surd_coarse", sympy.sqrt(50))
    assert _rate(prob, "7.1").marks_awarded == 0  # 1-dp is outside tolerance
    assert _rate(prob, "7.2").marks_awarded == 0


# --- generous default: rationals -------------------------------------------


def test_rational_accepts_fraction_and_two_dp_decimal():
    prob = _problem("rat_generous", sympy.Rational(1, 3))
    for good in ("1/3", "0.33", "0.3333333"):
        assert _rate(prob, good).marks_awarded == 1, good
    assert _rate(prob, "0.3").marks_awarded == 0  # 1-dp too coarse


# --- expression answers stay strict ----------------------------------------


def test_expression_answer_is_not_loosened():
    prob = _problem("expr_strict", 2 * _x + 3)
    assert _rate(prob, 2 * _x + 3).marks_awarded == 1  # exact expression
    assert _rate(prob, sympy.expand((2 * _x + 3) * 1)).marks_awarded == 1  # equiv form
    assert _rate(prob, "5.01").marks_awarded == 0  # a bare number is not the line
    assert _rate(prob, 2 * _x + 3.0001).marks_awarded == 0  # wrong intercept


# --- require_exact_form opts out (the surd-form variant) --------------------


def test_require_exact_form_rejects_decimal_but_keeps_surds():
    prob = _problem("surd_strict", sympy.sqrt(50), {"require_exact_form": True})
    assert _rate(prob, "sqrt(50)").marks_awarded == 1
    assert _rate(prob, "5*sqrt(2)").marks_awarded == 1  # any exact form still ok
    assert _rate(prob, "7.07").marks_awarded == 0  # decimal now loses the mark
    assert _rate(prob, "7.0710678").marks_awarded == 0


# --- explicit tolerance overrides the generous default ----------------------


def test_explicit_tolerance_widens_acceptance():
    prob = _problem("surd_wide", sympy.sqrt(50), {"tolerance": 0.1})
    assert _rate(prob, "7.1").marks_awarded == 1  # now inside the wider band


def test_far_wrong_number_still_zero():
    prob = _problem("surd_far", sympy.sqrt(50))
    assert _rate(prob, "8").marks_awarded == 0
    assert _rate(prob, "6.9").marks_awarded == 0
