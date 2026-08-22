"""
Functions & Graphs — ``parabola_from_graph``.

Determine the equation of a parabola from its sketch. The sketch labels the two
x-intercepts and the y-intercept; the student writes the factored form
``a(x - r1)(x - r2)``, uses the y-intercept to pin the leading coefficient ``a``,
and expands. Graded on the expanded polynomial (``symbolic_equality``, 3 marks:
factored form, solve a, expand).

**Forward read-off, so wire-only (no F1 gate).** The equation is fully pinned by
the presented intercepts — the x-intercepts give the factors and the y-intercept
gives ``a`` — and because both roots are nonzero the y-intercept ``a·r1·r2`` is
always nonzero, so ``a`` is always recoverable. There is no draw that makes the
ask ill-posed, so gating would be tautological (cf. the sharpened F1 rule: forward
read-off → wire-only; only backward-constructed well-posedness needs a gate). This
sits in the same class as ``trig_graph_amplitude`` ("from the graph, state a, b").

Display-only (see ``render/DESIGN.md``): the generator bakes the whole equation;
the sketch is drawn *from* the baked roots and coefficient, never measured.
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

_x = sympy.Symbol("x")


def _gen(rng: random.Random) -> dict:
    # Distinct nonzero integer roots keep the y-intercept (a·r1·r2) nonzero, so
    # `a` is always recoverable. Small range keeps the sketch window legible (a
    # real viewport constraint, not a cosmetic answer-band limit).
    choices = [-4, -3, -2, -1, 1, 2, 3, 4]
    r1 = rng.choice(choices)
    r2 = rng.choice(choices)
    while r2 == r1:
        r2 = rng.choice(choices)
    r1, r2 = sorted((r1, r2))

    # a = 1 stays in play: rather than hide the "easy" case, the memo always runs
    # the coefficient-pinning step (f(0) = a·r1·r2 ⟹ a = …), so a = 1 is a value
    # the student *verifies* from the y-intercept, not one they assume by reading
    # the roots and multiplying. Keeping it in also stops the leading coefficient
    # from silently signalling "never 1", which would itself be a giveaway.
    a = rng.choice([-3, -2, -1, 1, 2, 3])
    answer = sympy.expand(a * (_x - r1) * (_x - r2))
    y_intercept = a * r1 * r2  # f(0), the coefficient-pinning point

    return {
        "a": a,
        "root1": r1,
        "root2": r2,
        "y_intercept": y_intercept,
        "answer": answer,  # expanded ax² + bx + c, graded by symbolic_equality
    }


parabola_from_graph = Problem(
    id="parabola_from_graph",
    type_id="parabola_from_graph",
    name="Determine the equation of a parabola from its sketch (intercepts given)",
    artifact_type="practice",
    problem_spec=_gen,
    verifier_spec={
        "kind": "symbolic_equality",
        "marks_possible": 3,  # factored form + solve for a + expand
        "param_key": "answer",
    },
    corpus_anchor=CorpusAnchor(
        paper="2025 May/June P1",
        question="4.1",  # determine-the-equation-of-the-graph item
        marks=3,
    ),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(
        registry=InMemoryRegistry({parabola_from_graph.id: parabola_from_graph})
    )

    def show(label, inst, *answers):
        attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
        r = inst.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  "
            f"is_correct={r.is_correct}"
        )

    for seed in (1, 7, 13):
        inst = engine.instantiate(parabola_from_graph.id, seed=seed)
        p = inst.params
        print(f"=== seed {seed} ===")
        print(
            f"  roots {p['root1']}, {p['root2']}   a={p['a']}   "
            f"y-int={p['y_intercept']}"
        )
        print(f"  answer: f(x) = {sympy.latex(p['answer'])}")
        show("Correct        ", inst, p["answer"])
        show(
            "Forgot a (a=1) ", inst, sympy.expand((_x - p["root1"]) * (_x - p["root2"]))
        )
