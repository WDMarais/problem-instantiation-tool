"""
Reference example: geometric sequence — general term and specific term.

Mirrors arithmetic_sequence.py in structure (one Problem per exam
sub-competency, symbolic_equality throughout). Two archetypes:

- nth_term_formula: canonical is a SymPy expression a·r^(n-1) in the
  variable n. symbolic_equality accepts any algebraically equivalent form.
- find_term: integer answer T_n = a·r^(n-1) for a given n.

Guards (per family-build-specs.md Family 1 #2): r ≠ 0 and r ≠ 1 (a ratio of
1 is not geometric in the exam sense; 0 collapses the sequence). Integer r is
kept small so a computed term stays legible on a printed page.
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import Problem

_n = sympy.Symbol("n")

_A_RANGE = [a for a in range(-6, 7) if a != 0]
_R_RANGE = [-3, -2, 2, 3]  # integer ratios, |r| ≥ 2, guards r ∉ {0, 1}


# ---------------------------------------------------------------------------
# 1. nth_term_formula — write the general term Tₙ = a·r^(n-1)
# ---------------------------------------------------------------------------


def _gen_nth_term_formula(rng: random.Random) -> dict:
    a = rng.choice(_A_RANGE)
    r = rng.choice(_R_RANGE)
    return {
        "a": a,
        "r": r,
        "t1": a,
        "t2": a * r,
        "t3": a * r * r,
        "variant": f"geo_nth:{a}:{r}",
        "answer": sympy.Integer(a) * sympy.Integer(r) ** (_n - 1),
    }


nth_term_formula = Problem(
    id="geo_seq_nth_term_formula",
    type_id="geometric_sequence",
    name="Write the general term Tₙ for a geometric sequence",
    artifact_type="practice",
    problem_spec=_gen_nth_term_formula,
    verifier_spec={"kind": "symbolic_equality", "marks_possible": 2},
)


# ---------------------------------------------------------------------------
# 2. find_term — calculate Tₙ for a given n
# ---------------------------------------------------------------------------


def _gen_find_term(rng: random.Random) -> dict:
    a = rng.choice(_A_RANGE)
    r = rng.choice([2, 3])  # positive-only keeps the printed term modest
    n_target = rng.randint(4, 7)
    return {
        "a": a,
        "r": r,
        "n_target": n_target,
        "variant": f"geo_find:{a}:{r}:{n_target}",
        "answer": a * r ** (n_target - 1),
    }


find_term = Problem(
    id="geo_seq_find_term",
    type_id="geometric_sequence",
    name="Calculate a specific term Tₙ of a geometric sequence",
    artifact_type="practice",
    problem_spec=_gen_find_term,
    verifier_spec={"kind": "symbolic_equality", "marks_possible": 2},
)


# ---------------------------------------------------------------------------
# 3. find_missing — the positive geometric mean between two terms
# ---------------------------------------------------------------------------


def _gen_find_missing(rng: random.Random) -> dict:
    """Three consecutive terms with the middle unknown. Kept all-positive (a>0,
    r>0) so the geometric mean x = √(t_before·t_after) is a single positive
    integer with no ± ambiguity."""
    a = rng.randint(1, 6)
    r = rng.choice([2, 3])
    pos = rng.randint(1, 4)  # index (0-based) of the term before the missing one
    return {
        "a": a,
        "r": r,
        "t_before": a * r**pos,
        "t_after": a * r ** (pos + 2),
        "answer": a * r ** (pos + 1),
        "variant": f"geomiss:{a}:{r}:{pos}",
    }


find_missing = Problem(
    id="geo_seq_find_missing",
    type_id="geometric_sequence",
    name="Find the positive geometric mean between two terms",
    artifact_type="practice",
    problem_spec=_gen_find_missing,
    verifier_spec={"kind": "symbolic_equality", "marks_possible": 2},
)


# ---------------------------------------------------------------------------
# 4. find_n — which term equals a given value
# ---------------------------------------------------------------------------


def _gen_find_n(rng: random.Random) -> dict:
    a = rng.choice([1, 2, 3])
    r = rng.choice([2, 3])
    n_target = rng.randint(5, 8)
    return {
        "a": a,
        "r": r,
        "t1": a,
        "t2": a * r,
        "t3": a * r * r,
        "target": a * r ** (n_target - 1),
        "answer": n_target,
        "variant": f"geofindn:{a}:{r}:{n_target}",
    }


find_n = Problem(
    id="geo_seq_find_n",
    type_id="geometric_sequence",
    name="Find which term of a geometric sequence equals a given value",
    artifact_type="practice",
    problem_spec=_gen_find_n,
    verifier_spec={"kind": "symbolic_equality", "marks_possible": 3},
)


# ---------------------------------------------------------------------------
# 5. next_terms — give the next two terms after a shown subsequence
# ---------------------------------------------------------------------------


def _gen_next_terms(rng: random.Random) -> dict:
    a = rng.choice(_A_RANGE)
    r = rng.choice(_R_RANGE)
    show_count = rng.randint(3, 4)
    terms_shown = [a * r**i for i in range(show_count)]
    return {
        "a": a,
        "r": r,
        "terms_shown": terms_shown,
        "next_1": a * r**show_count,
        "next_2": a * r ** (show_count + 1),
        "variant": f"geonext:{a}:{r}:{show_count}",
    }


next_terms = Problem(
    id="geo_seq_next_terms",
    type_id="geometric_sequence",
    name="Give the next two terms of a geometric sequence",
    artifact_type="practice",
    problem_spec=_gen_next_terms,
    verifier_spec=[
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "next_1"},
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "next_2"},
    ],
)


# ---------------------------------------------------------------------------
# 6. from_two_terms — find a and r from two given terms
# ---------------------------------------------------------------------------


def _gen_from_two_terms(rng: random.Random) -> dict:
    """Two terms Tₚ and T_q are given. r^(q−p) = T_q/Tₚ, so the student takes a
    (q−p)-th root. Gap is odd whenever r may be negative, so the sign of r is
    recoverable (an even power would hide it)."""
    a = rng.choice([x for x in range(-4, 5) if x != 0])
    r = rng.choice([2, 3, -2, -3])
    p = rng.choice([1, 2, 3])
    gap = rng.choice([1, 3]) if r < 0 else rng.choice([1, 2, 3])
    q = p + gap
    return {
        "a": a,
        "r": r,
        "p": p,
        "q": q,
        "tp": a * r ** (p - 1),
        "tq": a * r ** (q - 1),
        "variant": f"geo2t:{a}:{r}:{p}:{q}",
    }


from_two_terms = Problem(
    id="geo_seq_from_two_terms",
    type_id="geometric_sequence",
    name="Find a and r of a geometric sequence from two given terms",
    artifact_type="practice",
    problem_spec=_gen_from_two_terms,
    verifier_spec=[
        {"kind": "symbolic_equality", "marks_possible": 2, "param_key": "r"},
        {"kind": "symbolic_equality", "marks_possible": 2, "param_key": "a"},
    ],
)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    all_problems = {p.id: p for p in [nth_term_formula, find_term]}
    engine = Engine(registry=InMemoryRegistry(all_problems))

    def show_result(label, instance, *answers):
        attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
        r = instance.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  "
            f"is_correct={r.is_correct}"
        )

    print("=== geo nth_term_formula ===")
    inst = engine.instantiate(nth_term_formula.id, seed=1)
    p = inst.params
    print(f"  Sequence: {p['t1']}, {p['t2']}, {p['t3']}, ...")
    print(f"  Canonical: {inst.verifier.canonicals[0]}")
    show_result("Correct a*r^(n-1)", inst, p["answer"])

    print("\n=== geo find_term ===")
    inst = engine.instantiate(find_term.id, seed=1)
    p = inst.params
    print(f"  a={p['a']}, r={p['r']}, find T_{p['n_target']}")
    print(f"  Canonical: {inst.verifier.canonicals[0]}")
    show_result("Correct", inst, p["answer"])
    show_result("Wrong  ", inst, p["answer"] + 1)
