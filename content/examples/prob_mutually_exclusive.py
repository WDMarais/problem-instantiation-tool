"""
Probability, mutually exclusive events — ``prob_mutually_exclusive`` (P1 Q10.1).

For mutually exclusive A and B, P(A or B) = P(A) + P(B), so a missing operand is a
one-line subtraction: given P(A) and P(A∪B), find P(B) = P(A∪B) − P(A).

All probabilities are two-decimal (hundredths) with P(A) + P(B) ≤ 1, so a calculator
lands on the exact value and the answer stays a clean two-decimal probability. Values
are SymPy ``Rational`` so grading is exact; ``symbolic_equality`` accepts either the
fraction or the decimal. The single answer is graded whole (2 marks) — the subtraction
*is* the method, so there is no hand-marked line the engine cannot see.
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import CorpusAnchor, Problem


def _gen(rng: random.Random) -> dict:
    # Two-decimal probabilities with headroom so P(A∪B) = P(A) + P(B) ≤ 1.
    p_a = sympy.Rational(rng.randint(20, 55), 100)
    p_b = sympy.Rational(rng.randint(15, 40), 100)
    p_aub = p_a + p_b  # mutually exclusive: the union is the plain sum
    return {
        "p_a": p_a,
        "p_aub": p_aub,
        "answer": p_b,  # P(B) = P(A∪B) − P(A)
    }


prob_mutually_exclusive = Problem(
    id="prob_mutually_exclusive",
    type_id="prob_mutually_exclusive",
    name="Find P(B) for mutually exclusive events (addition rule)",
    artifact_type="practice",
    problem_spec=_gen,
    verifier_spec={"kind": "symbolic_equality", "marks_possible": 2},
    corpus_anchor=CorpusAnchor(
        paper="2025 May/June P1",
        question="10.1",
        marks=2,
    ),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(
        registry=InMemoryRegistry({prob_mutually_exclusive.id: prob_mutually_exclusive})
    )
    for seed in (1, 7, 13):
        inst = engine.instantiate(prob_mutually_exclusive.id, seed=seed)
        p = inst.params
        print(
            f"seed {seed}: P(A)={p['p_a']} P(A∪B)={p['p_aub']} → P(B)={p['answer']} "
            f"(~{float(p['answer']):.2f})"
        )
        attempt = SolutionAttempt(steps=[SubmittedStep(p["answer"])])
        r = inst.verifier.rate(attempt)
        print(f"  all-correct → {r.marks_awarded}/{r.marks_possible} ok={r.is_correct}")
