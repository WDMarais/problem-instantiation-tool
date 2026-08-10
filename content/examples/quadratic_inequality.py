"""
Q1 Algebra Extensions, archetype 1 — ``quadratic_inequality``.

Solve  a·x² + b·x + c  {<, ≤, >, ≥} 0.  The assessed skill is NOT the algebra of
finding the roots (that is ``quadratic_roots``, already built) — it is the
**sign analysis** that turns two critical values into a region. So the answer is
decomposed into the two decisions a marker actually rewards:

  1. the **critical values** — the roots of a·x² + b·x + c = 0
     (``set_equality``, 2 marks, partial credit: one root right is half the skill), and
  2. the **region** — "between" the critical values (a bounded interval) or
     "outside" them (a union of two rays) (``exact_equality``, 1 mark).

Two distinct sub-skills, two verifier steps, 3 marks total — matching the DBE
Q1.1.x quadratic-inequality item.

**Why "region" and not the interval itself.** The honest answer is a solution
*set* — an ``Interval`` or a ``Union`` of them. The engine has no set-answer
verifier, and ``symbolic_equality`` mis-handles SymPy ``Set`` objects
(``simplify(Interval(2,3) - Interval(2,3))`` is ``EmptySet``, and
``EmptySet == 0`` is ``False`` → a false negative on a *correct* answer). So the
region is captured as a categorical label — the exact sign-analysis decision —
while the memo still renders the full interval notation for the tutee. This
value-plus-categorical-reason shape is the ``value_and_reason`` verifier in
embryo: the region is a *structural reason* a plain value verifier can't express.
See memory ``project-quadratic-inequality-region-signal``.

**The sign-analysis guard — the whole point of the family.** The region does not
follow from the critical values alone: it flips with both the inequality
direction *and* the sign of ``a``. A downward parabola (a < 0) that is "> 0"
holds *between* its roots, not outside. That flip is where students lose the
mark, so the generator draws a < 0 as often as a > 0 to exercise it.
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

_x = sympy.Symbol("x")

# direction → (LaTeX relation symbol, wants the polynomial positive?)
_DIRECTIONS = {
    "<": (r"<", False),
    "<=": (r"\le", False),
    ">": (r">", True),
    ">=": (r"\ge", True),
}


def _gen(rng: random.Random) -> dict:
    # Distinct integer critical values: two *different* real roots is the scope
    # this archetype teaches (a double root / no-real-root is a separate skill).
    r1 = rng.randint(-8, 8)
    r2 = rng.randint(-8, 8)
    while r2 == r1:
        r2 = rng.randint(-8, 8)
    lo, hi = sorted((r1, r2))

    a = rng.choice([-2, -1, 1, 2])
    direction = rng.choice(list(_DIRECTIONS))
    rel_latex, wants_positive = _DIRECTIONS[direction]

    # Expanded coefficients of a·(x − lo)·(x − hi).
    expr = sympy.expand(a * (_x - lo) * (_x - hi))
    b = int(expr.coeff(_x, 1))
    c = int(expr.coeff(_x, 0))

    # Sign analysis. A parabola is positive OUTSIDE its roots when it opens up
    # (a > 0) and positive BETWEEN them when it opens down (a < 0). So the sought
    # region is "outside" exactly when the wanted sign matches the opening.
    region = "outside" if (wants_positive == (a > 0)) else "between"
    closed = direction in ("<=", ">=")

    if region == "between":
        rel = r"\le" if closed else "<"
        solution_latex = rf"{lo} {rel} x {rel} {hi}"
    else:  # outside: two rays
        left = r"\le" if closed else "<"
        right = r"\ge" if closed else ">"
        solution_latex = rf"x {left} {lo} \;\text{{ or }}\; x {right} {hi}"

    return {
        "a": a,
        "b": b,
        "c": c,
        "root1": lo,
        "root2": hi,
        "critical_values": frozenset({lo, hi}),
        "direction": direction,
        "polynomial_latex": rf"{sympy.latex(expr)} {rel_latex} 0",
        "region": region,
        "closed": closed,
        "solution_latex": solution_latex,
    }


quadratic_inequality = Problem(
    id="quadratic_inequality",
    type_id="quadratic_inequality",
    name="Solve a quadratic inequality  ax² + bx + c ⧠ 0  (critical values + region)",
    artifact_type="practice",
    problem_spec=_gen,
    verifier_spec=[
        {"kind": "set_equality", "marks_possible": 2, "param_key": "critical_values"},
        {"kind": "exact_equality", "marks_possible": 1, "param_key": "region"},
    ],
    corpus_anchor=CorpusAnchor(
        paper="2025 May/June P1",
        question="1.1.4",
        marks=3,  # critical values (2) + sign-analysis region (1)
    ),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(
        registry=InMemoryRegistry({quadratic_inequality.id: quadratic_inequality})
    )

    def show(label, inst, *answers):
        attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
        r = inst.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  "
            f"is_correct={r.is_correct}"
        )

    for seed in (1, 7, 13):
        inst = engine.instantiate(quadratic_inequality.id, seed=seed)
        p = inst.params
        print(f"=== seed {seed} ===")
        print(f"  Solve    : {p['polynomial_latex']}")
        print(f"  Criticals: {sorted(p['critical_values'])}   Region: {p['region']}")
        print(f"  Solution : {p['solution_latex']}")
        show("Fully correct       ", inst, p["critical_values"], p["region"])
        show("One critical value  ", inst, frozenset({p["root1"]}), p["region"])
        wrong_region = "between" if p["region"] == "outside" else "outside"
        show("Right roots, region✗", inst, p["critical_values"], wrong_region)
        show("All wrong           ", inst, frozenset({99, 100}), wrong_region)
