"""
Finance archetype 5 — ``present_value_annuity`` (solve-P / solve-x / solve-N /
total-interest rider), ordinary and due.

Answers are re-derived independently of the generator and round-tripped through
the verifier. The two payment-timing conventions are checked against each other
(due = ordinary × (1+i)), the solve-N mode is pinned at its floor/ceil boundary
with the ``x > P·i`` guard asserted, and the total-interest rider is checked as
x·N − P.
"""

import math

import pytest

from content.examples.present_value_annuity import (
    pv_annuity_amount,
    pv_annuity_n,
    pv_annuity_payment,
    pv_annuity_total_interest,
)
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

_ALL = [
    pv_annuity_amount,
    pv_annuity_payment,
    pv_annuity_n,
    pv_annuity_total_interest,
]


def _eng():
    return Engine(registry=InMemoryRegistry({p.id: p for p in _ALL}))


def _rate(inst, *answers):
    steps = [SubmittedStep(a) for a in answers]
    return inst.verifier.rate(SolutionAttempt(steps=steps))


def _ordinary_pv(x, i, n):
    return x * (1 - (1 + i) ** (-n)) / i


# --- generator correctness (re-derived answers) -----------------------------


@pytest.mark.parametrize("seed", range(30))
def test_amount_matches_formula_and_honours_timing(seed):
    p = _eng().instantiate(pv_annuity_amount.id, seed=seed).params
    i = p["rate"] / (100 * p["compounding"])
    assert p["periods"] == p["compounding"] * p["years"]
    ordinary = _ordinary_pv(p["payment"], i, p["periods"])
    expected = ordinary * (1 + i) if p["timing"] == "due" else ordinary
    assert math.isclose(p["answer"], expected, rel_tol=1e-12)
    # a due annuity is worth more today than the same ordinary one
    if p["timing"] == "due":
        assert p["answer"] > ordinary


@pytest.mark.parametrize("seed", range(30))
def test_payment_repays_the_loan(seed):
    p = _eng().instantiate(pv_annuity_payment.id, seed=seed).params
    i = p["rate"] / (100 * p["compounding"])
    # the recovered instalment, discounted back, returns the round loan amount
    pv = _ordinary_pv(p["answer"], i, p["periods"])
    recovered = pv * (1 + i) if p["timing"] == "due" else pv
    assert math.isclose(recovered, p["loan_amount"], rel_tol=1e-9)
    # every amortising instalment must exceed the interest on the whole loan
    assert p["answer"] > p["loan_amount"] * i


@pytest.mark.parametrize("seed", range(40))
def test_solve_n_rounds_by_mode_and_respects_the_guard(seed):
    p = _eng().instantiate(pv_annuity_n.id, seed=seed).params
    i = p["per_period_rate"]
    # guard: payment strictly exceeds per-period interest, else the log blows up
    assert p["payment"] > p["present_value"] * i
    solved = -math.log(1 - p["present_value"] * i / p["payment"]) / math.log(1 + i)
    if p["mode"] == "loan":
        assert math.ceil(solved) == p["answer"]  # a final part-payment still counts
        assert p["answer"] - 1 < solved < p["answer"]
    else:
        assert math.floor(solved) == p["answer"]  # only whole withdrawals count
        assert p["answer"] < solved < p["answer"] + 1


@pytest.mark.parametrize("seed", range(30))
def test_total_interest_is_payments_minus_principal(seed):
    p = _eng().instantiate(pv_annuity_total_interest.id, seed=seed).params
    i = p["rate"] / (100 * p["compounding"])
    x = p["loan_amount"] / ((1 - (1 + i) ** (-p["periods"])) / i)
    assert math.isclose(p["instalment"], x, rel_tol=1e-12)
    assert math.isclose(p["answer"], x * p["periods"] - p["loan_amount"], rel_tol=1e-12)
    assert p["answer"] > 0  # a loan always costs interest


# --- verifier round-trips ---------------------------------------------------


def test_all_modes_score_full_on_exact_answer():
    eng = _eng()
    for prob, marks in [
        (pv_annuity_amount, 3),
        (pv_annuity_payment, 4),
        (pv_annuity_n, 5),
        (pv_annuity_total_interest, 2),
    ]:
        inst = eng.instantiate(prob.id, seed=1)
        r = _rate(inst, inst.params["answer"])
        assert r.is_correct and r.marks_awarded == marks, prob.id


def test_money_modes_accept_two_dp_rounding():
    eng = _eng()
    for prob in (pv_annuity_amount, pv_annuity_payment, pv_annuity_total_interest):
        inst = eng.instantiate(prob.id, seed=2)
        assert _rate(inst, round(inst.params["answer"], 2)).is_correct, prob.id


def test_solve_n_rejects_off_by_one():
    inst = _eng().instantiate(pv_annuity_n.id, seed=2)
    assert not _rate(inst, inst.params["answer"] + 1).is_correct
    assert not _rate(inst, inst.params["answer"] - 1).is_correct


# --- the reason rel_tol exists: several-rand drift at loan scale -------------


def test_large_loan_payment_accepts_rounding_drift():
    """Find a large-answer amount instance; a few-rand rounding drift must pass
    the relative band while a gross error fails."""
    eng = _eng()
    inst = None
    for seed in range(200):
        cand = eng.instantiate(pv_annuity_amount.id, seed=seed)
        if cand.params["answer"] >= 500000:
            inst = cand
            break
    assert inst is not None
    exact = inst.params["answer"]
    assert _rate(inst, exact + exact * 5e-5).is_correct  # within rel_tol 1e-4
    assert not _rate(inst, exact * 1.01).is_correct  # 1% out — a real error
