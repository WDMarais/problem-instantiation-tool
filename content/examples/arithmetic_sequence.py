"""
Reference example: arithmetic sequence — five question variants.

Design decisions demonstrated:
- One file, five Problem objects — one per exam sub-competency. Content
  authors build libraries by composing Problems, not by switching on a
  "variant" key inside a monolithic generator.
- nth_term_formula: the canonical is a SymPy expression in the variable n.
  symbolic_equality accepts both a + (n-1)*d and d*n + (a-d) as correct,
  since sympy.simplify of their difference is 0. Content authors write the
  form that matches exam convention; the verifier accepts any equivalent form.
- find_term and find_n: integer answers, but symbolic_equality is used
  throughout for consistency. Using different verifier kinds for "formula"
  vs "integer" problems would surprise content authors; SymPy handles integers
  correctly with no overhead.
- find_missing: three consecutive terms with the middle one unknown. The
  missing value is the arithmetic mean of its neighbours — always an integer
  because both neighbours share the same parity offset relative to d.
- next_terms: two-step problem using param_key to route each step to its own
  canonical. A one-step verifier would give both steps the same canonical.
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import Problem

_n = sympy.Symbol("n")

_D_RANGE = [d for d in range(-10, 11) if d != 0]


# ---------------------------------------------------------------------------
# 1. nth_term_formula — write the general term Tₙ
# ---------------------------------------------------------------------------


def _gen_nth_term_formula(rng: random.Random) -> dict:
    a = rng.randint(-20, 20)
    d = rng.choice(_D_RANGE)
    return {
        "a": a,
        "d": d,
        "t1": a,
        "t2": a + d,
        "t3": a + 2 * d,
        "answer": sympy.Integer(a) + (_n - 1) * sympy.Integer(d),
    }


nth_term_formula = Problem(
    id="arith_seq_nth_term_formula",
    type_id="arithmetic_sequence",
    name="Write the general term Tₙ for an arithmetic sequence",
    artifact_type="practice",
    problem_spec=_gen_nth_term_formula,
    verifier_spec={"kind": "symbolic_equality", "marks_possible": 1},
)


# ---------------------------------------------------------------------------
# 2. find_term — calculate Tₙ for a given n
# ---------------------------------------------------------------------------


def _gen_find_term(rng: random.Random) -> dict:
    a = rng.randint(-20, 20)
    d = rng.choice(_D_RANGE)
    n_target = rng.randint(10, 30)
    return {
        "a": a,
        "d": d,
        "n_target": n_target,
        "answer": a + (n_target - 1) * d,
    }


find_term = Problem(
    id="arith_seq_find_term",
    type_id="arithmetic_sequence",
    name="Calculate a specific term Tₙ of an arithmetic sequence",
    artifact_type="practice",
    problem_spec=_gen_find_term,
    verifier_spec={"kind": "symbolic_equality", "marks_possible": 1},
)


# ---------------------------------------------------------------------------
# 3. find_n — find which term equals a given value
# ---------------------------------------------------------------------------


def _gen_find_n(rng: random.Random) -> dict:
    a = rng.randint(-20, 20)
    d = rng.choice(_D_RANGE)
    n_target = rng.randint(5, 50)
    return {
        "a": a,
        "d": d,
        "target": a + (n_target - 1) * d,
        "answer": n_target,
    }


find_n = Problem(
    id="arith_seq_find_n",
    type_id="arithmetic_sequence",
    name="Find which term of an arithmetic sequence equals a given value",
    artifact_type="practice",
    problem_spec=_gen_find_n,
    verifier_spec={"kind": "symbolic_equality", "marks_possible": 1},
)


# ---------------------------------------------------------------------------
# 4. find_missing — given two consecutive terms, find the one between them
# ---------------------------------------------------------------------------


def _gen_find_missing(rng: random.Random) -> dict:
    a = rng.randint(-20, 20)
    d = rng.choice(_D_RANGE)
    pos = rng.randint(3, 20)
    t_before = a + (pos - 2) * d
    t_missing = a + (pos - 1) * d
    t_after = a + pos * d
    return {
        "a": a,
        "d": d,
        "t_before": t_before,
        "t_after": t_after,
        "answer": t_missing,
    }


find_missing = Problem(
    id="arith_seq_find_missing",
    type_id="arithmetic_sequence",
    name="Find the missing middle term in three consecutive arithmetic terms",
    artifact_type="practice",
    problem_spec=_gen_find_missing,
    verifier_spec={"kind": "symbolic_equality", "marks_possible": 1},
)


# ---------------------------------------------------------------------------
# 5. next_terms — give the next two terms after a shown subsequence
# ---------------------------------------------------------------------------


def _gen_next_terms(rng: random.Random) -> dict:
    a = rng.randint(-20, 20)
    d = rng.choice(_D_RANGE)
    show_count = rng.randint(3, 5)
    terms_shown = [a + i * d for i in range(show_count)]
    return {
        "a": a,
        "d": d,
        "terms_shown": terms_shown,
        "next_1": a + show_count * d,
        "next_2": a + (show_count + 1) * d,
    }


next_terms = Problem(
    id="arith_seq_next_terms",
    type_id="arithmetic_sequence",
    name="Give the next two terms of an arithmetic sequence",
    artifact_type="practice",
    problem_spec=_gen_next_terms,
    verifier_spec=[
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "next_1"},
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "next_2"},
    ],
)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    all_problems = {
        p.id: p for p in [nth_term_formula, find_term, find_n, find_missing, next_terms]
    }
    engine = Engine(registry=InMemoryRegistry(all_problems))

    def show_result(label, instance, *answers):
        attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
        r = instance.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  "
            f"is_correct={r.is_correct}"
        )

    print("=== nth_term_formula ===")
    inst = engine.instantiate(nth_term_formula.id, seed=1)
    p = inst.params
    print(f"  Sequence: {p['t1']}, {p['t2']}, {p['t3']}, ...")
    print(f"  Canonical: {inst.verifier.canonicals[0]}")
    show_result("Correct a+(n-1)d form  ", inst, f"{p['a']} + (n-1)*{p['d']}")
    show_result("Equivalent d*n+(a-d)   ", inst, f"{p['d']}*n + {p['a'] - p['d']}")
    show_result("Wrong formula          ", inst, f"{p['a']} + n*{p['d']}")

    print()
    print("=== find_term ===")
    inst = engine.instantiate(find_term.id, seed=1)
    p = inst.params
    print(f"  a={p['a']}, d={p['d']}, find T_{p['n_target']}")
    print(f"  Canonical: {inst.verifier.canonicals[0]}")
    show_result("Correct  ", inst, p["answer"])
    show_result("Wrong    ", inst, p["answer"] + 1)

    print()
    print("=== find_n ===")
    inst = engine.instantiate(find_n.id, seed=1)
    p = inst.params
    print(f"  a={p['a']}, d={p['d']}, which term = {p['target']}?")
    print(f"  Canonical: {inst.verifier.canonicals[0]}")
    show_result("Correct  ", inst, p["answer"])
    show_result("Wrong    ", inst, p["answer"] + 1)

    print()
    print("=== find_missing ===")
    inst = engine.instantiate(find_missing.id, seed=1)
    p = inst.params
    print(f"  {p['t_before']}; p; {p['t_after']} — find p")
    print(f"  Canonical: {inst.verifier.canonicals[0]}")
    show_result("Correct  ", inst, p["answer"])
    show_result("Wrong    ", inst, p["answer"] + 1)

    print()
    print("=== next_terms ===")
    inst = engine.instantiate(next_terms.id, seed=1)
    p = inst.params
    print(f"  Shown: {p['terms_shown']}")
    print(f"  Canonicals: {inst.verifier.canonicals}")
    show_result("Both correct ", inst, p["next_1"], p["next_2"])
    show_result("First wrong  ", inst, p["next_1"] + 1, p["next_2"])
    show_result("Both wrong   ", inst, p["next_1"] + 1, p["next_2"] + 1)
