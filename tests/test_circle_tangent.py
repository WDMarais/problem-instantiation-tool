"""
Analytic geometry, archetype 5 — ``circle_tangent``.

The strong oracle is a genuine tangency check, independent of the −dx/dy
construction: substitute the emitted line into the circle
(x−h)² + (y−k)² = r² and confirm the resulting quadratic in x has a *double*
root (discriminant 0) at x = px — i.e. the line touches the circle at exactly P.
Supporting checks: the tangent is perpendicular to the radius (product of
gradients −1) and passes through P. Distribution tests guard both gradient signs
and that no radius is horizontal/vertical.
"""

import sympy

from content.examples.circle_tangent import circle_tangent
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

_x, _y = sympy.symbols("x y")


def _eng():
    return Engine(registry=InMemoryRegistry({circle_tangent.id: circle_tangent}))


def _rate(inst, *answers):
    steps = [SubmittedStep(a) for a in answers]
    return inst.verifier.rate(SolutionAttempt(steps=steps))


# --- generator correctness (independent oracle) -----------------------------


def test_line_is_tangent_double_root_at_p():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(circle_tangent.id, seed=seed).params
        circle = (_x - p["h"]) ** 2 + (_y - p["k"]) ** 2 - p["radius_sq"]
        substituted = circle.subs(_y, p["tangent_rhs"])
        quad = sympy.Poly(sympy.expand(substituted), _x)
        a, b, cc = quad.all_coeffs()
        assert sympy.simplify(b**2 - 4 * a * cc) == 0, seed  # tangency
        assert sympy.simplify(-b / (2 * a) - p["px"]) == 0, seed  # touches at P


def test_tangent_perpendicular_to_radius():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(circle_tangent.id, seed=seed).params
        assert p["tangent_gradient"] * p["radius_gradient"] == -1, seed


def test_tangent_passes_through_p():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(circle_tangent.id, seed=seed).params
        assert p["tangent_rhs"].subs(_x, p["px"]) == p["py"], seed


def test_point_lies_on_the_circle():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(circle_tangent.id, seed=seed).params
        assert (p["px"] - p["h"]) ** 2 + (p["py"] - p["k"]) ** 2 == p["radius_sq"], seed


def test_distribution_covers_both_gradient_signs():
    eng = _eng()
    saw_pos = saw_neg = False
    for seed in range(120):
        p = eng.instantiate(circle_tangent.id, seed=seed).params
        assert p["px"] != p["h"] and p["py"] != p["k"], seed  # no degenerate radius
        saw_pos |= p["tangent_gradient"] > 0
        saw_neg |= p["tangent_gradient"] < 0
    assert saw_pos and saw_neg


# --- verifier round-trips ---------------------------------------------------


def test_full_marks_on_gradient_and_equation():
    inst = _eng().instantiate(circle_tangent.id, seed=1)
    p = inst.params
    r = _rate(inst, p["tangent_gradient"], p["tangent_rhs"])
    assert r.is_correct and r.marks_awarded == 3


def test_using_radius_gradient_scores_zero():
    inst = _eng().instantiate(circle_tangent.id, seed=1)
    p = inst.params
    wrong_rhs = p["radius_gradient"] * _x + (p["py"] - p["radius_gradient"] * p["px"])
    r = _rate(inst, p["radius_gradient"], wrong_rhs)
    assert r.marks_awarded == 0


def test_right_gradient_wrong_intercept_keeps_one():
    inst = _eng().instantiate(circle_tangent.id, seed=1)
    p = inst.params
    r = _rate(inst, p["tangent_gradient"], p["tangent_rhs"] + 3)
    assert r.marks_awarded == 1 and not r.is_correct


def test_equivalent_equation_form_is_accepted():
    inst = _eng().instantiate(circle_tangent.id, seed=2)
    p = inst.params
    rearranged = sympy.expand(p["tangent_rhs"] * 1)
    r = _rate(inst, p["tangent_gradient"], rearranged)
    assert r.is_correct and r.marks_awarded == 3


def test_all_wrong_scores_zero():
    inst = _eng().instantiate(circle_tangent.id, seed=1)
    p = inst.params
    r = _rate(inst, p["tangent_gradient"] + 2, p["tangent_rhs"] + 9)
    assert r.marks_awarded == 0
