"""
Q1 Algebra Extensions, archetype 4 — ``nonlinear_simultaneous``.

Solve the system  y = m·x + k  (linear)  and  y = x² + p·x + q  (parabola)
simultaneously. Equating the two right-hand sides collapses the system to a
single quadratic in x; its two roots are the x-coordinates, and each must be
back-substituted into the *linear* equation to recover its partner y. The
assessed skill — the one students lose marks on — is **presenting BOTH complete
(x, y) pairs**, correctly paired, not just the two x-values. So the answer is
decomposed into the two decisions a marker rewards:

  1. the **x-values** — roots of the equated quadratic
     (``set_equality``, 2 marks, partial credit), and
  2. the **solution pairs** — each x paired with its own y, both presented
     (``set_equality``, 2 marks, partial credit: one complete pair is half).

The pair is encoded as a tuple ``(x, y)``; ``set_equality`` compares these by
plain Python equality, so a pair scores only when *both* coordinates match — the
faithful "did you pair correctly?" test. This is the first archetype whose answer
element is a **compound value**, not a scalar (see memory
``project-quadratic-inequality-region-signal``).

**Construction (backward, so both pairs are clean integers).** Pick the two
integer x-roots x₁ < x₂ and a linear equation y = m·x + k; that fixes both
y-values. The parabola is then forced through both points: passing y = x²+p·x+q
through (xᵢ, yᵢ) gives p = m − (x₁+x₂) and q = y₁ − x₁² − p·x₁, both integers. The
slope m is drawn non-zero so the line is genuinely oblique (a horizontal line
would make the two y-values coincide and hide the pairing skill).
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

_x, _y = sympy.symbols("x y")


def _gen(rng: random.Random) -> dict:
    x1 = rng.randint(-5, 5)
    x2 = rng.randint(-5, 5)
    while x2 == x1:
        x2 = rng.randint(-5, 5)
    x1, x2 = sorted((x1, x2))

    m = rng.choice([-2, -1, 1, 2])  # non-zero: a genuinely oblique line
    k = rng.randint(-5, 5)

    y1 = m * x1 + k
    y2 = m * x2 + k

    # Force y = x² + p·x + q through both (xᵢ, yᵢ).
    p = m - (x1 + x2)
    q = y1 - x1**2 - p * x1

    line_expr = m * _x + k
    parabola_expr = _x**2 + p * _x + q

    return {
        "m": m,
        "k": k,
        "p": p,
        "q": q,
        "x_values": frozenset({x1, x2}),
        "solution_pairs": frozenset({(x1, y1), (x2, y2)}),
        "line_latex": sympy.latex(sympy.Eq(_y, line_expr)),
        "parabola_latex": sympy.latex(sympy.Eq(_y, parabola_expr)),
    }


nonlinear_simultaneous = Problem(
    id="nonlinear_simultaneous",
    type_id="nonlinear_simultaneous",
    name="Solve a linear–quadratic system (find both (x,y) pairs)",
    artifact_type="practice",
    problem_spec=_gen,
    verifier_spec=[
        {"kind": "set_equality", "marks_possible": 2, "param_key": "x_values"},
        {"kind": "set_equality", "marks_possible": 2, "param_key": "solution_pairs"},
    ],
    corpus_anchor=CorpusAnchor(
        paper="2024 Nov P1",
        question="1.2",
        # marks left unset: the paper's 5th mark is the substitution-setup method
        # line (equate the two RHS), which an answer-grading engine can't allocate
        # until Level-2 per-line marks land. We grade the four answer-values:
        # x-values (2) + complete pairs (2).
    ),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(
        registry=InMemoryRegistry({nonlinear_simultaneous.id: nonlinear_simultaneous})
    )

    def show(label, inst, *answers):
        attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
        r = inst.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  "
            f"is_correct={r.is_correct}"
        )

    for seed in (1, 4, 9):
        inst = engine.instantiate(nonlinear_simultaneous.id, seed=seed)
        p = inst.params
        print(f"=== seed {seed} ===")
        print(f"  Solve  : {p['line_latex']}   and   {p['parabola_latex']}")
        print(f"  x-values: {sorted(p['x_values'])}")
        print(f"  Pairs   : {sorted(p['solution_pairs'])}")
        show("Both pairs correct  ", inst, p["x_values"], p["solution_pairs"])
        # found the x's but never computed y (a common lost-mark path):
        show("x-values only, no y ", inst, p["x_values"], p["x_values"])
        # one complete pair only:
        one_pair = frozenset({min(p["solution_pairs"])})
        show("One pair only       ", inst, p["x_values"], one_pair)
