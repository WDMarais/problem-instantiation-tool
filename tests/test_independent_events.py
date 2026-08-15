"""
Independent oracle for ``independent_events``.

For the intersection/union variants the generator uses the algebraic rules
P(A∩B) = P(A)P(B) and P(A∪B) = P(A)+P(B)−P(A)P(B). The oracle instead builds the
**joint sample space of two independent experiments** as an explicit grid of
equally likely outcomes and *counts* the favourable ones — no product or
inclusion–exclusion formula involved — then compares (via stdlib
``fractions.Fraction``, a different arithmetic path than SymPy) to the stored
answer.
"""

from __future__ import annotations

from fractions import Fraction

import pytest
import sympy

from content.examples.independent_events import (
    independent_decide,
    independent_intersection,
    independent_union,
)
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import (
    SolutionAttempt,
    SubmittedStep,
)

_PROBLEMS = {
    p.id: p for p in [independent_intersection, independent_union, independent_decide]
}
_ENGINE = Engine(registry=InMemoryRegistry(_PROBLEMS))


def _frac(r: sympy.Rational) -> Fraction:
    return Fraction(int(sympy.numer(r)), int(sympy.denom(r)))


def _grid_counts(p_a: sympy.Rational, p_b: sympy.Rational):
    """Enumerate the den_a × den_b joint outcome grid of two independent
    experiments; return (P(A∩B), P(A∪B)) as counted fractions."""
    da, na = int(sympy.denom(p_a)), int(sympy.numer(p_a))
    db, nb = int(sympy.denom(p_b)), int(sympy.numer(p_b))
    total = da * db
    inter = union = 0
    for i in range(da):
        for j in range(db):
            a_occurs = i < na  # "A" holds on the first na outcomes of expt 1
            b_occurs = j < nb
            if a_occurs and b_occurs:
                inter += 1
            if a_occurs or b_occurs:
                union += 1
    return Fraction(inter, total), Fraction(union, total)


@pytest.mark.parametrize("pid", ["independent_intersection", "independent_union"])
def test_answer_matches_grid_enumeration(pid):
    for seed in range(80):
        inst = _ENGINE.instantiate(pid, seed=seed)
        p = inst.params
        inter, union = _grid_counts(p["p_a"], p["p_b"])
        expected = inter if pid == "independent_intersection" else union
        assert _frac(p["answer"]) == expected, (pid, seed)


@pytest.mark.parametrize("pid", ["independent_intersection", "independent_union"])
def test_answer_is_a_valid_probability(pid):
    for seed in range(40):
        inst = _ENGINE.instantiate(pid, seed=seed)
        ans = _frac(inst.params["answer"])
        assert 0 <= ans <= 1, (pid, seed)


# --- the decide variant ------------------------------------------------------


def test_decide_product_and_verdict_are_consistent():
    for seed in range(120):
        inst = _ENGINE.instantiate("independent_decide", seed=seed)
        p = inst.params
        product = _frac(p["p_a"]) * _frac(p["p_b"])
        assert _frac(p["product"]) == product, seed
        expected = "independent" if _frac(p["p_ab"]) == product else "not_independent"
        assert p["verdict"] == expected, seed


def test_decide_intersection_is_admissible():
    for seed in range(120):
        inst = _ENGINE.instantiate("independent_decide", seed=seed)
        p = inst.params
        p_ab, p_a, p_b = _frac(p["p_ab"]), _frac(p["p_a"]), _frac(p["p_b"])
        assert 0 < p_ab <= min(p_a, p_b), seed
        assert p_a + p_b - p_ab <= 1, seed  # P(A∪B) ≤ 1


def test_decide_is_balanced_across_seeds():
    verdicts = set()
    for seed in range(60):
        inst = _ENGINE.instantiate("independent_decide", seed=seed)
        verdicts.add(inst.params["verdict"])
    assert verdicts == {"independent", "not_independent"}


# --- verifier round-trips ----------------------------------------------------


@pytest.mark.parametrize("pid", ["independent_intersection", "independent_union"])
def test_correct_scores_full_fraction_or_decimal(pid):
    inst = _ENGINE.instantiate(pid, seed=5)
    ans = inst.verifier.canonicals[0]
    for form in (ans, str(float(ans))):
        r = inst.verifier.rate(SolutionAttempt(steps=[SubmittedStep(form)]))
        assert r.marks_awarded == 1 and r.is_correct, (pid, form)


def test_decide_wrong_verdict_keeps_only_the_product_mark():
    inst = _ENGINE.instantiate("independent_decide", seed=1)
    p = inst.params
    flip = "not_independent" if p["verdict"] == "independent" else "independent"
    r = inst.verifier.rate(
        SolutionAttempt(steps=[SubmittedStep(p["product"]), SubmittedStep(flip)])
    )
    assert r.marks_awarded == 1 and not r.is_correct


def test_decide_wrong_product_keeps_only_the_verdict_mark():
    inst = _ENGINE.instantiate("independent_decide", seed=1)
    p = inst.params
    bad_product = p["product"] + sympy.Rational(1, 20)
    r = inst.verifier.rate(
        SolutionAttempt(steps=[SubmittedStep(bad_product), SubmittedStep(p["verdict"])])
    )
    assert r.marks_awarded == 1 and not r.is_correct
