"""
Calculus, archetype 5 — ``optimisation_solve``.

A quantity is **given** as  Q(x) = a·x + b/x  (x > 0) — a cost/material-type
function whose "show that Q(x) = …" derivation is the resistant (class-c) setup we
deliberately skip. The assessed, class-b step is the optimisation itself:
differentiate, solve Q′(x) = 0, and report the minimum. For a, b > 0 the function
has a single global minimum at x = √(b/a).

The answer is decomposed to mirror the DBE mark split:

  1. the **derivative**  Q′(x) = a − b/x²  (``symbolic_equality``, 1 mark) — note
     the b/x² term must be rewritten as b·x⁻² to differentiate, as in
     ``derivative_rules``;
  2. the **optimal x**  x = √(b/a)  (``numeric_equality``, 1 mark) — solving
     Q′(x) = 0 and keeping the positive root; and
  3. the **minimum value**  Q(x) = 2·a·√(b/a)  (``numeric_equality``, 1 mark).

**Construction** is backward from a clean optimum: choose a and the integer
optimal x = m, set b = a·m² so √(b/a) = m exactly; the minimum value is then
a·m + b/m = 2·a·m, also an integer. Q″(x) = 2b/x³ > 0 on the domain, so the
stationary point is always the minimum (no max/min ambiguity to resolve).
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

_x = sympy.Symbol("x", positive=True)


def _gen(rng: random.Random) -> dict:
    a = rng.randint(2, 6)
    m = rng.randint(2, 6)  # the optimal x
    b = a * m * m  # so √(b/a) = m exactly

    q = a * _x + sympy.Integer(b) / _x
    derivative = sympy.diff(q, _x)  # a − b/x²
    optimal_value = int(q.subs(_x, m))  # 2·a·m

    return {
        "a": a,
        "b": b,
        "optimal_x": m,
        "optimal_value": optimal_value,
        "derivative": derivative,
        "function_latex": rf"Q(x) = {sympy.latex(q)}",
        "derivative_latex": sympy.latex(derivative),
    }


optimisation_solve = Problem(
    id="optimisation_solve",
    type_id="optimisation_solve",
    name="Minimise a given quantity Q(x)=ax+b/x (differentiate, solve Q′=0)",
    artifact_type="practice",
    problem_spec=_gen,
    verifier_spec=[
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "derivative"},
        {"kind": "numeric_equality", "marks_possible": 1, "param_key": "optimal_x"},
        {"kind": "numeric_equality", "marks_possible": 1, "param_key": "optimal_value"},
    ],
    corpus_anchor=CorpusAnchor(
        paper="2023 Nov P1",
        question="9.2",
        marks=3,  # Q′(x) (1) + solve for x (1) + minimum value (1)
    ),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(
        registry=InMemoryRegistry({optimisation_solve.id: optimisation_solve})
    )

    def show(label, inst, *answers):
        attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
        r = inst.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  "
            f"is_correct={r.is_correct}"
        )

    for seed in range(3):
        inst = engine.instantiate(optimisation_solve.id, seed=seed)
        p = inst.params
        print(f"=== seed {seed} ===")
        print(f"  {p['function_latex']},  x > 0")
        print(
            f"  Q'(x) = {p['derivative']}   x* = {p['optimal_x']}   "
            f"min = {p['optimal_value']}"
        )
        show(
            "all correct        ",
            inst,
            p["derivative"],
            p["optimal_x"],
            p["optimal_value"],
        )
        show(
            "deriv+x, wrong min ",
            inst,
            p["derivative"],
            p["optimal_x"],
            p["optimal_value"] + 1,
        )
