"""
Three atomic skill drills for monic quadratic factorisation.

The combined problem x² + bx + c = 0 → roots silently chains three skills.
Separating them makes each link independently drillable and trackable.

factorise_skill_a  — equation → constraints (pattern recognition, no arithmetic)
  Given x² + bx + c = 0, write down mn and m+n from the identity
  (x−m)(x−n) = x²−(m+n)x+mn.  The error "m+n = b" instead of "m+n = −b"
  is invisible in the combined problem but surfaces immediately here.

factorise_skill_b  — constraints → sign case (sign reasoning, MCQ, no arithmetic)
  Given mn and m+n, deduce whether m,n are both positive, both negative, or
  have opposite signs.  This is where sign-flip confusion actually lives.

factorise_skill_c  — factor enumeration (arithmetic)
  Given mn, m+n, and the sign case, find m and n by listing factor pairs.
  The sign case is given so Skill B reasoning is not re-tested here.
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import Problem


# ── shared helpers ────────────────────────────────────────────────────────────

_SIGN_LABELS = {
    "both_positive": "both positive",
    "both_negative": "both negative",
    "opposite_signs": "opposite signs",
}


def _draw_roots(rng: random.Random, sign_case: str) -> tuple[int, int]:
    """Draw two distinct non-zero roots matching sign_case."""
    while True:
        if sign_case == "both_positive":
            r1, r2 = rng.randint(1, 8), rng.randint(1, 8)
        elif sign_case == "both_negative":
            r1, r2 = rng.randint(-8, -1), rng.randint(-8, -1)
        else:
            r1, r2 = rng.randint(1, 8), rng.randint(-8, -1)
        if r1 != r2:
            return r1, r2


def factor_pairs_for_display(mn: int, m_plus_n: int) -> list[tuple[int, int]]:
    """All integer pairs (a,b) with a*b=mn, sorted so the correct pair is last."""
    abs_mn = abs(mn)
    unsigned = [
        (a, abs_mn // a) for a in range(1, int(abs_mn**0.5) + 1) if abs_mn % a == 0
    ]
    if mn > 0:
        signed = (
            [(a, b) for a, b in unsigned]
            if m_plus_n > 0
            else [(-a, -b) for a, b in unsigned]
        )
    else:
        signed = [(a, -b) for a, b in unsigned] + [(-a, b) for a, b in unsigned]

    def _key(pair: tuple[int, int]) -> tuple[int, int, int]:
        a, b = pair
        return (1 if a + b == m_plus_n else 0, abs(a), a)

    return sorted(signed, key=_key)


# ── Skill A ───────────────────────────────────────────────────────────────────


def _gen_a(rng: random.Random) -> dict:
    sign_case = rng.choice(list(_SIGN_LABELS))
    r1, r2 = _draw_roots(rng, sign_case)
    b, c = -(r1 + r2), r1 * r2
    return {
        "b": b,
        "c": c,
        "answer_mn": sympy.Integer(c),
        "answer_m_plus_n": sympy.Integer(-b),
    }


factorise_skill_a = Problem(
    id="factorise_skill_a",
    type_id="factorise_skill",
    name="Equation → constraints: read mn and m+n from x² + bx + c = 0",
    artifact_type="practice",
    problem_spec=_gen_a,
    verifier_spec=[
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "answer_mn"},
        {
            "kind": "symbolic_equality",
            "marks_possible": 1,
            "param_key": "answer_m_plus_n",
        },
    ],
)


# ── Skill B ───────────────────────────────────────────────────────────────────


def _gen_b(rng: random.Random) -> dict:
    sign_case = rng.choice(list(_SIGN_LABELS))
    r1, r2 = _draw_roots(rng, sign_case)
    return {
        "mn": r1 * r2,
        "m_plus_n": r1 + r2,
        "sign_case": sign_case,
        "correct": _SIGN_LABELS[sign_case],
    }


factorise_skill_b = Problem(
    id="factorise_skill_b",
    type_id="factorise_skill",
    name="Constraints → sign case: given mn and m+n, state sign of m and n (MCQ)",
    artifact_type="practice",
    problem_spec=_gen_b,
    verifier_spec={"kind": "mcq", "marks_possible": 1},
)


# ── Skill C ───────────────────────────────────────────────────────────────────


def _gen_c(rng: random.Random) -> dict:
    sign_case = rng.choice(list(_SIGN_LABELS))
    r1, r2 = _draw_roots(rng, sign_case)
    mn, m_plus_n = r1 * r2, r1 + r2
    return {
        "mn": mn,
        "m_plus_n": m_plus_n,
        "sign_label": _SIGN_LABELS[sign_case],
        "root1": sympy.Integer(r1),
        "root2": sympy.Integer(r2),
        "factor_pairs": factor_pairs_for_display(mn, m_plus_n),
    }


factorise_skill_c = Problem(
    id="factorise_skill_c",
    type_id="factorise_skill",
    name="Factor enumeration: given mn, m+n, sign case — find m and n",
    artifact_type="practice",
    problem_spec=_gen_c,
    verifier_spec={"kind": "set_equality", "marks_possible": 2},
)


# ── Demo ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    all_probs = {
        p.id: p for p in [factorise_skill_a, factorise_skill_b, factorise_skill_c]
    }
    engine = Engine(registry=InMemoryRegistry(all_probs))

    def show(label: str, inst, *answers) -> None:
        attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
        r = inst.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  correct={r.is_correct}"
        )

    print("=== Skill A: x² - 7x + 12 = 0 ===")
    inst = engine.instantiate("factorise_skill_a", seed=1)
    p = inst.params
    print(f"  x² + {p['b']}x + {p['c']} = 0  →  mn=?, m+n=?")
    print(
        f"  Canonical: mn={inst.verifier.canonicals[0]}, m+n={inst.verifier.canonicals[1]}"
    )
    show(
        "Correct mn then m+n",
        inst,
        inst.verifier.canonicals[0],
        inst.verifier.canonicals[1],
    )
    show(
        "mn correct, m+n = b (sign error)",
        inst,
        inst.verifier.canonicals[0],
        sympy.Integer(p["b"]),
    )

    print()

    print("=== Skill B: sign reasoning ===")
    inst = engine.instantiate("factorise_skill_b", seed=1)
    p = inst.params
    print(f"  mn={p['mn']}, m+n={p['m_plus_n']}  →  sign case?")
    print(f"  Correct: {p['correct']}")
    show("Correct", inst, p["correct"])
    wrong = next(v for v in _SIGN_LABELS.values() if v != p["correct"])
    show(f"Wrong ({wrong!r})", inst, wrong)

    print()

    print("=== Skill C: factor enumeration ===")
    inst = engine.instantiate("factorise_skill_c", seed=1)
    p = inst.params
    print(f"  mn={p['mn']}, m+n={p['m_plus_n']} ({p['sign_label']})")
    print(f"  Factor pairs: {p['factor_pairs']}")
    canon = inst.verifier.canonicals[0]
    print(f"  Answer: {canon}")
    show("Correct", inst, canon)
    show("One root wrong", inst, frozenset({p["root1"]}))
