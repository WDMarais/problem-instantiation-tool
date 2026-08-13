"""
Calculus, archetype 1 — ``derivative_first_principles``.

Given  f(x) = a·x² + b·x + c,  find  f′(x)  **from first principles** — i.e. via
the limit definition

    f′(x) = lim_{h→0}  [ f(x+h) − f(x) ] / h .

The whole point of the question is the *method*: a student who simply applies the
power rule and writes ``f′(x) = 2ax + b`` has produced the right answer by the
wrong means and, in a real exam, earns almost nothing. So checking the final
derivative alone would be an unfaithful auto-marker — it would reward exactly the
shortcut the question forbids. Instead the answer is decomposed into the two
things a marker actually rewards:

  1. the **simplified difference quotient**  [f(x+h) − f(x)] / h  =  2ax + ah + b
     — an expression in *both* x and h, which can only be produced by doing the
     substitution, expansion, subtraction and division (``symbolic_equality``,
     3 marks); and
  2. the **derivative**  f′(x) = 2ax + b  — the h→0 limit of (1)
     (``symbolic_equality``, 2 marks).

The constant ``c`` deliberately survives into f(x) but vanishes from both the
quotient and the derivative, so the instance also exercises "the constant term
differentiates away". Both the quotient and the derivative are computed with
sympy (limit/expansion), never hand-derived, so the same generator would extend
unchanged to a simple cubic.

The full limit-notation *working* for the memo (retaining ``lim`` at each line,
which carries method marks a symbolic check cannot see) is a rendering concern,
deferred with the rest of the answer-key prose spine.
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

_x, _h = sympy.symbols("x h")


def _gen(rng: random.Random) -> dict:
    a = rng.choice([-3, -2, -1, 1, 2, 3])  # a ≠ 0 — genuinely quadratic
    b = rng.randint(-6, 6)
    c = rng.randint(-6, 6)

    f = a * _x**2 + b * _x + c
    # difference quotient BEFORE the limit — cancels the h in the denominator.
    quotient = sympy.simplify((f.subs(_x, _x + _h) - f) / _h)
    derivative = sympy.diff(f, _x)

    return {
        "a": a,
        "b": b,
        "c": c,
        "function_latex": rf"f(x) = {sympy.latex(f)}",
        "quotient": quotient,  # 2ax + ah + b, in x and h
        "derivative": derivative,  # 2ax + b
        "derivative_latex": sympy.latex(derivative),
    }


derivative_first_principles = Problem(
    id="derivative_first_principles",
    type_id="derivative_first_principles",
    name="Differentiate a quadratic from first principles (limit definition)",
    artifact_type="practice",
    problem_spec=_gen,
    verifier_spec=[
        {
            "kind": "symbolic_equality",
            "marks_possible": 3,
            "param_key": "quotient",
        },
        {
            "kind": "symbolic_equality",
            "marks_possible": 2,
            "param_key": "derivative",
        },
    ],
    corpus_anchor=CorpusAnchor(
        paper="2024 Nov P1",
        question="8.3.1",
        marks=5,  # difference quotient (3) + limit to f′(x) (2)
    ),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(
        registry=InMemoryRegistry(
            {derivative_first_principles.id: derivative_first_principles}
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
        inst = engine.instantiate(derivative_first_principles.id, seed=seed)
        p = inst.params
        print(f"=== seed {seed} ===")
        print(f"  {p['function_latex']}")
        print(f"  quotient   = {p['quotient']}")
        print(f"  f'(x)      = {p['derivative']}")
        show("both correct       ", inst, p["quotient"], p["derivative"])
        show("only f'(x) (power) ", inst, p["derivative"], p["derivative"])
        show("quotient only      ", inst, p["quotient"], p["quotient"])
