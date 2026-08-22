"""
CartesianScene — a coordinate-frame figure (function plots + analytic geometry)
and its dumb SVG emitter.

This is the shared spine promised in ``render/DESIGN.md``: a *pure data* scene (a
window plus a list of primitives in data coordinates) and a renderer that does
nothing but map data → pixels and draw. All domain knowledge (sampling a curve,
computing a vertex, splitting a hyperbola at its asymptote) lives in the per-family
*builders* (``render/parabola.py``, …) that construct a scene — never here.

The pixel-transform spine (``sx``/``sy``, margins, grid, ticks, clip) is lifted
from the proven ``render/graph.py`` trig renderer and generalised off sinusoids:
axes carry a numeric label mode, the curve is any sampled polyline, and points /
constant-lines are first-class. ``graph.py`` is deliberately left untouched — the
design marks porting trig onto this scene as a later follow-up.

Primitive vocabulary (a subset of the DESIGN.md matrix; grown per consumer):

    Polyline(points, color, width, dashed)   — a sampled curve (breaks: emit two)
    ConstantLine(orient, value, ...)          — dashed h/v line (axis of symmetry)
    Point(x, y, label, droplines)             — a dot, optional label + drop-lines
    Label(x, y, text, anchor)                 — free text at a coordinate

Display-only is a hard rule (see DESIGN.md): the *generator* bakes every answer;
a scene is orientation material, never a measurement instrument.
"""

from __future__ import annotations

from dataclasses import dataclass

_AXIS_COLOR = "#333333"
_GRID_COLOR = "#e0e0e0"
_CURVE_COLOR = "#2563EB"
_ACCENT_COLOR = "#DC2626"

_counter = 0


# ── primitives ────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Polyline:
    """A sampled curve in data coordinates. A `None` point marks a break (the
    emitter starts a fresh sub-polyline), so a discontinuity leaves a real gap
    rather than a false vertical streak across an asymptote."""

    points: tuple[tuple[float, float] | None, ...]
    color: str = _CURVE_COLOR
    width: float = 2.0
    dashed: bool = False


@dataclass(frozen=True)
class ConstantLine:
    """A dashed horizontal ('h') or vertical ('v') reference line at `value`."""

    orient: str  # 'h' | 'v'
    value: float
    color: str = _ACCENT_COLOR
    label: str | None = None


@dataclass(frozen=True)
class Point:
    """A dot at (x, y), optional text label and dashed drop-lines to both axes."""

    x: float
    y: float
    label: str | None = None
    droplines: bool = False
    color: str = _AXIS_COLOR


@dataclass(frozen=True)
class Label:
    """Free text anchored at a data coordinate."""

    x: float
    y: float
    text: str
    color: str = _AXIS_COLOR
    anchor: str = "middle"  # SVG text-anchor: start | middle | end


@dataclass(frozen=True)
class CartesianScene:
    """A window plus a list of primitives, all in data coordinates.

    `x_ticks` / `y_ticks` are the numeric gridline/label positions; the builder
    picks them (it knows which values are meaningful — roots, the vertex, 0)."""

    x_min: float
    x_max: float
    y_min: float
    y_max: float
    items: tuple[object, ...] = ()
    x_ticks: tuple[float, ...] = ()
    y_ticks: tuple[float, ...] = ()
    x_label: str = "x"
    y_label: str = "y"


# ── emitter ─────────────────────────────────────────────────────────────────


def _fmt(v: float) -> str:
    """Integer-valued floats render without a trailing '.0'; else 1 dp."""
    return f"{int(round(v))}" if abs(v - round(v)) < 1e-9 else f"{v:.1f}"


def render_scene(scene: CartesianScene, *, width: int = 300, height: int = 220) -> str:
    """Return an inline SVG string for `scene`. Pure data → pixels; no maths
    beyond the linear window→viewport transform."""
    global _counter
    _counter += 1
    clip_id = f"csc{_counter}"

    x_min, x_max = float(scene.x_min), float(scene.x_max)
    y_min, y_max = float(scene.y_min), float(scene.y_max)
    xspan = x_max - x_min or 1.0
    yspan = y_max - y_min or 1.0

    ml, mr, mt, mb = 30, 16, 12, 24  # margins: left, right, top, bottom
    pw = width - ml - mr
    ph = height - mt - mb

    def sx(xd: float) -> float:
        return ml + (xd - x_min) / xspan * pw

    def sy(yv: float) -> float:
        return mt + (y_max - yv) / yspan * ph

    # axis lines clamped into the plot area (so an off-window origin still draws)
    ax_y = min(max(sy(0.0), mt), mt + ph)  # the x-axis (y = 0)
    ax_x = min(max(sx(0.0), ml), ml + pw)  # the y-axis (x = 0)

    out: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"'
        f' viewBox="0 0 {width} {height}"'
        f' style="display:block;max-width:100%;height:auto">',
        f'<defs><clipPath id="{clip_id}">'
        f'<rect x="{ml}" y="{mt}" width="{pw}" height="{ph}"/>'
        f"</clipPath></defs>",
    ]

    # grid
    for xt in scene.x_ticks:
        if x_min <= xt <= x_max:
            xi = sx(xt)
            out.append(
                f'<line x1="{xi:.1f}" y1="{mt}" x2="{xi:.1f}" y2="{mt + ph}"'
                f' stroke="{_GRID_COLOR}" stroke-width="1"/>'
            )
    for yt in scene.y_ticks:
        if y_min <= yt <= y_max:
            yi = sy(yt)
            out.append(
                f'<line x1="{ml}" y1="{yi:.1f}" x2="{ml + pw}" y2="{yi:.1f}"'
                f' stroke="{_GRID_COLOR}" stroke-width="1"/>'
            )

    # axes
    out.append(
        f'<line x1="{ml}" y1="{ax_y:.1f}" x2="{ml + pw}" y2="{ax_y:.1f}"'
        f' stroke="{_AXIS_COLOR}" stroke-width="1.5"/>'
    )
    out.append(
        f'<line x1="{ax_x:.1f}" y1="{mt}" x2="{ax_x:.1f}" y2="{mt + ph}"'
        f' stroke="{_AXIS_COLOR}" stroke-width="1.5"/>'
    )
    out.append(
        f'<text x="{ml + pw - 2:.1f}" y="{ax_y - 4:.1f}" font-size="10"'
        f' text-anchor="end" font-style="italic" fill="{_AXIS_COLOR}"'
        f' font-family="serif">{scene.x_label}</text>'
    )
    out.append(
        f'<text x="{ax_x + 4:.1f}" y="{mt + 8:.1f}" font-size="10"'
        f' font-style="italic" fill="{_AXIS_COLOR}"'
        f' font-family="serif">{scene.y_label}</text>'
    )

    # axis tick labels (numeric, skipping 0 to avoid clutter at the origin)
    for xt in scene.x_ticks:
        if x_min <= xt <= x_max and abs(xt) > 1e-9:
            out.append(
                f'<text x="{sx(xt):.1f}" y="{ax_y + 13:.1f}" font-size="9"'
                f' text-anchor="middle" fill="#555"'
                f' font-family="sans-serif">{_fmt(xt)}</text>'
            )
    for yt in scene.y_ticks:
        if y_min <= yt <= y_max and abs(yt) > 1e-9:
            out.append(
                f'<text x="{ax_x - 5:.1f}" y="{sy(yt) + 3:.1f}" font-size="9"'
                f' text-anchor="end" fill="#555"'
                f' font-family="sans-serif">{_fmt(yt)}</text>'
            )

    # primitives, in declared order (later ones draw on top)
    for item in scene.items:
        out.extend(_emit_item(item, sx, sy, clip_id, ml, mt, pw, ph, ax_x, ax_y))

    out.append("</svg>")
    return "\n".join(out)


def _emit_item(item, sx, sy, clip_id, ml, mt, pw, ph, ax_x, ax_y) -> list[str]:
    if isinstance(item, Polyline):
        return _emit_polyline(item, sx, sy, clip_id)
    if isinstance(item, ConstantLine):
        return _emit_constline(item, sx, sy, ml, mt, pw, ph)
    if isinstance(item, Point):
        return _emit_point(item, sx, sy, ax_x, ax_y)
    if isinstance(item, Label):
        return [
            f'<text x="{sx(item.x):.1f}" y="{sy(item.y):.1f}" font-size="10"'
            f' text-anchor="{item.anchor}" fill="{item.color}"'
            f' font-family="sans-serif">{item.text}</text>'
        ]
    raise TypeError(f"CartesianScene cannot emit primitive of type {type(item)!r}")


def _emit_polyline(pl: Polyline, sx, sy, clip_id) -> list[str]:
    dash = ' stroke-dasharray="5,3"' if pl.dashed else ""
    out: list[str] = []
    run: list[str] = []

    def flush() -> None:
        if len(run) >= 2:
            out.append(
                f'<polyline points="{" ".join(run)}" fill="none"'
                f' stroke="{pl.color}" stroke-width="{pl.width}"'
                f' stroke-linejoin="round" stroke-linecap="round"'
                f'{dash} clip-path="url(#{clip_id})"/>'
            )
        run.clear()

    for pt in pl.points:
        if pt is None:  # break: end this sub-polyline, start a fresh one
            flush()
            continue
        run.append(f"{sx(pt[0]):.1f},{sy(pt[1]):.1f}")
    flush()
    return out


def _emit_constline(cl: ConstantLine, sx, sy, ml, mt, pw, ph) -> list[str]:
    if cl.orient == "v":
        xi = sx(cl.value)
        line = (
            f'<line x1="{xi:.1f}" y1="{mt}" x2="{xi:.1f}" y2="{mt + ph}"'
            f' stroke="{cl.color}" stroke-width="1.3" stroke-dasharray="4,3"/>'
        )
    elif cl.orient == "h":
        yi = sy(cl.value)
        line = (
            f'<line x1="{ml}" y1="{yi:.1f}" x2="{ml + pw}" y2="{yi:.1f}"'
            f' stroke="{cl.color}" stroke-width="1.3" stroke-dasharray="4,3"/>'
        )
    else:
        raise ValueError(f"ConstantLine.orient must be 'h' or 'v', got {cl.orient!r}")
    out = [line]
    if cl.label is not None:
        if cl.orient == "v":
            out.append(
                f'<text x="{sx(cl.value):.1f}" y="{mt + 9:.1f}" font-size="9"'
                f' text-anchor="middle" fill="{cl.color}"'
                f' font-family="sans-serif">{cl.label}</text>'
            )
        else:
            out.append(
                f'<text x="{ml + pw - 2:.1f}" y="{sy(cl.value) - 3:.1f}"'
                f' font-size="9" text-anchor="end" fill="{cl.color}"'
                f' font-family="sans-serif">{cl.label}</text>'
            )
    return out


def _emit_point(pt: Point, sx, sy, ax_x, ax_y) -> list[str]:
    px, py = sx(pt.x), sy(pt.y)
    out: list[str] = []
    if pt.droplines:
        out.append(
            f'<line x1="{px:.1f}" y1="{py:.1f}" x2="{px:.1f}" y2="{ax_y:.1f}"'
            f' stroke="{pt.color}" stroke-width="1" stroke-dasharray="3,2"'
            f' opacity="0.7"/>'
        )
        out.append(
            f'<line x1="{px:.1f}" y1="{py:.1f}" x2="{ax_x:.1f}" y2="{py:.1f}"'
            f' stroke="{pt.color}" stroke-width="1" stroke-dasharray="3,2"'
            f' opacity="0.7"/>'
        )
    out.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="2.6" fill="{pt.color}"/>')
    if pt.label is not None:
        # place the label up-and-right of the dot, nudged to stay off the curve
        out.append(
            f'<text x="{px + 5:.1f}" y="{py - 5:.1f}" font-size="9.5"'
            f' fill="{pt.color}" font-family="sans-serif">{pt.label}</text>'
        )
    return out
