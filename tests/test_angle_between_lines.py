"""
Analytic geometry, archetype 3 — ``angle_between_lines``.

The generator combines two inclinations by subtraction; the oracle re-derives
the acute angle by the *independent* tan formula
    tan α = |(m₁ − m₂) / (1 + m₁·m₂)|,
with the perpendicular case (1 + m₁·m₂ = 0) giving 90° directly. Distribution
tests guard that the angle stays in (0°, 90°], that a perpendicular (90°) pair
is reachable, and that no vertical/parallel lines are emitted.
"""

import math

import sympy

from content.examples.angle_between_lines import angle_between_lines
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep


def _eng():
    return Engine(
        registry=InMemoryRegistry({angle_between_lines.id: angle_between_lines})
    )


def _rate(inst, *answers):
    steps = [SubmittedStep(a) for a in answers]
    return inst.verifier.rate(SolutionAttempt(steps=steps))


def _tan_formula_angle(m1, m2):
    denom = 1 + m1 * m2
    if denom == 0:
        return 90.0
    return math.degrees(math.atan(abs((m1 - m2) / denom)))


# --- generator correctness (independent oracle) -----------------------------


def test_gradients_are_rise_over_run():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(angle_between_lines.id, seed=seed).params
        assert p["m1"] == sympy.Rational(p["by"] - p["ay"], p["bx"] - p["ax"]), seed
        assert p["m2"] == sympy.Rational(p["dy"] - p["cy"], p["dx"] - p["cx"]), seed


def test_angle_matches_the_tan_formula():
    eng = _eng()
    for seed in range(120):
        p = eng.instantiate(angle_between_lines.id, seed=seed).params
        oracle = _tan_formula_angle(float(p["m1"]), float(p["m2"]))
        assert abs(oracle - p["angle_between"]) < 0.02, (
            seed,
            oracle,
            p["angle_between"],
        )


def test_inclinations_reproduce_the_gradients():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(angle_between_lines.id, seed=seed).params
        for theta, m in ((p["theta1"], p["m1"]), (p["theta2"], p["m2"])):
            mf = float(m)
            assert abs(math.tan(math.radians(theta)) - mf) < 2e-4 * (1 + mf * mf), seed


def test_angle_is_acute_and_positive():
    eng = _eng()
    for seed in range(120):
        p = eng.instantiate(angle_between_lines.id, seed=seed).params
        assert 0 < p["angle_between"] <= 90, (seed, p["angle_between"])


def test_perpendicular_pair_is_reachable_and_gives_ninety():
    eng = _eng()
    saw_perp = False
    for seed in range(400):
        p = eng.instantiate(angle_between_lines.id, seed=seed).params
        if 1 + p["m1"] * p["m2"] == 0:
            saw_perp = True
            assert abs(p["angle_between"] - 90) < 1e-9, seed
    assert saw_perp


def test_no_vertical_or_parallel_lines():
    eng = _eng()
    for seed in range(120):
        p = eng.instantiate(angle_between_lines.id, seed=seed).params
        assert p["ax"] != p["bx"] and p["cx"] != p["dx"], seed
        assert p["m1"] != p["m2"], seed


# --- verifier round-trips ---------------------------------------------------


def test_full_marks_on_all_three_steps():
    inst = _eng().instantiate(angle_between_lines.id, seed=1)
    p = inst.params
    r = _rate(inst, p["theta1"], p["theta2"], p["angle_between"])
    assert r.is_correct and r.marks_awarded == 3


def test_correct_inclinations_wrong_combine_keeps_two():
    inst = _eng().instantiate(angle_between_lines.id, seed=1)
    p = inst.params
    r = _rate(inst, p["theta1"], p["theta2"], p["angle_between"] + 25)
    assert r.marks_awarded == 2 and not r.is_correct


def test_one_decimal_rounding_still_scores():
    inst = _eng().instantiate(angle_between_lines.id, seed=2)
    p = inst.params
    r = _rate(
        inst,
        round(p["theta1"], 1),
        round(p["theta2"], 1),
        round(p["angle_between"], 1),
    )
    assert r.is_correct and r.marks_awarded == 3


def test_all_wrong_scores_zero():
    inst = _eng().instantiate(angle_between_lines.id, seed=1)
    p = inst.params
    r = _rate(inst, p["theta1"] + 15, p["theta2"] + 15, p["angle_between"] + 15)
    assert r.marks_awarded == 0
