"""
Reference example: financial mathematics — simple interest, compound growth,
reverse compound.

Design decisions demonstrated:
- Three Problem objects, one per competency. All share the same parameter
  families (principal, rate, years) but test different formulas.
- numeric_equality with tolerance 0.01 (±1 cent) is the right verifier for
  currency answers. Students compute on a calculator and round to 2 decimal
  places; the canonical is the unrounded exact answer. Any answer within 0.01
  of the exact value passes, which covers all standard rounding conventions.
- numeric_equality canonical extraction: like symbolic_equality, it falls
  through to params["answer"] by default. No special-casing needed — just put
  the answer under the "answer" key as usual.
- Simple interest A = P(1 + rt/100) is always exact for integer P, r, t
  (no float error in the canonical). Compound growth A = P(1 + r/100)ⁿ is
  generally irrational; Python float arithmetic introduces errors on the order
  of 1e-12, well within the 0.01 tolerance.
- Reverse compound: student finds P = A / (1 + r/100)ⁿ given a target amount
  A. When A is a round number (R5000, R10 000), the answer P is an exact float.
  If the student rounds A to 2dp before working back, propagated error stays
  below 0.01 for r ≤ 12% and n ≤ 5.
- Compounding frequency (Gr10 → Gr11 bridge). ``compound_growth`` /
  ``compound_reverse`` now carry a ``compounding`` (m) param and use the general
  form A = P(1 + i/m)^(m·n), i = r/100, with m ∈ {1, 4, 12} (annual is the m=1
  case). ``simple_interest`` stays annual Gr10 filler. The corpus-scale,
  large-principal work (solve-rate, appreciation) lives in
  ``compound_periodic.py``; these two share only the frequency change.
- rel_tol 1e-4 on the compound specs: at larger principals a student who rounds
  i = r/(100m) over many periods drifts past the ±cent absolute band, so the
  compound specs accept an absolute OR a 0.01% relative miss. simple_interest
  is exact and keeps the absolute-only band.
"""

from __future__ import annotations

import random

from problem_instantiation_tool.schemas import Problem

_PRINCIPALS = [500, 1000, 1500, 2000, 2500, 3000, 5000]
_TARGETS = [5000, 8000, 10000, 15000, 20000]
_RATES = [5, 6, 7, 8, 9, 10, 11, 12]
_YEARS = [2, 3, 4, 5]
_COMPOUNDING = [1, 4, 12]  # annual (Gr10), quarterly, monthly


# ---------------------------------------------------------------------------
# 1. simple_interest — A = P(1 + rt/100)
# ---------------------------------------------------------------------------


def _gen_simple_interest(rng: random.Random) -> dict:
    P = rng.choice(_PRINCIPALS)
    r = rng.choice(_RATES)
    t = rng.choice(_YEARS)
    return {
        "principal": P,
        "rate": r,
        "years": t,
        "answer": P * (1 + r * t / 100),
    }


simple_interest = Problem(
    id="finance_simple_interest",
    type_id="financial_maths",
    name="Calculate accumulated amount with simple interest  A = P(1 + rt/100)",
    artifact_type="practice",
    problem_spec=_gen_simple_interest,
    verifier_spec={"kind": "numeric_equality", "marks_possible": 1, "tolerance": 0.01},
)


# ---------------------------------------------------------------------------
# 2. compound_growth — A = P(1 + r/100)ⁿ
# ---------------------------------------------------------------------------


def _gen_compound_growth(rng: random.Random) -> dict:
    P = rng.choice(_PRINCIPALS)
    r = rng.choice(_RATES)
    n = rng.choice(_YEARS)
    m = rng.choice(_COMPOUNDING)
    return {
        "principal": P,
        "rate": r,
        "years": n,
        "compounding": m,
        "answer": P * (1 + r / (100 * m)) ** (m * n),
    }


compound_growth = Problem(
    id="finance_compound_growth",
    type_id="financial_maths",
    name="Calculate accumulated amount with compound interest  A = P(1 + i/m)^(m·n)",
    artifact_type="practice",
    problem_spec=_gen_compound_growth,
    verifier_spec={
        "kind": "numeric_equality",
        "marks_possible": 2,
        "tolerance": 0.01,
        "rel_tol": 1e-4,
    },
)


# ---------------------------------------------------------------------------
# 3. compound_reverse — find P given A = P(1 + r/100)ⁿ
# ---------------------------------------------------------------------------


def _gen_compound_reverse(rng: random.Random) -> dict:
    A = rng.choice(_TARGETS)
    r = rng.choice(_RATES)
    n = rng.choice(_YEARS)
    m = rng.choice(_COMPOUNDING)
    return {
        "target_amount": A,
        "rate": r,
        "years": n,
        "compounding": m,
        "answer": A / (1 + r / (100 * m)) ** (m * n),
    }


compound_reverse = Problem(
    id="finance_compound_reverse",
    type_id="financial_maths",
    name="Find original principal given accumulated amount  P = A / (1 + i/m)^(m·n)",
    artifact_type="practice",
    problem_spec=_gen_compound_reverse,
    verifier_spec={
        "kind": "numeric_equality",
        "marks_possible": 2,
        "tolerance": 0.01,
        "rel_tol": 1e-4,
    },
)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    all_problems = {
        p.id: p for p in [simple_interest, compound_growth, compound_reverse]
    }
    engine = Engine(registry=InMemoryRegistry(all_problems))

    def show(instance, label, answer):
        attempt = SolutionAttempt(steps=[SubmittedStep(answer)])
        r = instance.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  "
            f"is_correct={r.is_correct}"
        )

    print("=== simple_interest ===")
    inst = engine.instantiate(simple_interest.id, seed=42)
    p = inst.params
    exact = p["answer"]
    print(
        f"  P={p['principal']}, r={p['rate']}%, t={p['years']} yr  →  A = {exact:.2f}"
    )
    show(inst, "Exact float                    ", exact)
    show(inst, "Rounded to 2dp                 ", round(exact, 2))
    show(inst, "Off by 0.01 (boundary)         ", round(exact, 2) + 0.01)
    show(inst, "Off by 0.02 (outside tolerance)", round(exact, 2) + 0.02)

    print()
    print("=== compound_growth ===")
    inst = engine.instantiate(compound_growth.id, seed=42)
    p = inst.params
    exact = p["answer"]
    print(
        f"  P={p['principal']}, r={p['rate']}%, m={p['compounding']}, "
        f"n={p['years']} yr  →  A = {exact:.4f}"
    )
    show(inst, "Exact float                    ", exact)
    show(inst, "Rounded to 2dp                 ", round(exact, 2))
    show(inst, "Off by 0.02 (outside tolerance)", round(exact, 2) + 0.02)

    print()
    print("=== compound_growth (forced monthly, m=12) ===")
    # A worked monthly case: same generator, compounded 12×/yr.
    P, r, m, n = 5000, 12, 12, 5
    exact_monthly = P * (1 + r / (100 * m)) ** (m * n)
    print(f"  P={P}, r={r}%, m={m}, n={n} yr  →  A = {exact_monthly:.4f}")

    print()
    print("=== compound_reverse ===")
    inst = engine.instantiate(compound_reverse.id, seed=42)
    p = inst.params
    exact = p["answer"]
    print(
        f"  A={p['target_amount']}, r={p['rate']}%, n={p['years']} yr"
        f"  →  P = {exact:.4f}"
    )
    show(inst, "Exact float                    ", exact)
    show(inst, "Rounded to 2dp                 ", round(exact, 2))
    show(inst, "Off by 0.02 (outside tolerance)", round(exact, 2) + 0.02)
