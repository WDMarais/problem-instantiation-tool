"""
Exponent algebra — ``exponent_simplify_constant`` (P1 Q1.3).

Simplify a ratio of same-base powers whose variable exponent cancels, leaving a single
rational constant:

    (aˣ⁺ᵐ − aˣ) / aˣ⁺ᵏ  =  aˣ(aᵐ − 1) / (aˣ·aᵏ)  =  (aᵐ − 1) / aᵏ.

The ``aˣ`` cancels, so the value is the same for every integer ``x`` — the point of the
NSC "prove this is constant" original, here posed as a gradable *simplify* (a proof's
target value is given, so nothing is left to grade; a simplify's answer is not). Because
``a ∤ aᵐ − 1``, the result is always a proper fraction in lowest terms, keeping the
factor-and-cancel flavour. Well-posed for every draw, so no F1 scope predicate.

Engine-graded canonical total = 2 of the 3 headline marks: the simplified value. The
initial factoring/cancelling set-up line is the hand-marked method mark. The value is
graded with ``symbolic_equality`` (accepts the fraction or its decimal).
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

_A_CHOICES = (2, 3, 4, 5)
# (m, k): numerator top offset m > 0, denominator offset k with k < m so the ratio is a
# genuine reduction rather than ≥ 1 trivially; each gives a proper fraction.
_MK_CHOICES = ((2, 1), (3, 1), (3, 2), (2, 2))


def _gen(rng: random.Random) -> dict:
    a = rng.choice(_A_CHOICES)
    m, k = rng.choice(_MK_CHOICES)
    return {
        "a": a,
        "m": m,
        "k": k,
        "answer": sympy.Rational(a**m - 1, a**k),
    }


exponent_simplify_constant = Problem(
    id="exponent_simplify_constant",
    type_id="exponent_simplify_constant",
    name="Simplify a same-base power ratio to a constant (exponent cancels)",
    artifact_type="practice",
    problem_spec=_gen,
    verifier_spec={"kind": "symbolic_equality", "marks_possible": 2},
    corpus_anchor=CorpusAnchor(
        paper="2025 May/June P1",
        question="1.3",
        marks=3,
    ),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(
        registry=InMemoryRegistry(
            {exponent_simplify_constant.id: exponent_simplify_constant}
        )
    )
    for seed in (1, 3, 7, 13):
        inst = engine.instantiate(exponent_simplify_constant.id, seed=seed)
        p = inst.params
        a, m, k = p["a"], p["m"], p["k"]
        print(
            f"seed {seed}: a={a} m={m} k={k} → "
            f"({a}^(x+{m}) − {a}^x)/{a}^(x+{k}) = {p['answer']}"
        )
        r = inst.verifier.rate(SolutionAttempt(steps=[SubmittedStep(p["answer"])]))
        print(f"  all-correct → {r.marks_awarded}/{r.marks_possible} ok={r.is_correct}")
