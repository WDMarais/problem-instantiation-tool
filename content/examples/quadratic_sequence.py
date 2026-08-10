"""
Reference example: quadratic sequence — Tₙ = an² + bn + c.

Mirrors arithmetic_sequence.py / geometric_sequence.py in structure (one Problem
per exam sub-competency, symbolic_equality throughout). The defining property is a
*constant, non-zero second difference* equal to 2a; every method below is that fact
applied.

Four archetypes:
- next_terms: extend the pattern using the constant second difference alone — the
  introductory skill, needs no closed form.
- nth_term_formula: the load-bearing one. From four terms recover a, b, c via
  2a = (second difference), 3a + b = (first first-difference), a + b + c = T₁.
  The canonical is a SymPy expression in n; symbolic_equality accepts any
  algebraically equivalent form.
- find_term: a specific larger term T_k — the student must derive the closed form
  first, then substitute (numeric answer).
- find_n: which term equals a given value — solve a quadratic in n. Draws are
  constrained (a > 0, b ≥ 0) so the sequence is strictly increasing for n ≥ 1;
  the parabola's other root is then negative and the positive integer term index
  is unique (no ± ambiguity for the student to adjudicate).
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import Problem

_n = sympy.Symbol("n")

# a ≠ 0 (else it is not quadratic); kept small so 2a and the printed terms stay
# legible on a page. b, c span both signs for variety.
_A_RANGE = [-2, -1, 1, 2, 3]
_B_RANGE = list(range(-6, 7))
_C_RANGE = list(range(-6, 7))


def _terms(a: int, b: int, c: int, count: int) -> list[int]:
    return [a * k * k + b * k + c for k in range(1, count + 1)]


def _answer_expr(a: int, b: int, c: int) -> sympy.Expr:
    return sympy.Integer(a) * _n**2 + sympy.Integer(b) * _n + sympy.Integer(c)


# ---------------------------------------------------------------------------
# 1. next_terms — extend via the constant second difference
# ---------------------------------------------------------------------------


def _gen_next_terms(rng: random.Random) -> dict:
    a = rng.choice(_A_RANGE)
    b = rng.choice(_B_RANGE)
    c = rng.choice(_C_RANGE)
    shown = _terms(a, b, c, 4)
    return {
        "a": a,
        "b": b,
        "c": c,
        "terms_shown": shown,
        "next_1": a * 25 + b * 5 + c,  # T₅
        "next_2": a * 36 + b * 6 + c,  # T₆
        "variant": f"quadnext:{a}:{b}:{c}",
    }


next_terms = Problem(
    id="quad_seq_next_terms",
    type_id="quadratic_sequence",
    name="Give the next two terms of a quadratic sequence",
    artifact_type="practice",
    problem_spec=_gen_next_terms,
    verifier_spec=[
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "next_1"},
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "next_2"},
    ],
)


# ---------------------------------------------------------------------------
# 2. nth_term_formula — recover Tₙ = an² + bn + c from four terms
# ---------------------------------------------------------------------------


def _gen_nth_term_formula(rng: random.Random) -> dict:
    a = rng.choice(_A_RANGE)
    b = rng.choice(_B_RANGE)
    c = rng.choice(_C_RANGE)
    shown = _terms(a, b, c, 4)
    d1 = shown[1] - shown[0]  # first first-difference = 3a + b
    return {
        "a": a,
        "b": b,
        "c": c,
        "t1": shown[0],
        "t2": shown[1],
        "t3": shown[2],
        "t4": shown[3],
        "first_diff": d1,
        "second_diff": 2 * a,
        "variant": f"quadnth:{a}:{b}:{c}",
        "answer": _answer_expr(a, b, c),
    }


nth_term_formula = Problem(
    id="quad_seq_nth_term_formula",
    type_id="quadratic_sequence",
    name="Write the general term Tₙ for a quadratic sequence",
    artifact_type="practice",
    problem_spec=_gen_nth_term_formula,
    verifier_spec={"kind": "symbolic_equality", "marks_possible": 4},
)


# ---------------------------------------------------------------------------
# 3. find_term — evaluate a specific larger term T_k
# ---------------------------------------------------------------------------


def _gen_find_term(rng: random.Random) -> dict:
    a = rng.choice(_A_RANGE)
    b = rng.choice(_B_RANGE)
    c = rng.choice(_C_RANGE)
    n_target = rng.randint(10, 20)
    shown = _terms(a, b, c, 3)
    return {
        "a": a,
        "b": b,
        "c": c,
        "t1": shown[0],
        "t2": shown[1],
        "t3": shown[2],
        "second_diff": 2 * a,
        "n_target": n_target,
        "variant": f"quadfind:{a}:{b}:{c}:{n_target}",
        "answer": a * n_target * n_target + b * n_target + c,
    }


find_term = Problem(
    id="quad_seq_find_term",
    type_id="quadratic_sequence",
    name="Calculate a specific term Tₙ of a quadratic sequence",
    artifact_type="practice",
    problem_spec=_gen_find_term,
    verifier_spec={"kind": "symbolic_equality", "marks_possible": 3},
)


# ---------------------------------------------------------------------------
# 4. find_n — which term equals a given value (solve a quadratic in n)
# ---------------------------------------------------------------------------


def _gen_find_n(rng: random.Random) -> dict:
    """a > 0 and b ≥ 0 ⇒ the vertex sits at n = -b/(2a) ≤ 0, so the sequence is
    strictly increasing for n ≥ 1. The value at n_target is therefore reached by a
    single positive integer term index; the quadratic's other root is negative and
    the student rejects it, so 'which term' has one unambiguous answer."""
    a = rng.choice([1, 2])
    b = rng.randint(0, 6)
    c = rng.randint(-4, 6)
    n_target = rng.randint(4, 9)
    target = a * n_target * n_target + b * n_target + c
    shown = _terms(a, b, c, 3)
    return {
        "a": a,
        "b": b,
        "c": c,
        "t1": shown[0],
        "t2": shown[1],
        "t3": shown[2],
        "second_diff": 2 * a,
        "target": target,
        "other_root": sympy.Rational(-b, a) - n_target,  # < 0, rejected
        "variant": f"quadfindn:{a}:{b}:{c}:{n_target}",
        "answer": n_target,
    }


find_n = Problem(
    id="quad_seq_find_n",
    type_id="quadratic_sequence",
    name="Find which term of a quadratic sequence equals a given value",
    artifact_type="practice",
    problem_spec=_gen_find_n,
    verifier_spec={"kind": "symbolic_equality", "marks_possible": 4},
)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    all_problems = {p.id: p for p in [next_terms, nth_term_formula, find_term, find_n]}
    engine = Engine(registry=InMemoryRegistry(all_problems))

    def show_result(label, instance, *answers):
        attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
        r = instance.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  "
            f"is_correct={r.is_correct}"
        )

    print("=== quad nth_term_formula ===")
    inst = engine.instantiate(nth_term_formula.id, seed=1)
    p = inst.params
    print(f"  Sequence: {p['t1']}, {p['t2']}, {p['t3']}, {p['t4']}, ...")
    print(f"  2nd difference = {p['second_diff']}")
    print(f"  Canonical: {inst.verifier.canonicals[0]}")
    show_result("Correct an²+bn+c", inst, p["answer"])

    print("\n=== quad next_terms ===")
    inst = engine.instantiate(next_terms.id, seed=1)
    p = inst.params
    print(f"  Shown: {p['terms_shown']}")
    show_result("Both correct", inst, p["next_1"], p["next_2"])

    print("\n=== quad find_term ===")
    inst = engine.instantiate(find_term.id, seed=1)
    p = inst.params
    print(f"  a={p['a']}, b={p['b']}, c={p['c']}, find T_{p['n_target']}")
    show_result("Correct", inst, p["answer"])

    print("\n=== quad find_n ===")
    inst = engine.instantiate(find_n.id, seed=1)
    p = inst.params
    print(f"  which term = {p['target']}? (other root {p['other_root']})")
    show_result("Correct", inst, p["answer"])
