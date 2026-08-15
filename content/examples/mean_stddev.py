"""
Statistics, archetype 2 — ``mean_stddev``.

Given a raw dataset, find the **mean** x̄, the **(population) standard deviation**
σ, and the **number of data values within one standard deviation of the mean**
(i.e. in [x̄ − σ, x̄ + σ]). Like regression, this is a "drive the calculator's
stat mode" skill: x̄ and σ are calculator decimals graded with tolerance, and the
count is an exact integer.

The standard deviation is the **population** σ (÷ n), the DBE convention — a
student who reports the *sample* std-dev (÷ n−1) is off by the factor √(n/(n−1)),
several percent, which the 0.05 band rejects. That distinction is the assessed
point, so the band is deliberately tight enough to enforce it.

The within-one-σ boundary is |x − x̄| ≤ σ. Because σ is irrational while the data
and mean are rational, a value never lands exactly on the boundary, so the count
is unambiguous.

**Construction** draws n integer values from a spread wide enough to give a real
standard deviation, and rejects the zero-variance (all-equal) draw. Nothing is
clamped: x̄ and σ are whatever the sample produces.
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import CorpusAnchor, Problem


def _gen(rng: random.Random) -> dict:
    while True:
        n = rng.choice([8, 9, 10, 11, 12])
        data = sorted(rng.randint(10, 90) for _ in range(n))
        mean = sympy.Rational(sum(data), n)
        var = sum((x - mean) ** 2 for x in data) / n  # population variance
        if var == 0:  # all values equal — no spread
            continue
        break

    sigma = sympy.sqrt(var)
    lo = float(mean) - float(sigma)
    hi = float(mean) + float(sigma)
    within = sum(1 for x in data if lo <= x <= hi)

    return {
        "data": data,
        "n": n,
        "mean": mean,  # exact rational
        "stddev": round(float(sigma), 4),  # population σ, carries a surd
        "within_1sd": within,  # exact count
        "data_latex": r",\ ".join(str(x) for x in data),
    }


mean_stddev = Problem(
    id="mean_stddev",
    type_id="mean_stddev",
    name="Mean, standard deviation and count within one standard deviation",
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
    ],
    corpus_anchor=CorpusAnchor(
        paper="2023 Nov P2",
        question="1.5.1–1.5.3",  # mean / std-dev / threshold count
        # the three sub-parts share a 5-mark block in our provenance notes;
        # the standalone answer-mark split is left unset rather than forced.
    ),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(registry=InMemoryRegistry({mean_stddev.id: mean_stddev}))

    def show(label, inst, *answers):
        attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
        r = inst.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  "
            f"is_correct={r.is_correct}"
        )

    for seed in range(4):
        inst = engine.instantiate(mean_stddev.id, seed=seed)
        p = inst.params
        mean2 = round(float(p["mean"]), 2)
        print(f"=== seed {seed} ===")
        print(f"  data: {p['data']}")
        print(
            f"  x̄ = {mean2}   σ = {round(p['stddev'], 2)}   "
            f"within 1σ: {p['within_1sd']}/{p['n']}"
        )
        show("2-dp calc values", inst, mean2, round(p["stddev"], 2), p["within_1sd"])
        # sample std-dev (÷ n−1) instead of population σ → misses the σ mark
        sample_sd = round(
            float(
                sympy.sqrt(sum((x - p["mean"]) ** 2 for x in p["data"]) / (p["n"] - 1))
            ),
            2,
        )
        show("sample sd (÷n−1)", inst, mean2, sample_sd, p["within_1sd"])
