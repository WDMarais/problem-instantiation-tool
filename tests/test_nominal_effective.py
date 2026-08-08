"""
Finance archetype 2 — ``nominal_effective_rate`` (rate conversion, both
directions). Smallest build in the family: pure formula, no principal.

    1 + i_eff = (1 + i_nom/m)^m

Each generator's answer is re-derived independently, then round-tripped through
the verifier. The answer is a small percentage, so the absolute ±0.01 band (not
rel_tol) is what absorbs the student's 2-dp rounding.
"""

import math

import pytest

from content.examples.nominal_effective import (
    effective_to_nominal,
    nominal_to_effective,
)
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

_ALL = [nominal_to_effective, effective_to_nominal]


def _eng():
    return Engine(registry=InMemoryRegistry({p.id: p for p in _ALL}))


def _rate(inst, *answers):
    steps = [SubmittedStep(a) for a in answers]
    return inst.verifier.rate(SolutionAttempt(steps=steps))


# --- generator correctness (re-derived answers) -----------------------------


@pytest.mark.parametrize("seed", range(25))
def test_nominal_to_effective_matches_formula(seed):
    p = _eng().instantiate(nominal_to_effective.id, seed=seed).params
    i_nom, m = p["nominal_rate"], p["compounding"]
    expected = ((1 + (i_nom / 100) / m) ** m - 1) * 100
    assert math.isclose(p["answer"], expected, rel_tol=1e-12)
    # effective rate always exceeds nominal when m > 1
    assert p["answer"] > i_nom


@pytest.mark.parametrize("seed", range(25))
def test_effective_to_nominal_inverts_cleanly(seed):
    p = _eng().instantiate(effective_to_nominal.id, seed=seed).params
    i_eff, m = p["effective_rate"], p["compounding"]
    recovered = m * ((1 + i_eff / 100) ** (1 / m) - 1) * 100
    assert math.isclose(recovered, p["answer"], rel_tol=1e-9)
    # nominal is below the effective it produces
    assert p["answer"] < i_eff


# --- verifier round-trips ---------------------------------------------------


def test_both_directions_score_full_on_exact_answer():
    eng = _eng()
    for prob in (nominal_to_effective, effective_to_nominal):
        inst = eng.instantiate(prob.id, seed=1)
        r = _rate(inst, inst.params["answer"])
        assert r.is_correct and r.marks_awarded == 2, prob.id


def test_accepts_two_dp_rounding():
    eng = _eng()
    for prob in (nominal_to_effective, effective_to_nominal):
        inst = eng.instantiate(prob.id, seed=3)
        assert _rate(inst, round(inst.params["answer"], 2)).is_correct, prob.id


def test_rejects_wrong_by_a_tenth_of_a_percent():
    eng = _eng()
    for prob in (nominal_to_effective, effective_to_nominal):
        inst = eng.instantiate(prob.id, seed=4)
        assert not _rate(inst, inst.params["answer"] + 0.1).is_correct, prob.id


# The 2023 Q6.1.2 → 9.06% memo check now lives in the corpus-anchor sweep
# (tests/test_corpus_anchors.py), driven by nominal_to_effective's corpus_anchor.
