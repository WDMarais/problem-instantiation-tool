"""
Cabinet-oblique 3-D wireframe renderer (render/scene3d.py).

The renderer is dumb (projection + reuse of geometry.py's mark helpers), so the
tests pin the projection maths and the SVG surface, not pixel positions.
"""

from __future__ import annotations

import math

from render.geometry import Angle, Segment
from render.scene3d import Face, Point3D, Scene3D, View, _project, render_scene3d


def test_projection_cabinet_oblique():
    view = View(azimuth_deg=35.0, depth=0.5)
    # origin maps to origin
    assert _project(Point3D("O", 0, 0, 0), view) == (0.0, 0.0)
    # pure x is horizontal only; pure z is vertical only
    assert _project(Point3D("X", 2, 0, 0), view) == (2.0, 0.0)
    assert _project(Point3D("Z", 0, 0, 3), view) == (0.0, 3.0)
    # the receding y-axis rises at the azimuth, foreshortened by depth
    u, v = _project(Point3D("Y", 0, 4, 0), view)
    a = math.radians(35.0)
    assert math.isclose(u, 0.5 * 4 * math.cos(a))
    assert math.isclose(v, 0.5 * 4 * math.sin(a))


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
