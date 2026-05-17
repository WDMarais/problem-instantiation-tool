"""
Reference example: monic quadratic factorisation (symbolic_equality).

Design decisions demonstrated:
- This is distinct from quadratic_roots.py. That generator starts from the
  factored form and asks for roots (set_equality); this one starts from the
  expanded form x² + bx + c and expects the factored form back. Both appear
  in Gr10 exams but test different competencies.
- The code generator is used (not a dict spec) because b and c must be derived
  from root1 and root2, and the guards (b == 0, c == 0) require derived values.
  Dict specs can only draw independent ranges.
- symbolic_equality accepts any algebraically equivalent expression. A student
  who submits the expanded form x² + bx + c is technically correct by sympy's
  simplify check. In practice this is rarely a problem: the question explicitly
  asks for the factored form, and a student who expands back is penalised by the
  exam rubric, not by this verifier. The verifier's job is mathematical
  correctness, not presentation.
- marks_possible=1 (all-or-nothing) to start. The partial credit case —
  student gets one factor right, fumbles the other — requires either a two-step
  verifier spec (one step per factor) or a custom set-of-factors verifier. Left
  for a later generator once the basic one is in use.
- b == 0 is excluded (that's the difference of two squares case: x² - c,
  a separate generator). c == 0 is excluded (trivial: one root is 0, the
  factored form is just x(x - r)).
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import Problem

_x = sympy.Symbol("x")


def _generate(rng: random.Random) -> dict:
    while True:
        root1 = rng.randint(-8, 8)
        root2 = rng.randint(-8, 8)
        b = -(root1 + root2)
        c = root1 * root2
        if b == 0 or c == 0:
            continue
        break

    return {
        "root1": root1,
        "root2": root2,
        "b": b,
        "c": c,
        "answer": (_x - root1) * (_x - root2),
    }


problem = Problem(
    id="monic_factorise",
    type_id="quadratic_expression",
    name="Factorise a monic quadratic  x² + bx + c",
    artifact_type="srs_card",
    problem_spec=_generate,
    verifier_spec={"kind": "symbolic_equality", "marks_possible": 1},
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(registry=InMemoryRegistry({problem.id: problem}))
    instance = engine.instantiate(problem.id, seed=42)
    p = instance.params
    b_str = f"+ {p['b']}x" if p["b"] >= 0 else f"- {abs(p['b'])}x"
    c_str = f"+ {p['c']}" if p["c"] >= 0 else f"- {abs(p['c'])}"
    print(f"Question : Factorise x² {b_str} {c_str}")
    print(f"Roots    : {p['root1']}, {p['root2']}")
    print(f"Canonical: {instance.verifier.canonicals[0]}")
    print()

    def show(label, answer):
        attempt = SolutionAttempt(steps=[SubmittedStep(answer)])
        r = instance.verifier.rate(attempt)
        print(
            f"{label}: {r.marks_awarded}/{r.marks_possible}  is_correct={r.is_correct}"
        )

    r1, r2 = p["root1"], p["root2"]
    show(f"Correct  (x - {r1})(x - {r2})         ", f"(x - {r1}) * (x - {r2})")
    show(f"Reversed (x - {r2})(x - {r1})         ", f"(x - {r2}) * (x - {r1})")
    show(f"Expanded x² {b_str} {c_str}            ", f"x**2 + {p['b']}*x + {p['c']}")
    show(f"Wrong root  (x - {r1})(x - {r2 + 1})  ", f"(x - {r1}) * (x - {r2 + 1})")
