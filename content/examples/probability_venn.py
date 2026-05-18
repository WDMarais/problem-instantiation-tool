"""
Reference example: probability — Venn diagram variants (P1 Q7, 12 marks).

Two Problem objects, both testing the inclusion-exclusion identity
P(A∪B) = P(A) + P(B) − P(A∩B) in different surface presentations:

- prob_venn_intersection: probability form.
  Given P(A), P(B), P(A∪B), find P(A∩B).
  All values are multiples of 1/20 (i.e. 0.05 steps), stored as SymPy Rationals
  so symbolic_equality accepts both "3/20" and "0.15" from the student.
  P(A∩B) is chosen first, then P(A∪B) is derived; this guarantees consistency
  and avoids the edge case P(A∪B) > 1.

- prob_count_intersection: count form.
  Given n(A), n(B), n(neither), and n_total, find n(A∩B).
  n_A∩B is chosen first, then n_A, n_B are sampled to be comfortably larger, and
  n_neither = n_total − n_A∪B is derived. The "neither" count is kept ≥ 5 so it
  reads as a genuine Venn region rather than a trivial boundary case.
  Answer is a sympy.Integer; symbolic_equality handles it.
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import Problem

# P values are multiples of 1/20 (0.05 steps) in [0.10, 0.60]
_P_GRID = [sympy.Rational(k, 20) for k in range(2, 13)]


# ---------------------------------------------------------------------------
# 1. prob_venn_intersection  —  probability form
# ---------------------------------------------------------------------------


def _gen_venn_prob(rng: random.Random) -> dict:
    while True:
        p_a = rng.choice(_P_GRID)
        p_b = rng.choice(_P_GRID)
        p_min = min(p_a, p_b)
        # P(A∩B) ∈ (0, min(P(A), P(B))), multiples of 1/20
        ab_choices = [sympy.Rational(k, 20) for k in range(1, int(p_min * 20))]
        if not ab_choices:
            continue
        p_ab = rng.choice(ab_choices)
        p_aub = p_a + p_b - p_ab
        if p_aub > 1:
            continue
        return {
            "p_a": p_a,
            "p_b": p_b,
            "p_aub": p_aub,
            "answer": p_ab,
        }


prob_venn_intersection = Problem(
    id="prob_venn_intersection",
    type_id="probability",
    name="Find P(A∩B) given P(A), P(B), and P(A∪B)",
    artifact_type="practice",
    problem_spec=_gen_venn_prob,
    verifier_spec={"kind": "symbolic_equality", "marks_possible": 1},
)


# ---------------------------------------------------------------------------
# 2. prob_count_intersection  —  count form
# ---------------------------------------------------------------------------

_TOTALS = [50, 100, 150, 200]


def _gen_count_prob(rng: random.Random) -> dict:
    while True:
        n_total = rng.choice(_TOTALS)
        n_ab = rng.randint(3, n_total // 5)
        max_single = n_total * 2 // 3
        n_a = rng.randint(n_ab + 3, max_single)
        n_b = rng.randint(n_ab + 3, max_single)
        n_aub = n_a + n_b - n_ab
        n_neither = n_total - n_aub
        if n_neither < 5:
            continue
        return {
            "n_total": n_total,
            "n_a": n_a,
            "n_b": n_b,
            "n_neither": n_neither,
            "answer": sympy.Integer(n_ab),
        }


prob_count_intersection = Problem(
    id="prob_count_intersection",
    type_id="probability",
    name="Find n(A∩B) given counts n(A), n(B), n(neither), and the total",
    artifact_type="practice",
    problem_spec=_gen_count_prob,
    verifier_spec={"kind": "symbolic_equality", "marks_possible": 1},
)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    all_problems = {p.id: p for p in [prob_venn_intersection, prob_count_intersection]}
    engine = Engine(registry=InMemoryRegistry(all_problems))

    def show(label, instance, answer):
        attempt = SolutionAttempt(steps=[SubmittedStep(answer)])
        r = instance.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  is_correct={r.is_correct}"
        )

    print("=== prob_venn_intersection ===")
    inst = engine.instantiate(prob_venn_intersection.id, seed=42)
    p = inst.params
    print(
        f"  P(A)={float(p['p_a']):.2f}  P(B)={float(p['p_b']):.2f}"
        f"  P(A∪B)={float(p['p_aub']):.2f}"
    )
    ans = inst.verifier.canonicals[0]
    print(f"  Answer: P(A∩B) = {ans}  ({float(ans):.2f})")
    show("Correct (Rational)    ", inst, ans)
    show("Correct (float str)   ", inst, str(float(ans)))
    show("Correct (decimal str) ", inst, str(ans))
    show("Wrong                 ", inst, ans + sympy.Rational(1, 20))

    print()

    print("=== prob_count_intersection ===")
    inst = engine.instantiate(prob_count_intersection.id, seed=42)
    p = inst.params
    print(
        f"  n(A)={p['n_a']}  n(B)={p['n_b']}"
        f"  n(neither)={p['n_neither']}  total={p['n_total']}"
    )
    ans = inst.verifier.canonicals[0]
    print(f"  Answer: n(A∩B) = {ans}")
    show("Correct (int)  ", inst, ans)
    show("Wrong          ", inst, int(ans) + 5)
