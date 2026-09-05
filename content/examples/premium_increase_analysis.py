"""
Statistics — ``premium_increase_analysis`` (the shared-stem P2 Q1).

One dataset of 15 monthly insurance premiums (in rands) carries the whole question:

    1.1  the mean x̄                                              (auto: mean)
    1.2  the (population) standard deviation σ                   (auto: stddev)
    1.3  how many premiums lie within one σ, |x − x̄| ≤ σ         (auto: count)
    1.4  a weighted increase — premiums < R500 rise by p%, premiums ≥ R500
         by k%, and the new mean is given → solve for k         (auto: k)

1.1–1.3 are the standard "drive the calculator's stat mode" skills (x̄ and σ are
calculator decimals graded with tolerance; σ is the population value, ÷ n, the DBE
convention). 1.4 is a weighted-mean inverse: the two threshold groups are increased by
different percentages and the resulting mean pins the unknown k.

Built forward — the k% increase is chosen and the new mean computed from it, then
presented rounded to the cent (as the exam does), so k recovers to well within its
grading tolerance. Well-posed for every draw (both threshold groups populated, non-zero
spread, distinct values), so no F1 scope predicate.

Engine-graded canonical total = 4 of the 9 headline marks: x̄, σ, the count and k — one
value each. The "sum then divide" line (1.1), the σ-interval boundary (1.3) and the
whole weighted-mean set-up (1.4) are the hand-marked method; 1.2 is a pure "write down"
so it is fully auto.
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

_N = 15
_THRESHOLD = 500  # the R500 split for the 1.4 weighted increase
_LOW_PCT = (10, 12, 15, 18, 20)  # given % increase on the below-threshold group
_K_PCT = (15, 18, 20, 21, 24, 25, 28, 30)  # the 1.4 answer: % on the at-or-above group


def _analyse(data: list[int], low_pct: int, k_pct: int) -> dict | None:
    """Re-derive the whole question from the dataset and the two percentages. Pure —
    used by the generator; returns None for a degenerate (zero-spread) draw."""
    n = len(data)
    mean = sympy.Rational(sum(data), n)
    var = sum((x - mean) ** 2 for x in data) / n  # population variance (÷ n)
    if var == 0:
        return None
    sigma = sympy.sqrt(var)
    lo_b, hi_b = float(mean) - float(sigma), float(mean) + float(sigma)
    within = sum(1 for x in data if lo_b <= x <= hi_b)

    low = [x for x in data if x < _THRESHOLD]
    high = [x for x in data if x >= _THRESHOLD]
    low_sum, high_sum = sum(low), sum(high)
    low_increased = low_sum * (1 + sympy.Rational(low_pct, 100))
    new_total = low_increased + high_sum * (1 + sympy.Rational(k_pct, 100))
    new_mean = new_total / n

    return {
        "n": n,
        "mean": mean,  # exact rational; graded as a decimal with tolerance
        "stddev": round(float(sigma), 4),  # population σ (carries a surd)
        "within_1sd": within,  # exact count
        "low_count": len(low),
        "high_count": len(high),
        "low_sum": low_sum,
        "high_sum": high_sum,
        "low_increased": round(float(low_increased), 2),
        "low_pct": low_pct,
        "k": k_pct,  # the 1.4 answer
        "new_mean": new_mean,  # exact
        "new_mean_presented": round(float(new_mean), 2),  # what the question states
    }


def _gen(rng: random.Random) -> dict:
    while True:
        data = sorted(rng.randint(120, 1250) for _ in range(_N))
        if len(set(data)) != _N:  # distinct premiums so the table reads cleanly
            continue
        low = [x for x in data if x < _THRESHOLD]
        high = [x for x in data if x >= _THRESHOLD]
        if len(low) < 4 or len(high) < 4:  # both threshold groups well populated
            continue
        low_pct = rng.choice(_LOW_PCT)
        k_pct = rng.choice(_K_PCT)
        res = _analyse(data, low_pct, k_pct)
        if res is not None:
            break

    return {
        "data": data,
        "threshold": _THRESHOLD,
        **res,
    }


premium_increase_analysis = Problem(
    id="premium_increase_analysis",
    type_id="premium_increase_analysis",
    name="Premium data — mean, σ, within-one-σ count, weighted k% (Q1)",
    artifact_type="practice",
    problem_spec=_gen,
    verifier_spec=[
        {
            "kind": "numeric_equality",
            "marks_possible": 1,
            "param_key": "mean",
            "tolerance": 0.05,
        },
        {
            "kind": "numeric_equality",
            "marks_possible": 1,
            "param_key": "stddev",
            "tolerance": 0.05,
        },
        {"kind": "numeric_equality", "marks_possible": 1, "param_key": "within_1sd"},
        {
            "kind": "numeric_equality",
            "marks_possible": 1,
            "param_key": "k",
            "tolerance": 0.5,
        },
    ],
    corpus_anchor=CorpusAnchor(
        paper="2025 May/June P2",
        question="1",
        marks=9,
    ),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(
        registry=InMemoryRegistry(
            {premium_increase_analysis.id: premium_increase_analysis}
        )
    )
    for seed in (1, 7, 13):
        inst = engine.instantiate(premium_increase_analysis.id, seed=seed)
        p = inst.params
        print(
            f"seed {seed}: x̄={float(p['mean']):.2f} σ={p['stddev']:.2f} "
            f"within={p['within_1sd']} | 1.4: +{p['low_pct']}%/<500, +k%/≥500, "
            f"new mean R{p['new_mean_presented']} → k={p['k']}"
        )
        keys = ["mean", "stddev", "within_1sd", "k"]
        attempt = SolutionAttempt(steps=[SubmittedStep(p[key]) for key in keys])
        r = inst.verifier.rate(attempt)
        print(f"  all-correct → {r.marks_awarded}/{r.marks_possible} ok={r.is_correct}")
