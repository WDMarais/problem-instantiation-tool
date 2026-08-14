"""
Independent-oracle tests for ``perpendicular_foot``.

The generator never solves for the foot — it *places* it and steps P off along
the normal. The honest check recovers the foot the way a student would: intersect
L with the perpendicular through P. That is a different computation from the
generator, so it is a real oracle, not a mirror of the same arithmetic.
"""

from __future__ import annotations

import random

import sympy

from content.examples.perpendicular_foot import _gen, perpendicular_foot
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

_x, _y = sympy.symbols("x y")


def _params(seed):
    return _gen(random.Random(seed))


def _solve_foot(p):
    """Recover F by intersecting L with the perpendicular through P."""
    line = sympy.Eq(p["A"] * _x + p["B"] * _y + p["C"], 0)
    # perpendicular through P has gradient B/A → B(x−px) − A(y−py) = 0
    perp = sympy.Eq(p["B"] * (_x - p["px"]) - p["A"] * (_y - p["py"]), 0)
    sol = sympy.solve([line, perp], [_x, _y], dict=True)
    assert len(sol) == 1
    return sol[0][_x], sol[0][_y]


# --- the oracle: intersecting the two lines recovers the stored foot ---------


def test_two_line_intersection_recovers_stored_foot():
    for seed in range(200):
        p = _params(seed)
        fx, fy = _solve_foot(p)
        assert fx == p["foot_x"], seed
        assert fy == p["foot_y"], seed


def test_foot_lies_on_the_line_and_pf_is_perpendicular():
    for seed in range(200):
        p = _params(seed)
        # F on L
        assert p["A"] * p["foot_x"] + p["B"] * p["foot_y"] + p["C"] == 0, seed
        # PF ⊥ L: PF · (line direction (B, −A)) == 0
        pfx = p["foot_x"] - p["px"]
        pfy = p["foot_y"] - p["py"]
        assert pfx * p["B"] + pfy * (-p["A"]) == 0, seed


# --- construction is well-formed --------------------------------------------


def test_line_is_oblique_and_p_is_off_it():
    for seed in range(300):
        p = _params(seed)
        assert p["A"] != 0 and p["B"] != 0, seed  # no vertical/horizontal L
        assert p["B"] > 0, seed  # sign-normalised
        # P is genuinely off the line (non-zero perpendicular distance)
        assert p["A"] * p["px"] + p["B"] * p["py"] + p["C"] != 0, seed


def test_gradient_matches_the_general_form():
    for seed in range(100):
        p = _params(seed)
        assert p["gradient"] == sympy.Rational(-p["A"], p["B"]), seed


# --- distribution honesty ----------------------------------------------------


def test_feet_and_gradients_are_not_stuck():
    xs, ys, grads = set(), set(), set()
    for seed in range(300):
        p = _params(seed)
        xs.add(p["foot_x"])
        ys.add(p["foot_y"])
        grads.add(p["gradient"])
    assert len(xs) > 8 and len(ys) > 8  # feet roam the (-6..6) box
    assert len(grads) > 6  # a real spread of line gradients, both signs
    assert any(g < 0 for g in grads) and any(g > 0 for g in grads)


# --- verifier round-trips ----------------------------------------------------


def _rate(inst, *answers):
    attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
    return inst.verifier.rate(attempt)


def test_correct_foot_scores_full():
    engine = Engine(
        registry=InMemoryRegistry({perpendicular_foot.id: perpendicular_foot})
    )
    for seed in range(30):
        inst = engine.instantiate(perpendicular_foot.id, seed=seed)
        p = inst.params
        r = _rate(inst, p["foot_x"], p["foot_y"])
        assert r.marks_awarded == 2 and r.is_correct, seed


def test_one_wrong_coordinate_scores_exactly_one():
    engine = Engine(
        registry=InMemoryRegistry({perpendicular_foot.id: perpendicular_foot})
    )
    for seed in range(30):
        inst = engine.instantiate(perpendicular_foot.id, seed=seed)
        p = inst.params
        r = _rate(inst, p["foot_x"] + 1, p["foot_y"])
        assert r.marks_awarded == 1 and not r.is_correct, seed


def test_reflection_confusion_does_not_score_full():
    # Reflecting P in L gives 2F − P, not the foot F; since P is off L they
    # never coincide, so this common confusion must never earn full marks.
    engine = Engine(
        registry=InMemoryRegistry({perpendicular_foot.id: perpendicular_foot})
    )
    full = 0
    for seed in range(60):
        inst = engine.instantiate(perpendicular_foot.id, seed=seed)
        p = inst.params
        rx = 2 * p["foot_x"] - p["px"]
        ry = 2 * p["foot_y"] - p["py"]
        if _rate(inst, rx, ry).marks_awarded == 2:
            full += 1
    assert full == 0
