"""
The ``set_solution`` step — grade an answer that is a solution *set* (an
``Interval`` or a ``Union`` of them), not a single value. This is what an
inequality's answer actually is, and the reason it needs its own kind: SymPy
``Set`` objects break ``symbolic_equality`` (``simplify(A - A)`` is ``EmptySet``
and ``EmptySet == 0`` is ``False`` → a false negative on a *correct* answer), so
equality is done by mutual subset. Endpoint openness (strict ``<`` vs ``≤``) is
graded — it is the whole point of the skill.
"""

import sympy

from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import (
    Problem,
    SolutionAttempt,
    SubmittedStep,
)

_oo = sympy.oo


def _problem(solution, marks=3):
    return Problem(
        id="setsol",
        type_id="setsol",
        name="setsol",
        artifact_type="practice",
        problem_spec=lambda rng: {"solution": solution},
        verifier_spec=[
            {"kind": "set_solution", "marks_possible": marks, "param_key": "solution"}
        ],
    )


def _rate(problem, submitted):
    eng = Engine(registry=InMemoryRegistry({problem.id: problem}))
    inst = eng.instantiate(problem.id, seed=0)
    return inst.verifier.rate(SolutionAttempt(steps=[SubmittedStep(submitted)]))


def test_exact_interval_scores_full():
    sol = sympy.Interval(2, 3, False, True)  # 2 ≤ x < 3
    r = _rate(_problem(sol), sympy.Interval(2, 3, False, True))
    assert r.is_correct and r.marks_awarded == 3


def test_correct_set_is_not_a_false_negative():
    # the trap the quadratic_inequality docstring warns about: a *correct* set
    # must not be scored wrong because EmptySet != 0
    sol = sympy.Interval(2, 3, False, True)
    assert _rate(_problem(sol), sympy.Interval(2, 3, False, True)).is_correct


def test_endpoint_openness_is_graded():
    sol = sympy.Interval(2, 3, False, True)  # half-open
    # closed interval is a *different* answer (includes x = 3) → no marks
    r = _rate(_problem(sol), sympy.Interval(2, 3, False, False))
    assert r.marks_awarded == 0 and not r.is_correct


def test_wrong_endpoints_score_zero():
    sol = sympy.Interval(2, 3, False, True)
    assert _rate(_problem(sol), sympy.Interval(2, 4, False, True)).marks_awarded == 0


def test_union_of_rays_is_order_independent():
    # x < -2 or x > 3 — the "outside the roots" region
    sol = sympy.Union(
        sympy.Interval(-_oo, -2, True, True), sympy.Interval(3, _oo, True, True)
    )
    # student writes the two rays in the other order
    submitted = sympy.Union(
        sympy.Interval(3, _oo, True, True), sympy.Interval(-_oo, -2, True, True)
    )
    r = _rate(_problem(sol, marks=1), submitted)
    assert r.is_correct and r.marks_awarded == 1


def test_interval_and_union_are_distinguished():
    # "between" vs "outside" must never collide
    between = sympy.Interval(-2, 3, True, True)
    outside = sympy.Union(
        sympy.Interval(-_oo, -2, True, True), sympy.Interval(3, _oo, True, True)
    )
    assert _rate(_problem(between), outside).marks_awarded == 0
    assert _rate(_problem(outside), between).marks_awarded == 0


def test_string_answer_is_sympified():
    sol = sympy.Interval(2, 3, False, True)
    # a submission that sympifies to the same set is accepted
    assert _rate(_problem(sol), "Interval(2, 3, False, True)").is_correct


def test_unparseable_answer_scores_zero_not_raises():
    sol = sympy.Interval(2, 3, False, True)
    r = _rate(_problem(sol), "this is not a set")
    assert r.marks_awarded == 0 and not r.is_correct
