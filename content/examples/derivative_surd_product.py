"""
Calculus, archetype 2b — ``derivative_surd_product``.

Differentiate  g(x) = c·√x·(x − r)²  — a product of a surd and a squared binomial
that the power rule cannot touch until it is **multiplied out and rewritten as a
sum of powers**:

    c·√x·(x − r)²  =  c·x^{5/2} − 2rc·x^{3/2} + r²c·x^{1/2}
    g′(x)          =  (5/2)c·x^{3/2} − 3rc·x^{1/2} + (r²c/2)·x^{-1/2}.

Expanding the product and turning √x into x^{1/2} is the assessed skill; a student
who leaves the product or the surd in place cannot differentiate at all. As with
``derivative_rules`` the rewrite is not separately checkable (√x and x^{1/2} are
the *same* expression to sympy, so ``symbolic_equality`` cannot tell an expanded
line from the original product). What we can do is (a) always generate a genuine
surd-times-binomial product, and (b) check the final derivative with
``symbolic_equality``, which accepts any algebraically-equal form the student
writes (``x^{-1/2}`` or ``1/√x``, …). The NSC prints this as the 4-mark partner of
the plain power-rule warm-up (source 8.2.2: g(x) = −2√x(x − 1)²).

The expanded power form and the derivative are both computed with sympy, never
hand-derived.
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

_x = sympy.Symbol("x")


def _gen(rng: random.Random) -> dict:
    c = rng.choice([-3, -2, 2, 3])  # nonzero outer coefficient
    r = rng.choice([-2, -1, 1, 2])  # nonzero root → a genuine binomial (x − r)

    g = c * sympy.sqrt(_x) * (_x - r) ** 2
    expanded = sympy.expand(g)  # c·x^{5/2} − 2rc·x^{3/2} + r²c·x^{1/2}
    # differentiate the expanded power form so the stored derivative is the clean
    # sum-of-powers the memo shows (grades identically to the product-rule form)
    derivative = sympy.diff(expanded, _x)

    return {
        "c": c,
        "r": r,
        "function_latex": rf"g(x) = {sympy.latex(g)}",
        "expanded_latex": sympy.latex(expanded),
        "derivative": derivative,
        "derivative_latex": sympy.latex(derivative),
    }


derivative_surd_product = Problem(
    id="derivative_surd_product",
    type_id="derivative_surd_product",
    name="Differentiate a surd × squared-binomial product (expand to powers first)",
    artifact_type="practice",
    problem_spec=_gen,
    verifier_spec={
        "kind": "symbolic_equality",
        "marks_possible": 4,
        "param_key": "derivative",
    },
    corpus_anchor=CorpusAnchor(
        paper="2025 May/June P1",
        question="8.2.2",
        marks=4,
    ),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(
        registry=InMemoryRegistry({derivative_surd_product.id: derivative_surd_product})
    )

    def show(label, inst, *answers):
        attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
        r = inst.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  "
            f"is_correct={r.is_correct}"
        )

    for seed in range(3):
        inst = engine.instantiate(derivative_surd_product.id, seed=seed)
        p = inst.params
        print(f"=== seed {seed} ===")
        print(f"  {p['function_latex']}")
        print(f"  expanded = {p['expanded_latex']}")
        print(f"  g'(x)    = {p['derivative']}")
        show("correct", inst, p["derivative"])
