"""
Reference example: linear equations — five question variants (P1 Q2, 14 marks).

Design decisions demonstrated:

- linear_expand: Form a − b(cx − d) = −(x − e). Coefficients are chosen first;
  x_sol is picked, then a is back-computed as (bc−1)·x_sol − bd + e to ensure the
  equation holds exactly. This guarantees an integer solution and avoids solving
  a system of diophantine constraints.

- linear_literal: Form ax − bq = cx where q is a symbolic literal parameter.
  Answer is the SymPy expression bq/(a−c) with the gcd reduced. symbolic_equality
  accepts any algebraically equivalent form — e.g. 4q/3 and 4/3*q both pass.

- linear_rational: Form Ax/(x−p) + Bx/(x−q) = ((A+B)x²+C)/((x−p)(x−q)).
  The constant C is chosen so the quadratic terms cancel when multiplied through,
  leaving the linear equation (A+B)·x·... = ... with integer solution x_sol.
  Domain restriction x ≠ p, x ≠ q is stated but not enforced by the verifier —
  this matches how SA marking guidelines work (the verifier checks the value, the
  rubric awards a separate mark for the domain statement).
  Params include `denom_b` and `denom_c` so a template can render the denominator
  in expanded form (e.g. x²−5x+6) matching exam convention.

- linear_double_inequality: Form p < ax + b < q. Integer solution bounds x_lo and
  x_hi are picked first; p and q are derived as the boundary values of ax+b at those
  x-values. This construction works correctly for both positive and negative a,
  because min/max normalise the direction. Two symbolic_equality steps via param_key
  verify the lower and upper bounds independently.

- simultaneous_2x2: Integer solution (x_sol, y_sol) is picked first; RHS constants
  c and f are derived. Determinant check prevents degenerate (dependent/inconsistent)
  systems. Two symbolic_equality steps via param_key verify x and y independently.
"""

from __future__ import annotations

import random
from math import gcd

import sympy

from problem_instantiation_tool.schemas import Problem

_x = sympy.Symbol("x")
_y = sympy.Symbol("y")
_q = sympy.Symbol("q")  # literal parameter used in linear_literal


# ---------------------------------------------------------------------------
# 1. linear_expand
#    a − b(cx − d) = −(x − e)   →   x (integer)
# ---------------------------------------------------------------------------


def _gen_linear_expand(rng: random.Random) -> dict:
    while True:
        b = rng.choice([2, 3, 4])
        c = rng.choice([2, 3])  # bc − 1 >= 3, so the denominator is non-trivial
        d = rng.randint(1, 8)
        e = rng.randint(1, 8)
        x_sol = rng.choice([i for i in range(-5, 6) if i != 0])
        a = (b * c - 1) * x_sol - b * d + e
        if abs(a) > 15 or a == 0:
            continue
        return {
            "a": a,
            "b": b,
            "c": c,
            "d": d,
            "e": e,
            "answer": sympy.Integer(x_sol),
        }


linear_expand = Problem(
    id="linear_expand",
    type_id="linear_equation",
    name="Solve a linear equation requiring expansion of brackets",
    artifact_type="practice",
    problem_spec=_gen_linear_expand,
    verifier_spec={"kind": "symbolic_equality", "marks_possible": 1},
)


# ---------------------------------------------------------------------------
# 2. linear_literal
#    ax − bq = cx   →   x = bq / (a − c)   (q is a symbolic literal)
# ---------------------------------------------------------------------------


def _gen_linear_literal(rng: random.Random) -> dict:
    while True:
        a = rng.randint(3, 8)
        c = rng.randint(1, a - 2)  # ensures a − c >= 2 (avoids answer = q)
        b = rng.randint(2, 8)
        denom = a - c
        g = gcd(b, denom)
        answer = sympy.Rational(b // g, denom // g) * _q
        return {
            "a": a,
            "b": b,
            "c": c,
            "answer": answer,
        }


linear_literal = Problem(
    id="linear_literal",
    type_id="linear_equation",
    name="Solve a literal equation for x in terms of q",
    artifact_type="practice",
    problem_spec=_gen_linear_literal,
    verifier_spec={"kind": "symbolic_equality", "marks_possible": 1},
)


# ---------------------------------------------------------------------------
# 3. linear_rational
#    Ax/(x−p) + Bx/(x−q) = ((A+B)x² + C) / ((x−p)(x−q))
#    The x² terms cancel after multiplying through by the LCD, leaving a
#    linear equation with solution x_sol.
#    Domain restriction x ≠ p, x ≠ q is noted in params but not verified.
# ---------------------------------------------------------------------------


def _gen_linear_rational(rng: random.Random) -> dict:
    while True:
        A = rng.choice([1, 2])
        B = rng.choice([1, 2])
        p = rng.randint(1, 5)
        q_val = rng.choice([i for i in range(1, 8) if i != p])
        x_sol = rng.randint(-8, 8)
        if x_sol == 0 or x_sol == p or x_sol == q_val:
            continue
        C = -(A * q_val + B * p) * x_sol
        return {
            "A": A,
            "B": B,
            "p": p,
            "q": q_val,
            "rhs_quad_coeff": A + B,  # coefficient of x² in RHS numerator
            "rhs_const": C,  # constant term in RHS numerator
            "denom_b": -(p + q_val),  # x²+bx+c form: b = −(p+q)
            "denom_c": p * q_val,  # x²+bx+c form: c = p·q
            "domain_excl": [p, q_val],
            "answer": sympy.Integer(x_sol),
        }


linear_rational = Problem(
    id="linear_rational",
    type_id="linear_equation",
    name="Solve a rational equation that reduces to a linear equation",
    artifact_type="practice",
    problem_spec=_gen_linear_rational,
    verifier_spec={"kind": "symbolic_equality", "marks_possible": 1},
)


# ---------------------------------------------------------------------------
# 4. linear_double_inequality
#    p < ax + b < q   →   answer_lower < x < answer_upper
#    Both bounds are integers. a ∈ {±2, ±3} so the division step is
#    non-trivial and the sign-flip case (a < 0) appears naturally.
# ---------------------------------------------------------------------------


def _gen_double_inequality(rng: random.Random) -> dict:
    while True:
        a = rng.choice([-3, -2, 2, 3])
        b = rng.randint(-4, 4)
        x_lo = rng.randint(-4, 2)
        x_hi = x_lo + rng.randint(2, 5)
        val_lo = a * x_lo + b
        val_hi = a * x_hi + b
        if val_lo == val_hi:
            continue
        return {
            "a": a,
            "b": b,
            "p": min(val_lo, val_hi),  # left bound of compound inequality
            "q": max(val_lo, val_hi),  # right bound
            "answer_lower": sympy.Integer(x_lo),
            "answer_upper": sympy.Integer(x_hi),
        }


linear_double_inequality = Problem(
    id="linear_double_inequality",
    type_id="linear_inequality",
    name="Solve a compound linear inequality for x",
    artifact_type="practice",
    problem_spec=_gen_double_inequality,
    verifier_spec=[
        {
            "kind": "symbolic_equality",
            "marks_possible": 1,
            "param_key": "answer_lower",
        },
        {
            "kind": "symbolic_equality",
            "marks_possible": 1,
            "param_key": "answer_upper",
        },
    ],
)


# ---------------------------------------------------------------------------
# 5. simultaneous_2x2
#    ax + by = c
#    dx + ey = f
#    Answer: x_sol, y_sol  (integers)
# ---------------------------------------------------------------------------


def _gen_simultaneous_2x2(rng: random.Random) -> dict:
    _nonzero = [-4, -3, -2, -1, 1, 2, 3, 4]
    while True:
        a = rng.choice(_nonzero)
        b = rng.choice(_nonzero)
        d = rng.choice(_nonzero)
        e = rng.choice(_nonzero)
        if a * e - b * d == 0:  # singular — skip
            continue
        x_sol = rng.randint(-5, 5)
        y_sol = rng.randint(-5, 5)
        if x_sol == 0 and y_sol == 0:
            continue
        return {
            "a": a,
            "b": b,
            "c": a * x_sol + b * y_sol,
            "d": d,
            "e": e,
            "f": d * x_sol + e * y_sol,
            "answer_x": sympy.Integer(x_sol),
            "answer_y": sympy.Integer(y_sol),
        }


simultaneous_2x2 = Problem(
    id="simultaneous_2x2",
    type_id="simultaneous_equations",
    name="Solve a 2×2 system of linear equations",
    artifact_type="practice",
    problem_spec=_gen_simultaneous_2x2,
    verifier_spec=[
        {
            "kind": "symbolic_equality",
            "marks_possible": 1,
            "param_key": "answer_x",
        },
        {
            "kind": "symbolic_equality",
            "marks_possible": 1,
            "param_key": "answer_y",
        },
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
        p.id: p
        for p in [
            linear_expand,
            linear_literal,
            linear_rational,
            linear_double_inequality,
            simultaneous_2x2,
        ]
    }
    engine = Engine(registry=InMemoryRegistry(all_problems))

    def show(label, instance, *answers):
        attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
        r = instance.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  is_correct={r.is_correct}"
        )

    # --- linear_expand ---
    print("=== linear_expand ===")
    inst = engine.instantiate(linear_expand.id, seed=42)
    p = inst.params
    print(f"  {p['a']} - {p['b']}({p['c']}x - {p['d']}) = -(x - {p['e']})")
    ans = inst.verifier.canonicals[0]
    print(f"  Answer: x = {ans}")
    show("Correct           ", inst, ans)
    show("Off by one        ", inst, int(ans) + 1)

    print()

    # --- linear_literal ---
    print("=== linear_literal ===")
    inst = engine.instantiate(linear_literal.id, seed=42)
    p = inst.params
    print(f"  {p['a']}x - {p['b']}q = {p['c']}x  →  solve for x")
    ans = inst.verifier.canonicals[0]
    print(f"  Answer: x = {ans}")
    show("Correct (exact form)     ", inst, ans)
    show("Equivalent (*q form)     ", inst, ans / _q * _q)
    show("Wrong (missing q)        ", inst, sympy.Rational(ans.coeff(_q)))

    print()

    # --- linear_rational ---
    print("=== linear_rational ===")
    inst = engine.instantiate(linear_rational.id, seed=42)
    p = inst.params
    print(
        f"  {p['A']}x/(x-{p['p']}) + {p['B']}x/(x-{p['q']}) "
        f"= ({p['rhs_quad_coeff']}x²+({p['rhs_const']})) / "
        f"(x²+({p['denom_b']})x+{p['denom_c']})"
    )
    print(f"  Domain: x ≠ {p['domain_excl'][0]}, x ≠ {p['domain_excl'][1]}")
    ans = inst.verifier.canonicals[0]
    print(f"  Answer: x = {ans}")
    show("Correct      ", inst, ans)
    show("Wrong        ", inst, int(ans) + 2)

    print()

    # --- linear_double_inequality ---
    print("=== linear_double_inequality ===")
    inst = engine.instantiate(linear_double_inequality.id, seed=42)
    p = inst.params
    b_str = f"+ {p['b']}" if p["b"] >= 0 else f"- {abs(p['b'])}"
    print(f"  {p['p']} < {p['a']}x {b_str} < {p['q']}")
    lo, hi = inst.verifier.canonicals
    print(f"  Answer: {lo} < x < {hi}")
    show("Both correct      ", inst, lo, hi)
    show("Lower wrong       ", inst, int(lo) - 1, hi)
    show("Both wrong        ", inst, int(lo) - 1, int(hi) + 1)

    print()

    # --- simultaneous_2x2 ---
    print("=== simultaneous_2x2 ===")
    inst = engine.instantiate(simultaneous_2x2.id, seed=42)
    p = inst.params
    print(f"  {p['a']}x + {p['b']}y = {p['c']}")
    print(f"  {p['d']}x + {p['e']}y = {p['f']}")
    x_ans, y_ans = inst.verifier.canonicals
    print(f"  Answer: x = {x_ans}, y = {y_ans}")
    show("Both correct  ", inst, x_ans, y_ans)
    show("x wrong       ", inst, int(x_ans) + 1, y_ans)
    show("Both wrong    ", inst, int(x_ans) + 1, int(y_ans) + 1)
