"""
Independent-oracle tests for ``circumcentre``.

The generator never solves for the circumcentre — it *places* three vertices on
a circle of chosen centre (h, k). So the honest check is to recover (h, k) by
the method a student would use: intersect two perpendicular bisectors. That is a
genuinely different computation from the generator, which makes it a real oracle
rather than a mirror of the same arithmetic.
"""

from __future__ import annotations

import random

import sympy

from content.examples.circumcentre import _gen, _lattice_offsets, circumcentre
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

_x, _y = sympy.symbols("x y")


def _params(seed):
    return _gen(random.Random(seed))


def _solve_circumcentre(p):
    """Recover P by intersecting two perpendicular bisectors (student method)."""

    def sq(dx, dy):
        return dx * dx + dy * dy

    # |PA|² = |PB|²  and  |PB|² = |PC|²  — each collapses to a linear equation.
    eq1 = sympy.Eq(sq(_x - p["ax"], _y - p["ay"]), sq(_x - p["bx"], _y - p["by"]))
    eq2 = sympy.Eq(sq(_x - p["bx"], _y - p["by"]), sq(_x - p["cx"], _y - p["cy"]))
    sol = sympy.solve([eq1, eq2], [_x, _y], dict=True)
    assert len(sol) == 1, "three distinct vertices must give a unique circumcentre"
    return sol[0][_x], sol[0][_y]


# --- the oracle: solving the bisector system recovers the stored centre ------


def test_bisector_intersection_recovers_stored_centre():
    for seed in range(200):
        p = _params(seed)
        px, py = _solve_circumcentre(p)
        assert px == p["centre_x"], seed
        assert py == p["centre_y"], seed


def test_all_three_vertices_are_equidistant_from_the_centre():
    for seed in range(200):
        p = _params(seed)
        h, k = p["centre_x"], p["centre_y"]
        d2 = {
            (p["ax"] - h) ** 2 + (p["ay"] - k) ** 2,
            (p["bx"] - h) ** 2 + (p["by"] - k) ** 2,
            (p["cx"] - h) ** 2 + (p["cy"] - k) ** 2,
        }
        assert d2 == {p["radius_sq"]}, seed


# --- construction is well-formed --------------------------------------------


def test_the_three_vertices_are_distinct():
    for seed in range(200):
        p = _params(seed)
        verts = {
            (p["ax"], p["ay"]),
            (p["bx"], p["by"]),
            (p["cx"], p["cy"]),
        }
        assert len(verts) == 3, seed


def test_every_declared_radius_actually_carries_three_lattice_points():
    from content.examples.circumcentre import _LATTICE_RADII_SQ

    for r_sq in _LATTICE_RADII_SQ:
        offs = _lattice_offsets(r_sq)
        assert len(offs) >= 3, r_sq
        # every listed offset really is on the circle
        assert all(dx * dx + dy * dy == r_sq for dx, dy in offs), r_sq


# --- distribution honesty ----------------------------------------------------


def test_centres_and_radii_are_not_stuck():
    xs, ys, radii = set(), set(), set()
    for seed in range(300):
        p = _params(seed)
        xs.add(p["centre_x"])
        ys.add(p["centre_y"])
        radii.add(p["radius_sq"])
    assert len(xs) > 8 and len(ys) > 8  # centres roam the (-6..6) box
    assert len(radii) >= 4  # more than one circle size is drawn


# --- verifier round-trips ----------------------------------------------------


def _rate(inst, *answers):
    attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
    return inst.verifier.rate(attempt)


def test_correct_coordinates_score_full():
    engine = Engine(registry=InMemoryRegistry({circumcentre.id: circumcentre}))
    for seed in range(30):
        inst = engine.instantiate(circumcentre.id, seed=seed)
        p = inst.params
        r = _rate(inst, p["centre_x"], p["centre_y"])
        assert r.marks_awarded == 2 and r.is_correct, seed


def test_one_wrong_coordinate_scores_exactly_one():
    engine = Engine(registry=InMemoryRegistry({circumcentre.id: circumcentre}))
    for seed in range(30):
        inst = engine.instantiate(circumcentre.id, seed=seed)
        p = inst.params
        r = _rate(inst, p["centre_x"], p["centre_y"] + 1)
        assert r.marks_awarded == 1 and not r.is_correct, seed


def test_centroid_confusion_does_not_score_full():
    # The mean of the vertices is the centroid, not the circumcentre (they
    # coincide only for an equilateral triangle, which the lattice draw avoids).
    engine = Engine(registry=InMemoryRegistry({circumcentre.id: circumcentre}))
    full = 0
    for seed in range(60):
        inst = engine.instantiate(circumcentre.id, seed=seed)
        p = inst.params
        gx = sympy.Rational(p["ax"] + p["bx"] + p["cx"], 3)
        gy = sympy.Rational(p["ay"] + p["by"] + p["cy"], 3)
        if _rate(inst, gx, gy).marks_awarded == 2:
            full += 1
    assert full == 0
