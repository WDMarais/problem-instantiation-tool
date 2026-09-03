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

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

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
# 4. effective_rate — annual effective rate from a nominal rate (NSC Q7.1)
# ---------------------------------------------------------------------------

_NOMINAL_RATES = [9, 10.5, 12, 13.5, 15, 16.5, 18]
_EFF_COMPOUNDING = [2, 4, 12]  # m > 1 so the effective rate genuinely exceeds nominal


def _gen_effective_rate(rng: random.Random) -> dict:
    """Nominal r% p.a. compounded m×/yr → annual effective rate as a *percentage*:
    ``i_eff = (1 + r/(100m))^m − 1``. m > 1, so i_eff > r (the whole point)."""
    r = rng.choice(_NOMINAL_RATES)
    m = rng.choice(_EFF_COMPOUNDING)
    i = r / (100 * m)
    return {
        "nominal_rate": r,
        "compounding": m,
        "per_period_rate": i,
        "answer": ((1 + i) ** m - 1) * 100,  # effective rate, as a percentage
    }


effective_rate = Problem(
    id="finance_effective_rate",
    type_id="financial_maths",
    name="Effective annual rate from a nominal rate  i_eff = (1 + i/m)^m − 1",
    artifact_type="practice",
    problem_spec=_gen_effective_rate,
    verifier_spec={
        "kind": "numeric_equality",
        "marks_possible": 2,
        "tolerance": 0.01,
        "rel_tol": 1e-4,
    },
    corpus_anchor=CorpusAnchor(
        paper="2025 May/June P1",
        question="7.1",
        marks=2,
        memo_value=16.08,  # (1 + 0,15/12)^12 − 1 ≈ 16,08%
        inputs={"nominal_rate": 15, "compounding": 12},
    ),
)


# ---------------------------------------------------------------------------
# 5. lump_plus_annuity — a lump sum grows while a later regular deposit stream
#    accumulates; total at the valuation date (NSC Q7.3)
# ---------------------------------------------------------------------------

_LUMP_PRINCIPALS = [8000, 10000, 12000, 15000, 20000]
_MONTHLY_DEPOSITS = [300, 400, 500, 750, 1000]
_Q7_RATES = [8, 9, 9.5, 10.5, 11]
_LUMP_YEARS = [3, 4, 5]  # total months the lump grows
_DEPOSIT_YEARS = [1, 2, 3]  # deposit phase (< lump phase → the stream is deferred)


def _gen_lump_plus_annuity(rng: random.Random) -> dict:
    """A once-off lump P grows for the full term at r% p.a. compounded monthly; a
    monthly deposit stream of x starts partway in and accumulates to the valuation
    date (its last deposit coincides with that date, so it is an ordinary annuity
    of N_ann terms). Total = P(1+i)^N_lump + x·[(1+i)^N_ann − 1]/i."""
    p = rng.choice(_LUMP_PRINCIPALS)
    x = rng.choice(_MONTHLY_DEPOSITS)
    r = rng.choice(_Q7_RATES)
    lump_years = rng.choice(_LUMP_YEARS)
    # deposit phase strictly shorter than the lump phase (a genuinely deferred
    # stream, as in the source: 4-year lump, 2-year deposit stream).
    deposit_years = rng.choice([d for d in _DEPOSIT_YEARS if d < lump_years])
    i = r / (100 * 12)
    n_lump = 12 * lump_years
    n_ann = 12 * deposit_years
    lump_fv = p * (1 + i) ** n_lump
    annuity_fv = x * ((1 + i) ** n_ann - 1) / i
    return {
        "principal": p,
        "deposit": x,
        "rate": r,
        "compounding": 12,
        "lump_years": lump_years,
        "deposit_years": deposit_years,
        "defer_years": lump_years - deposit_years,
        "per_period_rate": i,
        "n_lump": n_lump,
        "n_ann": n_ann,
        "lump_fv": lump_fv,
        "annuity_fv": annuity_fv,
        "answer": lump_fv + annuity_fv,
    }


lump_plus_annuity = Problem(
    id="finance_lump_plus_annuity",
    type_id="financial_maths",
    name="Lump sum + deferred monthly annuity, total at valuation date",
    artifact_type="practice",
    problem_spec=_gen_lump_plus_annuity,
    verifier_spec={
        "kind": "numeric_equality",
        "marks_possible": 6,
        "tolerance": 0.01,
        "rel_tol": 1e-4,
    },
    corpus_anchor=CorpusAnchor(
        paper="2025 May/June P1",
        question="7.3",
        marks=6,
        memo_value=30679.83,
        # R12 000 lump for 4 yr + R500/mo for the last 2 yr, 9,5% monthly
        inputs={"principal": 12000, "deposit": 500, "rate": 9.5},
    ),
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
