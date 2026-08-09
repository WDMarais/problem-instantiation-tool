"""
Finance archetype 6 — ``depreciation`` (solve-A both sub-models / solve-r /
straight-line-to-zero).

Answers are re-derived independently of the generator and round-tripped through
the verifier. Straight-line instances are checked to keep a positive book value,
the recovered rate is checked to reproduce the given book value, and the to-zero
count is pinned at the year the straight-line value first passes zero.
"""

import math

import pytest

from content.examples.depreciation import (
    depreciation_amount,
    depreciation_rate,
    depreciation_to_zero,
)
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

_ALL = [depreciation_amount, depreciation_rate, depreciation_to_zero]


def _eng():
    return Engine(registry=InMemoryRegistry({p.id: p for p in _ALL}))


def _rate(inst, *answers):
    steps = [SubmittedStep(a) for a in answers]
    return inst.verifier.rate(SolutionAttempt(steps=steps))


# --- generator correctness (re-derived answers) -----------------------------


@pytest.mark.parametrize("seed", range(40))
def test_amount_matches_the_named_sub_model(seed):
    p = _eng().instantiate(depreciation_amount.id, seed=seed).params
    i = p["rate"] / 100
    if p["model"] == "straight_line":
        expected = p["book_price"] * (1 - i * p["years"])
    else:
        expected = p["book_price"] * (1 - i) ** p["years"]
    assert math.isclose(p["answer"], expected, rel_tol=1e-12)
    # a real asset never depreciates below zero
    assert 0 < p["answer"] <= p["book_price"]


@pytest.mark.parametrize("seed", range(30))
def test_rate_reproduces_the_book_value(seed):
    p = _eng().instantiate(depreciation_rate.id, seed=seed).params
    i = p["answer"] / 100
    # the recovered rate, applied straight-line, returns the given book value
    assert math.isclose(
        p["book_price"] * (1 - i * p["years"]), p["book_value"], rel_tol=1e-12
    )
    assert p["book_value"] > 0


@pytest.mark.parametrize("seed", range(30))
def test_to_zero_is_the_year_value_first_passes_zero(seed):
    p = _eng().instantiate(depreciation_to_zero.id, seed=seed).params
    i = p["rate"] / 100
    n = p["answer"]
    assert n == math.ceil(1 / i)
    # value is still positive the year before, and hits/passes zero at n
    assert p["book_price"] * (1 - i * (n - 1)) > 0
    assert p["book_price"] * (1 - i * n) <= 1e-9


# --- verifier round-trips ---------------------------------------------------


def test_all_modes_score_full_on_exact_answer():
    eng = _eng()
    for prob in _ALL:
        inst = eng.instantiate(prob.id, seed=1)
        r = _rate(inst, inst.params["answer"])
        assert r.is_correct and r.marks_awarded == 2, prob.id


def test_amount_accepts_two_dp_rounding():
    inst = _eng().instantiate(depreciation_amount.id, seed=2)
    assert _rate(inst, round(inst.params["answer"], 2)).is_correct


def test_to_zero_rejects_off_by_one():
    inst = _eng().instantiate(depreciation_to_zero.id, seed=2)
    assert not _rate(inst, inst.params["answer"] + 1).is_correct
    assert not _rate(inst, inst.params["answer"] - 1).is_correct


def test_both_sub_models_actually_occur():
    eng = _eng()
    seen = {
        eng.instantiate(depreciation_amount.id, seed=s).params["model"]
        for s in range(40)
    }
    assert seen == {"straight_line", "reducing_balance"}


# --- the reason rel_tol exists: several-rand drift at price scale ------------


def test_large_book_value_accepts_rounding_drift():
    """Find a large-answer amount instance; a few-rand rounding drift must pass
    the relative band while a gross error fails."""
    eng = _eng()
    inst = None
    for seed in range(200):
        cand = eng.instantiate(depreciation_amount.id, seed=seed)
        if cand.params["answer"] >= 50000:
            inst = cand
            break
    assert inst is not None
    exact = inst.params["answer"]
    assert _rate(inst, exact + exact * 5e-5).is_correct  # within rel_tol 1e-4
    assert not _rate(inst, exact * 1.01).is_correct  # 1% out — a real error
