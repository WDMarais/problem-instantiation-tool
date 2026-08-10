"""
Q1 Algebra Extensions, archetype 1 — ``quadratic_inequality``.

The generator's own arithmetic is never trusted: each instance is re-solved
*independently* with ``sympy.solveset`` over the reals, and both the critical
values and the categorical region are checked against that solution set. The
verifier chain is round-tripped for full marks, partial credit on one critical
value, and the sign-analysis region mark in isolation.
"""

import sympy

from content.examples.quadratic_inequality import quadratic_inequality
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

_x = sympy.Symbol("x")
_REL = {
    "<": sympy.StrictLessThan,
    "<=": sympy.LessThan,
    ">": sympy.StrictGreaterThan,
    ">=": sympy.GreaterThan,
}


def _eng():
    return Engine(
        registry=InMemoryRegistry({quadratic_inequality.id: quadratic_inequality})
    )


def _rate(inst, *answers):
    steps = [SubmittedStep(a) for a in answers]
    return inst.verifier.rate(SolutionAttempt(steps=steps))


def _independent_solution(p) -> sympy.Set:
    """Solve the *presented* polynomial inequality from scratch, over the reals."""
    expr = p["a"] * _x**2 + p["b"] * _x + p["c"]
    return sympy.solveset(_REL[p["direction"]](expr, 0), _x, sympy.S.Reals)


def _region_to_set(p) -> sympy.Set:
    """Reconstruct the solution set from (critical_values, region, closed) only —
    the labels the verifier actually grades. Must equal the independent solve."""
    lo, hi = sorted(p["critical_values"])
    if p["region"] == "between":
        return sympy.Interval(lo, hi) if p["closed"] else sympy.Interval.open(lo, hi)
    left = (
        sympy.Interval(-sympy.oo, lo)
        if p["closed"]
        else sympy.Interval.open(-sympy.oo, lo)
    )
    right = (
        sympy.Interval(hi, sympy.oo)
        if p["closed"]
        else sympy.Interval.open(hi, sympy.oo)
    )
    return sympy.Union(left, right)


# --- generator correctness (independently re-derived) -----------------------


def test_critical_values_and_region_match_an_independent_solve():
    eng = _eng()
    for seed in range(60):
        p = eng.instantiate(quadratic_inequality.id, seed=seed).params
        expr = p["a"] * _x**2 + p["b"] * _x + p["c"]

        # critical values are exactly the real roots of the presented polynomial
        roots = {int(r) for r in sympy.solve(sympy.Eq(expr, 0), _x)}
        assert roots == set(p["critical_values"]), (seed, p["polynomial_latex"])

        # the graded labels reconstruct the true solution set
        assert _region_to_set(p) == _independent_solution(p), (
            seed,
            p["polynomial_latex"],
            p["region"],
        )


def test_two_distinct_integer_critical_values():
    eng = _eng()
    for seed in range(60):
        p = eng.instantiate(quadratic_inequality.id, seed=seed).params
        assert len(p["critical_values"]) == 2, seed


def test_draws_exercise_both_openings_and_both_regions():
    """The a<0 flip is the whole family — the sweep must actually hit it, and both
    region outcomes, or a green here would be vacuous."""
    eng = _eng()
    seen_a_signs, seen_regions = set(), set()
    for seed in range(60):
        p = eng.instantiate(quadratic_inequality.id, seed=seed).params
        seen_a_signs.add(p["a"] > 0)
        seen_regions.add(p["region"])
    assert seen_a_signs == {True, False}
    assert seen_regions == {"between", "outside"}


# --- verifier round-trips ---------------------------------------------------


def test_full_marks_on_exact_answer():
    inst = _eng().instantiate(quadratic_inequality.id, seed=1)
    p = inst.params
    r = _rate(inst, p["critical_values"], p["region"])
    assert r.is_correct and r.marks_awarded == 3


def test_partial_credit_on_one_critical_value():
    inst = _eng().instantiate(quadratic_inequality.id, seed=1)
    p = inst.params
    lo, _ = sorted(p["critical_values"])
    # one root right (1 of 2) + correct region (1) = 2/3, not fully correct
    r = _rate(inst, frozenset({lo}), p["region"])
    assert r.marks_awarded == 2 and not r.is_correct


def test_wrong_region_loses_exactly_the_sign_analysis_mark():
    inst = _eng().instantiate(quadratic_inequality.id, seed=1)
    p = inst.params
    wrong = "between" if p["region"] == "outside" else "outside"
    r = _rate(inst, p["critical_values"], wrong)
    assert r.marks_awarded == 2 and not r.is_correct


def test_region_label_is_case_insensitive():
    inst = _eng().instantiate(quadratic_inequality.id, seed=1)
    p = inst.params
    r = _rate(inst, p["critical_values"], p["region"].upper())
    assert r.is_correct


def test_all_wrong_scores_zero():
    inst = _eng().instantiate(quadratic_inequality.id, seed=1)
    p = inst.params
    wrong = "between" if p["region"] == "outside" else "outside"
    r = _rate(inst, frozenset({99, 100}), wrong)
    assert r.marks_awarded == 0
