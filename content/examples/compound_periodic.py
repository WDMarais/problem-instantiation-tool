"""
Finance / Annuities — archetype 1: ``compound_periodic`` (Gr12).

The Gr10 annual ``compound_growth`` / ``compound_reverse`` lifted to non-annual
compounding (``m`` times a year), plus the two modes the Gr10 file never had:
**solve-for-rate** and the **appreciation / inflation** framing.

Formula (family finance-family-spec.md, archetype 1):
    A = P·(1 + i/m)^(m·n),   i = r/100

Four modes, one Problem each (each carries its own DBE-calibrated marks):

- ``compound_periodic_amount``    solve A given P, r, m, n            → 2 marks
- ``compound_periodic_principal`` solve P (reverse) given A, r, m, n  → 2 marks
- ``compound_periodic_rate``      solve r given A, P, m, n            → 3 marks
                                  r = 100·m·[(A/P)^(1/(m·n)) − 1]
- ``appreciation``                solve A, "will cost"/inflation frame → 2 marks
                                  (annual, m = 1, per NSC inflation convention)

Verifier — ``numeric_equality`` with **both** an absolute band (``tolerance``
0.01 = one cent) and a **relative** band (``rel_tol`` 1e-4 = 0.01%). At corpus
scale (P up to R1.6m) a student who rounds i to 5 dp over 100+ periods drifts
several rand off the exact canonical — a drift every NSC marker accepts, that
the absolute cent-band alone would wrongly reject. The rate mode's answer is a
small percentage, so there the absolute band does the work.

Canonicals are the *unrounded* exact values; the tolerance absorbs the
student's 2-dp rounding. Money → 2 dp; rate → 2 dp %.

Params are corpus-grounded: P ∈ {5 000 … 1 600 000}, m ∈ {4, 12} (annual is the
Gr10 case), r drawn from the DBE rate menu, n ∈ {2 … 16} years.
Anchors: 2024 Nov Q7.1 (quarterly, 16 yr), 2025 Nov Q7.1 (inflation).
"""

from __future__ import annotations

import random

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

# Corpus-grounded parameter menus.
_PRINCIPALS = [5000, 12000, 25000, 48000, 85000, 150000, 320000, 750000, 1600000]
_TARGETS = [50000, 100000, 250000, 500000, 1000000, 1600000]
_RATES = [5.8, 6, 6.8, 7.8, 8.7, 9.5, 11.2, 13.5, 15]
_M = [4, 12]  # quarterly, monthly; annual (m=1) is the Gr10 case
_YEARS = list(range(2, 17))

# Inflation / appreciation is conventionally an annual figure; its rate menu is
# the lower, "price-growth" end of the corpus.
_PRICES = [8500, 15000, 24999, 42000, 68000, 125000, 350000]
_INFLATION_RATES = [5.8, 6, 6.8, 7.8, 8.7]

_MONEY_VERIFIER = {
    "kind": "numeric_equality",
    "tolerance": 0.01,
    "rel_tol": 1e-4,
}


# ---------------------------------------------------------------------------
# 1. compound_periodic_amount — solve A = P(1 + i/m)^(m·n)
# ---------------------------------------------------------------------------


def _gen_compound_amount(rng: random.Random) -> dict:
    p = rng.choice(_PRINCIPALS)
    r = rng.choice(_RATES)
    m = rng.choice(_M)
    n = rng.choice(_YEARS)
    periods = m * n
    per_period = r / (100 * m)
    return {
        "principal": p,
        "rate": r,
        "compounding": m,
        "years": n,
        "periods": periods,
        "per_period_rate": per_period,
        "answer": p * (1 + per_period) ** periods,
        "variant": f"cp_amt:{p}:{r}:{m}:{n}",
    }


compound_amount = Problem(
    id="finance_compound_periodic_amount",
    type_id="financial_maths",
    name="Accumulated amount with non-annual compounding  A = P(1 + i/m)^(m·n)",
    artifact_type="practice",
    problem_spec=_gen_compound_amount,
    verifier_spec={**_MONEY_VERIFIER, "marks_possible": 3},
    corpus_anchor=CorpusAnchor(
        paper="2024 Nov P1",
        question="7.1",
        marks=3,  # official memo: i&n / substitution / answer
        memo_value=14706.56,
        inputs={"principal": 5000, "rate": 6.8, "compounding": 4, "years": 16},
    ),
)


# ---------------------------------------------------------------------------
# 2. compound_periodic_principal — reverse: find P given the future amount
# ---------------------------------------------------------------------------


def _gen_compound_principal(rng: random.Random) -> dict:
    amount = rng.choice(_TARGETS)
    r = rng.choice(_RATES)
    m = rng.choice(_M)
    n = rng.choice(_YEARS)
    periods = m * n
    per_period = r / (100 * m)
    return {
        "target_amount": amount,
        "rate": r,
        "compounding": m,
        "years": n,
        "periods": periods,
        "per_period_rate": per_period,
        "answer": amount / (1 + per_period) ** periods,
        "variant": f"cp_prin:{amount}:{r}:{m}:{n}",
    }


compound_principal = Problem(
    id="finance_compound_periodic_principal",
    type_id="financial_maths",
    name="Present value with non-annual compounding  P = A / (1 + i/m)^(m·n)",
    artifact_type="practice",
    problem_spec=_gen_compound_principal,
    verifier_spec={**_MONEY_VERIFIER, "marks_possible": 2},
)


# ---------------------------------------------------------------------------
# 3. compound_periodic_rate — solve for the nominal rate r
# ---------------------------------------------------------------------------


def _gen_compound_rate(rng: random.Random) -> dict:
    """Given P grows to A over n years compounded m times a year, find the
    nominal annual rate  r = 100·m·[(A/P)^(1/(m·n)) − 1].  The amount is drawn
    by growing a known rate, so the canonical is that exact rate; the extra
    root/log step is why this mode is worth an extra mark over solve-A."""
    p = rng.choice(_PRINCIPALS)
    r = rng.choice(_RATES)
    m = rng.choice(_M)
    n = rng.choice(_YEARS)
    periods = m * n
    per_period = r / (100 * m)
    return {
        "principal": p,
        "amount": p * (1 + per_period) ** periods,
        "compounding": m,
        "years": n,
        "periods": periods,
        "answer": r,  # nominal annual rate, as a percentage
        "variant": f"cp_rate:{p}:{r}:{m}:{n}",
    }


compound_rate = Problem(
    id="finance_compound_periodic_rate",
    type_id="financial_maths",
    name="Solve for the nominal rate  r = 100m[(A/P)^(1/mn) − 1]",
    artifact_type="practice",
    problem_spec=_gen_compound_rate,
    verifier_spec={**_MONEY_VERIFIER, "marks_possible": 3},
    corpus_anchor=CorpusAnchor(
        paper="2023 Nov P1",
        question="6.1",
        marks=3,
        memo_value=8.70,
        # R18 500 → R19 319,48 over 6 months compounded monthly
        inputs={
            "principal": 18500,
            "amount": 19319.48,
            "compounding": 12,
            "periods": 6,
        },
    ),
)


# ---------------------------------------------------------------------------
# 4. appreciation — "will cost" / inflation framing (annual compounding)
# ---------------------------------------------------------------------------


def _gen_appreciation(rng: random.Random) -> dict:
    """Same compound-growth arithmetic as solve-A, in the inflation/appreciation
    framing ("what will it cost in n years"). Inflation is quoted annually, so
    m = 1 here by convention."""
    price = rng.choice(_PRICES)
    r = rng.choice(_INFLATION_RATES)
    n = rng.choice(list(range(3, 11)))
    return {
        "price": price,
        "rate": r,
        "years": n,
        "answer": price * (1 + r / 100) ** n,
        "variant": f"appr:{price}:{r}:{n}",
    }


appreciation = Problem(
    id="finance_appreciation",
    type_id="financial_maths",
    name="Future cost under inflation / appreciation  A = P(1 + r/100)ⁿ",
    artifact_type="practice",
    problem_spec=_gen_appreciation,
    verifier_spec={**_MONEY_VERIFIER, "marks_possible": 2},
    corpus_anchor=CorpusAnchor(
        paper="2025 Nov P1",
        question="7.1",
        marks=2,
        memo_value=58230.94,
        inputs={"price": 40000, "rate": 7.8, "years": 5},
    ),
)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    problems = [compound_amount, compound_principal, compound_rate, appreciation]
    engine = Engine(registry=InMemoryRegistry({p.id: p for p in problems}))

    def show(instance, label, answer):
        attempt = SolutionAttempt(steps=[SubmittedStep(answer)])
        r = instance.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  "
            f"is_correct={r.is_correct}"
        )

    print("=== compound_periodic_amount (quarterly, corpus scale) ===")
    inst = engine.instantiate(compound_amount.id, seed=7)
    p = inst.params
    exact = p["answer"]
    print(
        f"  P={p['principal']}, r={p['rate']}%, m={p['compounding']}, "
        f"n={p['years']} yr  →  A = {exact:.2f}"
    )
    show(inst, "Rounded to 2dp                 ", round(exact, 2))
    show(inst, "Off by several rand (rounding) ", round(exact, 2) + 0.9)

    print("\n=== compound_periodic_rate ===")
    inst = engine.instantiate(compound_rate.id, seed=7)
    p = inst.params
    print(
        f"  P={p['principal']}, A={p['amount']:.2f}, m={p['compounding']}, "
        f"n={p['years']} yr  →  r = {p['answer']}%"
    )
    show(inst, "Exact rate                     ", p["answer"])
    show(inst, "Rounded rate 2dp               ", round(p["answer"], 2))
