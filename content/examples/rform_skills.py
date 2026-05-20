"""
Four atomic skill drills for the R-form identity.

Goal: rewrite a·sin x − b·cos x as R·sin(x − φ), then solve R·sin(x − φ) = k.
The combined solve silently chains four distinct skills; separating them makes
each link independently drillable.

rform_match_coefficients  — structural recognition (no arithmetic)
  Expand R·sin(x − φ) via compound angle identity, match coefficients with
  a·sin x − b·cos x.  The two equations R·cosφ = a and R·sinφ = b are the
  answer.  Tests whether the student sees the identity as a coefficient-matching
  step rather than a memorised formula.

rform_find_R  — Pythagorean step (arithmetic on the coefficient equations)
  Given R·cosφ = a and R·sinφ = b, square both and add.  cos²φ + sin²φ = 1
  collapses the left side to R².  Connects the abstract identity to ordinary
  Pythagoras on the triangle with legs a, b and hypotenuse R.

rform_find_phi  — arctan step (calculator skill)
  Divide the two equations: tanφ = b/a → φ = arctan(b/a).  Tested separately
  because the division step is easy to skip or confuse with arcsin.

rform_solve  — solve R·sin(x − φ) = k  (pure arcsin algebra)
  R, φ, and k are given explicitly so no prior skills are re-tested.  Two
  solutions exist in [0°, 360°]; tolerance 0.5° for calculator rounding.

Design note: generator uses a, b > 0 throughout, so φ ∈ (0°, 90°) and R is
unambiguous.  Sign cases (φ in other quadrants) are a natural extension.
"""

from __future__ import annotations

import math
import random

import sympy

from problem_instantiation_tool.schemas import Problem

_A_CHOICES = [1, 2, 3, 4]
_B_CHOICES = [1, 2, 3, 4]


def _r_and_phi(a: int, b: int) -> tuple[sympy.Basic, float]:
    """Return (R as SymPy expr, φ in degrees)."""
    return sympy.sqrt(a**2 + b**2), math.degrees(math.atan2(b, a))


# ── Skill α: match coefficients ───────────────────────────────────────────────


def _gen_match(rng: random.Random) -> dict:
    a = rng.choice(_A_CHOICES)
    b = rng.choice(_B_CHOICES)
    return {
        "a": a,
        "b": b,
        "answer_R_cos_phi": sympy.Integer(a),
        "answer_R_sin_phi": sympy.Integer(b),
    }


rform_match_coefficients = Problem(
    id="rform_match_coefficients",
    type_id="rform_skill",
    name="Expand R·sin(x−φ) via compound angle identity; match coefficients with a·sinx − b·cosx",
    artifact_type="practice",
    problem_spec=_gen_match,
    verifier_spec=[
        {
            "kind": "symbolic_equality",
            "marks_possible": 1,
            "param_key": "answer_R_cos_phi",
        },
        {
            "kind": "symbolic_equality",
            "marks_possible": 1,
            "param_key": "answer_R_sin_phi",
        },
    ],
)


# ── Skill β: find R ────────────────────────────────────────────────────────────


def _gen_find_R(rng: random.Random) -> dict:
    a = rng.choice(_A_CHOICES)
    b = rng.choice(_B_CHOICES)
    R_sym, _ = _r_and_phi(a, b)
    return {
        "a": a,
        "b": b,
        "answer_R": R_sym,
    }


rform_find_R = Problem(
    id="rform_find_R",
    type_id="rform_skill",
    name="Given R·cosφ = a and R·sinφ = b, find R by squaring and adding (Pythagoras)",
    artifact_type="practice",
    problem_spec=_gen_find_R,
    verifier_spec={
        "kind": "symbolic_equality",
        "marks_possible": 1,
        "param_key": "answer_R",
    },
)


# ── Skill γ: find φ ────────────────────────────────────────────────────────────


def _gen_find_phi(rng: random.Random) -> dict:
    a = rng.choice(_A_CHOICES)
    b = rng.choice(_B_CHOICES)
    _, phi_deg = _r_and_phi(a, b)
    return {
        "a": a,
        "b": b,
        "answer_phi_deg": phi_deg,
    }


rform_find_phi = Problem(
    id="rform_find_phi",
    type_id="rform_skill",
    name="Given R·cosφ = a and R·sinφ = b, find φ by dividing (tanφ = b/a)",
    artifact_type="practice",
    problem_spec=_gen_find_phi,
    verifier_spec={
        "kind": "numeric_equality",
        "marks_possible": 1,
        "param_key": "answer_phi_deg",
        "tolerance": 0.5,
    },
)


# ── Skill δ: solve R·sin(x − φ) = k ───────────────────────────────────────────


def _gen_solve(rng: random.Random) -> dict:
    while True:
        a = rng.choice(_A_CHOICES)
        b = rng.choice(_B_CHOICES)
        R_sym, phi_deg = _r_and_phi(a, b)
        R_val = float(R_sym)
        k_max = math.floor(R_val - 1e-9)
        if k_max < 1:
            continue
        k = rng.randint(1, k_max)
        alpha = math.degrees(math.asin(k / R_val))
        x1 = (phi_deg + alpha) % 360
        x2 = (phi_deg + 180 - alpha) % 360
        x1, x2 = sorted([x1, x2])
        return {
            "a": a,
            "b": b,
            "R_sym": R_sym,
            "phi_deg": phi_deg,
            "k": k,
            "answer_x1": x1,
            "answer_x2": x2,
        }


rform_solve = Problem(
    id="rform_solve",
    type_id="rform_skill",
    name="Given explicit R and φ, solve R·sin(x − φ) = k for x ∈ [0°, 360°]",
    artifact_type="practice",
    problem_spec=_gen_solve,
    verifier_spec=[
        {
            "kind": "numeric_equality",
            "marks_possible": 1,
            "param_key": "answer_x1",
            "tolerance": 0.5,
        },
        {
            "kind": "numeric_equality",
            "marks_possible": 1,
            "param_key": "answer_x2",
            "tolerance": 0.5,
        },
    ],
)


# ── Demo ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    all_probs = {
        p.id: p
        for p in [rform_match_coefficients, rform_find_R, rform_find_phi, rform_solve]
    }
    engine = Engine(registry=InMemoryRegistry(all_probs))

    def show(label, inst, *answers):
        attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
        r = inst.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  correct={r.is_correct}"
        )

    print("=== Skill α: match coefficients ===")
    inst = engine.instantiate(rform_match_coefficients.id, seed=1)
    p = inst.params
    print(f"  {p['a']}·sin x − {p['b']}·cos x  →  R·cosφ = ?, R·sinφ = ?")
    c1, c2 = inst.verifier.canonicals
    show("Correct               ", inst, c1, c2)
    show("Swapped (common error)", inst, c2, c1)

    print()

    print("=== Skill β: find R ===")
    inst = engine.instantiate(rform_find_R.id, seed=1)
    p = inst.params
    print(f"  R·cosφ = {p['a']},  R·sinφ = {p['b']}  →  R = ?")
    (canon,) = inst.verifier.canonicals
    print(f"  R = {canon}")
    show("Correct        ", inst, canon)
    show("Forgot sqrt    ", inst, sympy.Integer(p["a"] ** 2 + p["b"] ** 2))

    print()

    print("=== Skill γ: find φ ===")
    inst = engine.instantiate(rform_find_phi.id, seed=1)
    p = inst.params
    print(f"  R·cosφ = {p['a']},  R·sinφ = {p['b']}  →  φ = ?")
    (canon,) = inst.verifier.canonicals
    print(f"  φ ≈ {canon:.2f}°")
    show("Correct (exact)   ", inst, canon)
    show("Correct (rounded) ", inst, round(canon, 1))
    show("Off by 1°         ", inst, canon + 1.0)

    print()

    print("=== Skill δ: solve ===")
    inst = engine.instantiate(rform_solve.id, seed=1)
    p = inst.params
    R_latex = sympy.latex(p["R_sym"])
    print(f"  {R_latex}·sin(x − {p['phi_deg']:.1f}°) = {p['k']},  x ∈ [0°, 360°]")
    x1_c, x2_c = inst.verifier.canonicals
    print(f"  x ≈ {x1_c:.2f}° or {x2_c:.2f}°")
    show("Both correct (exact)   ", inst, x1_c, x2_c)
    show("Both correct (rounded) ", inst, round(x1_c, 1), round(x2_c, 1))
    show("x1 off by 1°           ", inst, x1_c + 1.0, x2_c)
