"""
Exponent algebra — ``exponent_simplify_constant`` (P1 Q1.3).

The ratio (aˣ⁺ᵐ − aˣ)/aˣ⁺ᵏ simplifies to (aᵐ − 1)/aᵏ, a constant independent of x.
Every answer is re-derived (and checked to be x-free) directly; the verifier
round-trips; the shipped source value 8/3 is reproduced.
"""

import sympy

from content.examples.exponent_simplify_constant import exponent_simplify_constant
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep


def _eng():
    return Engine(
        registry=InMemoryRegistry(
            {exponent_simplify_constant.id: exponent_simplify_constant}
        )
    )


def _rate(inst, answer):
    return inst.verifier.rate(SolutionAttempt(steps=[SubmittedStep(answer)]))


def test_answer_is_the_x_free_constant():
    # evaluate the ratio at concrete integer x with exact arithmetic; equal across
    # different x proves the exponent cancels, and equal to the stored constant
    eng = _eng()
    for seed in range(120):
        p = eng.instantiate(exponent_simplify_constant.id, seed=seed).params
        a, m, k = p["a"], p["m"], p["k"]
        for xv in (0, 1, 5):
            ratio = sympy.Rational(a ** (xv + m) - a**xv, a ** (xv + k))
            assert ratio == p["answer"]  # same for every x → x-free, and correct
        assert p["answer"] == sympy.Rational(a**m - 1, a**k)


def test_answer_is_a_proper_fraction():
    # a ∤ aᵐ − 1, so the value never reduces to an integer (keeps the cancel flavour)
    eng = _eng()
    for seed in range(120):
        p = eng.instantiate(exponent_simplify_constant.id, seed=seed).params
        assert p["answer"].q != 1


def test_variety():
    eng = _eng()
    seen = {
        eng.instantiate(exponent_simplify_constant.id, seed=s).params["answer"]
        for s in range(120)
    }
    assert len(seen) >= 8


def test_verifier_grades_value_and_decimal():
    inst = _eng().instantiate(exponent_simplify_constant.id, seed=1)
    ans = inst.params["answer"]
    assert _rate(inst, ans).marks_awarded == 2  # exact fraction
    approx = sympy.Float(round(float(ans), 4))
    assert _rate(inst, approx).marks_awarded == 2  # calculator decimal
    assert _rate(inst, ans + sympy.Rational(1, 2)).marks_awarded == 0


def test_reproduces_source_value():
    # NSC 2025 M/J P1 Q1.3: (3^{x+2} − 3^x)/3^{x+1} = 8/3
    eng = _eng()
    for seed in range(120):
        p = eng.instantiate(exponent_simplify_constant.id, seed=seed).params
        if (p["a"], p["m"], p["k"]) == (3, 2, 1):
            assert p["answer"] == sympy.Rational(8, 3)
            return
    raise AssertionError("source instance (a,m,k)=(3,2,1) not reachable in 120 seeds")


def test_template_builds_and_is_registered():
    from worksheets.generate import PROBLEMS, template_exponent_simplify_constant

    p = _eng().instantiate(exponent_simplify_constant.id, seed=1).params
    for detail in ("full", "short"):
        card = template_exponent_simplify_constant(p, detail=detail)
        assert card.worked_steps and card.display_math
    assert exponent_simplify_constant.id in PROBLEMS
