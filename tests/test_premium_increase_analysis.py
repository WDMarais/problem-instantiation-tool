"""
Statistics — ``premium_increase_analysis`` (the shared-stem P2 Q1).

One dataset of 15 premiums drives four sub-parts: the mean (1.1), the population
standard deviation (1.2), the count within one σ (1.3) and a weighted-increase inverse
for k (1.4). Every answer is independently re-derived here (no reuse of the generator's
``_analyse``); the verifier round-trips all four; k recovers from the *rounded*
presented mean the question states, well inside its grading tolerance.
"""

import math

import sympy

from content.examples.premium_increase_analysis import premium_increase_analysis
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

_THRESHOLD = 500


def _eng():
    return Engine(
        registry=InMemoryRegistry(
            {premium_increase_analysis.id: premium_increase_analysis}
        )
    )


def _params(seed):
    return _eng().instantiate(premium_increase_analysis.id, seed=seed).params


def test_stats_match_independent_rederivation():
    for seed in range(60):
        p = _params(seed)
        data = p["data"]
        n = len(data)
        assert n == 15
        mean = sum(data) / n
        var = sum((x - mean) ** 2 for x in data) / n  # population variance (÷ n)
        sigma = math.sqrt(var)
        within = sum(1 for x in data if abs(x - mean) <= sigma)

        assert float(p["mean"]) == mean
        assert abs(float(p["stddev"]) - sigma) < 5e-5  # stored σ is rounded to 4 dp
        assert p["within_1sd"] == within


def test_both_threshold_groups_are_populated():
    for seed in range(60):
        p = _params(seed)
        low = [x for x in p["data"] if x < _THRESHOLD]
        high = [x for x in p["data"] if x >= _THRESHOLD]
        assert len(low) >= 4 and len(high) >= 4
        assert p["low_count"] == len(low)
        assert p["high_count"] == len(high)


def test_k_recovers_from_the_rounded_presented_mean():
    # the question states the new mean rounded to the cent; k must still be recoverable
    # from that rounded value to within the grading tolerance (0.5)
    for seed in range(60):
        p = _params(seed)
        n = len(p["data"])
        low_inc = p["low_sum"] * (1 + p["low_pct"] / 100)
        # invert: presented_mean * n = low_inc + high_sum * (1 + k/100)
        presented_total = p["new_mean_presented"] * n
        k_recovered = (presented_total - low_inc) / p["high_sum"] * 100 - 100
        assert abs(k_recovered - p["k"]) < 0.5


def test_variety():
    seen = {(_params(s)["mean"], _params(s)["k"]) for s in range(60)}
    assert len(seen) >= 20


def test_verifier_grades_all_four():
    inst = _eng().instantiate(premium_increase_analysis.id, seed=7)
    p = inst.params
    keys = ["mean", "stddev", "within_1sd", "k"]
    attempt = SolutionAttempt(steps=[SubmittedStep(p[key]) for key in keys])
    r = inst.verifier.rate(attempt)
    assert r.marks_awarded == 4 and r.marks_possible == 4 and r.is_correct


def test_verifier_partial_credit():
    inst = _eng().instantiate(premium_increase_analysis.id, seed=7)
    p = inst.params
    # correct mean + σ, wrong count + k → 2 of 4
    steps = [p["mean"], p["stddev"], p["within_1sd"] + 3, p["k"] + 20]
    r = inst.verifier.rate(SolutionAttempt(steps=[SubmittedStep(s) for s in steps]))
    assert r.marks_awarded == 2 and not r.is_correct


def test_mean_accepts_calculator_decimal():
    inst = _eng().instantiate(premium_increase_analysis.id, seed=3)
    p = inst.params
    approx = sympy.Float(round(float(p["mean"]), 2))
    steps = [approx, p["stddev"], p["within_1sd"], p["k"]]
    r = inst.verifier.rate(SolutionAttempt(steps=[SubmittedStep(s) for s in steps]))
    assert r.marks_awarded == 4


def test_template_is_shared_stem_compound():
    from worksheets.generate import PROBLEMS, template_premium_increase_analysis

    p = _params(1)
    for detail in ("full", "short"):
        card = template_premium_increase_analysis(p, detail=detail)
        assert len(card.subparts) == 4
        assert sum(sp.marks for sp in card.subparts) == 9  # NSC headline
        assert sum(sp.auto_marks for sp in card.subparts) == 4  # canonical total
        assert card.display_math  # the dataset is on the stem
        assert all(sp.memo_steps for sp in card.subparts)
    assert premium_increase_analysis.id in PROBLEMS


def test_reproduces_source_marks_and_topic():
    a = premium_increase_analysis.corpus_anchor
    assert a.paper == "2025 May/June P2"
    assert a.question == "1"
    assert a.marks == 9
