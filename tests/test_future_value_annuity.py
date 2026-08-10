"""
Finance archetype 4 — ``future_value_annuity`` (solve-F / solve-x / solve-N),
ordinary and due.

Answers are re-derived independently of the generator, round-tripped through the
verifier, and the two payment-timing conventions are checked against each other
(due = ordinary × (1+i)). The solve-N mode is pinned at its ceil boundary.
"""

import math

import pytest

from content.examples.future_value_annuity import (
    fv_annuity_amount,
    fv_annuity_deposit,
    fv_annuity_n,
)
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

_ALL = [fv_annuity_amount, fv_annuity_deposit, fv_annuity_n]


def _eng():
    return Engine(registry=InMemoryRegistry({p.id: p for p in _ALL}))


def _rate(inst, *answers):
    steps = [SubmittedStep(a) for a in answers]
    return inst.verifier.rate(SolutionAttempt(steps=steps))


def _ordinary_fv(x, i, n):
    return x * ((1 + i) ** n - 1) / i


# --- generator correctness (re-derived answers) -----------------------------


@pytest.mark.parametrize("seed", range(30))
def test_amount_matches_formula_and_honours_timing(seed):
    p = _eng().instantiate(fv_annuity_amount.id, seed=seed).params
    i = p["rate"] / (100 * p["compounding"])
    assert p["periods"] == p["compounding"] * p["years"]
    ordinary = _ordinary_fv(p["deposit"], i, p["periods"])
    expected = ordinary * (1 + i) if p["timing"] == "due" else ordinary
    assert math.isclose(p["answer"], expected, rel_tol=1e-12)
    # a due annuity always accumulates more than the same ordinary one
    if p["timing"] == "due":
        assert p["answer"] > ordinary


@pytest.mark.parametrize("seed", range(30))
def test_deposit_reaches_the_target(seed):
    p = _eng().instantiate(fv_annuity_deposit.id, seed=seed).params
    i = p["rate"] / (100 * p["compounding"])
    ordinary = _ordinary_fv(p["answer"], i, p["periods"])
    grown = ordinary * (1 + i) if p["timing"] == "due" else ordinary
    # the recovered deposit, accumulated, returns the round target
    assert math.isclose(grown, p["target_amount"], rel_tol=1e-9)


@pytest.mark.parametrize("seed", range(30))
def test_solve_n_is_the_ceil_of_the_exact_solve(seed):
    p = _eng().instantiate(fv_annuity_n.id, seed=seed).params
    i = p["per_period_rate"]
    solved = math.log(1 + p["target_amount"] * i / p["deposit"]) / math.log(1 + i)
    assert math.ceil(solved) == p["answer"]
    # target sits strictly inside the (N-1, N) accumulation gap → unambiguous ceil
    assert p["answer"] - 1 < solved < p["answer"]


# --- verifier round-trips ---------------------------------------------------


def test_all_modes_score_full_on_exact_answer():
    eng = _eng()
    for prob, marks in [
        (fv_annuity_amount, 4),
        (fv_annuity_deposit, 4),
        (fv_annuity_n, 4),
    ]:
        inst = eng.instantiate(prob.id, seed=1)
        r = _rate(inst, inst.params["answer"])
        assert r.is_correct and r.marks_awarded == marks, prob.id


def test_money_modes_accept_two_dp_rounding():
    eng = _eng()
    for prob in (fv_annuity_amount, fv_annuity_deposit):
        inst = eng.instantiate(prob.id, seed=2)
        assert _rate(inst, round(inst.params["answer"], 2)).is_correct, prob.id


def test_solve_n_rejects_off_by_one():
    inst = _eng().instantiate(fv_annuity_n.id, seed=2)
    assert not _rate(inst, inst.params["answer"] + 1).is_correct
    assert not _rate(inst, inst.params["answer"] - 1).is_correct


# --- the reason rel_tol exists: several-rand drift at target scale -----------


def test_large_target_deposit_accepts_rounding_drift():
    """Find a large-answer deposit instance; a few-rand rounding drift must pass
    the relative band while a gross error fails."""
    eng = _eng()
    inst = None
    for seed in range(200):
        cand = eng.instantiate(fv_annuity_deposit.id, seed=seed)
        if cand.params["answer"] >= 5000:
            inst = cand
            break
    assert inst is not None
    exact = inst.params["answer"]
    assert _rate(inst, exact + exact * 5e-5).is_correct  # within rel_tol 1e-4
    assert not _rate(inst, exact * 1.01).is_correct  # 1% out — a real error
