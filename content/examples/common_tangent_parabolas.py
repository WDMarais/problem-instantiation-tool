"""
Calculus, archetype 3b — ``common_tangent_parabolas``.

A line  y = m·x + k  is a **common tangent** to two parabolas — it touches
f(x) = A·x² + B·x + C  and  g(x) = a·x² + b·x + c₀  **at the same point** — and
f, the line and g's constant term c₀ are given; find the unknown a and b (source
8.3: y = 4x − 14 tangent to f = 2x² − 4x − 6 and g = ax² + bx − 18 ⇒ a = −1, b = 8).

The method a marker rewards:

  1. differentiate f and use the line's gradient to locate the point of tangency
     on f:  f′(x_t) = m ⇒ x_t,  y_t = f(x_t);
  2. impose that g touches the *same* point with the *same* gradient —
        g′(x_t) = 2a·x_t + b = m   and   g(x_t) = a·x_t² + b·x_t + c₀ = y_t —
     a 2×2 linear system whose unique solution is a and b.

Only the two answer values a and b are engine-checkable (``numeric_equality``,
1 mark each); the differentiation, the point of tangency and the setup of the
system are method the paper layer marks by hand (the slot declares auto_marks = 2
against its 6 headline marks). The instance is *constructed forward* from a chosen
touch point x_t and a chosen leading coefficient a, so g is always a genuine
parabola and a, b come out integer — there is no ill-posed draw, hence no F1
scope predicate (as with the other forward-well-posed calculus reports).
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

_x, _y = sympy.symbols("x y")


def _gen(rng: random.Random) -> dict:
    A = rng.choice([-2, -1, 1, 2])  # f leading coefficient, nonzero
    B = rng.randint(-6, 6)
    C = rng.randint(-9, 9)
    x_t = rng.choice([-3, -2, -1, 1, 2, 3])  # common touch point (nonzero)
    # g leading coefficient — the answer a; a ≠ A so g is a genuinely different
    # parabola (a == A forces g ≡ f, a degenerate "common tangent")
    a = rng.choice([c for c in (-3, -2, -1, 1, 2, 3) if c != A])

    m = 2 * A * x_t + B  # common tangent gradient = f′(x_t)
    y_t = A * x_t**2 + B * x_t + C  # touch point y = f(x_t)
    k = y_t - m * x_t  # tangent line intercept
    b = m - 2 * a * x_t  # from g′(x_t) = m
    c0 = k + a * x_t**2  # from g(x_t) = y_t  (given constant of g)

    f = A * _x**2 + B * _x + C
    g = a * _x**2 + b * _x + c0
    line = m * _x + k

    return {
        "A": A,
        "B": B,
        "C": C,
        "x_t": x_t,
        "m": m,
        "k": k,
        "y_t": y_t,
        "c0": c0,
        "a": a,  # answer
        "b": b,  # answer
        "f_latex": rf"f(x) = {sympy.latex(f)}",
        "g_latex": rf"g(x) = {sympy.latex(g)}",
        "line_latex": sympy.latex(sympy.Eq(_y, line)),
        "f_prime_latex": sympy.latex(sympy.diff(f, _x)),
    }


common_tangent_parabolas = Problem(
    id="common_tangent_parabolas",
    type_id="common_tangent_parabolas",
    name="Common tangent to two parabolas — solve for the unknown coefficients a, b",
    artifact_type="practice",
    problem_spec=_gen,
    verifier_spec=[
        {"kind": "numeric_equality", "marks_possible": 1, "param_key": "a"},
        {"kind": "numeric_equality", "marks_possible": 1, "param_key": "b"},
    ],
    corpus_anchor=CorpusAnchor(
        paper="2025 May/June P1",
        question="8.3",
        marks=6,  # method (find touch point, form + solve system) + the two answers
    ),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(
        registry=InMemoryRegistry(
            {common_tangent_parabolas.id: common_tangent_parabolas}
        )
    )

    def show(label, inst, *answers):
        attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
        r = inst.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  "
            f"is_correct={r.is_correct}"
        )

    for seed in range(3):
        inst = engine.instantiate(common_tangent_parabolas.id, seed=seed)
        p = inst.params
        print(f"=== seed {seed} ===")
        print(f"  {p['f_latex']}")
        print(f"  {p['g_latex']}   (a, b unknown; c0 = {p['c0']} given)")
        print(f"  common tangent: {p['line_latex']}")
        print(f"  a = {p['a']},  b = {p['b']}")
        show("both correct", inst, p["a"], p["b"])
        show("a right, b wrong", inst, p["a"], p["b"] + 1)
