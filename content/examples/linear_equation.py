"""
Reference example: single-step linear equation (symbolic_equality).

Design decisions demonstrated:
- Code generator is the right tool when the answer must be computed from
  the question params (here: x = b - a). Dict specs can only draw ranges;
  they cannot derive one value from another.
- The generator puts `answer` in params explicitly. Without it, symbolic_equality
  would pick the first param by insertion order — fragile and non-obvious.
  Params that exist to render the question (a, b) and params that ARE the answer
  (x) should be distinguished by name, not position.
- `a` and `b` stay in params even though the verifier only needs `answer`.
  A downstream consumer (PDF renderer, SRS card) needs to know the full
  equation "x + 5 = 15" to display the question; storing only the answer
  would make reconstruction impossible.
"""

from __future__ import annotations

import random

from problem_instantiation_tool.schemas import Problem

_PROBLEM_SPEC = {
    "kind": "linear_add_pos",
    "a_range": [1, 15],
    "x_range": [-10, 10],
}


def _generate(rng: random.Random) -> dict:
    a = rng.randint(1, 15)
    x = rng.randint(-10, 10)
    return {"a": a, "b": x + a, "answer": x}


problem = Problem(
    id="linear_add_pos",
    type_id="linear_equation",
    name="Subtract a positive constant to isolate x  (x + a = b)",
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
    print(f"Question : x + {p['a']} = {p['b']}")
    print(f"Params   : {p}")
    print(f"Canonical: {instance.verifier.canonicals[0]}")

    correct = SolutionAttempt(steps=[SubmittedStep(p["answer"])])
    wrong = SolutionAttempt(steps=[SubmittedStep(p["answer"] + 1)])
    print(f"Correct  : {instance.verifier.rate(correct).is_correct}")
    print(f"Wrong    : {instance.verifier.rate(wrong).is_correct}")
