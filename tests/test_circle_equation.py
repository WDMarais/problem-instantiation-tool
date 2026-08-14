"""
Analytic geometry, archetype 4 — ``circle_equation``.

The oracle avoids re-using the centre = −D/2 formula. Instead it treats the
general-form equation as a black box and checks two independent facts:
  - the point (centre_x + radius, centre_y) — one radius east of the claimed
    centre — actually lies on the given circle (satisfies the equation); and
  - expanding (x − cx)² + (y − cy)² − r² reproduces the given polynomial.
Together these pin down that the claimed centre and radius describe exactly the
circle the equation defines. Distribution tests confirm both perfect-square and
irrational radii are produced (no cosmetic clamping to whole radii).
"""

import sympy

from content.examples.circle_equation import circle_equation
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

_x, _y = sympy.symbols("x y")


def _eng():
    return Engine(registry=InMemoryRegistry({circle_equation.id: circle_equation}))


def _rate(inst, *answers):
    steps = [SubmittedStep(a) for a in answers]
    return inst.verifier.rate(SolutionAttempt(steps=steps))


# --- generator correctness (independent oracle) -----------------------------


def test_point_one_radius_from_centre_lies_on_the_circle():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(circle_equation.id, seed=seed).params
        east = p["equation_poly"].subs(
            {_x: p["centre_x"] + p["radius"], _y: p["centre_y"]}
        )
        north = p["equation_poly"].subs(
            {_x: p["centre_x"], _y: p["centre_y"] + p["radius"]}
        )
        assert sympy.simplify(east) == 0, seed
        assert sympy.simplify(north) == 0, seed


def test_completed_square_reproduces_the_equation():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(circle_equation.id, seed=seed).params
        rebuilt = (
            (_x - p["centre_x"]) ** 2 + (_y - p["centre_y"]) ** 2 - p["radius"] ** 2
        )
        assert sympy.expand(rebuilt - p["equation_poly"]) == 0, seed


def test_radius_squared_matches_the_radius():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(circle_equation.id, seed=seed).params
        assert sympy.simplify(p["radius"] ** 2 - p["radius_sq"]) == 0, seed
        assert p["radius_sq"] > 0, seed


def test_general_form_coefficients_are_integers():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(circle_equation.id, seed=seed).params
        assert all(isinstance(p[k], int) for k in ("D", "E", "F")), seed


def test_distribution_has_both_rational_and_irrational_radii():
    eng = _eng()
    saw_int = saw_surd = False
    for seed in range(120):
        p = eng.instantiate(circle_equation.id, seed=seed).params
        if p["radius"].is_Integer:
            saw_int = True
        else:
            saw_surd = True
    assert saw_int and saw_surd


# --- verifier round-trips ---------------------------------------------------


def test_full_marks_on_centre_and_radius():
    inst = _eng().instantiate(circle_equation.id, seed=1)
    p = inst.params
    r = _rate(inst, p["centre_x"], p["centre_y"], p["radius"])
    assert r.is_correct and r.marks_awarded == 3


def test_unsimplified_radius_is_accepted():
    # a seed whose radius simplifies (e.g. 2*sqrt(7)) — sqrt(radius_sq) must score
    eng = _eng()
    seed = next(
        s
        for s in range(200)
        if not eng.instantiate(circle_equation.id, seed=s).params["radius"].is_Integer
    )
    inst = eng.instantiate(circle_equation.id, seed=seed)
    p = inst.params
    r = _rate(inst, p["centre_x"], p["centre_y"], sympy.sqrt(p["radius_sq"]))
    assert r.is_correct and r.marks_awarded == 3


def test_centre_sign_slip_loses_centre_marks_only():
    # a seed with a non-zero, asymmetric centre so both signs actually flip
    eng = _eng()
    seed = next(
        s
        for s in range(200)
        if (pp := eng.instantiate(circle_equation.id, seed=s).params)["centre_x"]
        not in (0, pp["centre_y"])
        and pp["centre_y"] != 0
    )
    inst = eng.instantiate(circle_equation.id, seed=seed)
    p = inst.params
    r = _rate(inst, -p["centre_x"], -p["centre_y"], p["radius"])
    assert r.marks_awarded == 1 and not r.is_correct  # only the radius mark survives


def test_all_wrong_scores_zero():
    inst = _eng().instantiate(circle_equation.id, seed=1)
    p = inst.params
    r = _rate(inst, p["centre_x"] + 3, p["centre_y"] + 3, p["radius"] + 1)
    assert r.marks_awarded == 0
