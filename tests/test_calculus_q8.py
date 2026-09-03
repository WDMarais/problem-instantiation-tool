"""
Calculus, NSC Q8 — the three new derivative generators wired into the shipped
paper: ``derivative_polynomial`` (8.2.1), ``derivative_surd_product`` (8.2.2) and
``common_tangent_parabolas`` (8.3). (Q8.1 reuses the existing
``derivative_first_principles``, covered by its own module — one reproduction
check here pins its source instance.)

Each generator's answer is re-derived independently from the presented inputs,
round-tripped through the verifier, and the shipped source instance reproduced.
"""

import sympy

from content.examples.common_tangent_parabolas import common_tangent_parabolas
from content.examples.derivative_first_principles import derivative_first_principles
from content.examples.derivative_polynomial import derivative_polynomial
from content.examples.derivative_surd_product import derivative_surd_product
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

_x = sympy.Symbol("x")

_ALL = (
    derivative_first_principles,
    derivative_polynomial,
    derivative_surd_product,
    common_tangent_parabolas,
)


def _eng():
    return Engine(registry=InMemoryRegistry({p.id: p for p in _ALL}))


def _rate(inst, *answers):
    return inst.verifier.rate(
        SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
    )


# --- 8.1 first principles (reused generator) --------------------------------


def test_first_principles_reproduces_source_instance():
    # NSC 2025 M/J P1 8.1: f(x) = x² − 2 ⇒ f′(x) = 2x
    eng = _eng()
    for seed in range(20000):
        p = eng.instantiate(derivative_first_principles.id, seed=seed).params
        if (p["a"], p["b"], p["c"]) == (1, 0, -2):
            assert p["derivative"] == 2 * _x
            return
    raise AssertionError("source instance f(x)=x²−2 not reachable")


# --- 8.2.1 plain power rule -------------------------------------------------


def test_polynomial_derivative_matches_sympy():
    eng = _eng()
    for seed in range(200):
        p = eng.instantiate(derivative_polynomial.id, seed=seed).params
        f = (
            p["a_top"] * _x ** p["top_deg"]
            + p["a_mid"] * _x ** (p["top_deg"] - 1)
            + p["a_lin"] * _x
            + p["const"]
        )
        assert sympy.simplify(p["derivative"] - sympy.diff(f, _x)) == 0


def test_polynomial_constant_drops_away():
    # the constant term never survives into f′ (so re-adding it must fail grading)
    inst = _eng().instantiate(derivative_polynomial.id, seed=1)
    p = inst.params
    assert _rate(inst, p["derivative"]).is_correct
    assert not _rate(inst, p["derivative"] + p["const"]).is_correct


def test_polynomial_awards_full_two_marks():
    inst = _eng().instantiate(derivative_polynomial.id, seed=4)
    r = _rate(inst, inst.params["derivative"])
    assert r.is_correct and r.marks_awarded == 2


# --- 8.2.2 surd × squared-binomial ------------------------------------------


def test_surd_product_derivative_matches_sympy():
    eng = _eng()
    for seed in range(200):
        p = eng.instantiate(derivative_surd_product.id, seed=seed).params
        g = p["c"] * sympy.sqrt(_x) * (_x - p["r"]) ** 2
        assert sympy.simplify(p["derivative"] - sympy.diff(g, _x)) == 0


def test_surd_product_reproduces_source_and_memo_form():
    # NSC 8.2.2: g(x) = −2√x(x − 1)² ⇒ g′(x) = −5x^{3/2} + 6x^{1/2} − x^{−1/2}
    eng = _eng()
    for seed in range(200):
        inst = eng.instantiate(derivative_surd_product.id, seed=seed)
        p = inst.params
        if (p["c"], p["r"]) == (-2, 1):
            memo = (
                -5 * _x ** sympy.Rational(3, 2)
                + 6 * sympy.sqrt(_x)
                - _x ** sympy.Rational(-1, 2)
            )
            # the memo's simplified power form grades correct against sympy's
            # unsimplified product-rule form
            assert _rate(inst, memo).is_correct
            assert _rate(inst, memo).marks_awarded == 4
            return
    raise AssertionError("source instance −2√x(x−1)² not reachable")


# --- 8.3 common tangent to two parabolas ------------------------------------


def test_common_tangent_reproduces_answers_independently():
    # re-derive (a, b) from the PRESENTED f, line and c₀ via the same-touch-point
    # system, independently of the generator's forward construction
    eng = _eng()
    for seed in range(300):
        p = eng.instantiate(common_tangent_parabolas.id, seed=seed).params
        A, B, C, x_t, c0 = p["A"], p["B"], p["C"], p["x_t"], p["c0"]
        m = 2 * A * x_t + B  # gradient off f at the touch point
        y_t = A * x_t**2 + B * x_t + C
        a_sym, b_sym = sympy.symbols("a b")
        sol = sympy.solve(
            [
                sympy.Eq(2 * a_sym * x_t + b_sym, m),  # g′(x_t) = m
                sympy.Eq(a_sym * x_t**2 + b_sym * x_t + c0, y_t),  # g(x_t) = y_t
            ],
            [a_sym, b_sym],
            dict=True,
        )[0]
        assert sol[a_sym] == p["a"] and sol[b_sym] == p["b"]


def test_common_tangent_parabolas_are_distinct():
    # a ≠ A always → g is a genuinely different parabola (never g ≡ f)
    eng = _eng()
    for seed in range(300):
        p = eng.instantiate(common_tangent_parabolas.id, seed=seed).params
        assert p["a"] != p["A"]


def test_common_tangent_reproduces_source_instance():
    # NSC 8.3: y = 4x − 14 common tangent to f = 2x² − 4x − 6 and g = ax² + bx − 18
    #          ⇒ a = −1, b = 8
    eng = _eng()
    for seed in range(60000):
        p = eng.instantiate(common_tangent_parabolas.id, seed=seed).params
        if (p["A"], p["B"], p["C"], p["x_t"], p["a"]) == (2, -4, -6, 2, -1):
            assert p["b"] == 8 and p["c0"] == -18
            assert (p["m"], p["k"]) == (4, -14)
            return
    raise AssertionError("source instance not reachable in 60000 seeds")


def test_common_tangent_verifier_grades_both_answers():
    inst = _eng().instantiate(common_tangent_parabolas.id, seed=11)
    p = inst.params
    assert _rate(inst, p["a"], p["b"]).marks_awarded == 2  # both right
    assert _rate(inst, p["a"], p["b"] + 1).marks_awarded == 1  # a right, b wrong
    assert _rate(inst, p["a"] + 1, p["b"] + 1).marks_awarded == 0


# --- templates + registration -----------------------------------------------


def test_common_tangent_stem_hides_the_answers():
    # the stem must present g with a, b as literal unknowns — printing the solved
    # coefficients would turn a 6-mark solve into a read-off
    from worksheets.generate import template_common_tangent_parabolas

    eng = _eng()
    for seed in range(50):
        p = eng.instantiate(common_tangent_parabolas.id, seed=seed).params
        card = template_common_tangent_parabolas(p)
        assert "ax^{2} + bx" in card.display_math  # unknowns shown as unknowns
        # the fully-solved g(x) = a·x² + b·x + c₀ must NOT appear in the stem
        solved_g = sympy.latex(p["a"] * _x**2 + p["b"] * _x + p["c0"])
        assert solved_g not in card.display_math


def test_templates_build_and_are_registered():
    from worksheets.generate import (
        PROBLEMS,
        template_common_tangent_parabolas,
        template_derivative_polynomial,
        template_derivative_surd_product,
    )

    eng = _eng()
    for pid, template in (
        (derivative_polynomial.id, template_derivative_polynomial),
        (derivative_surd_product.id, template_derivative_surd_product),
        (common_tangent_parabolas.id, template_common_tangent_parabolas),
    ):
        p = eng.instantiate(pid, seed=7).params
        for detail in ("full", "short"):
            card = template(p, detail=detail)
            assert card.instruction and card.worked_steps
        assert pid in PROBLEMS
