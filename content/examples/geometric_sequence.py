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
