"""
Analytic geometry, archetype 2 — ``line_equation``.

The oracle re-derives the given line's gradient from its two points and checks
the required gradient against the defining relation independently: for a parallel
line the two gradients are equal, for a perpendicular line their product is −1.
It also confirms the emitted line actually passes through P. Distribution tests
guard that both relations occur and that no horizontal/vertical L is emitted.
"""

import sympy

from content.examples.line_equation import line_equation
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

_x = sympy.Symbol("x")


def _eng():
    return Engine(registry=InMemoryRegistry({line_equation.id: line_equation}))


def _rate(inst, *answers):
    steps = [SubmittedStep(a) for a in answers]
    return inst.verifier.rate(SolutionAttempt(steps=steps))


# --- generator correctness (independent oracle) -----------------------------


def test_given_gradient_is_rise_over_run():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(line_equation.id, seed=seed).params
        expected = sympy.Rational(p["gy2"] - p["gy1"], p["gx2"] - p["gx1"])
        assert p["given_gradient"] == expected, seed


def test_required_gradient_satisfies_the_relation():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(line_equation.id, seed=seed).params
        if p["relation"] == "parallel":
            assert p["required_gradient"] == p["given_gradient"], seed
        else:
            assert p["required_gradient"] * p["given_gradient"] == -1, seed


def test_line_passes_through_the_point():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(line_equation.id, seed=seed).params
        assert p["equation_rhs"].subs(_x, p["px"]) == p["py"], seed


def test_equation_rhs_has_the_required_gradient_and_c():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(line_equation.id, seed=seed).params
        poly = sympy.Poly(p["equation_rhs"], _x)
        assert poly.coeff_monomial(_x) == p["required_gradient"], seed
        assert poly.coeff_monomial(1) == p["c"], seed


def test_distribution_covers_both_relations_and_no_degenerate_L():
    eng = _eng()
    seen = set()
    for seed in range(120):
        p = eng.instantiate(line_equation.id, seed=seed).params
        seen.add(p["relation"])
        assert p["gx1"] != p["gx2"] and p["gy1"] != p["gy2"], seed
    assert seen == {"parallel", "perpendicular"}


# --- verifier round-trips ---------------------------------------------------


def test_full_marks_on_gradient_and_equation():
    inst = _eng().instantiate(line_equation.id, seed=1)
    p = inst.params
    r = _rate(inst, p["required_gradient"], p["equation_rhs"])
    assert r.is_correct and r.marks_awarded == 3


def test_wrong_gradient_still_earns_equation_marks_if_equation_right():
    # gradient step and equation step are independent canonicals
    inst = _eng().instantiate(line_equation.id, seed=1)
    p = inst.params
    r = _rate(inst, p["required_gradient"] + 1, p["equation_rhs"])
    assert r.marks_awarded == 2 and not r.is_correct


def test_negative_reciprocal_confusion_scores_zero():
    inst = _eng().instantiate(line_equation.id, seed=1)
    p = inst.params
    confused_m = -1 / p["required_gradient"]
    confused_eq = confused_m * _x + p["c"]
    r = _rate(inst, confused_m, confused_eq)
    assert r.marks_awarded == 0


def test_equivalent_equation_form_is_accepted():
    inst = _eng().instantiate(line_equation.id, seed=2)
    p = inst.params
    rearranged = sympy.expand(p["equation_rhs"] + _x - _x)  # trivially equal
    r = _rate(inst, p["required_gradient"], rearranged)
    assert r.is_correct and r.marks_awarded == 3


def test_all_wrong_scores_zero():
    inst = _eng().instantiate(line_equation.id, seed=1)
    p = inst.params
    r = _rate(inst, p["required_gradient"] + 5, p["equation_rhs"] + 7)
    assert r.marks_awarded == 0
