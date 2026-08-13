"""
Analytic geometry, archetype 1 — ``inclination_angle``.

The oracle re-derives the inclination by a genuinely different route than the
generator: the generator uses ``atan`` plus a sign-conditional +180°, the oracle
uses ``atan2(dy, dx)`` reduced mod 180° — the direction-vector angle of the line,
independent of which endpoint is named first. Distribution tests guard that both
acute (positive-gradient) and obtuse (negative-gradient) inclinations occur, and
that the two degenerate lines (vertical, horizontal) are never emitted.
"""

import math

import sympy

from content.examples.inclination_angle import inclination_angle
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep


def _eng():
    return Engine(registry=InMemoryRegistry({inclination_angle.id: inclination_angle}))


def _rate(inst, *answers):
    steps = [SubmittedStep(a) for a in answers]
    return inst.verifier.rate(SolutionAttempt(steps=steps))


# --- generator correctness (independent oracle) -----------------------------


def test_gradient_is_rise_over_run():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(inclination_angle.id, seed=seed).params
        expected = sympy.Rational(p["y2"] - p["y1"], p["x2"] - p["x1"])
        assert p["gradient"] == expected, seed


def test_inclination_matches_atan2_mod_180():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(inclination_angle.id, seed=seed).params
        dx, dy = p["x2"] - p["x1"], p["y2"] - p["y1"]
        oracle = math.degrees(math.atan2(dy, dx)) % 180
        assert abs(oracle - p["inclination"]) < 0.02, (seed, oracle, p["inclination"])


def test_tan_of_inclination_recovers_the_gradient():
    # The angle is stored rounded to 2 dp; tan is sensitive near 90°, so the
    # recovery tolerance scales with sec²θ = 1 + m² (steep lines amplify the
    # rounding error).
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(inclination_angle.id, seed=seed).params
        m = float(p["gradient"])
        tan_theta = math.tan(math.radians(p["inclination"]))
        assert abs(tan_theta - m) < 2e-4 * (1 + m * m)


def test_inclination_is_in_the_open_half_circle():
    eng = _eng()
    for seed in range(120):
        p = eng.instantiate(inclination_angle.id, seed=seed).params
        assert 0 < p["inclination"] < 180, (seed, p["inclination"])
        assert abs(p["inclination"] - 90) > 1e-9  # never vertical


def test_no_degenerate_lines_and_both_orientations_occur():
    eng = _eng()
    saw_acute = saw_obtuse = False
    for seed in range(120):
        p = eng.instantiate(inclination_angle.id, seed=seed).params
        assert p["x1"] != p["x2"] and p["y1"] != p["y2"], seed
        saw_acute |= p["gradient"] > 0
        saw_obtuse |= p["gradient"] < 0
    assert saw_acute and saw_obtuse


# --- verifier round-trips ---------------------------------------------------


def test_full_marks_on_gradient_and_angle():
    inst = _eng().instantiate(inclination_angle.id, seed=1)
    p = inst.params
    r = _rate(inst, p["gradient"], p["inclination"])
    assert r.is_correct and r.marks_awarded == 2


def test_rounding_to_one_decimal_still_earns_the_angle_mark():
    inst = _eng().instantiate(inclination_angle.id, seed=1)
    p = inst.params
    r = _rate(inst, p["gradient"], round(p["inclination"], 1))
    assert r.is_correct and r.marks_awarded == 2


def test_missing_quadrant_adjustment_loses_the_angle_mark():
    # A negative-gradient instance: the raw calculator value (θ − 180) is the
    # classic error and must not score.
    eng = _eng()
    seed = next(
        s
        for s in range(200)
        if eng.instantiate(inclination_angle.id, seed=s).params["gradient"] < 0
    )
    inst = eng.instantiate(inclination_angle.id, seed=seed)
    p = inst.params
    r = _rate(inst, p["gradient"], round(p["inclination"] - 180, 2))
    assert r.marks_awarded == 1 and not r.is_correct


def test_equivalent_gradient_form_is_accepted():
    inst = _eng().instantiate(inclination_angle.id, seed=3)
    p = inst.params
    unsimplified = sympy.Rational((p["y2"] - p["y1"]) * 3, (p["x2"] - p["x1"]) * 3)
    r = _rate(inst, unsimplified, p["inclination"])
    assert r.is_correct and r.marks_awarded == 2


def test_all_wrong_scores_zero():
    inst = _eng().instantiate(inclination_angle.id, seed=1)
    p = inst.params
    r = _rate(inst, p["gradient"] + 1, p["inclination"] + 30)
    assert r.marks_awarded == 0
