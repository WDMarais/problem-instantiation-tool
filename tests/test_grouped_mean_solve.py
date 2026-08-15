"""
Independent-oracle tests for ``grouped_mean_solve``.

The generator solves for k with a closed-form rearrangement. The oracle checks
it two independent ways: substitute k back into the grouped-mean definition and
confirm it reproduces the stated mean exactly, and solve the same equation
symbolically with SymPy (a different route than the closed form).
"""

from __future__ import annotations

import random

import sympy

from content.examples.grouped_mean_solve import _MIDPOINTS, _gen, grouped_mean_solve
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep


def _params(seed):
    return _gen(random.Random(seed))


def _known_sums(p):
    j = p["unknown_index"]
    sum_f = sum(f for i, f in enumerate(p["frequencies"]) if i != j)
    sum_fm = sum(f * _MIDPOINTS[i] for i, f in enumerate(p["frequencies"]) if i != j)
    return j, sum_f, sum_fm


# --- the oracle: k reproduces the stated mean, and SymPy resolves it ---------


def test_substituting_k_reproduces_the_stated_mean():
    for seed in range(300):
        p = _params(seed)
        j, sum_f, sum_fm = _known_sums(p)
        k = p["unknown_frequency"]
        mean = sympy.Rational(sum_fm + k * _MIDPOINTS[j], sum_f + k)
        assert mean == p["mean_given"], seed


def test_symbolic_solve_recovers_k():
    k = sympy.Symbol("k", positive=True)
    for seed in range(200):
        p = _params(seed)
        j, sum_f, sum_fm = _known_sums(p)
        eq = sympy.Eq((sum_fm + k * _MIDPOINTS[j]) / (sum_f + k), p["mean_given"])
        sols = sympy.solve(eq, k)
        assert sols == [p["unknown_frequency"]], seed


# --- construction is well-formed --------------------------------------------


def test_k_is_a_positive_whole_frequency_and_class_is_valid():
    for seed in range(300):
        p = _params(seed)
        assert isinstance(p["unknown_frequency"], int), seed
        assert 1 <= p["unknown_frequency"] <= 40, seed
        j = p["unknown_index"]
        assert p["frequencies"][j] is None, seed  # the unknown slot is blank
        assert _MIDPOINTS[j] != p["mean_given"], seed  # no divide-by-zero class


# --- distribution honesty ----------------------------------------------------


def test_unknowns_means_and_classes_are_not_stuck():
    ks, means, js = set(), set(), set()
    for seed in range(400):
        p = _params(seed)
        ks.add(p["unknown_frequency"])
        means.add(p["mean_given"])
        js.add(p["unknown_index"])
    assert len(ks) > 12  # a real spread of answers
    assert len(means) > 8  # the given mean varies
    assert js == set(range(len(_MIDPOINTS)))  # every class can hold the unknown


# --- verifier round-trips ----------------------------------------------------


def _rate(inst, *answers):
    attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
    return inst.verifier.rate(attempt)


def test_correct_k_scores_full():
    engine = Engine(
        registry=InMemoryRegistry({grouped_mean_solve.id: grouped_mean_solve})
    )
    for seed in range(40):
        inst = engine.instantiate(grouped_mean_solve.id, seed=seed)
        p = inst.params
        r = _rate(inst, p["unknown_frequency"])
        assert r.marks_awarded == 1 and r.is_correct, seed


def test_wrong_k_scores_zero():
    engine = Engine(
        registry=InMemoryRegistry({grouped_mean_solve.id: grouped_mean_solve})
    )
    for seed in range(40):
        inst = engine.instantiate(grouped_mean_solve.id, seed=seed)
        p = inst.params
        r = _rate(inst, p["unknown_frequency"] + 1)
        assert r.marks_awarded == 0 and not r.is_correct, seed
