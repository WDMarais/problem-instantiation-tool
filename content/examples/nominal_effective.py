"""
Finance / Annuities — archetype 2: ``nominal_effective_rate`` (Gr12).

The smallest build in the family: pure rate conversion, no principal. Warms up
the percentage conventions the annuity archetypes then lean on.

Formula (finance-family-spec.md, archetype 2):
    1 + i_eff = (1 + i_nom/m)^m     ⇒     i_eff = (1 + i_nom/m)^m − 1

Two modes, one Problem each:

- ``nominal_to_effective``  given a nominal rate compounded m×/yr, find the
                            effective annual rate (dominant direction).
- ``effective_to_nominal``  the inverse, i_nom = m·[(1 + i_eff)^(1/m) − 1].

Both answers are small percentages (single-digit-ish), so the verifier's
**absolute** ±0.01 band — not rel_tol — is what absorbs the student's 2-dp
rounding. Answer to 2 dp %. Params: i_nom ∈ {6 … 15}%, m ∈ {4, 12}.
Anchor: 2023 Nov Q6.1.2 (8.7% monthly → 9.06%), 2025 M/J Q7.1.
"""

from __future__ import annotations

import random

from problem_instantiation_tool.schemas import Problem

_NOMINAL_RATES = [6, 6.8, 7.8, 8.7, 9.5, 11.2, 12, 13.5, 15]
_M = [4, 12]  # quarterly, monthly — m = 1 makes the two rates equal (degenerate)

# Answer is a small percentage: the absolute cent-band does the work, and a
# relative band would be far tighter than any marker applies. rel_tol stays 0.
_RATE_VERIFIER = {
    "kind": "numeric_equality",
    "marks_possible": 2,
    "tolerance": 0.01,
}


# ---------------------------------------------------------------------------
# 1. nominal_to_effective — the dominant direction
# ---------------------------------------------------------------------------


def _gen_nominal_to_effective(rng: random.Random) -> dict:
    i_nom = rng.choice(_NOMINAL_RATES)
    m = rng.choice(_M)
    i_eff = ((1 + (i_nom / 100) / m) ** m - 1) * 100
    return {
        "nominal_rate": i_nom,
        "compounding": m,
        "answer": i_eff,  # effective annual rate, as a percentage
        "variant": f"nom2eff:{i_nom}:{m}",
    }


nominal_to_effective = Problem(
    id="finance_nominal_to_effective",
    type_id="financial_maths",
    name="Convert a nominal rate to the effective annual rate  i_eff=(1+i/m)^m−1",
    artifact_type="practice",
    problem_spec=_gen_nominal_to_effective,
    verifier_spec=dict(_RATE_VERIFIER),
)


# ---------------------------------------------------------------------------
# 2. effective_to_nominal — the inverse
# ---------------------------------------------------------------------------


def _gen_effective_to_nominal(rng: random.Random) -> dict:
    """Present the effective rate, ask for the nominal one. The effective rate
    is produced by growing a known nominal rate, so the canonical is that exact
    nominal rate:  i_nom = m·[(1 + i_eff)^(1/m) − 1]."""
    i_nom = rng.choice(_NOMINAL_RATES)
    m = rng.choice(_M)
    i_eff = ((1 + (i_nom / 100) / m) ** m - 1) * 100
    return {
        "effective_rate": i_eff,
        "compounding": m,
        "answer": i_nom,  # nominal annual rate, as a percentage
        "variant": f"eff2nom:{i_nom}:{m}",
    }


effective_to_nominal = Problem(
    id="finance_effective_to_nominal",
    type_id="financial_maths",
    name="Convert an effective rate to the nominal rate  i=m[(1+i_eff)^(1/m)−1]",
    artifact_type="practice",
    problem_spec=_gen_effective_to_nominal,
    verifier_spec=dict(_RATE_VERIFIER),
)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    problems = [nominal_to_effective, effective_to_nominal]
    engine = Engine(registry=InMemoryRegistry({p.id: p for p in problems}))

    def show(instance, label, answer):
        attempt = SolutionAttempt(steps=[SubmittedStep(answer)])
        r = instance.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  "
            f"is_correct={r.is_correct}"
        )

    print("=== nominal_to_effective ===")
    inst = engine.instantiate(nominal_to_effective.id, seed=5)
    p = inst.params
    print(
        f"  i_nom={p['nominal_rate']}% compounded m={p['compounding']}"
        f"  →  i_eff = {p['answer']:.2f}%"
    )
    show(inst, "Rounded to 2dp %", round(p["answer"], 2))

    print("\n=== effective_to_nominal ===")
    inst = engine.instantiate(effective_to_nominal.id, seed=5)
    p = inst.params
    print(
        f"  i_eff={p['effective_rate']:.4f}% compounded m={p['compounding']}"
        f"  →  i_nom = {p['answer']}%"
    )
    show(inst, "Exact nominal   ", p["answer"])

    print("\n=== corpus anchor 2023 Q6.1.2 (8.7% monthly) ===")
    i_eff = ((1 + (8.7 / 100) / 12) ** 12 - 1) * 100
    print(f"  8.7% p.a. compounded monthly  →  i_eff = {i_eff:.2f}%  (memo: 9.06%)")
