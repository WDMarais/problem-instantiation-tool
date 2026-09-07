"""
Elevated-axonometric 3-D wireframe renderer (render/scene3d.py).

The renderer is dumb (projection + reuse of geometry.py's mark helpers), so the
tests pin the projection maths and the SVG surface, not pixel positions.
"""

from __future__ import annotations

import math

from render.geometry import Angle, Segment
from render.scene3d import Face, Point3D, Scene3D, View, _project, render_scene3d


def test_projection_elevated_axonometric():
    view = View(azimuth_deg=35.0, elevation_deg=30.0)
    a, e = math.radians(35.0), math.radians(30.0)
    # origin maps to origin
    assert _project(Point3D("O", 0, 0, 0), view) == (0.0, 0.0)
    # pure z stays on the vertical (u == 0), foreshortened by cos(elevation)
    uz, vz = _project(Point3D("Z", 0, 0, 3), view)
    assert math.isclose(uz, 0.0)
    assert math.isclose(vz, 3.0 * math.cos(e))
    # pure x turntables by the azimuth and picks up a little height from the tilt
    ux, vx = _project(Point3D("X", 2, 0, 0), view)
    assert math.isclose(ux, 2.0 * math.cos(a))
    assert math.isclose(vx, 2.0 * math.sin(a) * math.sin(e))
    # the receding y-axis: u swings the other way, v rises with the elevation
    uy, vy = _project(Point3D("Y", 0, 4, 0), view)
    assert math.isclose(uy, -4.0 * math.sin(a))
    assert math.isclose(vy, 4.0 * math.cos(a) * math.sin(e))


def test_vertical_stays_vertical_on_screen():
    # two points sharing (x, y) but differing in z must share their screen u
    view = View(azimuth_deg=25.0, elevation_deg=35.0)
    uf, _ = _project(Point3D("F", 0.6, 3.0, 0.0), view)
    ut, _ = _project(Point3D("T", 0.6, 3.0, 5.2), view)
    assert math.isclose(uf, ut)  # the tower does not tip over at any elevation


def test_vertical_point_is_higher_on_screen():
    # a point straight up from the foot must sit above it (smaller screen y)
    scene = Scene3D(
        points=[Point3D("F", 0, 0, 0), Point3D("T", 0, 0, 5)],
        segments=[Segment("F", "T")],
    )
    svg = render_scene3d(scene)
    # pull the two <line> endpoints back out
    import re

    (x1, y1, x2, y2) = map(
        float,
        re.search(
            r'x1="([\d.]+)" y1="([\d.]+)" x2="([\d.]+)" y2="([\d.]+)"', svg
        ).groups(),
    )
    fy, ty = (y1, y2) if abs(x1) < 1e6 else (y2, y1)  # both share x here
    assert ty < fy  # T rendered above F


def test_svg_surface_and_reused_marks():
    scene = Scene3D(
        points=[
            Point3D("A", -3, 0, 0),
            Point3D("B", 2, 4, 0),
            Point3D("F", 0, 0, 0),
            Point3D("T", 0, 0, 5),
        ],
        segments=[
            Segment("A", "F"),
            Segment("B", "F", ticks=1),
            Segment("T", "B", dashed=True),
        ],
        angles=[Angle(vertex="F", a="A", b="T", right=True)],
    )
    svg = render_scene3d(scene)
    assert svg.startswith("<svg") and svg.rstrip().endswith("</svg>")
    assert svg.count("<line") >= 3
    assert "stroke-dasharray" in svg  # the hidden edge is dashed
    assert "polyline" in svg  # right-angle square + tick marks reused from geometry
    for name in ("A", "B", "F", "T"):
        assert f">{name}</text>" in svg


def test_faces_and_axes_render():
    scene = Scene3D(
        points=[
            Point3D("A", -4, 0, 0),
            Point3D("B", 4, 0, 0),
            Point3D("F", 0, 3, 0),
            Point3D("T", 0, 3, 5),
        ],
        faces=[Face(("A", "B", "F"), fill="#d97706", opacity=0.13)],
        segments=[Segment("F", "T")],
        axes=True,
    )
    svg = render_scene3d(scene)
    assert "<polygon" in svg and 'fill-opacity="0.13"' in svg  # tinted ground plane
    for axis in ("x", "y", "z"):
        assert f">{axis}</text>" in svg  # orientation triad


def test_azimuth_varies_layout():
    pts = [Point3D("A", -3, 0, 0), Point3D("B", 2, 5, 0), Point3D("T", 0, 0, 5)]
    a = render_scene3d(Scene3D(points=pts, view=View(azimuth_deg=25)))
    b = render_scene3d(Scene3D(points=pts, view=View(azimuth_deg=50)))
    assert a != b  # rotating the view azimuth gives a genuinely different figure
