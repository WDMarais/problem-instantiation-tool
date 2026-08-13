"""
Calculus, archetype 5 — ``optimisation_solve``.

The oracle re-solves the optimisation independently: differentiate the given
Q(x), solve Q′(x)=0, keep the positive root, and confirm via Q″>0 that it is a
minimum; the minimum value is Q evaluated there. Distribution tests guard that
the construction yields integer optima and that the stationary point is always a
minimum (never a maximum or inflection).
"""

import sympy

from content.examples.optimisation_solve import optimisation_solve
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

_x = sympy.Symbol("x", positive=True)


def _eng():
    return Engine(
        registry=InMemoryRegistry({optimisation_solve.id: optimisation_solve})
    )


def _rate(inst, *answers):
    steps = [SubmittedStep(a) for a in answers]
    return inst.verifier.rate(SolutionAttempt(steps=steps))


def _Q(p):
    return p["a"] * _x + sympy.Integer(p["b"]) / _x


# --- generator correctness (independent oracle) -----------------------------


def test_optimal_x_solves_the_derivative():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(optimisation_solve.id, seed=seed).params
        roots = [r for r in sympy.solve(sympy.diff(_Q(p), _x), _x) if r > 0]
        assert len(roots) == 1 and roots[0] == p["optimal_x"], (
            seed,
            p["function_latex"],
        )


def test_optimal_value_is_Q_at_the_optimum():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(optimisation_solve.id, seed=seed).params
        assert _Q(p).subs(_x, p["optimal_x"]) == p["optimal_value"], seed


def test_derivative_is_correct():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(optimisation_solve.id, seed=seed).params
        assert sympy.simplify(sympy.diff(_Q(p), _x) - p["derivative"]) == 0, seed


def test_stationary_point_is_always_a_minimum():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(optimisation_solve.id, seed=seed).params
        second = sympy.diff(_Q(p), _x, 2).subs(_x, p["optimal_x"])
        assert second > 0, seed  # Q″ > 0 ⇒ minimum


def test_distribution_integer_optima():
    eng = _eng()
    seen_x = set()
    for seed in range(120):
        p = eng.instantiate(optimisation_solve.id, seed=seed).params
        assert p["a"] > 0 and p["b"] > 0, seed
        assert isinstance(p["optimal_x"], int) and isinstance(
            p["optimal_value"], int
        ), seed
        # b = a·x*²  ⇒  the optimum is exact, and the min value is 2·a·x*
        assert p["b"] == p["a"] * p["optimal_x"] ** 2, seed
        assert p["optimal_value"] == 2 * p["a"] * p["optimal_x"], seed
        seen_x.add(p["optimal_x"])
    assert len(seen_x) >= 3


# --- verifier round-trips ---------------------------------------------------


def test_full_marks_on_all_three_steps():
    inst = _eng().instantiate(optimisation_solve.id, seed=1)
    p = inst.params
    r = _rate(inst, p["derivative"], p["optimal_x"], p["optimal_value"])
    assert r.is_correct and r.marks_awarded == 3


def test_derivative_right_but_wrong_root_keeps_one_mark():
    inst = _eng().instantiate(optimisation_solve.id, seed=1)
    p = inst.params
    # correct Q′, but kept the spurious negative root and a bogus value
    r = _rate(inst, p["derivative"], -p["optimal_x"], 0)
    assert r.marks_awarded == 1 and not r.is_correct


def test_equivalent_derivative_form_is_accepted():
    inst = _eng().instantiate(optimisation_solve.id, seed=2)
    p = inst.params
    # a − b·x⁻² written with an explicit negative power
    powered = p["a"] - p["b"] * _x ** (-2)
    r = _rate(inst, powered, p["optimal_x"], p["optimal_value"])
    assert r.is_correct and r.marks_awarded == 3


def test_all_wrong_scores_zero():
    inst = _eng().instantiate(optimisation_solve.id, seed=1)
    r = _rate(inst, sympy.Integer(0), 999, 999)
    assert r.marks_awarded == 0
