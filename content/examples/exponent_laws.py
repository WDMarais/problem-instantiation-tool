"""
Reference example: exponent laws — two question variants.

Design decisions demonstrated:

- exponent_variable_simplify: The "simplify to a constant" form where both
  numerator terms and the denominator share the same base raised to a linear
  expression in n.

  Parametric structure:

      (k · b^(p·n+a) − m · b^(p·n+c)) / b^(p·n+d)

  where a > c ≥ d ≥ 0, b ∈ {2,3,5,7}, p ∈ {1,2}. Factor b^(p·n+c) from
  the numerator; this cancels with b^(p·n+d) in the denominator, leaving
  the constant  b^(c−d) · (k·b^(a−c) − m).

  When p=2, the denominator can be written (b²)^n · b^d — e.g. 49^n · b^d
  when b=7 — matching the SA exam convention. `denom_base = b**p` is stored
  so a template can render this notation.

  The answer is always a positive integer ≤ 100. k·b^(a−c) > m is enforced
  so the numerator factor is positive.

- exponent_algebraic_simplify: The "negative fractional exponent + product
  minus a power" form. Structure:

      (C^k · x^(k·a))^(−1/k) · B · x^(−a) − x^(−2a)

  Expanding: (C^k)^(−1/k) · x^(−a) · B · x^(−a) − x^(−2a)
           = C^(−1) · B · x^(−2a) − x^(−2a)
           = (B/C − 1) · x^(−2a)

  Parametrized by choosing B = C·(1+t) for integer t ≥ 0, so the answer
  coefficient is exactly t. When t=0, the answer is 0; when t=1 the
  coefficient is 1 and is omitted in standard notation.

  k ∈ {2,3} (square / cube root). x is treated as positive to avoid
  absolute values when simplifying even roots.

  symbolic_equality is used for both problems. For the variable form, the
  canonical is a SymPy Integer; for the algebraic form it is a SymPy
  expression in x (possibly 0).
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import Problem

_x = sympy.Symbol("x", positive=True)

_BASES = [2, 3, 5, 7]


# ---------------------------------------------------------------------------
# 1. exponent_variable_simplify
#    (k · b^(p·n+a) − m · b^(p·n+c)) / b^(p·n+d)  →  integer
# ---------------------------------------------------------------------------


def _gen_variable_simplify(rng: random.Random) -> dict:
    while True:
        b = rng.choice(_BASES)
        p = rng.choice([1, 2])

        # Offsets satisfy a > c >= d >= 0
        d = rng.randint(0, 1)
        c = rng.randint(d, d + 2)
        delta = rng.randint(1, 2)  # a - c
        a = c + delta

        k = rng.randint(1, 4)
        inner = k * (b**delta)  # k · b^(a−c)

        # m must be < inner so the numerator factor is positive
        if inner <= 1:
            continue
        m = rng.randint(1, inner - 1)

        answer_val = (b ** (c - d)) * (inner - m)

        # Keep answer small and non-trivial
        if not (2 <= answer_val <= 100):
            continue

        return {
            "base": b,
            "p": p,
            "k": k,
            "m": m,
            "a": a,
            "c": c,
            "d": d,
            "denom_base": b**p,  # (b^p)^n form for template display
            "answer": sympy.Integer(answer_val),
        }


exponent_variable_simplify = Problem(
    id="exponent_variable_simplify",
    type_id="exponent_laws",
    name="Simplify an exponential expression with a variable exponent",
    artifact_type="practice",
    problem_spec=_gen_variable_simplify,
    verifier_spec={"kind": "symbolic_equality", "marks_possible": 1},
)


# ---------------------------------------------------------------------------
# 2. exponent_algebraic_simplify
#    (C^k · x^(k·a))^(−1/k) · B · x^(−a) − x^(−2a)  →  t · x^(−2a)
# ---------------------------------------------------------------------------


def _gen_algebraic_simplify(rng: random.Random) -> dict:
    while True:
        k = rng.choice([2, 3])  # square or cube root
        C = rng.choice([2, 3, 4])
        a = rng.choice([2, 3, 4, 6])

        if k * a > 12:  # keep displayed exponents readable
            continue

        t = rng.randint(0, 3)  # answer coefficient; 0 → answer is 0
        B = C * (1 + t)

        answer_expr = sympy.Integer(t) * _x ** sympy.Integer(-2 * a)

        return {
            "C": C,
            "Ck": C**k,  # displayed as the coefficient: (Ck · x^ka)^(−1/k)
            "k": k,
            "a": a,
            "ka": k * a,
            "B": B,
            "t": t,
            "answer": answer_expr,
        }


exponent_algebraic_simplify = Problem(
    id="exponent_algebraic_simplify",
    type_id="exponent_laws",
    name="Simplify an expression with a negative fractional exponent",
    artifact_type="practice",
    problem_spec=_gen_algebraic_simplify,
    verifier_spec={"kind": "symbolic_equality", "marks_possible": 1},
)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    all_problems = {
        p.id: p for p in [exponent_variable_simplify, exponent_algebraic_simplify]
    }
    engine = Engine(registry=InMemoryRegistry(all_problems))

    def show(label, instance, answer):
        attempt = SolutionAttempt(steps=[SubmittedStep(answer)])
        r = instance.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  is_correct={r.is_correct}"
        )

    # --- exponent_variable_simplify ---
    print("=== exponent_variable_simplify ===")
    inst = engine.instantiate(exponent_variable_simplify.id, seed=42)
    p = inst.params
    # Display as: (k·b^(pn+a) − m·b^(pn+c)) / (denom_base)^n · b^d
    print(
        f"  ({p['k']}·{p['base']}^({p['p']}n+{p['a']}) − {p['m']}·{p['base']}^({p['p']}n+{p['c']}))"
        f" / ({p['denom_base']}^n · {p['base']}^{p['d']})"
    )
    print(f"  Canonical: {inst.verifier.canonicals[0]}")
    ans = int(inst.verifier.canonicals[0])
    show("Correct answer              ", inst, ans)
    show("Off by one                  ", inst, ans + 1)
    show("Equivalent SymPy expression ", inst, sympy.Integer(ans))

    print()

    # --- exponent_algebraic_simplify (exam-like: t=0, answer=0) ---
    print("=== exponent_algebraic_simplify (exam replica: seed for t=0) ===")
    # Seed 1 gives the t=0 (answer=0) variant; adjust if needed
    for seed in range(1, 20):
        inst = engine.instantiate(exponent_algebraic_simplify.id, seed=seed)
        if inst.params["t"] == 0:
            break
    p = inst.params
    print(
        f"  ({p['Ck']}x^{p['ka']})^(−1/{p['k']}) × {p['B']}x^(−{p['a']}) − x^(−{2 * p['a']})"
    )
    print(f"  Canonical: {inst.verifier.canonicals[0]}")
    show("Answer 0 (correct)          ", inst, 0)
    show("Answer x^(-8) (wrong)       ", inst, _x ** (-2 * p["a"]))

    print()

    # --- exponent_algebraic_simplify (non-zero answer) ---
    print("=== exponent_algebraic_simplify (non-zero answer) ===")
    for seed in range(1, 30):
        inst = engine.instantiate(exponent_algebraic_simplify.id, seed=seed)
        if inst.params["t"] >= 1:
            break
    p = inst.params
    print(
        f"  ({p['Ck']}x^{p['ka']})^(−1/{p['k']}) × {p['B']}x^(−{p['a']}) − x^(−{2 * p['a']})"
    )
    print(f"  Canonical: {inst.verifier.canonicals[0]}")
    canonical = inst.verifier.canonicals[0]
    show("Correct answer              ", inst, canonical)
    show("Coefficient off by one      ", inst, (p["t"] + 1) * _x ** (-2 * p["a"]))
