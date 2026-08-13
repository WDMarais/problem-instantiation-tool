"""
Calculus, archetype 2 — ``derivative_rules``.

Differentiate a function whose terms must be **rewritten as powers before the
power rule applies** — a surd  a·√x → a·x^½, and a quotient  a/xⁿ → a·x⁻ⁿ. That
rewrite is the assessed skill: a student who leaves ``√x`` or ``a/x²`` in place
cannot apply  d/dx xⁿ = n·xⁿ⁻¹  at all.

The rewrite itself is *not* a separately checkable step — ``√x`` and ``x^½`` are
the **same** expression to sympy, so ``symbolic_equality`` cannot tell a rewritten
line from the original. What we can do, and do here, is (a) generate functions
that genuinely require the rewrite (every instance carries a surd term and a
reciprocal term), and (b) check the derivative f′(x) with ``symbolic_equality``,
which accepts any algebraically-equal form the student writes (``1/√x`` or
``x^{-1/2}``, ``-6x^{-3}`` or ``-6/x³``, …). A constant term is always present in
f and vanishes from f′, exercising "the constant differentiates away".

The rewrite-line *working* for the memo (showing each term as a power before
differentiating) is a rendering concern, deferred with the answer-key prose.
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

_x = sympy.Symbol("x")


def _gen(rng: random.Random) -> dict:
    # a plain power term (already a power — no rewrite needed)
    a_plain = rng.choice([-5, -4, -3, -2, 2, 3, 4, 5])
    n_plain = rng.choice([2, 3, 4])
    # a surd term  a·√x  → rewrite a·x^{1/2}
    a_surd = rng.choice([-6, -4, -3, -2, 2, 3, 4, 6])
    # a reciprocal term  a/xⁿ  → rewrite a·x^{-n}
    a_recip = rng.choice([-6, -4, -3, -2, 2, 3, 4, 6])
    n_recip = rng.choice([1, 2, 3])
    const = rng.choice([-9, -7, -5, -3, 3, 5, 7, 9])  # nonzero; drops in f′

    f = a_plain * _x**n_plain + a_surd * sympy.sqrt(_x) + a_recip / _x**n_recip + const
    derivative = sympy.diff(f, _x)

    return {
        "a_plain": a_plain,
        "n_plain": n_plain,
        "a_surd": a_surd,
        "a_recip": a_recip,
        "n_recip": n_recip,
        "const": const,
        "function_latex": rf"f(x) = {sympy.latex(f)}",
        "derivative": derivative,
        "derivative_latex": sympy.latex(derivative),
    }


derivative_rules = Problem(
    id="derivative_rules",
    type_id="derivative_rules",
    name="Differentiate using the rules (rewrite surds/quotients as powers first)",
    artifact_type="practice",
    problem_spec=_gen,
    verifier_spec={
        "kind": "symbolic_equality",
        "marks_possible": 3,  # power term + surd term + reciprocal term
        "param_key": "derivative",
    },
    corpus_anchor=CorpusAnchor(
        paper="2025 May/June P1",
        question="8.2.1",  # part of the 8.2 derivative-rules pair
        # sub-part mark split not in our provenance notes → left unset
    ),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(registry=InMemoryRegistry({derivative_rules.id: derivative_rules}))

    def show(label, inst, *answers):
        attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
        r = inst.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  "
            f"is_correct={r.is_correct}"
        )

    for seed in range(3):
        inst = engine.instantiate(derivative_rules.id, seed=seed)
        p = inst.params
        print(f"=== seed {seed} ===")
        print(f"  {p['function_latex']}")
        print(f"  f'(x) = {p['derivative']}")
        show("correct           ", inst, p["derivative"])
        show("forgot const drops", inst, p["derivative"] + p["const"])
