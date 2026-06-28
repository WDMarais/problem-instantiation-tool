"""
Reference example: one-variable statistics (mode, median, quartiles, range, percentile).

Design decisions demonstrated:
- The SA/CAPS exclusive-median quartile convention is implemented explicitly.
  Python's statistics.quantiles defaults to "inclusive" (median included in
  both halves for odd n); numpy.percentile and scipy defaults also diverge.
  The SA convention: Q1 = median of the lower n//2 values, Q3 = median of the
  upper n//2 values (the overall median is excluded from both halves when n is
  odd). This must be pinned manually — never delegate to a library default.
- A unique mode is enforced by the generator guard. Datasets with tied maximum
  frequency are resampled. The exam expects a single-valued mode answer.
- Median and quartiles are stored as sympy.Rational to handle the x.5 case.
  symbolic_equality accepts "5/2", "2.5", and Rational(5,2) as equivalent.
- pct_above_q3: count of values strictly above Q3, divided by n, as a
  percentage. numeric_equality with tolerance 0.5 accepts expected student
  rounding. This is approximately 25% by construction but not exactly, since
  Q3 is computed from a finite dataset.
- All sub-answers use param_key routing — same pattern as
  analytic_geometry_triangle.py.
"""

from __future__ import annotations

import random
from collections import Counter

import sympy

from problem_instantiation_tool.schemas import Problem


def _median_of(data: list[int]) -> sympy.Basic:
    m = len(data)
    if m % 2 == 1:
        return sympy.Integer(data[m // 2])
    return sympy.Rational(data[m // 2 - 1] + data[m // 2], 2)


def _generate(rng: random.Random) -> dict:
    while True:
        n = rng.choice([20, 25, 30])
        data = sorted(rng.randint(10, 90) for _ in range(n))

        counts = Counter(data)
        top = counts.most_common(2)
        if len(top) < 2 or top[0][1] == top[1][1]:
            continue  # no unique mode — resample

        q1 = _median_of(data[: n // 2])
        q3 = _median_of(data[(n + 1) // 2 :])

        return {
            "data": data,
            "n": n,
            "mode": sympy.Integer(top[0][0]),
            "median": _median_of(data),
            "q1": q1,
            "q3": q3,
            "data_range": sympy.Integer(data[-1] - data[0]),
            "pct_above_q3": sum(1 for x in data if x > float(q3)) / n * 100,
        }


problem = Problem(
    id="stats_one_var",
    type_id="statistics",
    name="Mode, median, quartiles, range, and percentile from a raw dataset",
    artifact_type="practice",
    problem_spec=_generate,
    verifier_spec=[
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "mode"},
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "median"},
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "q1"},
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "q3"},
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "data_range"},
        {
            "kind": "numeric_equality",
            "marks_possible": 1,
            "param_key": "pct_above_q3",
            "tolerance": 0.5,
        },
    ],
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(registry=InMemoryRegistry({problem.id: problem}))
    instance = engine.instantiate(problem.id, seed=42)
    p = instance.params

    print(f"n = {p['n']}")
    print(f"Data     : {p['data']}")
    print(f"Mode     : {p['mode']}")
    print(f"Median   : {p['median']}")
    print(f"Q1       : {p['q1']}")
    print(f"Q3       : {p['q3']}")
    print(f"Range    : {p['data_range']}")
    print(f"% > Q3   : {p['pct_above_q3']:.1f}%")
    print()

    def show(label, *answers):
        attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
        r = instance.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  "
            f"is_correct={r.is_correct}"
        )

    show(
        "All correct (canonical values)     ",
        p["mode"],
        p["median"],
        p["q1"],
        p["q3"],
        p["data_range"],
        p["pct_above_q3"],
    )
    # Demonstrate symbolic_equality accepts "3/2" string for Rational(3, 2) canonical
    show(
        "Median as fraction string          ",
        p["mode"],
        str(p["median"]),
        p["q1"],
        p["q3"],
        p["data_range"],
        p["pct_above_q3"],
    )
    show(
        "Wrong mode, rest correct           ",
        p["mode"] + 1,
        p["median"],
        p["q1"],
        p["q3"],
        p["data_range"],
        p["pct_above_q3"],
    )
    show(
        "Pct rounded to nearest int (±0.5)  ",
        p["mode"],
        p["median"],
        p["q1"],
        p["q3"],
        p["data_range"],
        round(p["pct_above_q3"]),
    )
