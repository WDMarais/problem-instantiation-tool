"""
Calculus, archetype 1 — ``derivative_first_principles``.

The oracle is deliberately independent of the generator's ``sympy.diff``: the
derivative is re-derived from the *limit definition* itself
(``sympy.limit((f(x+h)−f(x))/h, h, 0)``), and the stored difference quotient is
checked to be genuinely (f(x+h)−f(x))/h. Distribution tests guard the archetype's
honesty — the leading coefficient is never zero (so it is really a quadratic),
the constant term varies and never appears in the derivative (so "the constant
differentiates away" is exercised), and both signs of ``a`` occur.
"""

import sympy

from content.examples.derivative_first_principles import derivative_first_principles
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

_x, _h = sympy.symbols("x h")


def _eng():
    return Engine(
        registry=InMemoryRegistry(
            {derivative_first_principles.id: derivative_first_principles}
        )
    )


def _rate(inst, *answers):
    steps = [SubmittedStep(a) for a in answers]
    return inst.verifier.rate(SolutionAttempt(steps=steps))


def _f(p):
    return p["a"] * _x**2 + p["b"] * _x + p["c"]


# --- generator correctness (independent oracle) -----------------------------


def test_derivative_matches_the_limit_definition():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(derivative_first_principles.id, seed=seed).params
        f = _f(p)
        oracle = sympy.limit((f.subs(_x, _x + _h) - f) / _h, _h, 0)
        assert sympy.simplify(oracle - p["derivative"]) == 0, (
            seed,
            p["function_latex"],
        )


def test_quotient_is_the_difference_quotient():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(derivative_first_principles.id, seed=seed).params
        f = _f(p)
        raw = (f.subs(_x, _x + _h) - f) / _h
        assert sympy.simplify(raw - p["quotient"]) == 0, (seed, p["function_latex"])


def test_quotient_limit_is_the_derivative():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(derivative_first_principles.id, seed=seed).params
        # taking h→0 in the quotient must land on the derivative
        assert sympy.limit(p["quotient"], _h, 0) == p["derivative"], seed


def test_constant_term_vanishes_from_the_derivative():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(derivative_first_principles.id, seed=seed).params
        # f′(x) depends on x only (degree 1), never on the constant c or on h
        assert _h not in p["derivative"].free_symbols, seed
        assert sympy.degree(p["derivative"], _x) == 1, seed


def test_distribution_is_honest():
    eng = _eng()
    saw_pos_a = saw_neg_a = False
    saw_nonzero_c = False
    for seed in range(120):
        p = eng.instantiate(derivative_first_principles.id, seed=seed).params
        assert p["a"] != 0, seed
        saw_pos_a |= p["a"] > 0
        saw_neg_a |= p["a"] < 0
        saw_nonzero_c |= p["c"] != 0
        # the constant differentiates away: f′ is unchanged if c is dropped
        without_c = sympy.diff(p["a"] * _x**2 + p["b"] * _x, _x)
        assert sympy.simplify(without_c - p["derivative"]) == 0, seed
    assert saw_pos_a and saw_neg_a
    assert saw_nonzero_c


# --- verifier round-trips ---------------------------------------------------


def test_full_marks_on_quotient_then_derivative():
    inst = _eng().instantiate(derivative_first_principles.id, seed=1)
    p = inst.params
    r = _rate(inst, p["quotient"], p["derivative"])
    assert r.is_correct and r.marks_awarded == 5


def test_power_rule_shortcut_loses_the_method_marks():
    """A student who skips first principles and writes only f′(x) supplies the
    derivative where the quotient is expected → forfeits the 3 method marks."""
    inst = _eng().instantiate(derivative_first_principles.id, seed=1)
    p = inst.params
    r = _rate(inst, p["derivative"], p["derivative"])
    assert r.marks_awarded == 2 and not r.is_correct


def test_quotient_right_derivative_missing_scores_three():
    inst = _eng().instantiate(derivative_first_principles.id, seed=1)
    p = inst.params
    # correct quotient, but forgot to take the limit (left h in the answer)
    r = _rate(inst, p["quotient"], p["quotient"])
    assert r.marks_awarded == 3 and not r.is_correct


def test_unsimplified_quotient_still_accepted():
    """The quotient step accepts any algebraically-equal form, e.g. the
    un-cancelled (f(x+h)−f(x))/h, since symbolic_equality simplifies."""
    inst = _eng().instantiate(derivative_first_principles.id, seed=3)
    p = inst.params
    f = _f(p)
    raw = (f.subs(_x, _x + _h) - f) / _h  # not simplified
    r = _rate(inst, raw, p["derivative"])
    assert r.is_correct and r.marks_awarded == 5


def test_all_wrong_scores_zero():
    inst = _eng().instantiate(derivative_first_principles.id, seed=1)
    r = _rate(inst, sympy.Integer(0), sympy.Integer(0))
    assert r.marks_awarded == 0
