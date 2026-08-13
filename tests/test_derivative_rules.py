"""
Calculus, archetype 2 — ``derivative_rules``.

The oracle re-derives f′(x) by applying the power rule **by hand** to each term
in its rewritten power form — n·xⁿ⁻¹ per term — never calling ``sympy.diff``,
which is what the generator uses. Distribution tests guard that every instance
genuinely requires the rewrite (a surd term AND a reciprocal term are always
present) and that the constant differentiates away.
"""

import sympy

from content.examples.derivative_rules import derivative_rules
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

_x = sympy.Symbol("x")
_half = sympy.Rational(1, 2)


def _eng():
    return Engine(registry=InMemoryRegistry({derivative_rules.id: derivative_rules}))


def _rate(inst, *answers):
    steps = [SubmittedStep(a) for a in answers]
    return inst.verifier.rate(SolutionAttempt(steps=steps))


def _hand_derivative(p):
    """Power rule applied by hand to each rewritten term (oracle)."""
    plain = p["a_plain"] * p["n_plain"] * _x ** (p["n_plain"] - 1)
    surd = p["a_surd"] * _half * _x ** (_half - 1)
    recip = p["a_recip"] * (-p["n_recip"]) * _x ** (-p["n_recip"] - 1)
    # the constant contributes nothing
    return plain + surd + recip


# --- generator correctness (independent oracle) -----------------------------


def test_derivative_matches_hand_power_rule():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(derivative_rules.id, seed=seed).params
        assert sympy.simplify(_hand_derivative(p) - p["derivative"]) == 0, (
            seed,
            p["function_latex"],
        )


def test_every_instance_requires_a_rewrite():
    """A surd term and a reciprocal term are always present — so the rewrite
    step can never be skipped."""
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(derivative_rules.id, seed=seed).params
        assert p["a_surd"] != 0, seed
        assert p["a_recip"] != 0, seed
        assert p["n_recip"] >= 1, seed


def test_constant_differentiates_away():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(derivative_rules.id, seed=seed).params
        assert p["const"] != 0, seed
        # f′ is unchanged if the constant is dropped from f
        f_no_const = (
            p["a_plain"] * _x ** p["n_plain"]
            + p["a_surd"] * sympy.sqrt(_x)
            + p["a_recip"] / _x ** p["n_recip"]
        )
        assert sympy.simplify(sympy.diff(f_no_const, _x) - p["derivative"]) == 0, seed


def test_distribution_covers_both_signs():
    eng = _eng()
    saw_pos = saw_neg = False
    saw_recip_square = False
    for seed in range(120):
        p = eng.instantiate(derivative_rules.id, seed=seed).params
        saw_pos |= p["a_plain"] > 0
        saw_neg |= p["a_plain"] < 0
        saw_recip_square |= p["n_recip"] >= 2
    assert saw_pos and saw_neg
    assert saw_recip_square


# --- verifier round-trips ---------------------------------------------------


def test_full_marks_on_correct_derivative():
    inst = _eng().instantiate(derivative_rules.id, seed=1)
    p = inst.params
    r = _rate(inst, p["derivative"])
    assert r.is_correct and r.marks_awarded == 3


def test_equivalent_power_form_is_accepted():
    """The same derivative written with explicit negative/fractional powers
    instead of surds and fractions still earns full marks."""
    inst = _eng().instantiate(derivative_rules.id, seed=1)
    p = inst.params
    powered = p["derivative"].replace(
        lambda e: e == 1 / sympy.sqrt(_x), lambda e: _x ** (-_half)
    )
    r = _rate(inst, powered)
    assert r.is_correct and r.marks_awarded == 3


def test_forgetting_the_constant_dropped_scores_zero():
    inst = _eng().instantiate(derivative_rules.id, seed=1)
    p = inst.params
    r = _rate(inst, p["derivative"] + p["const"])
    assert r.marks_awarded == 0 and not r.is_correct


def test_wrong_derivative_scores_zero():
    inst = _eng().instantiate(derivative_rules.id, seed=1)
    r = _rate(inst, sympy.Integer(0))
    assert r.marks_awarded == 0
