"""
SVG renderer for Euclidean geometry figures (no coordinate frame).

Unlike render/graph.py — which is Cartesian, metric, and axes-bound — a
GeometryFigure lives in abstract *layout* coordinates: positions are chosen for
legibility and are deliberately NOT to scale. The figure is display-only: the
generator bakes the answer (e.g. the value of angle x); nothing is read off the
drawing.

Layout coordinates are y-up (mathematical convention). The renderer fits the
bounding box of all points into the viewBox and flips y for SVG.

See render/DESIGN.md for the GeometryFigure primitive vocabulary.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

_STROKE = "#333333"
_LABEL = "#111111"
_MARK = "#2563EB"  # angle / parallel / tick marks — blue, distinct from outline


@dataclass(frozen=True)
class Point:
    name: str  # unique id, referenced by Segment/Angle; default label text too
    x: float
    y: float
    dot: bool = True  # False = no marker dot (e.g. a construction-line endpoint)
    label: str | None = None  # display text: None = use name; "" = draw no label
    label_dir: tuple[float, float] | None = None  # layout-space (x→right, y→up),
    # figure-relative push direction for the label (rotates/reflects with the pose);
    # None = radially outward from the centroid


@dataclass(frozen=True)
class Segment:
    p1: str  # point name
    p2: str  # point name
    arrows: int = 0  # parallel-mark chevrons: 0 none, 1 single, 2 double
    ticks: int = 0  # equal-length tick marks: 0..3
    dashed: bool = False
    mark_pos: float = 0.5  # fraction along p1->p2 for chevrons/ticks (0.5 = midpoint)


@dataclass(frozen=True)
class Angle:
    vertex: str  # point name
    a: str  # point naming the first ray (vertex -> a)
    b: str  # point naming the second ray (vertex -> b)
    label: str = ""  # plain text shown in the arc, e.g. "x" or "70°"
    arcs: int = 1  # concentric arcs (equal-angle marks)
    right: bool = False  # draw a right-angle square instead of an arc


@dataclass(frozen=True)
class Pose:
    """A similarity transform applied for visual variety: optional reflection,
    rotation by any angle, and a uniform scale given as a *fraction of the
    viewport-fill size* (~0.7-1.0). Similarities preserve angles, so drawn angles
    stay faithful to their labels no matter the orientation or size. Shape variety
    (acute angle, side ratio) belongs to the figure, not the pose."""

    rotate_deg: float = 0.0
    scale: float = 1.0  # fraction of the fit-to-viewport size; clamps figure inside
    reflect: bool = False


@dataclass
class GeometryFigure:
    points: list[Point]
    segments: list[Segment] = field(default_factory=list)
    angles: list[Angle] = field(default_factory=list)
    pose: Pose = field(default_factory=Pose)
    width: int = 300
    height: int = 230
    pad: int = 30


def render_figure(fig: GeometryFigure) -> str:
    # ── apply the pose (similarity transform) about the figure's centroid ──────
    n = len(fig.points)
    c0x = sum(p.x for p in fig.points) / n
    c0y = sum(p.y for p in fig.points) / n
    th = math.radians(fig.pose.rotate_deg)
    cos_t, sin_t = math.cos(th), math.sin(th)
    sgn = -1.0 if fig.pose.reflect else 1.0  # reflect across the vertical axis

    wpts: dict[str, tuple[float, float]] = {}
    for p in fig.points:
        dx = (p.x - c0x) * sgn
        dy = p.y - c0y
        wpts[p.name] = (
            c0x + dx * cos_t - dy * sin_t,
            c0y + dx * sin_t + dy * cos_t,
        )

    xs = [x for x, _ in wpts.values()]
    ys = [y for _, y in wpts.values()]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    span_x = max(x_max - x_min, 1e-9)
    span_y = max(y_max - y_min, 1e-9)

    avail_w = fig.width - 2 * fig.pad
    avail_h = fig.height - 2 * fig.pad
    # fit-to-viewport size for this pose, then shrink to the requested fraction
    s_fill = min(avail_w / span_x, avail_h / span_y)
    scale = s_fill * max(0.05, min(fig.pose.scale, 1.0))

    # centre the (possibly inset) figure within the available area
    used_w = span_x * scale
    used_h = span_y * scale
    off_x = fig.pad + (avail_w - used_w) / 2
    off_y = fig.pad + (avail_h - used_h) / 2

    def sx(x: float) -> float:
        return off_x + (x - x_min) * scale

    def sy(y: float) -> float:
        # flip: layout y-up -> screen y-down
        return off_y + (y_max - y) * scale

    def S(name: str) -> tuple[float, float]:
        wx, wy = wpts[name]
        return sx(wx), sy(wy)

    # screen-space centroid, used to push labels outward
    cx = sum(sx(wx) for wx, _ in wpts.values()) / n
    cy = sum(sy(wy) for _, wy in wpts.values()) / n

    out: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{fig.width}"'
        f' height="{fig.height}" viewBox="0 0 {fig.width} {fig.height}"'
        f' style="display:block;max-width:100%;height:auto"'
        f' font-family="Georgia, serif">'
    ]

    # ── segments ──────────────────────────────────────────────────────────────
    for seg in fig.segments:
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

    # ── angle marks ───────────────────────────────────────────────────────────
    for ang in fig.angles:
        vx, vy = S(ang.vertex)
        ax, ay = S(ang.a)
        bx, by = S(ang.b)
        out += _angle_mark(vx, vy, ax, ay, bx, by, ang)

    # ── vertices + labels ─────────────────────────────────────────────────────
    for p in fig.points:
        px, py = S(p.name)
        if p.dot:
            out.append(
                f'<circle cx="{px:.1f}" cy="{py:.1f}" r="2.1" fill="{_STROKE}"/>'
            )
        text = p.name if p.label is None else p.label
        if text:
            if p.label_dir is not None:
                # figure-relative (layout y-up): reflect, rotate, then flip to screen
                ldx, ldy = p.label_dir[0] * sgn, p.label_dir[1]
                dx = ldx * cos_t - ldy * sin_t
                dy = -(ldx * sin_t + ldy * cos_t)
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

    out.append("</svg>")
    return "\n".join(out)


# ── primitive helpers ──────────────────────────────────────────────────────────


def _unit(dx: float, dy: float) -> tuple[float, float]:
    d = math.hypot(dx, dy) or 1.0
    return dx / d, dy / d


def _chevrons(
    x1: float, y1: float, x2: float, y2: float, n: int, pos: float = 0.5
) -> list[str]:
    """`n` ">" chevrons at `pos` along the segment, pointing along it."""
    mx, my = x1 + (x2 - x1) * pos, y1 + (y2 - y1) * pos
    ux, uy = _unit(x2 - x1, y2 - y1)  # along
    px, py = -uy, ux  # perpendicular
    size = 5.0
    gap = 4.0
    out: list[str] = []
    # spread n chevrons symmetrically about the midpoint along the segment
    starts = [(i - (n - 1) / 2) * gap for i in range(n)]
    for s in starts:
        tipx, tipy = mx + ux * s, my + uy * s  # forward point of the ">"
        a1x, a1y = tipx - ux * size + px * size, tipy - uy * size + py * size
        a2x, a2y = tipx - ux * size - px * size, tipy - uy * size - py * size
        out.append(
            f'<polyline points="{a1x:.1f},{a1y:.1f} {tipx:.1f},{tipy:.1f}'
            f' {a2x:.1f},{a2y:.1f}" fill="none" stroke="{_MARK}"'
            f' stroke-width="1.4"/>'
        )
    return out


def _ticks(
    x1: float, y1: float, x2: float, y2: float, n: int, pos: float = 0.5
) -> list[str]:
    """`n` short perpendicular tick marks at `pos` along the segment."""
    mx, my = x1 + (x2 - x1) * pos, y1 + (y2 - y1) * pos
    ux, uy = _unit(x2 - x1, y2 - y1)
    px, py = -uy, ux
    half = 5.0
    gap = 3.5
    out: list[str] = []
    starts = [(i - (n - 1) / 2) * gap for i in range(n)]
    for s in starts:
        bx, by = mx + ux * s, my + uy * s
        out.append(
            f'<line x1="{bx - px * half:.1f}" y1="{by - py * half:.1f}"'
            f' x2="{bx + px * half:.1f}" y2="{by + py * half:.1f}"'
            f' stroke="{_MARK}" stroke-width="1.4"/>'
        )
    return out


def _angle_mark(
    vx: float,
    vy: float,
    ax: float,
    ay: float,
    bx: float,
    by: float,
    ang: Angle,
) -> list[str]:
    """Arc (or right-angle square) at vertex V between rays V->A and V->B."""
    ua = _unit(ax - vx, ay - vy)
    ub = _unit(bx - vx, by - vy)
    out: list[str] = []

    if ang.right:
        q = 11.0
        c1x, c1y = vx + ua[0] * q, vy + ua[1] * q
        c2x, c2y = vx + ua[0] * q + ub[0] * q, vy + ua[1] * q + ub[1] * q
        c3x, c3y = vx + ub[0] * q, vy + ub[1] * q
        out.append(
            f'<polyline points="{c1x:.1f},{c1y:.1f} {c2x:.1f},{c2y:.1f}'
            f' {c3x:.1f},{c3y:.1f}" fill="none" stroke="{_MARK}"'
            f' stroke-width="1.4"/>'
        )
        return out

    # Sample the arc as a polyline rather than use SVG's A command: the arc
    # command's sweep flag is ambiguous (it can centre the arc on the chord's
    # mirror point), whereas sampling from theta1 across the minor sweep is
    # guaranteed centred on the vertex.
    t1 = math.atan2(ua[1], ua[0])
    t2 = math.atan2(ub[1], ub[0])
    delta = math.atan2(math.sin(t2 - t1), math.cos(t2 - t1))  # minor signed sweep
    base_r = 17.0
    for i in range(ang.arcs):
        r = base_r + i * 4.0
        steps = 14
        pts = [
            f"{vx + r * math.cos(t1 + delta * k / steps):.1f},"
            f"{vy + r * math.sin(t1 + delta * k / steps):.1f}"
            for k in range(steps + 1)
        ]
        out.append(
            f'<polyline points="{" ".join(pts)}" fill="none"'
            f' stroke="{_MARK}" stroke-width="1.4"/>'
        )

    if ang.label:
        bis = _unit(ua[0] + ub[0], ua[1] + ub[1])
        lr = base_r + (ang.arcs - 1) * 4.0 + 12.0
        lx, ly = vx + bis[0] * lr, vy + bis[1] * lr
        out.append(
            f'<text x="{lx:.1f}" y="{ly + 4:.1f}" font-size="12.5"'
            f' text-anchor="middle" fill="{_MARK}">{ang.label}</text>'
        )
    return out
