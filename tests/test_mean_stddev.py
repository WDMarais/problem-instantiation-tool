"""
Independent-oracle tests for ``mean_stddev``.

The generator computes the mean and population variance in exact SymPy
rationals. The oracle recomputes them with Python's stdlib ``statistics``
(``mean`` / ``pstdev``) — a separate implementation — and re-derives the
within-one-σ count directly, so agreement is a genuine cross-check.
"""

from __future__ import annotations

import random
import statistics

from content.examples.mean_stddev import _gen, mean_stddev
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep


def _params(seed):
    return _gen(random.Random(seed))


# --- the oracle: stdlib statistics reproduces mean and population σ ----------


def test_stdlib_reproduces_mean_and_population_sigma():
    for seed in range(200):
        p = _params(seed)
        assert abs(float(p["mean"]) - statistics.mean(p["data"])) < 1e-9, seed
        assert abs(p["stddev"] - statistics.pstdev(p["data"])) < 1e-4, seed


def test_within_one_sd_count_is_reproduced():
    for seed in range(200):
        p = _params(seed)
        mu = statistics.mean(p["data"])
        sd = statistics.pstdev(p["data"])
        count = sum(1 for x in p["data"] if mu - sd <= x <= mu + sd)
        assert count == p["within_1sd"], seed


def test_it_is_population_not_sample_sd():
    # The stored σ must be the population value (÷ n), not the sample value.
    for seed in range(100):
        p = _params(seed)
        pop = statistics.pstdev(p["data"])
        sample = statistics.stdev(p["data"])
        assert abs(p["stddev"] - pop) < 1e-4, seed
        assert abs(p["stddev"] - sample) > 1e-3, seed  # genuinely different


# --- construction is well-formed --------------------------------------------


def test_variance_is_non_zero_and_count_is_sane():
    for seed in range(300):
        p = _params(seed)
        assert p["stddev"] > 0, seed
        assert 1 <= p["within_1sd"] <= p["n"], seed


# --- distribution honesty ----------------------------------------------------


def test_means_and_sigmas_are_not_stuck():
    means, sigmas, ns = set(), set(), set()
    for seed in range(300):
        p = _params(seed)
        means.add(round(float(p["mean"]), 1))
        sigmas.add(round(p["stddev"], 1))
        ns.add(p["n"])
    assert len(means) > 50 and len(sigmas) > 30
    assert ns == {8, 9, 10, 11, 12}


# --- verifier round-trips ----------------------------------------------------


def _rate(inst, *answers):
    attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
    return inst.verifier.rate(attempt)


def test_two_dp_calculator_answers_score_full():
    engine = Engine(registry=InMemoryRegistry({mean_stddev.id: mean_stddev}))
    for seed in range(40):
        inst = engine.instantiate(mean_stddev.id, seed=seed)
        p = inst.params
        res = _rate(
            inst, round(float(p["mean"]), 2), round(p["stddev"], 2), p["within_1sd"]
        )
        assert res.marks_awarded == 3 and res.is_correct, seed


def test_sample_sd_confusion_misses_only_the_sigma_mark():
    engine = Engine(registry=InMemoryRegistry({mean_stddev.id: mean_stddev}))
    for seed in range(40):
        inst = engine.instantiate(mean_stddev.id, seed=seed)
        p = inst.params
        sample_sd = round(statistics.stdev(p["data"]), 2)
        res = _rate(inst, round(float(p["mean"]), 2), sample_sd, p["within_1sd"])
        assert res.marks_awarded == 2 and not res.is_correct, seed


def test_wrong_count_loses_only_its_mark():
    engine = Engine(registry=InMemoryRegistry({mean_stddev.id: mean_stddev}))
    for seed in range(30):
        inst = engine.instantiate(mean_stddev.id, seed=seed)
        p = inst.params
        res = _rate(
            inst, round(float(p["mean"]), 2), round(p["stddev"], 2), p["within_1sd"] + 1
        )
        assert res.marks_awarded == 2 and not res.is_correct, seed
