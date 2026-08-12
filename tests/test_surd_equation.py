"""
Q1 Algebra Extensions, archetype 2 — ``surd_equation``.

The oracle is the *original* radical equation, evaluated numerically with
``math.sqrt`` — fully independent of the backward construction. Candidate roots
are cross-checked against an independent solve of the squared quadratic; validity
against the numeric truth of √(a·t+b) = s·t+c. Distribution tests guard the two
things that make the archetype honest: the extraneous case actually occurs, and
the extraneous root is the smaller one as often as the larger.
"""

import math

import sympy

from content.examples.surd_equation import surd_equation
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

_x = sympy.Symbol("x")


def _eng():
    return Engine(registry=InMemoryRegistry({surd_equation.id: surd_equation}))


def _rate(inst, *answers):
    steps = [SubmittedStep(a) for a in answers]
    return inst.verifier.rate(SolutionAttempt(steps=steps))


# --- generator correctness (independent numeric oracle) ---------------------


def test_candidates_solve_the_squared_quadratic():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(surd_equation.id, seed=seed).params
        # squared equation: a·x + b = (s·x + c)²
        squared = sympy.Eq(p["a"] * _x + p["b"], (p["s"] * _x + p["c"]) ** 2)
        roots = {int(r) for r in sympy.solve(squared, _x)}
        assert roots == set(p["candidate_roots"]), (seed, p["equation_latex"])


def test_valid_roots_are_exactly_those_satisfying_the_original_equation():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(surd_equation.id, seed=seed).params
        numeric_valid = set()
        for t in p["candidate_roots"]:
            inner = p["a"] * t + p["b"]
            assert inner >= 0, (seed, t)  # surd defined at every candidate
            if math.isclose(math.sqrt(inner), p["s"] * t + p["c"], abs_tol=1e-9):
                numeric_valid.add(t)
        assert numeric_valid == set(p["valid_roots"]), (seed, p["equation_latex"])
        # extraneous = candidates that fail the check
        assert set(p["extraneous_roots"]) == set(p["candidate_roots"]) - numeric_valid


def test_distribution_is_honest():
    """The extraneous case must occur, both RHS orientations must appear, and the
    extraneous root must land on the smaller AND the larger root across draws —
    otherwise the archetype teaches a false 'reject the smaller root' shortcut."""
    eng = _eng()
    saw_extraneous = saw_both_valid = False
    saw_s_pos = saw_s_neg = False
    extraneous_is_min = extraneous_is_max = False
    for seed in range(120):
        p = eng.instantiate(surd_equation.id, seed=seed).params
        saw_s_pos |= p["s"] == 1
        saw_s_neg |= p["s"] == -1
        if p["extraneous_roots"]:
            saw_extraneous = True
            ext = next(iter(p["extraneous_roots"]))
            extraneous_is_min |= ext == min(p["candidate_roots"])
            extraneous_is_max |= ext == max(p["candidate_roots"])
        else:
            saw_both_valid = True
    assert saw_extraneous and saw_both_valid
    assert saw_s_pos and saw_s_neg
    assert extraneous_is_min and extraneous_is_max


def test_two_distinct_integer_candidates():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(surd_equation.id, seed=seed).params
        assert len(p["candidate_roots"]) == 2, seed


# --- verifier round-trips ---------------------------------------------------


def _first_seed_with_extraneous():
    eng = _eng()
    for seed in range(200):
        inst = eng.instantiate(surd_equation.id, seed=seed)
        if inst.params["extraneous_roots"]:
            return inst
    raise AssertionError("no extraneous-root instance found")


def test_full_marks_on_solve_and_reject():
    inst = _first_seed_with_extraneous()
    p = inst.params
    r = _rate(inst, p["candidate_roots"], p["valid_roots"])
    assert r.is_correct and r.marks_awarded == 3


def test_forgetting_to_reject_loses_exactly_the_rejection_mark():
    inst = _first_seed_with_extraneous()
    p = inst.params
    # both candidates solved (2), but no rejection → valid step wrong (0)
    r = _rate(inst, p["candidate_roots"], p["candidate_roots"])
    assert r.marks_awarded == 2 and not r.is_correct


def test_partial_credit_on_one_candidate_root():
    inst = _first_seed_with_extraneous()
    p = inst.params
    one = frozenset({min(p["candidate_roots"])})
    r = _rate(inst, one, p["valid_roots"])
    # one candidate (1 of 2) + correct valid set (1) = 2
    assert r.marks_awarded == 2 and not r.is_correct


def test_all_wrong_scores_zero():
    inst = _first_seed_with_extraneous()
    r = _rate(inst, frozenset({99, 100}), frozenset({99}))
    assert r.marks_awarded == 0
