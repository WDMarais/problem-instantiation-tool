"""
Q1 Algebra, common-base exponential equation — ``exponential_common_base``.

Solve  a^(x+k) + a^x = N  by **factoring the shared power**:

    a^(x+k) + a^x = a^x(a^k + 1) = N   ⇒   a^x = N / (a^k + 1) = a^n   ⇒   x = n.

This is a *different, simpler* skill than ``exponential_equation`` (which
substitutes u = a^x to get a **quadratic in u** and then rejects u ≤ 0). Here
there is no quadratic and nothing to reject — the whole assessed idea is
recognising the common base, factoring it out, and equating exponents. It is the
2025 M/J P1 Q1.1.3 archetype (``2^(x+4) + 2^x = 8704`` → x = 9), a 3-mark item,
whereas the substitution problem is the 4–5 mark 1.1.4-type slot.

The answer decomposes into the two values a marker can read off the working:

  1. the **simplified power** — the value of a^x after dividing by (a^k + 1),
     i.e. a^n (``symbolic_equality``, 1 mark), and
  2. the **exponent** — x = n once a^x = a^n (``symbolic_equality``, 1 mark).

The paper's 3rd mark is the factoring line ``a^x(a^k + 1)`` — a method step with
no verifier behind it, marked by hand (see the ``auto_marks`` split in
``worksheets/paper.py``).

**Construction (backward, so every number is clean).** Pick a small base
a ∈ {2, 3, 5}, an answer exponent n (so a^n is an exam-sized power) and a gap
k ≥ 1. Then a^k + 1 is a small integer coefficient and N = (a^k + 1)·a^n is an
integer by construction, so the division a^x = N/(a^k + 1) is always exact.
"""

from __future__ import annotations

import random

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

_BASES = (2, 3, 5)

# Per base, the exponents that keep both a^n and N exam-sized (N stays < ~90000,
# matching the scale of the real 2025 M/J item, 8704).
_N_RANGE = {2: range(3, 10), 3: range(2, 6), 5: range(2, 4)}
_K_RANGE = {2: (1, 2, 3, 4), 3: (1, 2), 5: (1, 2)}


def _gen(rng: random.Random) -> dict:
    a = rng.choice(_BASES)
    k = rng.choice(_K_RANGE[a])
    n = rng.choice(list(_N_RANGE[a]))

    power = a**n  # the value a^x resolves to
    coeff = a**k + 1  # the factored-out constant (a^k + 1)
    total = coeff * power  # N, exact by construction

    equation_latex = rf"{a}^{{x + {k}}} + {a}^{{x}} = {total}"

    return {
        "base": a,
        "k": k,
        "n": n,
        "coeff": coeff,
        "power": power,  # a^x = a^n  (step 1 answer)
        "x_answer": n,  # x = n      (step 2 answer)
        "total": total,
        "equation_latex": equation_latex,
    }


exponential_common_base = Problem(
    id="exponential_common_base",
    type_id="exponential_common_base",
    name="Solve a^(x+k)+a^x=N by factoring the common power and equating exponents",
    artifact_type="practice",
    problem_spec=_gen,
    verifier_spec=[
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "power"},
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "x_answer"},
    ],
    corpus_anchor=CorpusAnchor(
        paper="2025 May/June P1",
        question="1.1.3",
        # marks left unset: the paper's 3rd mark is the factoring line
        # a^x(a^k+1), a method step with no verifier behind it. We grade the two
        # answer-values: the simplified power a^x = a^n (1) + x = n (1).
    ),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(
        registry=InMemoryRegistry({exponential_common_base.id: exponential_common_base})
    )

    for seed in (0, 1, 2, 7):
        inst = engine.instantiate(exponential_common_base.id, seed=seed)
        p = inst.params
        print(f"=== seed {seed} ===")
        print(f"  Solve : {p['equation_latex']}")
        print(f"  a^x = {p['power']}   x = {p['x_answer']}")
        attempt = SolutionAttempt(
            steps=[SubmittedStep(p["power"]), SubmittedStep(p["x_answer"])]
        )
        r = inst.verifier.rate(attempt)
        print(f"  correct: {r.marks_awarded}/{r.marks_possible}  ok={r.is_correct}")
