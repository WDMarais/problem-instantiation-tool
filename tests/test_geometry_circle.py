"""
Euclidean circle primitive in render/geometry.py (Circle + circle_point).

The renderer is display-only and not-to-scale, so these pin the geometry that MUST
hold: circumference points land on the drawn ring (they share the fit scale), the
ring survives the bounding box even when points cluster on one arc, and a circle
stays a circle under the pose (uniform transform).
"""

from __future__ import annotations

import math
import re

from render.geometry import (
    Circle,
    GeometryFigure,
    Point,
    Pose,
    circle_point,
    render_figure,
)


def _ring_and_dot_dists(svg: str) -> tuple[float, list[float]]:
    """(drawn ring radius, screen distance of each vertex dot from the ring centre)."""
    outline = re.search(
        r'<circle cx="([\d.]+)" cy="([\d.]+)" r="([\d.]+)" fill="none"', svg
    )
    assert outline is not None, "no circle outline emitted"
    ox, oy, r = (float(g) for g in outline.groups())
    dots = re.findall(r'<circle cx="([\d.]+)" cy="([\d.]+)" r="2\.1"', svg)
    return r, [math.hypot(float(x) - ox, float(y) - oy) for x, y in dots]


def test_circle_point_places_on_ring():
    # layout y-up: 0° = east, 90° = north, counter-clockwise
    e = circle_point("E", 2.0, 1.0, 3.0, 0)
    n = circle_point("N", 2.0, 1.0, 3.0, 90)
    assert math.isclose(e.x, 5.0) and math.isclose(e.y, 1.0, abs_tol=1e-9)
    assert math.isclose(n.x, 2.0, abs_tol=1e-9) and math.isclose(n.y, 4.0)


def test_outline_is_drawn_behind_and_unfilled():
    fig = GeometryFigure(
        points=[Point("O", 0, 0), circle_point("A", 0, 0, 1, 0)],
        circles=[Circle("O", 1.0)],
    )
    svg = render_figure(fig)
    # the ring is fill="none" (an outline), distinct from the filled r=2.1 vertex dots
    assert re.search(r'<circle[^>]*r="[\d.]+" fill="none"', svg)


def test_circumference_points_land_on_the_drawn_ring():
    # the whole point of sharing the fit scale: a circle_point sits ON the outline
    fig = GeometryFigure(
        points=[Point("O", 0, 0)]
        + [
            circle_point(nm, 0, 0, 1.0, a)
            for nm, a in [("A", 205), ("B", 335), ("C", 100), ("D", 55)]
        ],
        circles=[Circle("O", 1.0)],
    )
    r, dists = _ring_and_dot_dists(render_figure(fig))
    on_ring = [d for d in dists if abs(d - r) < 0.5]
    at_centre = [d for d in dists if d < 0.5]
    assert len(on_ring) == 4  # A, B, C, D all on the ring
    assert len(at_centre) == 1  # O at the centre


def test_ring_fits_viewbox_when_points_cluster_on_one_arc():
    # circumference points all on the top arc — the ring bulges past them, so the
    # bbox must fold in the circle's own extent or the outline would clip.
    fig = GeometryFigure(
        points=[Point("O", 0, 0)]
        + [
            circle_point(nm, 0, 0, 1.0, a)
            for nm, a in [("A", 70), ("B", 90), ("C", 110)]
        ],
        circles=[Circle("O", 1.0)],
        width=300,
        height=230,
        pad=30,
    )
    outline = re.search(
        r'<circle cx="([\d.]+)" cy="([\d.]+)" r="([\d.]+)" fill="none"',
        render_figure(fig),
    )
    ox, oy, r = (float(g) for g in outline.groups())
    assert ox - r >= 0 and ox + r <= 300  # ring within the viewBox horizontally
    assert oy - r >= 0 and oy + r <= 230  # and vertically


def test_circle_stays_circle_under_reflect_and_rotate():
    fig = GeometryFigure(
        points=[Point("O", 0, 0)]
        + [
            circle_point(nm, 0, 0, 1.0, a)
            for nm, a in [("A", 0), ("B", 120), ("C", 240)]
        ],
        circles=[Circle("O", 1.0)],
        pose=Pose(rotate_deg=40, reflect=True),
    )
    r, dists = _ring_and_dot_dists(render_figure(fig))
    on_ring = [d for d in dists if abs(d - r) < 0.5]
    assert len(on_ring) == 3  # points still on the ring after the similarity transform
