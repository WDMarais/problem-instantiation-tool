"""
Probability, independent events — ``independent_events`` (P1 Q10.1).

The multiplication rule for independent events, P(A∩B) = P(A)·P(B), in the three
surfaces the exam uses:

- ``independent_intersection`` — given independence, find P(A∩B) = P(A)·P(B).
- ``independent_union``        — given independence, find
                                 P(A∪B) = P(A) + P(B) − P(A)·P(B).
- ``independent_decide``       — given P(A), P(B), P(A∩B), compute the product
                                 P(A)·P(B) and decide whether A and B are
                                 independent. Graded as two steps: the product
                                 (numeric) and the verdict (a closed token).

All probabilities are drawn from a pool with terminating decimals (denominators
in {2, 4, 5, 10}); products and sums of these terminate too, so a calculator
lands on the exact value and ``symbolic_equality`` accepts either the fraction or
the decimal. Values are SymPy ``Rational`` so the grading is exact.

The ``decide`` variant is genuinely balanced — independence holds on about half of
the draws and fails on the rest, so the verdict token is load-bearing rather than
always "independent".
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

# Probabilities with terminating decimals; every pairwise product and the
# inclusion-exclusion union also terminate, so calculator answers are exact.
_NICE_P: tuple[sympy.Rational, ...] = (
    sympy.Rational(1, 4),
    sympy.Rational(1, 2),
    sympy.Rational(3, 4),
    sympy.Rational(1, 5),
    sympy.Rational(2, 5),
    sympy.Rational(3, 5),
    sympy.Rational(4, 5),
    sympy.Rational(1, 10),
    sympy.Rational(3, 10),
    sympy.Rational(7, 10),
    sympy.Rational(9, 10),
)


def _gen_intersection(rng: random.Random) -> dict:
    p_a = rng.choice(_NICE_P)
    p_b = rng.choice(_NICE_P)
    return {
        "p_a": p_a,
        "p_b": p_b,
        "answer": p_a * p_b,
    }


def _gen_union(rng: random.Random) -> dict:
    p_a = rng.choice(_NICE_P)
    p_b = rng.choice(_NICE_P)
    return {
        "p_a": p_a,
        "p_b": p_b,
        # P(A∪B) = P(A) + P(B) − P(A)·P(B); always ≤ 1 for probabilities.
        "answer": p_a + p_b - p_a * p_b,
    }


def _gen_decide(rng: random.Random) -> dict:
    """Half the time the given P(A∩B) equals the product (independent); the rest
    of the time it is a different admissible value (dependent)."""
    while True:
        p_a = rng.choice(_NICE_P)
        p_b = rng.choice(_NICE_P)
        product = p_a * p_b
        if rng.random() < 0.5:
            p_ab = product  # genuinely independent
        else:
            # a different admissible intersection: 0 < P(A∩B) ≤ min(P(A), P(B)),
            # P(A∪B) ≤ 1, and not equal to the product (so the verdict flips).
            p_min = min(p_a, p_b)
            choices = [
                sympy.Rational(k, 20)
                for k in range(1, int(p_min * 20) + 1)
                if sympy.Rational(k, 20) != product
                and p_a + p_b - sympy.Rational(k, 20) <= 1
            ]
            if not choices:
                continue
            p_ab = rng.choice(choices)
        verdict = "independent" if p_ab == product else "not_independent"
        return {
            "p_a": p_a,
            "p_b": p_b,
            "p_ab": p_ab,
            "product": product,  # P(A)·P(B), the computed comparison value
            "verdict": verdict,
        }


independent_intersection = Problem(
    id="independent_intersection",
    type_id="independent_events",
    name="Find P(A∩B) for independent events (product rule)",
    artifact_type="practice",
    problem_spec=_gen_intersection,
    verifier_spec={"kind": "symbolic_equality", "marks_possible": 1},
    corpus_anchor=CorpusAnchor(paper="2023 Nov P1", question="10.1.1"),
)

independent_union = Problem(
    id="independent_union",
    type_id="independent_events",
    name="Find P(A∪B) for independent events (inclusion–exclusion)",
    artifact_type="practice",
    problem_spec=_gen_union,
    verifier_spec={"kind": "symbolic_equality", "marks_possible": 1},
    corpus_anchor=CorpusAnchor(paper="2023 Nov P1", question="10.1.2"),
)

independent_decide = Problem(
    id="independent_decide",
    type_id="independent_events",
    name="Decide whether two events are independent (compare product to P(A∩B))",
    artifact_type="practice",
    problem_spec=_gen_decide,
    verifier_spec=[
        {
            "kind": "numeric_equality",
            "marks_possible": 1,
            "param_key": "product",
        },
        {
            "kind": "exact_equality",
            "marks_possible": 1,
            "param_key": "verdict",
        },
    ],
    corpus_anchor=CorpusAnchor(paper="2023 Nov P1", question="10.1.1"),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    problems = {
        p.id: p
        for p in [independent_intersection, independent_union, independent_decide]
    }
    engine = Engine(registry=InMemoryRegistry(problems))

    def show(label, inst, *answers):
        attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
        r = inst.verifier.rate(attempt)
        print(f"  {label}: {r.marks_awarded}/{r.marks_possible}  ok={r.is_correct}")

    for pid in ("independent_intersection", "independent_union"):
        inst = engine.instantiate(pid, seed=7)
        p = inst.params
        ans = inst.verifier.canonicals[0]
        print(f"=== {pid} ===  P(A)={p['p_a']}  P(B)={p['p_b']}  answer={ans}")
        show("correct (rational)", inst, ans)
        show("correct (decimal) ", inst, str(float(ans)))
        show("wrong             ", inst, ans + sympy.Rational(1, 20))
        print()

    for seed in (1, 2):
        inst = engine.instantiate("independent_decide", seed=seed)
        p = inst.params
        print(
            f"=== independent_decide (seed {seed}) ===  P(A)={p['p_a']} "
            f"P(B)={p['p_b']}  P(A∩B)={p['p_ab']}  →  {p['verdict']}"
        )
        show("product ✓ verdict ✓", inst, p["product"], p["verdict"])
        # the classic error: multiplying correctly but misreading the comparison
        wrong_verdict = (
            "not_independent" if p["verdict"] == "independent" else "independent"
        )
        show("product ✓ verdict ✗", inst, p["product"], wrong_verdict)
        print()
