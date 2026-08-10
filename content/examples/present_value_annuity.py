"""
Finance / Annuities — archetype 5: ``present_value_annuity`` (Gr12, flagship B).

Loans and withdrawal funds: a present lump sum ``P`` that a stream of equal
payments ``x`` either repays (loan) or draws down (withdrawal fund). Highest
recurrence in the corpus — all four papers carry it — and **solve-N is the
load-bearing hard part** (the floor-vs-ceil distinction is the assessed idea).

Formula (finance-family-spec.md, archetype 5):
    ordinary:  P = x·[1 − (1 + i)^(−N)] / i,   i = r/(100m),  N = m·n
    due:       P_due = P·(1 + i)              (payments at the start of each period)
    solve-N:   N = −ln(1 − P·i/x) / ln(1 + i),  then floor OR ceil (see below)

Four modes, one Problem each:

- ``pv_annuity_amount``  solve P: the loan/fund a payment x supports    → 3 marks
- ``pv_annuity_payment`` solve x: the instalment/withdrawal for a loan P → 4 marks
- ``pv_annuity_n``       solve N: how many payments clear it            → 5 marks
      **loan repayment → ceil** (a final smaller payment still clears the debt,
      so it counts as a payment); **withdrawal fund → floor** (a final partial
      withdrawal is not a full one — the question asks for whole withdrawals).
- ``pv_annuity_total_interest``  total interest x·N − P over a loan      → 2 marks

Guard (the assessed concept): ``x > P·i`` — the payment must exceed the interest
accruing each period, else ``1 − P·i/x ≤ 0``, the log is undefined and the debt
never clears. Every generator here holds x strictly above P·i by construction
(P is derived from x, so P·i = x·[1 − (1+i)^(−N)] < x automatically).

Money verifier: ``numeric_equality`` with the absolute ±cent band and rel_tol
1e-4 — this is the archetype that needs the relative band most (P runs to
R1.6m). The solve-N answer is a count, graded exactly.

Params corpus-grounded (finance-family-spec.md §5): P ∈ {100k … 1.6m},
x ∈ {2 300.98, 10 000, 11 250, 20 000}, r ∈ {6, 6.8, 11.2, 13.5}%, m ∈ {4, 12}.
Anchors: 2025 M/J Q7.2 (solve #withdrawals), 2024 Nov Q7.3.1 (loan total interest).
"""

from __future__ import annotations

import math
import random

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

_PRINCIPALS = [100000, 250000, 500000, 750000, 1000000, 1250000, 1600000]
_INSTALMENTS = [2300.98, 10000, 11250, 20000]
_RATES = [6, 6.8, 11.2, 13.5]
_M = [4, 12]  # quarterly, monthly
_YEARS = list(range(5, 26))  # loans run long: 5–25 years
_TIMING = ["ordinary", "due"]

_MONEY_VERIFIER = {
    "kind": "numeric_equality",
    "tolerance": 0.01,
    "rel_tol": 1e-4,
}


def _pv_ordinary(x: float, i: float, n_periods: int) -> float:
    """Present value of an ordinary annuity of N payments of x at rate i."""
    return x * (1 - (1 + i) ** (-n_periods)) / i


# ---------------------------------------------------------------------------
# 1. pv_annuity_amount — solve the present value P a payment x supports
# ---------------------------------------------------------------------------


def _gen_pv_amount(rng: random.Random) -> dict:
    x = rng.choice(_INSTALMENTS)
    r = rng.choice(_RATES)
    m = rng.choice(_M)
    n = rng.choice(_YEARS)
    timing = rng.choice(_TIMING)
    i = r / (100 * m)
    periods = m * n
    p = _pv_ordinary(x, i, periods)
    if timing == "due":
        p *= 1 + i
    return {
        "payment": x,
        "rate": r,
        "compounding": m,
        "years": n,
        "periods": periods,
        "timing": timing,
        "answer": p,
        "variant": f"pv_amt:{x}:{r}:{m}:{n}:{timing}",
    }


pv_annuity_amount = Problem(
    id="finance_pv_annuity_amount",
    type_id="financial_maths",
    name="Present value of a regular annuity  P = x[1 − (1+i)^−N]/i  (ordinary/due)",
    artifact_type="practice",
    problem_spec=_gen_pv_amount,
    verifier_spec={**_MONEY_VERIFIER, "marks_possible": 3},
)


# ---------------------------------------------------------------------------
# 2. pv_annuity_payment — solve the instalment x that repays a loan P
# ---------------------------------------------------------------------------


def _gen_pv_payment(rng: random.Random) -> dict:
    """Loan amount P given; find the regular payment x that repays it over N
    periods. x = P·i / [1 − (1+i)^(−N)]; a due annuity divides that by (1+i)."""
    p = rng.choice(_PRINCIPALS)
    r = rng.choice(_RATES)
    m = rng.choice(_M)
    n = rng.choice(_YEARS)
    timing = rng.choice(_TIMING)
    i = r / (100 * m)
    periods = m * n
    factor = (1 - (1 + i) ** (-periods)) / i
    if timing == "due":
        factor *= 1 + i
    return {
        "loan_amount": p,
        "rate": r,
        "compounding": m,
        "years": n,
        "periods": periods,
        "timing": timing,
        "answer": p / factor,
        "variant": f"pv_pmt:{p}:{r}:{m}:{n}:{timing}",
    }


pv_annuity_payment = Problem(
    id="finance_pv_annuity_payment",
    type_id="financial_maths",
    name="Instalment that repays a loan  x = P·i/[1 − (1+i)^−N]",
    artifact_type="practice",
    problem_spec=_gen_pv_payment,
    verifier_spec={**_MONEY_VERIFIER, "marks_possible": 4},
)


# ---------------------------------------------------------------------------
# 3. pv_annuity_n — solve for the number of payments (floor vs ceil)
# ---------------------------------------------------------------------------


def _gen_pv_n(rng: random.Random) -> dict:
    """How many payments of Rx clear a present value P?
    N = −ln(1 − P·i/x)/ln(1+i), then **ceil** for a loan (a final smaller
    payment still clears the debt) or **floor** for a withdrawal fund (a final
    partial withdrawal is not a whole one).

    P is derived from x and a chosen non-integer exact solve N* placed strictly
    inside the gap on the correct side of the target count, so floor/ceil is
    unambiguous and the count is exact — and P·i < x holds by construction."""
    x = rng.choice(_INSTALMENTS)
    r = rng.choice(_RATES)
    m = rng.choice(_M)
    n_payments = rng.randint(24, 180)
    mode = rng.choice(["loan", "withdrawal"])
    i = r / (100 * m)
    offset = rng.uniform(0.15, 0.85)  # keeps N* strictly interior to its gap
    # loan → answer is ceil → put N* just below the count;
    # withdrawal → answer is floor → put N* just above the count.
    n_exact = n_payments - offset if mode == "loan" else n_payments + offset
    p = _pv_ordinary(x, i, n_exact)
    return {
        "payment": x,
        "rate": r,
        "compounding": m,
        "present_value": p,
        "per_period_rate": i,
        "mode": mode,  # loan (ceil) | withdrawal (floor)
        "answer": n_payments,  # number of payments (a count)
        "variant": f"pv_n:{x}:{r}:{m}:{n_payments}:{mode}",
    }


pv_annuity_n = Problem(
    id="finance_pv_annuity_n",
    type_id="financial_maths",
    name="Number of payments to clear a loan/fund  N = −ln(1 − P·i/x)/ln(1+i)",
    artifact_type="practice",
    problem_spec=_gen_pv_n,
    verifier_spec={"kind": "numeric_equality", "marks_possible": 5, "tolerance": 0.01},
    corpus_anchor=CorpusAnchor(
        paper="2025 M/J P1",
        question="7.2",
        marks=5,
        memo_value=73,  # n = 73,788… → 73 whole withdrawals (floor)
        # R500 000 fund, R11 250 quarterly withdrawals at 6%
        inputs={"present_value": 500000, "payment": 11250, "rate": 6, "compounding": 4},
    ),
)


# ---------------------------------------------------------------------------
# 4. pv_annuity_total_interest — total interest paid over a loan (rider)
# ---------------------------------------------------------------------------


def _gen_pv_total_interest(rng: random.Random) -> dict:
    """A fully amortising loan P repaid by N equal instalments x; the total
    interest paid is total = x·N − P (payments minus principal). Ordinary."""
    p = rng.choice(_PRINCIPALS)
    r = rng.choice(_RATES)
    m = rng.choice(_M)
    n = rng.choice(_YEARS)
    i = r / (100 * m)
    periods = m * n
    x = p / ((1 - (1 + i) ** (-periods)) / i)
    return {
        "loan_amount": p,
        "rate": r,
        "compounding": m,
        "years": n,
        "periods": periods,
        "instalment": x,
        "answer": x * periods - p,
        "variant": f"pv_int:{p}:{r}:{m}:{n}",
    }


pv_annuity_total_interest = Problem(
    id="finance_pv_annuity_total_interest",
    type_id="financial_maths",
    name="Total interest paid over a loan  total = x·N − P",
    artifact_type="practice",
    problem_spec=_gen_pv_total_interest,
    verifier_spec={**_MONEY_VERIFIER, "marks_possible": 2},
    corpus_anchor=CorpusAnchor(
        paper="2024 Nov P1",
        question="7.3.1",
        marks=2,
        memo_value=38058.80,  # 2 300,98 × 60 − 100 000
        inputs={"loan_amount": 100000, "instalment": 2300.98, "periods": 60},
    ),
)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    problems = [
        pv_annuity_amount,
        pv_annuity_payment,
        pv_annuity_n,
        pv_annuity_total_interest,
    ]
    engine = Engine(registry=InMemoryRegistry({p.id: p for p in problems}))

    def show(instance, label, answer):
        attempt = SolutionAttempt(steps=[SubmittedStep(answer)])
        r = instance.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  "
            f"is_correct={r.is_correct}"
        )

    print("=== pv_annuity_payment ===")
    inst = engine.instantiate(pv_annuity_payment.id, seed=3)
    p = inst.params
    print(
        f"  P={p['loan_amount']}, r={p['rate']}%, m={p['compounding']}, "
        f"n={p['years']} yr, {p['timing']}  →  x = {p['answer']:.2f}"
    )
    show(inst, "Rounded to 2dp", round(p["answer"], 2))

    print("\n=== pv_annuity_n (floor vs ceil) ===")
    inst = engine.instantiate(pv_annuity_n.id, seed=3)
    p = inst.params
    i = p["per_period_rate"]
    solved = -math.log(1 - p["present_value"] * i / p["payment"]) / math.log(1 + i)
    rounded = math.ceil(solved) if p["mode"] == "loan" else math.floor(solved)
    print(
        f"  x={p['payment']}, P={p['present_value']:.2f}, mode={p['mode']}  →  "
        f"solve N = {solved:.3f}, rounded = {rounded}  (answer {p['answer']})"
    )
    show(inst, "Exact count   ", p["answer"])
