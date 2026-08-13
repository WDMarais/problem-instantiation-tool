"""
Calculus, archetype 3 — ``tangent_line``.

The oracle re-derives the tangent independently: the gradient as the limit-free
derivative evaluated at x₀ (via ``sympy.diff``), and the line from the
point-slope form  y − f(x₀) = m·(x − x₀)  solved for y. Every reported tangent is
additionally confirmed to (a) pass through (x₀, f(x₀)) and (b) have gradient
equal to f′(x₀). Distribution tests guard that both gradient signs occur and that
the cubic is genuine (a ≠ 0).
"""

import sympy

from content.examples.tangent_line import tangent_line
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

_x = sympy.Symbol("x")


def _eng():
    return Engine(registry=InMemoryRegistry({tangent_line.id: tangent_line}))


def _rate(inst, *answers):
    steps = [SubmittedStep(a) for a in answers]
    return inst.verifier.rate(SolutionAttempt(steps=steps))


def _f(p):
    return p["a"] * _x**3 + p["b"] * _x**2 + p["c"] * _x + p["d"]


# --- generator correctness (independent oracle) -----------------------------


def test_gradient_is_the_derivative_at_x0():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(tangent_line.id, seed=seed).params
        oracle_m = sympy.diff(_f(p), _x).subs(_x, p["x0"])
        assert oracle_m == p["gradient"], (seed, p["function_latex"])


def test_line_is_the_point_slope_form():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(tangent_line.id, seed=seed).params
        m = sympy.diff(_f(p), _x).subs(_x, p["x0"])
        y0 = _f(p).subs(_x, p["x0"])
        oracle_line = m * (_x - p["x0"]) + y0  # point-slope solved for y
        assert sympy.simplify(oracle_line - p["tangent_rhs"]) == 0, seed


def test_tangent_touches_the_curve_at_x0():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(tangent_line.id, seed=seed).params
        # the tangent and the curve agree in value at x₀
        assert p["tangent_rhs"].subs(_x, p["x0"]) == _f(p).subs(_x, p["x0"]), seed
        assert p["y0"] == int(_f(p).subs(_x, p["x0"])), seed


def test_distribution_covers_both_gradient_signs():
    eng = _eng()
    saw_pos = saw_neg = False
    saw_pos_a = saw_neg_a = False
    for seed in range(120):
        p = eng.instantiate(tangent_line.id, seed=seed).params
        assert p["a"] != 0, seed
        saw_pos |= p["gradient"] > 0
        saw_neg |= p["gradient"] < 0
        saw_pos_a |= p["a"] > 0
        saw_neg_a |= p["a"] < 0
    assert saw_pos and saw_neg
    assert saw_pos_a and saw_neg_a


# --- verifier round-trips ---------------------------------------------------


def test_full_marks_on_gradient_and_line():
    inst = _eng().instantiate(tangent_line.id, seed=1)
    p = inst.params
    r = _rate(inst, p["gradient"], p["tangent_rhs"])
    assert r.is_correct and r.marks_awarded == 3


def test_gradient_right_intercept_wrong_scores_one():
    inst = _eng().instantiate(tangent_line.id, seed=1)
    p = inst.params
    # correct gradient, wrong y-intercept → keeps the gradient mark only
    r = _rate(inst, p["gradient"], p["tangent_rhs"] + 3)
    assert r.marks_awarded == 1 and not r.is_correct


def test_equivalent_line_form_is_accepted():
    inst = _eng().instantiate(tangent_line.id, seed=2)
    p = inst.params
    factored = sympy.factor(p["tangent_rhs"])  # e.g. -(x + 2)
    r = _rate(inst, p["gradient"], factored)
    assert r.is_correct and r.marks_awarded == 3


def test_wrong_gradient_wrong_line_scores_zero():
    inst = _eng().instantiate(tangent_line.id, seed=1)
    p = inst.params
    r = _rate(inst, p["gradient"] + 5, p["tangent_rhs"] + 5)
    assert r.marks_awarded == 0
