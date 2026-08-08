"""
Finance / Annuities — archetype 4: ``future_value_annuity`` (Gr12, flagship A).

Regular equal deposits accumulating to a future value. The first archetype
where **payment timing** (ordinary vs due) earns its keep — it is a param,
stated in the stem, and changes the canonical by a factor of (1 + i).

Formula (finance-family-spec.md, archetype 4):
    ordinary:  F = x·[(1 + i)^N − 1] / i,   i = r/(100m),  N = m·n
    due:       F_due = F·(1 + i)             (deposits at the start of each period)

Three modes, one Problem each:

- ``fv_annuity_amount``   solve F given the deposit x                → 3 marks
- ``fv_annuity_deposit``  solve x to reach a target F (round goal)   → 4 marks
- ``fv_annuity_n``        solve N: how many deposits reach the goal   → 4 marks
                          N = ln(1 + F·i/x) / ln(1 + i), then **ceil**
                          ("how many deposits until the fund reaches ≥ target"
                          — a final smaller top-up still counts as a deposit).

Money verifier: ``numeric_equality`` with the absolute ±cent band and rel_tol
1e-4 (targets run to R1.5m, so the relative band absorbs rounding drift). The
solve-N answer is a count, graded exactly.

Guards: i > 0 always (positive rates); solve-N draws a true integer count and
sets the target strictly between the (N−1)-th and N-th accumulated values, so
the ceil is unambiguous. Params corpus-grounded (finance-family-spec.md §4):
x ∈ {500 … 5 000}, r ∈ {5.8 … 9.5}%, m ∈ {4, 12}.
Anchors: 2023 Nov Q6.2.2 (solve deposit), 2025 Nov Q7.2 (due, quarterly).
"""

from __future__ import annotations

import math
import random

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

_DEPOSITS = [500, 750, 1000, 1500, 2000, 2300, 3000, 5000]
_TARGETS = [100000, 250000, 500000, 750000, 1000000, 1500000]
_RATES = [5.8, 6.8, 7.8, 8.7, 9.5]
_M = [4, 12]  # quarterly, monthly
_YEARS = list(range(3, 21))
_TIMING = ["ordinary", "due"]

_MONEY_VERIFIER = {
    "kind": "numeric_equality",
    "tolerance": 0.01,
    "rel_tol": 1e-4,
}


def _fv_ordinary(x: float, i: float, n_periods: int) -> float:
    return x * ((1 + i) ** n_periods - 1) / i


# ---------------------------------------------------------------------------
# 1. fv_annuity_amount — solve the accumulated future value F
# ---------------------------------------------------------------------------


def _gen_fv_amount(rng: random.Random) -> dict:
    x = rng.choice(_DEPOSITS)
    r = rng.choice(_RATES)
    m = rng.choice(_M)
    n = rng.choice(_YEARS)
    timing = rng.choice(_TIMING)
    i = r / (100 * m)
    periods = m * n
    f = _fv_ordinary(x, i, periods)
    if timing == "due":
        f *= 1 + i
    return {
        "deposit": x,
        "rate": r,
        "compounding": m,
        "years": n,
        "periods": periods,
        "timing": timing,
        "answer": f,
        "variant": f"fv_amt:{x}:{r}:{m}:{n}:{timing}",
    }


fv_annuity_amount = Problem(
    id="finance_fv_annuity_amount",
    type_id="financial_maths",
    name="Future value of a regular annuity  F = x[(1+i)^N − 1]/i  (ordinary/due)",
    artifact_type="practice",
    problem_spec=_gen_fv_amount,
    verifier_spec={**_MONEY_VERIFIER, "marks_possible": 3},
    corpus_anchor=CorpusAnchor(paper="2025 Nov P1", question="7.2", marks=3),
)


# ---------------------------------------------------------------------------
# 2. fv_annuity_deposit — solve the deposit x needed to reach a target F
# ---------------------------------------------------------------------------


def _gen_fv_deposit(rng: random.Random) -> dict:
    """Round savings goal F given; find the regular deposit x that reaches it.
    x = F / (accumulation factor), where the factor carries the (1+i) for a due
    annuity."""
    target = rng.choice(_TARGETS)
    r = rng.choice(_RATES)
    m = rng.choice(_M)
    n = rng.choice(_YEARS)
    timing = rng.choice(_TIMING)
    i = r / (100 * m)
    periods = m * n
    factor = ((1 + i) ** periods - 1) / i
    if timing == "due":
        factor *= 1 + i
    return {
        "target_amount": target,
        "rate": r,
        "compounding": m,
        "years": n,
        "periods": periods,
        "timing": timing,
        "answer": target / factor,
        "variant": f"fv_dep:{target}:{r}:{m}:{n}:{timing}",
    }


fv_annuity_deposit = Problem(
    id="finance_fv_annuity_deposit",
    type_id="financial_maths",
    name="Deposit needed to reach a savings goal  x = F·i/[(1+i)^N − 1]",
    artifact_type="practice",
    problem_spec=_gen_fv_deposit,
    verifier_spec={**_MONEY_VERIFIER, "marks_possible": 4},
    corpus_anchor=CorpusAnchor(paper="2023 Nov P1", question="6.2.2", marks=4),
)


# ---------------------------------------------------------------------------
# 3. fv_annuity_n — solve for the number of deposits (ordinary, ceil framing)
# ---------------------------------------------------------------------------


def _gen_fv_n(rng: random.Random) -> dict:
    """How many deposits of Rx accumulate to at least the target?
    N = ln(1 + F·i/x)/ln(1+i), rounded **up** (a final smaller top-up still
    counts). The target is placed strictly between the accumulated values after
    N−1 and N deposits, so the ceil is unambiguous and the count is exact."""
    x = rng.choice(_DEPOSITS)
    r = rng.choice(_RATES)
    m = rng.choice(_M)
    n_deposits = rng.randint(12, 60)
    i = r / (100 * m)
    f_prev = _fv_ordinary(x, i, n_deposits - 1)
    f_at = _fv_ordinary(x, i, n_deposits)
    target = (f_prev + f_at) / 2  # between the two → ceil of the solve is n_deposits
    return {
        "deposit": x,
        "rate": r,
        "compounding": m,
        "target_amount": target,
        "per_period_rate": i,
        "answer": n_deposits,  # number of deposits (a count)
        "variant": f"fv_n:{x}:{r}:{m}:{n_deposits}",
    }


fv_annuity_n = Problem(
    id="finance_fv_annuity_n",
    type_id="financial_maths",
    name="Number of deposits to reach a goal  N = ⌈ln(1 + F·i/x)/ln(1+i)⌉",
    artifact_type="practice",
    problem_spec=_gen_fv_n,
    verifier_spec={"kind": "numeric_equality", "marks_possible": 4, "tolerance": 0.01},
)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    problems = [fv_annuity_amount, fv_annuity_deposit, fv_annuity_n]
    engine = Engine(registry=InMemoryRegistry({p.id: p for p in problems}))

    def show(instance, label, answer):
        attempt = SolutionAttempt(steps=[SubmittedStep(answer)])
        r = instance.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  "
            f"is_correct={r.is_correct}"
        )

    print("=== fv_annuity_amount ===")
    inst = engine.instantiate(fv_annuity_amount.id, seed=3)
    p = inst.params
    print(
        f"  x={p['deposit']}, r={p['rate']}%, m={p['compounding']}, "
        f"n={p['years']} yr, {p['timing']}  →  F = {p['answer']:.2f}"
    )
    show(inst, "Rounded to 2dp", round(p["answer"], 2))

    print("\n=== fv_annuity_n (ceil framing) ===")
    inst = engine.instantiate(fv_annuity_n.id, seed=3)
    p = inst.params
    i = p["per_period_rate"]
    solved = math.log(1 + p["target_amount"] * i / p["deposit"]) / math.log(1 + i)
    print(
        f"  x={p['deposit']}, target={p['target_amount']:.2f}  →  "
        f"solve N = {solved:.3f}, ⌈N⌉ = {math.ceil(solved)}  (answer {p['answer']})"
    )
    show(inst, "Exact count   ", p["answer"])
