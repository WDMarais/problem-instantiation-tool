"""
Finance / Annuities — archetype 6: ``depreciation`` (Gr12).

Assets losing value over time under one of **two named sub-models** — the stem
must say which, because the arithmetic differs:

    straight-line (simple):   A = P·(1 − i·n)      value drops by a fixed R amount
    reducing-balance:         A = P·(1 − i)^n      value drops by a fixed % of book

with ``i = r/100``. Straight-line reaches exactly zero at ``n = 1/i`` and would
go negative after that — a real asset is simply scrapped — so every straight-line
generator here keeps ``i·n`` comfortably below 1 (book value stays positive).

Three modes, one Problem each:

- ``depreciation_amount``   solve A (either sub-model, named in the stem)  → 2 marks
- ``depreciation_rate``     solve r from P and the book value (straight-line) → 2 marks
- ``depreciation_to_zero``  straight-line: after how many years is it worth
                            R0?  n = 1/i, rounded **up** (the year the value
                            first hits/passes zero)                       → 2 marks

Verifier: ``numeric_equality`` abs ±cent / rel 1e-4 for the money answer; the
rate mode is a 2-dp percentage (small, absolute band only); the to-zero mode is
an exact integer count.

Params corpus-grounded (finance-family-spec.md §depreciation): P ∈ {5k … 200k},
r ∈ {10, 15, 20, 25}%, n ∈ {3 … 8}. Anchors: 2024 Nov Q7.2 (determine the rate),
2023 Nov Q6.2.1 (straight-line to zero).
"""

from __future__ import annotations

import math
import random

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

_PRINCIPALS = [5000, 12000, 18000, 45000, 80000, 120000, 200000]
_RATES = [10, 15, 20, 25]
_YEARS = [3, 4, 5, 6, 7, 8]
_MODELS = ["straight_line", "reducing_balance"]

# Keep straight-line book value positive: i·n must stay below 1. Cap at 0.85 so
# at least ~15% of the price remains — a sane, non-degenerate asset.
_SL_CAP = 0.85

_MONEY_VERIFIER = {
    "kind": "numeric_equality",
    "tolerance": 0.01,
    "rel_tol": 1e-4,
}


def _straight_line_years(i: float) -> list[int]:
    """Years from the menu that keep a straight-line asset above zero."""
    return [n for n in _YEARS if i * n <= _SL_CAP]


# ---------------------------------------------------------------------------
# 1. depreciation_amount — solve the book value A (either sub-model)
# ---------------------------------------------------------------------------


def _gen_depr_amount(rng: random.Random) -> dict:
    model = rng.choice(_MODELS)
    p = rng.choice(_PRINCIPALS)
    r = rng.choice(_RATES)
    i = r / 100
    if model == "straight_line":
        n = rng.choice(_straight_line_years(i))
        a = p * (1 - i * n)
    else:
        n = rng.choice(_YEARS)
        a = p * (1 - i) ** n
    return {
        "book_price": p,
        "rate": r,
        "years": n,
        "model": model,  # straight_line | reducing_balance
        "answer": a,
        "variant": f"depr_amt:{p}:{r}:{n}:{model}",
    }


depreciation_amount = Problem(
    id="finance_depreciation_amount",
    type_id="financial_maths",
    name="Depreciated book value  A = P(1−i·n) [SL] / P(1−i)^n [reducing]",
    artifact_type="practice",
    problem_spec=_gen_depr_amount,
    verifier_spec={**_MONEY_VERIFIER, "marks_possible": 2},
)


# ---------------------------------------------------------------------------
# 2. depreciation_rate — solve the straight-line rate from the book value
# ---------------------------------------------------------------------------


def _gen_depr_rate(rng: random.Random) -> dict:
    """Straight-line: given price P and book value A after n years, determine the
    annual rate. r = 100·(1 − A/P)/n. A is built from a clean rate so it recovers
    exactly."""
    p = rng.choice(_PRINCIPALS)
    r = rng.choice(_RATES)
    i = r / 100
    n = rng.choice(_straight_line_years(i))
    a = p * (1 - i * n)
    return {
        "book_price": p,
        "book_value": a,
        "years": n,
        "model": "straight_line",
        "answer": r,  # the percentage rate
        "variant": f"depr_rate:{p}:{r}:{n}",
    }


depreciation_rate = Problem(
    id="finance_depreciation_rate",
    type_id="financial_maths",
    name="Straight-line depreciation rate  r = 100(1 − A/P)/n",
    artifact_type="practice",
    problem_spec=_gen_depr_rate,
    verifier_spec={"kind": "numeric_equality", "marks_possible": 2, "tolerance": 0.01},
    corpus_anchor=CorpusAnchor(paper="2024 Nov P1", question="7.2", marks=2),
)


# ---------------------------------------------------------------------------
# 3. depreciation_to_zero — straight-line: years until the value reaches R0
# ---------------------------------------------------------------------------


def _gen_depr_to_zero(rng: random.Random) -> dict:
    """Straight-line value hits zero at n = 1/i. Where that is not a whole number
    the asset is scrapped in the year the value first passes zero → round up."""
    p = rng.choice(_PRINCIPALS)
    r = rng.choice(_RATES)
    i = r / 100
    return {
        "book_price": p,
        "rate": r,
        "model": "straight_line",
        "answer": math.ceil(1 / i),  # ceil(100/r)
        "variant": f"depr_zero:{p}:{r}",
    }


depreciation_to_zero = Problem(
    id="finance_depreciation_to_zero",
    type_id="financial_maths",
    name="Years to zero book value (straight-line)  n = ⌈1/i⌉",
    artifact_type="practice",
    problem_spec=_gen_depr_to_zero,
    verifier_spec={"kind": "numeric_equality", "marks_possible": 2, "tolerance": 0.01},
    corpus_anchor=CorpusAnchor(paper="2023 Nov P1", question="6.2.1", marks=2),
)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    problems = [depreciation_amount, depreciation_rate, depreciation_to_zero]
    engine = Engine(registry=InMemoryRegistry({p.id: p for p in problems}))

    def show(instance, label, answer):
        attempt = SolutionAttempt(steps=[SubmittedStep(answer)])
        r = instance.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  "
            f"is_correct={r.is_correct}"
        )

    print("=== depreciation_amount ===")
    inst = engine.instantiate(depreciation_amount.id, seed=4)
    p = inst.params
    print(
        f"  P={p['book_price']}, r={p['rate']}%, n={p['years']} yr, "
        f"{p['model']}  →  A = {p['answer']:.2f}"
    )
    show(inst, "Rounded to 2dp", round(p["answer"], 2))

    print("\n=== depreciation_to_zero ===")
    inst = engine.instantiate(depreciation_to_zero.id, seed=4)
    p = inst.params
    print(
        f"  P={p['book_price']}, r={p['rate']}%  →  1/i = {100 / p['rate']:.3f}, "
        f"⌈·⌉ = {p['answer']} years"
    )
    show(inst, "Exact count   ", p["answer"])
