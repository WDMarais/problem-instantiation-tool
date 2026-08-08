"""
Reference example: series sums — arithmetic Sₙ, finite geometric Sₙ, and
infinite geometric S∞.

Mirrors the sequence examples (one Problem per exam sub-competency,
symbolic_equality throughout, canonical in the ``answer`` param).

Formulae (family-build-specs.md Family 1 #1/#3/#4):
- arithmetic_series_sum:      Sₙ = n/2 · [2a + (n-1)d]           → integer
- geometric_series_finite:    Sₙ = a(rⁿ − 1)/(r − 1)             → integer (int r)
- geometric_series_infinite:  S∞ = a/(1 − r),  guarded |r| < 1   → Rational

Guards: integer-r series keep terms legible; the infinite series draws r as a
proper fraction so |r| < 1 holds by construction (convergence is the assessed
concept — S∞ only exists when |r| < 1).
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import Problem

_A_RANGE = [a for a in range(-6, 7) if a != 0]


# ---------------------------------------------------------------------------
# 1. arithmetic_series_sum — Sₙ of an arithmetic series
# ---------------------------------------------------------------------------


def _gen_arith_series_sum(rng: random.Random) -> dict:
    a = rng.randint(-10, 15)
    d = rng.choice([x for x in range(-6, 7) if x != 0])
    n = rng.randint(8, 25)
    # n/2·(2a+(n-1)d) is always integral: (n-1)d + 2a is even whenever n is odd,
    # and n/2 is integral whenever n is even.
    total = n * (2 * a + (n - 1) * d) // 2
    return {
        "a": a,
        "d": d,
        "n": n,
        "variant": f"arith_sum:{a}:{d}:{n}",
        "answer": sympy.Integer(total),
    }


arithmetic_series_sum = Problem(
    id="arith_series_sum",
    type_id="arithmetic_series",
    name="Sum the first n terms of an arithmetic series",
    artifact_type="practice",
    problem_spec=_gen_arith_series_sum,
    verifier_spec={"kind": "symbolic_equality", "marks_possible": 3},
)


# ---------------------------------------------------------------------------
# 2. geometric_series_finite — Sₙ of a finite geometric series
# ---------------------------------------------------------------------------


def _gen_geo_series_finite(rng: random.Random) -> dict:
    a = rng.choice(_A_RANGE)
    r = rng.choice([2, 3])
    n = rng.randint(5, 9)
    # a(rⁿ−1)/(r−1): for r=2 the divisor is 1; for r=3, rⁿ−1 is even → integral.
    total = a * (r**n - 1) // (r - 1)
    return {
        "a": a,
        "r": r,
        "n": n,
        "variant": f"geo_sum:{a}:{r}:{n}",
        "answer": sympy.Integer(total),
    }


geometric_series_finite = Problem(
    id="geo_series_finite",
    type_id="geometric_series",
    name="Sum the first n terms of a geometric series",
    artifact_type="practice",
    problem_spec=_gen_geo_series_finite,
    verifier_spec={"kind": "symbolic_equality", "marks_possible": 3},
)


# ---------------------------------------------------------------------------
# 3. geometric_series_infinite — S∞ of a convergent geometric series
# ---------------------------------------------------------------------------


def _gen_geo_series_infinite(rng: random.Random) -> dict:
    denom = rng.choice([2, 3, 4, 5])
    num = rng.choice([x for x in range(-(denom - 1), denom) if x != 0])
    r = sympy.Rational(num, denom)  # |r| < 1 by construction, r ≠ 0
    a = rng.choice(_A_RANGE)
    total = sympy.Rational(a) / (1 - r)
    return {
        "a": a,
        "r": r,
        "variant": f"geo_inf:{a}:{num}:{denom}",
        "answer": sympy.nsimplify(total),
    }


geometric_series_infinite = Problem(
    id="geo_series_infinite",
    type_id="geometric_series",
    name="Sum to infinity of a convergent geometric series",
    artifact_type="practice",
    problem_spec=_gen_geo_series_infinite,
    verifier_spec={"kind": "symbolic_equality", "marks_possible": 3},
)


# ---------------------------------------------------------------------------
# 4. find_n_from_sum — given Sₙ, find how many terms (arithmetic)
# ---------------------------------------------------------------------------


def _gen_find_n_from_sum(rng: random.Random) -> dict:
    """Given the sum of the first n terms, find n — i.e. solve the quadratic
    Sₙ = n/2[2a+(n-1)d] for n. Kept a>0, d>0 so the partial sums are strictly
    increasing and n is the unique positive root (no spurious second solution)."""
    a = rng.randint(1, 10)
    d = rng.randint(1, 6)
    n = rng.randint(5, 12)
    total = sum(a + i * d for i in range(n))
    return {
        "a": a,
        "d": d,
        "t1": a,
        "t2": a + d,
        "t3": a + 2 * d,
        "sn": total,
        "answer": sympy.Integer(n),
        "variant": f"find_n:{a}:{d}:{n}",
    }


find_n_from_sum = Problem(
    id="arith_series_find_n",
    type_id="arithmetic_series",
    name="Find the number of terms of an arithmetic series from its sum",
    artifact_type="practice",
    problem_spec=_gen_find_n_from_sum,
    verifier_spec={"kind": "symbolic_equality", "marks_possible": 4},
)


# ---------------------------------------------------------------------------
# 5. sigma_evaluate — evaluate a linear sum written in sigma notation
# ---------------------------------------------------------------------------


def _gen_sigma_evaluate(rng: random.Random) -> dict:
    """Evaluate Σₖ₌₁ⁿ (p·k + q). It is an arithmetic series (first term p+q,
    difference p), so the value is p·n(n+1)/2 + q·n — always an integer."""
    p = rng.randint(1, 4)
    q = rng.randint(-5, 5)
    n = rng.randint(4, 8)
    total = sum(p * k + q for k in range(1, n + 1))
    return {
        "p": p,
        "q": q,
        "n": n,
        "answer": sympy.Integer(total),
        "variant": f"sigma:{p}:{q}:{n}",
    }


sigma_evaluate = Problem(
    id="arith_series_sigma",
    type_id="arithmetic_series",
    name="Evaluate a linear series given in sigma notation",
    artifact_type="practice",
    problem_spec=_gen_sigma_evaluate,
    verifier_spec={"kind": "symbolic_equality", "marks_possible": 3},
)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    problems = [
        arithmetic_series_sum,
        geometric_series_finite,
        geometric_series_infinite,
    ]
    engine = Engine(registry=InMemoryRegistry({p.id: p for p in problems}))

    def show(label, instance):
        attempt = SolutionAttempt(steps=[SubmittedStep(instance.params["answer"])])
        r = instance.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible} correct={r.is_correct} "
            f"answer={instance.params['answer']}"
        )

    for prob in problems:
        inst = engine.instantiate(prob.id, seed=1)
        show(prob.id, inst)
