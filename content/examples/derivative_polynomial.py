"""
Calculus, archetype 2a — ``derivative_polynomial``.

Differentiate a plain polynomial by the power rule — every term is already a
power  a·xⁿ  with a whole-number exponent, so no surd/quotient rewrite is needed
(that is the sibling ``derivative_rules`` archetype). This is the routine
"d/dx [ … ]" ask: apply  d/dx xⁿ = n·xⁿ⁻¹  term by term. The NSC prints it as a
short 2-mark warm-up (source 8.2.1: d/dx[3x² − 4x] = 6x − 4).

The only engine-checkable value is the derivative, checked with
``symbolic_equality`` so any algebraically-equal form the student writes is
accepted. A constant term is always present and vanishes from f′, exercising
"the constant differentiates away". The derivative is computed with sympy, never
hand-derived.
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

_x = sympy.Symbol("x")


def _gen(rng: random.Random) -> dict:
    # top term degree 2 or 3 — genuinely a polynomial, never linear
    top_deg = rng.choice([2, 3])
    a_top = rng.choice([-4, -3, -2, 2, 3, 4])  # nonzero leading coefficient
    a_mid = rng.choice([-5, -4, -3, -2, 2, 3, 4, 5])  # the x^{deg-1} term, nonzero
    a_lin = rng.randint(-6, 6)  # the linear term (may be 0)
    const = rng.choice([-9, -7, -5, -3, 3, 5, 7, 9])  # nonzero; drops in f′

    f = a_top * _x**top_deg + a_mid * _x ** (top_deg - 1) + a_lin * _x + const
    derivative = sympy.diff(f, _x)

    return {
        "top_deg": top_deg,
        "a_top": a_top,
        "a_mid": a_mid,
        "a_lin": a_lin,
        "const": const,
        "function_latex": rf"{sympy.latex(f)}",
        "derivative": derivative,
        "derivative_latex": sympy.latex(derivative),
    }


derivative_polynomial = Problem(
    id="derivative_polynomial",
    type_id="derivative_polynomial",
    name="Differentiate a plain polynomial by the power rule",
    artifact_type="practice",
    problem_spec=_gen,
    verifier_spec={
        "kind": "symbolic_equality",
        "marks_possible": 2,
        "param_key": "derivative",
    },
    corpus_anchor=CorpusAnchor(
        paper="2025 May/June P1",
        question="8.2.1",
        marks=2,
    ),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(
        registry=InMemoryRegistry({derivative_polynomial.id: derivative_polynomial})
    )

    def show(label, inst, *answers):
        attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
        r = inst.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  "
            f"is_correct={r.is_correct}"
        )

    for seed in range(3):
        inst = engine.instantiate(derivative_polynomial.id, seed=seed)
        p = inst.params
        print(f"=== seed {seed} ===")
        print(f"  f(x) = {p['function_latex']}")
        print(f"  f'(x) = {p['derivative']}")
        show("correct           ", inst, p["derivative"])
        show("forgot const drops", inst, p["derivative"] + p["const"])
