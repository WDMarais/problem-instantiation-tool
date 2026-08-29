"""
Q1 Algebra, quadratic solved by formula — ``quadratic_formula``.

The oracle is independent of the generator: each reported root is substituted
back into a·x² + b·x + c and must evaluate to ~0, the discriminant must be
positive and non-square (else the item would factorise), and the roots must be
distinct to two decimals. Verifier round-trips confirm the 2-dp tolerance and
per-root partial credit.
"""

import math

from content.examples.quadratic_formula import quadratic_formula
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep


def _eng():
    return Engine(registry=InMemoryRegistry({quadratic_formula.id: quadratic_formula}))


def _rate(inst, *answers):
    return inst.verifier.rate(
        SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
    )


# --- generator correctness (independent oracle) -----------------------------


def test_roots_satisfy_the_quadratic():
    eng = _eng()
    for seed in range(150):
        p = eng.instantiate(quadratic_formula.id, seed=seed).params
        a, b, c = p["a"], p["b"], p["c"]
        for r in (p["root_small"], p["root_large"]):
            # r is rounded to 2 dp, so allow a residual from the rounding
            assert abs(a * r * r + b * r + c) < 0.5, (seed, p["equation_latex"], r)


def test_discriminant_is_positive_and_non_square():
    eng = _eng()
    for seed in range(150):
        p = eng.instantiate(quadratic_formula.id, seed=seed).params
        disc = p["discriminant"]
        assert disc == p["b"] ** 2 - 4 * p["a"] * p["c"]
        assert disc > 0
        root = math.isqrt(disc)
        assert root * root != disc, (seed, disc)  # non-factorisable → formula forced


def test_roots_ordered_distinct_and_exam_sized():
    eng = _eng()
    for seed in range(200):
        p = eng.instantiate(quadratic_formula.id, seed=seed).params
        assert p["root_small"] < p["root_large"]
        assert p["a"] >= 2  # non-monic, visibly a formula item
        assert abs(p["root_small"]) <= 20 and abs(p["root_large"]) <= 20


# --- verifier round-trips ---------------------------------------------------


def test_full_marks_on_both_roots():
    inst = _eng().instantiate(quadratic_formula.id, seed=7)
    p = inst.params
    r = _rate(inst, p["root_small"], p["root_large"])
    assert r.is_correct and r.marks_awarded == 2


def test_tolerance_accepts_a_more_precise_decimal():
    inst = _eng().instantiate(quadratic_formula.id, seed=7)
    p = inst.params
    a, b = p["a"], p["b"]
    disc = p["discriminant"]
    # full-precision roots (student used a calculator, didn't round to 2 dp)
    exact_small = (-b - math.sqrt(disc)) / (2 * a)
    exact_large = (-b + math.sqrt(disc)) / (2 * a)
    r = _rate(inst, exact_small, exact_large)
    assert r.is_correct and r.marks_awarded == 2


def test_partial_credit_one_root_right():
    inst = _eng().instantiate(quadratic_formula.id, seed=7)
    p = inst.params
    r = _rate(inst, p["root_small"], p["root_large"] + 1.0)
    assert r.marks_awarded == 1 and not r.is_correct


def test_all_wrong_scores_zero():
    inst = _eng().instantiate(quadratic_formula.id, seed=7)
    p = inst.params
    r = _rate(inst, p["root_small"] + 1.0, p["root_large"] + 1.0)
    assert r.marks_awarded == 0
