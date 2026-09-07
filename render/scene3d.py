"""
SVG renderer for 3-D wireframe figures (elevated axonometric projection).

This is the *fourth* visual domain (see render/DESIGN.md's three-way split). The
first three all ask "is there a coordinate frame?"; a 3-D scene forces a second
question the others never faced:

    **Is angle preserved by the transform?**

Function plots and analytic geometry are metric (angles are computed);
``GeometryFigure`` uses a *similarity* ``Pose`` (angles preserved — a drawn 90°
reads as 90°). A parallel projection preserves *neither* length nor angle: a true
90° corner projects to something else on paper. Textbooks live with this — the
value is *labelled* (``60°``), the projected arc merely orients. So the
display-only contract is unchanged (the generator bakes every answer; nothing is
read off the figure), but a projected angle mark is orientation, never a faithful
measurement the way a ``Pose``-transformed one is.

Only the projection is new. Once each ``Point3D`` is mapped to a screen point, the
segment / dash / angle-arc / right-angle / tick / label machinery is exactly
``render.geometry``'s — reused verbatim, not re-implemented (DRY lives at the
emitter, per DESIGN.md). ``Segment`` and ``Angle`` are that module's dataclasses.

Coordinates: ``x`` right, ``y`` receding into the page, ``z`` up. The view is an
*elevated axonometric*: turntable the scene about the vertical by ``azimuth_deg``,
raise the camera ``elevation_deg`` above the ground, then project orthographically.
This is a real rotation, not the cabinet *shear* it replaces — its payoff is that a
near-edge-on ground plane opens into an actual triangle "seen from above" (so a
ground angle stops projecting to an illegible sliver), while a vertical edge stays
exactly vertical on screen (points sharing ``x``/``y`` share their screen ``u``, so
the tower does not tip over). SRS variety comes from rotating the ``View`` azimuth —
the whole solid turns coherently; ``elevation_deg`` is the fixed camera height.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from render.geometry import (
    Angle,
    Segment,
    _angle_mark,
    _chevrons,
    _ticks,
)

_STROKE = "#333333"
_LABEL = "#111111"
_AXIS = "#94a3b8"  # subtle slate for the orientation triad


@dataclass(frozen=True)
class Point3D:
    name: str  # unique id, referenced by Segment/Angle; default label text too
    x: float  # right
    y: float  # receding into the page
    z: float  # up
    dot: bool = True  # False = no marker dot
    label: str | None = None  # display text: None = use name; "" = draw no label
    label_dir: tuple[float, float] | None = None  # screen-space push (x→right, y→up);
    # None = radially outward from the projected centroid


@dataclass(frozen=True)
class Face:
    """A filled polygon (3+ point names) drawn *behind* the edges — a translucent
    plane tint is the strongest orientation cue for an otherwise edge-on figure
    (e.g. a horizontal ground plane vs a vertical wall in a distinct hue)."""

    points: tuple[str, ...]
    fill: str = "#64748b"
    opacity: float = 0.12


@dataclass(frozen=True)
class Guide:
    """A faint construction/mesh line given in raw 3-D coordinates (not named
    points). A grid of guides laid in a plane shows the two in-plane directions —
    the strongest cue for *which way* a plane recedes."""

    p0: tuple[float, float, float]
    p1: tuple[float, float, float]
    color: str = "#94a3b8"
    width: float = 0.6
    dashed: bool = False


@dataclass(frozen=True)
class View:
    """The elevated-axonometric view. ``azimuth_deg`` turntables the scene about the
    vertical (vary it for figure-to-figure variety); ``elevation_deg`` is the camera
    height above the ground plane — larger tilts the eye further over the top, which
    opens near-horizontal planes but never tips verticals (they stay vertical on
    screen at any elevation). 0° elevation is a flat front view."""

    azimuth_deg: float = 35.0
    elevation_deg: float = 30.0


@dataclass
class Scene3D:
    points: list[Point3D]
    segments: list[Segment] = field(default_factory=list)
    angles: list[Angle] = field(default_factory=list)
    faces: list[Face] = field(default_factory=list)
    guides: list[Guide] = field(default_factory=list)
    view: View = field(default_factory=View)
    width: int = 320
    height: int = 260
    pad: int = 34
    axes: bool = False  # draw a small x/y/z orientation triad (top-left overlay)


def _axis_gnomon(view: View, ox: float, oy: float, length: float = 28.0) -> list[str]:
    """A small x/y/z orientation triad rooted at screen point (ox, oy). The arrow
    *directions* come from the projection (so they anchor the oblique view); their
    lengths are fixed pixels, so the triad reads as an overlay key rather than part
    of the deliberately-unscaled figure. Points are Euclidean, not coordinates —
    this orients the projection without implying an analytic frame."""
    a = math.radians(view.azimuth_deg)
    e = math.radians(view.elevation_deg)
    dirs = {  # projected unit axes in screen space (y is down, so v-up is negated)
        "x": (math.cos(a), -math.sin(a) * math.sin(e)),
        "y": (-math.sin(a), -math.cos(a) * math.sin(e)),
        "z": (0.0, -math.cos(e)),
    }
    out: list[str] = []
    for name, (dx, dy) in dirs.items():
        d = math.hypot(dx, dy) or 1.0
        ux, uy = dx / d, dy / d
        tx, ty = ox + ux * length, oy + uy * length
        a1x, a1y = tx - ux * 5 + uy * 3, ty - uy * 5 - ux * 3
        a2x, a2y = tx - ux * 5 - uy * 3, ty - uy * 5 + ux * 3
        out.append(
            f'<line x1="{ox:.1f}" y1="{oy:.1f}" x2="{tx:.1f}" y2="{ty:.1f}"'
            f' stroke="{_AXIS}" stroke-width="1.2"/>'
        )
        out.append(
            f'<polyline points="{a1x:.1f},{a1y:.1f} {tx:.1f},{ty:.1f}'
            f' {a2x:.1f},{a2y:.1f}" fill="none" stroke="{_AXIS}" stroke-width="1.2"/>'
        )
        out.append(
            f'<text x="{tx + ux * 7:.1f}" y="{ty + uy * 7 + 4:.1f}" font-size="11"'
            f' text-anchor="middle" fill="{_AXIS}" font-style="italic">{name}</text>'
        )
    return out


def _project(p: Point3D, view: View) -> tuple[float, float]:
    """(x, y, z) → (u, v) with v up. Elevated axonometric: turntable by
    ``azimuth_deg`` about the vertical, then tilt the camera up by ``elevation_deg``
    and drop the depth (orthographic). Verticals (fixed x, y) keep a constant u, so
    they stay vertical on screen; the ground plane opens as elevation increases."""
    a = math.radians(view.azimuth_deg)
    e = math.radians(view.elevation_deg)
    u = p.x * math.cos(a) - p.y * math.sin(a)
    v = p.z * math.cos(e) + (p.x * math.sin(a) + p.y * math.cos(a)) * math.sin(e)
    return u, v


def render_scene3d(scene: Scene3D) -> str:
    # ── project, then fit the projected bounding box to the viewBox ─────────────
    proj = {p.name: _project(p, scene.view) for p in scene.points}
    us = [u for u, _ in proj.values()]
    vs = [v for _, v in proj.values()]
    u_min, u_max = min(us), max(us)
    v_min, v_max = min(vs), max(vs)
    span_u = max(u_max - u_min, 1e-9)
    span_v = max(v_max - v_min, 1e-9)

    avail_w = scene.width - 2 * scene.pad
    avail_h = scene.height - 2 * scene.pad
    scale = min(avail_w / span_u, avail_h / span_v)
    off_x = scene.pad + (avail_w - span_u * scale) / 2
    off_y = scene.pad + (avail_h - span_v * scale) / 2

    def S(name: str) -> tuple[float, float]:
        u, v = proj[name]
        # flip: projected v-up -> screen y-down
        return off_x + (u - u_min) * scale, off_y + (v_max - v) * scale

    n = len(scene.points)
    cx = sum(S(p.name)[0] for p in scene.points) / n
    cy = sum(S(p.name)[1] for p in scene.points) / n

    out: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{scene.width}"'
        f' height="{scene.height}" viewBox="0 0 {scene.width} {scene.height}"'
        f' style="display:block;max-width:100%;height:auto"'
        f' font-family="Georgia, serif">'
    ]

    # ── faces (translucent plane tints, drawn behind the edges) ─────────────────
    for face in scene.faces:
        pts = " ".join(f"{S(name)[0]:.1f},{S(name)[1]:.1f}" for name in face.points)
        out.append(
            f'<polygon points="{pts}" fill="{face.fill}"'
            f' fill-opacity="{face.opacity}" stroke="none"/>'
        )

    # ── guide/mesh lines (raw 3-D coords, drawn on the fill, under the edges) ────
    def Sxyz(pt: tuple[float, float, float]) -> tuple[float, float]:
        u, v = _project(Point3D("", *pt), scene.view)
        return off_x + (u - u_min) * scale, off_y + (v_max - v) * scale

    for g in scene.guides:
        gx1, gy1 = Sxyz(g.p0)
        gx2, gy2 = Sxyz(g.p1)
        gdash = ' stroke-dasharray="4,3"' if g.dashed else ""
        out.append(
            f'<line x1="{gx1:.1f}" y1="{gy1:.1f}" x2="{gx2:.1f}" y2="{gy2:.1f}"'
            f' stroke="{g.color}" stroke-width="{g.width}"{gdash}/>'
        )

    # ── edges (reusing geometry.py's screen-space mark helpers) ─────────────────
    for seg in scene.segments:
        x1, y1 = S(seg.p1)
        x2, y2 = S(seg.p2)
        dash = ' stroke-dasharray="5,3"' if seg.dashed else ""
        out.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"'
            f' stroke="{_STROKE}" stroke-width="1.6"{dash}/>'
        )
        if seg.arrows:
            out += _chevrons(x1, y1, x2, y2, seg.arrows, seg.mark_pos)
        if seg.ticks:
            out += _ticks(x1, y1, x2, y2, seg.ticks, seg.mark_pos)

    # ── angle marks (projected — orientation, not a faithful measure) ───────────
    for ang in scene.angles:
        vx, vy = S(ang.vertex)
        ax, ay = S(ang.a)
        bx, by = S(ang.b)
        out += _angle_mark(vx, vy, ax, ay, bx, by, ang)

    # ── vertices + labels ───────────────────────────────────────────────────────
    for p in scene.points:
        px, py = S(p.name)
        if p.dot:
            out.append(
                f'<circle cx="{px:.1f}" cy="{py:.1f}" r="2.1" fill="{_STROKE}"/>'
            )
        text = p.name if p.label is None else p.label
        if text:
            if p.label_dir is not None:
                dx, dy = p.label_dir[0], -p.label_dir[1]  # screen y is down
            else:
                dx, dy = px - cx, py - cy
            d = math.hypot(dx, dy) or 1.0
            lx = px + dx / d * 14
            ly = py + dy / d * 14
            out.append(
                f'<text x="{lx:.1f}" y="{ly + 4:.1f}" font-size="13"'
                f' text-anchor="middle" fill="{_LABEL}"'
                f' font-style="italic">{text}</text>'
            )

    if scene.axes:
        out += _axis_gnomon(scene.view, scene.pad + 16, scene.pad + 40)

    out.append("</svg>")
    return "\n".join(out)
