"""
Reference example: quadratic factoring (set_equality, partial credit).

Design decisions demonstrated:
- set_equality is the right verifier when the answer is an unordered collection.
  A student who writes (x-3)(x+5)=0 first and (x+5)(x-3)=0 second has the
  same understanding; penalising ordering is a display artefact, not a
  mathematical distinction.
- marks_possible=2 (one per root) enables partial credit by default. A student
  who finds one root correctly but fumbles arithmetic on the other demonstrates
  real understanding of factoring; giving them 0/2 overstates the error.
  Set partial_credit=False to get all-or-nothing if needed (e.g. high-stakes
  marking where partial answers are not acceptable).
- Partial credit only activates when marks_possible > 1. marks_possible=1
  treats the whole set as an atomic answer and is always all-or-nothing,
  regardless of the partial_credit flag.
- The dict spec is sufficient here because root_range draws root1 and root2
  independently — no computation between params is needed. Code generators
  are only necessary when one param is derived from another (see linear_equation.py).
- leading_coeff is in params but not in the answer. set_equality extracts all
  keys starting with "root*"; leading_coeff is correctly ignored. A consumer
  rendering "2(x-3)(x+5)=0" needs leading_coeff; the verifier does not.
- root_range is a special-cased key in the dict generator: it produces root1
  and root2, not a single "root" param. Any other *_range key produces one param
  named by stripping "_range" (so leading_coeff_range → leading_coeff).
"""

from problem_instantiation_tool.schemas import Problem

problem = Problem(
    id="quadratic_factor",
    type_id="quadratic_equation",
    name="Solve a factorisable quadratic  a(x − r₁)(x − r₂) = 0",
    artifact_type="srs_card",
    problem_spec={
        "kind": "quadratic_factor",
        "root_range": [-10, 10],
        "leading_coeff_range": [1, 3],
    },
    verifier_spec={"kind": "set_equality", "marks_possible": 2},
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(registry=InMemoryRegistry({problem.id: problem}))
    instance = engine.instantiate(problem.id, seed=42)
    p = instance.params
    r1, r2 = p["root1"], p["root2"]
    print(f"Question : {p['leading_coeff']}(x − {r1})(x − {r2}) = 0")
    print(f"Params   : {p}")
    print(f"Canonical: {instance.verifier.canonicals[0]}")

    both_correct = SolutionAttempt(steps=[SubmittedStep(frozenset({r1, r2}))])
    one_correct = SolutionAttempt(steps=[SubmittedStep(frozenset({r1, r2 + 1}))])
    both_wrong = SolutionAttempt(steps=[SubmittedStep(frozenset({r1 + 1, r2 + 1}))])

    for label, attempt in [
        ("Both correct", both_correct),
        ("One correct ", one_correct),
        ("Both wrong  ", both_wrong),
    ]:
        r = instance.verifier.rate(attempt)
        print(
            f"{label}: {r.marks_awarded}/{r.marks_possible}  "
            f"is_correct={r.is_correct}  "
            f"mistake={r.steps[0].mistake_type}"
        )
