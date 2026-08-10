"""
Finance archetype 1 — ``compound_periodic`` (amount / principal / rate /
appreciation), plus the ``m``-frequency upgrade to the Gr10 ``finance.py``
compound specs.

Each generator is checked by *re-deriving* the answer independently of the
generator's own arithmetic, then round-tripping it through the verifier. The
relative-tolerance behaviour is exercised at corpus scale (R1.6m), where a
several-rand rounding drift must pass but a gross error must not.
"""

import math

import pytest

from content.examples.compound_periodic import (
    appreciation,
    compound_amount,
    compound_principal,
    compound_rate,
)
from content.examples.finance import compound_growth, compound_reverse
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

_ALL = [
    compound_amount,
    compound_principal,
    compound_rate,
    appreciation,
    compound_growth,
    compound_reverse,
]


def _eng():
    return Engine(registry=InMemoryRegistry({p.id: p for p in _ALL}))


def _rate(inst, *answers):
    steps = [SubmittedStep(a) for a in answers]
    return inst.verifier.rate(SolutionAttempt(steps=steps))


# --- generator correctness (re-derived answers) -----------------------------


@pytest.mark.parametrize("seed", range(25))
def test_amount_matches_periodic_formula(seed):
    p = _eng().instantiate(compound_amount.id, seed=seed).params
    expected = p["principal"] * (1 + p["rate"] / (100 * p["compounding"])) ** (
        p["compounding"] * p["years"]
    )
    assert p["periods"] == p["compounding"] * p["years"]
    assert math.isclose(p["answer"], expected, rel_tol=1e-12)


@pytest.mark.parametrize("seed", range(25))
def test_principal_is_the_discounted_target(seed):
    p = _eng().instantiate(compound_principal.id, seed=seed).params
    grow = (1 + p["rate"] / (100 * p["compounding"])) ** (p["compounding"] * p["years"])
    # the recovered principal, grown back up, must return the target amount
    assert math.isclose(p["answer"] * grow, p["target_amount"], rel_tol=1e-12)
    assert p["answer"] < p["target_amount"]


@pytest.mark.parametrize("seed", range(25))
def test_rate_is_recoverable_from_amount(seed):
    p = _eng().instantiate(compound_rate.id, seed=seed).params
    n_periods = p["compounding"] * p["years"]
    r = 100 * p["compounding"] * ((p["amount"] / p["principal"]) ** (1 / n_periods) - 1)
    assert math.isclose(r, p["answer"], rel_tol=1e-9)
    assert p["amount"] > p["principal"]  # growth, not decay


@pytest.mark.parametrize("seed", range(25))
def test_appreciation_is_annual_compound_growth(seed):
    p = _eng().instantiate(appreciation.id, seed=seed).params
    expected = p["price"] * (1 + p["rate"] / 100) ** p["years"]
    assert math.isclose(p["answer"], expected, rel_tol=1e-12)


# --- verifier round-trips ---------------------------------------------------


def test_all_modes_score_full_on_the_exact_answer():
    eng = _eng()
    for prob, marks in [
        (compound_amount, 3),
        (compound_principal, 2),
        (compound_rate, 3),
        (appreciation, 2),
    ]:
        inst = eng.instantiate(prob.id, seed=1)
        r = _rate(inst, inst.params["answer"])
        assert r.is_correct, prob.id
        assert r.marks_awarded == marks, prob.id


def test_money_modes_accept_two_dp_rounding():
    eng = _eng()
    for prob in (compound_amount, compound_principal, appreciation):
        inst = eng.instantiate(prob.id, seed=2)
        r = _rate(inst, round(inst.params["answer"], 2))
        assert r.is_correct, prob.id


def test_rate_mode_accepts_two_dp_percentage():
    inst = _eng().instantiate(compound_rate.id, seed=2)
    assert _rate(inst, round(inst.params["answer"], 2)).is_correct


# --- the reason rel_tol exists: several-rand drift at corpus scale ----------


def _first_seed_with_large_amount(prob_id, key, threshold):
    eng = _eng()
    for seed in range(200):
        params = eng.instantiate(prob_id, seed=seed).params
        if params[key] >= threshold:
            return eng.instantiate(prob_id, seed=seed)
    raise AssertionError(f"no {prob_id} instance with {key} ≥ {threshold} found")


def test_large_scale_amount_accepts_several_rand_rounding_drift():
    """On a large accumulated amount, a student rounding i over 100+ periods can
    land a few rand off the exact canonical. The relative band accepts it; the
    absolute cent-band alone would not."""
    inst = _first_seed_with_large_amount(compound_amount.id, "answer", 500_000)
    exact = inst.params["answer"]
    drifted = exact + 3.0  # 3 rand high — a legitimate rounding drift at scale
    assert drifted - exact > 0.01  # beyond the absolute cent-band
    assert _rate(inst, drifted).is_correct


def test_large_scale_amount_still_rejects_gross_error():
    inst = _first_seed_with_large_amount(compound_amount.id, "answer", 500_000)
    exact = inst.params["answer"]
    gross = exact * 1.01  # 1% out — a real mistake, well beyond rel_tol 1e-4
    assert not _rate(inst, gross).is_correct


# --- finance.py Gr10 upgrade: m threaded through, still annual-by-default ----


@pytest.mark.parametrize("seed", range(25))
def test_finance_compound_growth_honours_compounding(seed):
    p = _eng().instantiate(compound_growth.id, seed=seed).params
    m = p["compounding"]
    expected = p["principal"] * (1 + p["rate"] / (100 * m)) ** (m * p["years"])
    assert math.isclose(p["answer"], expected, rel_tol=1e-12)


@pytest.mark.parametrize("seed", range(25))
def test_finance_compound_reverse_honours_compounding(seed):
    p = _eng().instantiate(compound_reverse.id, seed=seed).params
    m = p["compounding"]
    grow = (1 + p["rate"] / (100 * m)) ** (m * p["years"])
    assert math.isclose(p["answer"] * grow, p["target_amount"], rel_tol=1e-12)


def test_finance_compound_specs_recalibrated_to_two_marks():
    eng = _eng()
    for prob in (compound_growth, compound_reverse):
        inst = eng.instantiate(prob.id, seed=1)
        r = _rate(inst, inst.params["answer"])
        assert r.is_correct and r.marks_awarded == 2, prob.id
