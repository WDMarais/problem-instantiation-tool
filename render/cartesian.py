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

# One palette for the whole graph family (see render/DESIGN.md). Data is blue and
# reference geometry is muted grey, mirroring the geometry renderer's convention so
# a function plot and a Euclidean figure read as the same product. Every label is
# drawn over a white glyph-halo (see `_text`) so it stays legible where it crosses a
# curve, a gridline or an axis.
_AXIS_COLOR = "#333333"  # axis lines
_GRID_COLOR = "#e0e0e0"  # gridlines
_TICK_COLOR = "#555555"  # numeric tick labels (margin furniture)
_CURVE_COLOR = "#2563EB"  # curves — and, by default, all data (points + their labels)
_POINT_COLOR = "#2563EB"  # a given point and its coordinate callout ("blue text")
_REFERENCE_COLOR = "#6B7280"  # asymptotes, radii — muted so data reads in front
_ACCENT_COLOR = "#DC2626"  # reserved emphasis, only when a caller asks for it
_HALO = "#FFFFFF"  # glyph-halo colour stroked behind every label

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
    color: str = _POINT_COLOR


@dataclass(frozen=True)
class Circle:
    """A circle centred at (cx, cy) with radius `r`, all in data coordinates.

    The emitter draws it as a native SVG ellipse whose radii follow the two axis
    scales, so it is faithful to the window→pixel transform. Set the scene's
    `equal_aspect` so the two scales match and it renders visually round."""

    cx: float
    cy: float
    r: float
    color: str = _CURVE_COLOR
    width: float = 2.0
    dashed: bool = False


@dataclass(frozen=True)
class Label:
    """Free text anchored at a data coordinate."""

    x: float
    y: float
    text: str
    color: str = _CURVE_COLOR
    anchor: str = "middle"  # SVG text-anchor: start | middle | end
    italic: bool = False


@dataclass(frozen=True)
class Band:
    """A translucent strip spanning the plot: horizontal ('h', between two y values,
    full width) or vertical ('v', between two x values, full height). Used for a
    range band or a highlighted x-interval. `edges` draws dashed lines at lo/hi."""

    orient: str  # 'h' | 'v'
    lo: float
    hi: float
    color: str = _CURVE_COLOR
    opacity: float = 0.1
    edges: bool = False


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
    equal_aspect: bool = False  # match x/y pixel scales (circles render round)
    x_tick_suffix: str = ""  # appended to each x label (e.g. "°" for degrees)
    y_tick_suffix: str = ""
    edge_ticks: bool = False  # labels at the plot edges + axis tick marks, and
    # keep the 0 label (for graphs whose axis sits mid-plot, e.g. a sinusoid)


# ── emitter ─────────────────────────────────────────────────────────────────


def _fmt(v: float) -> str:
    """Integer-valued floats render without a trailing '.0'; else 1 dp."""
    return f"{int(round(v))}" if abs(v - round(v)) < 1e-9 else f"{v:.1f}"


def _text(
    x: float,
    y: float,
    s: str,
    *,
    size: float,
    fill: str,
    anchor: str = "middle",
    italic: bool = False,
    family: str = "Georgia, serif",
) -> str:
    """A label with a white glyph halo (``paint-order="stroke"``): the fill text is
    drawn over a fat white outline of itself, so it stays legible over any curve,
    gridline or axis it lands on. Every ``<text>`` in the graph family goes through
    here — the same convention the geometry renderer already uses (render/geometry.py),
    so a plot and a Euclidean figure read as one product."""
    style = ' font-style="italic"' if italic else ""
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}"'
        f' text-anchor="{anchor}" fill="{fill}"{style} font-family="{family}"'
        f' paint-order="stroke" stroke="{_HALO}" stroke-width="3"'
        f' stroke-linejoin="round">{s}</text>'
    )


def _text_box(
    px: float, py: float, s: str, size: float, anchor: str
) -> tuple[float, float, float, float]:
    """Rough pixel bounding box (x1, y1, x2, y2) of a label of text `s` at baseline
    (`px`, `py`) with the given anchor. Width is a proportional-font estimate; it only
    has to be good enough to keep labels from stacking on each other."""
    w = 0.58 * size * len(s)
    if anchor == "start":
        x1, x2 = px, px + w
    elif anchor == "end":
        x1, x2 = px - w, px
    else:  # middle
        x1, x2 = px - w / 2, px + w / 2
    return (x1, py - size * 0.8, x2, py + size * 0.2)


def _overlap(a: tuple, b: tuple) -> bool:
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


class _LabelPlacer:
    """Greedy, deterministic placement for point callouts: try a small ring of
    offsets around the dot and take the first that clears every label / dot already
    placed (and stays inside the plot). The halo makes a label readable *over* the
    curve; this keeps two labels from landing on top of *each other*. Fixed-position
    labels (axis captions, asymptote tags, the 'turning point' note) are registered as
    obstacles via :meth:`block` but never moved."""

    # candidate (dx, dy) nudges in px; dy<0 is up. Ordered by preference: up-right
    # first, then the other quadrants, then further out.
    _CANDS = (
        (6, -6),
        (-6, -6),
        (6, 12),
        (-6, 12),
        (10, -16),
        (-10, -16),
        (14, -6),
        (-14, -6),
    )

    def __init__(self, ml: float, mt: float, pw: float, ph: float) -> None:
        self._boxes: list[tuple[float, float, float, float]] = []
        self._bounds = (ml, mt, ml + pw, mt + ph)

    def block(self, box: tuple[float, float, float, float]) -> None:
        self._boxes.append(box)

    def _fits(self, box: tuple) -> bool:
        bl, bt, br, bb = self._bounds
        # allow a little bleed past the plot edge, but reject a big overhang
        if box[0] < bl - 6 or box[2] > br + 6 or box[1] < bt - 6 or box[3] > bb + 6:
            return False
        return not any(_overlap(box, o) for o in self._boxes)

    def place(self, px: float, py: float, text: str, size: float, fill: str) -> str:
        # the dot itself is an obstacle for later labels
        chosen = None
        for dx, dy in self._CANDS:
            anchor = "start" if dx >= 0 else "end"
            box = _text_box(px + dx, py + dy, text, size, anchor)
            if self._fits(box):
                chosen = (px + dx, py + dy, anchor, box)
                break
        if chosen is None:  # nothing clear: fall back to up-right, place it anyway
            dx, dy = self._CANDS[0]
            anchor = "start"
            box = _text_box(px + dx, py + dy, text, size, anchor)
            chosen = (px + dx, py + dy, anchor, box)
        lx, ly, anchor, box = chosen
        self._boxes.append(box)
        return _text(lx, ly, text, size=size, fill=fill, anchor=anchor)


def render_scene(
    scene: CartesianScene,
    *,
    width: int = 300,
    height: int = 220,
    margins: tuple[int, int, int, int] | None = None,
) -> str:
    """Return an inline SVG string for `scene`. Pure data → pixels; no maths
    beyond the linear window→viewport transform. `margins` is (left, right, top,
    bottom) in pixels; a consumer that labels the plot edges (e.g. the trig graph)
    passes roomier margins."""
    global _counter
    _counter += 1
    clip_id = f"csc{_counter}"

    x_min, x_max = float(scene.x_min), float(scene.x_max)
    y_min, y_max = float(scene.y_min), float(scene.y_max)
    xspan = x_max - x_min or 1.0
    yspan = y_max - y_min or 1.0

    ml, mr, mt, mb = margins or (30, 16, 12, 24)  # left, right, top, bottom
    pw = width - ml - mr
    ph = height - mt - mb

    # equal aspect: grow the roomier axis so data-units-per-pixel match on both,
    # keeping each window centre fixed. A circle then renders round regardless of
    # the plot area's shape (matplotlib's set_aspect('equal')).
    if scene.equal_aspect:
        upp = max(xspan / pw, yspan / ph)  # target units per pixel
        new_xspan, new_yspan = upp * pw, upp * ph
        cx0, cy0 = (x_min + x_max) / 2, (y_min + y_max) / 2
        x_min, x_max = cx0 - new_xspan / 2, cx0 + new_xspan / 2
        y_min, y_max = cy0 - new_yspan / 2, cy0 + new_yspan / 2
        xspan, yspan = new_xspan, new_yspan

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
    placer = _LabelPlacer(ml, mt, pw, ph)

    # All text (axis captions, tick numbers, point callouts) is collected here and
    # emitted AFTER the primitives so its white halo sits on top of the curve /
    # asymptote / drop-lines it crosses — otherwise a later-drawn line paints over the
    # halo and the number reads cramped against it. Tick *marks* (the short axis
    # dashes) stay under, drawn inline below.
    axis_text: list[str] = []

    def _axis_label(x, y, s, **kw) -> None:
        placer.block(_text_box(x, y, s, kw.get("size", 9), kw.get("anchor", "middle")))
        axis_text.append(_text(x, y, s, **kw))

    if scene.x_label:
        _axis_label(
            ml + pw - 2,
            ax_y - 4,
            scene.x_label,
            size=13,
            fill=_AXIS_COLOR,
            anchor="end",
            italic=True,
        )
    if scene.y_label:
        _axis_label(
            ax_x + 4,
            mt + 8,
            scene.y_label,
            size=13,
            fill=_AXIS_COLOR,
            anchor="start",
            italic=True,
        )

    # axis tick labels. Default: near the axis, skipping 0. `edge_ticks`: at the
    # plot edges (bottom / left) with a short tick mark on the axis, 0 kept — for
    # graphs whose axis runs mid-plot (a sinusoid), where on-axis labels collide.
    edge = scene.edge_ticks
    for xt in scene.x_ticks:
        if not (x_min <= xt <= x_max) or (abs(xt) <= 1e-9 and not edge):
            continue
        xi = sx(xt)
        text = f"{_fmt(xt)}{scene.x_tick_suffix}"
        if edge:
            out.append(
                f'<line x1="{xi:.1f}" y1="{ax_y - 3:.1f}" x2="{xi:.1f}"'
                f' y2="{ax_y + 3:.1f}" stroke="{_AXIS_COLOR}" stroke-width="1"/>'
            )
            _axis_label(xi, mt + ph + 15, text, size=13, fill=_TICK_COLOR)
        else:
            _axis_label(xi, ax_y + 13, text, size=13, fill=_TICK_COLOR)
    for yt in scene.y_ticks:
        if not (y_min <= yt <= y_max) or (abs(yt) <= 1e-9 and not edge):
            continue
        yi = sy(yt)
        text = f"{_fmt(yt)}{scene.y_tick_suffix}"
        if edge:
            out.append(
                f'<line x1="{ax_x - 3:.1f}" y1="{yi:.1f}" x2="{ax_x + 3:.1f}"'
                f' y2="{yi:.1f}" stroke="{_AXIS_COLOR}" stroke-width="1"/>'
            )
        _axis_label(
            ax_x - (6 if edge else 5),
            yi + 3,
            text,
            size=13,
            fill=_TICK_COLOR,
            anchor="end",
        )

    # primitives, in declared order (later ones draw on top).
    deferred_points: list[tuple[Point, str]] = []
    for item in scene.items:
        out.extend(
            _emit_item(
                item,
                sx,
                sy,
                clip_id,
                ml,
                mt,
                pw,
                ph,
                ax_x,
                ax_y,
                placer,
                deferred_points,
            )
        )

    # on top of everything: axis numbers/captions (halo reads over the curve), then
    # the point callouts (nudged to dodge every dot and every label already placed).
    out.extend(axis_text)
    for pt, dot_svg in deferred_points:
        out.append(dot_svg)
        if pt.label is not None:
            out.append(placer.place(sx(pt.x), sy(pt.y), pt.label, 13, pt.color))

    out.append("</svg>")
    return "\n".join(out)


def _emit_item(
    item, sx, sy, clip_id, ml, mt, pw, ph, ax_x, ax_y, placer, deferred_points
) -> list[str]:
    if isinstance(item, Polyline):
        return _emit_polyline(item, sx, sy, clip_id)
    if isinstance(item, ConstantLine):
        return _emit_constline(item, sx, sy, ml, mt, pw, ph)
    if isinstance(item, Circle):
        return _emit_circle(item, sx, sy, clip_id)
    if isinstance(item, Band):
        return _emit_band(item, sx, sy, ml, mt, pw, ph)
    if isinstance(item, Point):
        # draw drop-lines + dot now (in declared z-order); defer the label so it can
        # avoid every fixed label and dot on the scene. The dot is registered as an
        # obstacle immediately so other callouts steer clear of it.
        dot_svg, defer = _emit_point(item, sx, sy, ax_x, ax_y, placer)
        if defer is not None:
            deferred_points.append(defer)
        return dot_svg
    if isinstance(item, Label):
        px, py = sx(item.x), sy(item.y)
        placer.block(_text_box(px, py, item.text, 12.5, item.anchor))
        return [
            _text(
                px,
                py,
                item.text,
                size=12.5,
                fill=item.color,
                anchor=item.anchor,
                italic=item.italic,
            )
        ]
    raise TypeError(f"CartesianScene cannot emit primitive of type {type(item)!r}")


def _emit_band(b: Band, sx, sy, ml, mt, pw, ph) -> list[str]:
    edge = ' stroke-dasharray="4,3"'
    if b.orient == "h":
        y_hi, y_lo = sy(b.hi), sy(b.lo)  # hi maps to the smaller pixel y (top)
        out = [
            f'<rect x="{ml}" y="{y_hi:.1f}" width="{pw}" height="{y_lo - y_hi:.1f}"'
            f' fill="{b.color}" opacity="{b.opacity}"/>'
        ]
        if b.edges:
            for py in (y_hi, y_lo):
                out.append(
                    f'<line x1="{ml}" y1="{py:.1f}" x2="{ml + pw}" y2="{py:.1f}"'
                    f' stroke="{b.color}" stroke-width="1.2"{edge} opacity="0.6"/>'
                )
        return out
    if b.orient == "v":
        x_lo, x_hi = sx(b.lo), sx(b.hi)
        out = [
            f'<rect x="{x_lo:.1f}" y="{mt}" width="{x_hi - x_lo:.1f}" height="{ph}"'
            f' fill="{b.color}" opacity="{b.opacity}"/>'
        ]
        if b.edges:
            for px in (x_lo, x_hi):
                out.append(
                    f'<line x1="{px:.1f}" y1="{mt}" x2="{px:.1f}" y2="{mt + ph}"'
                    f' stroke="{b.color}" stroke-width="1.2"{edge} opacity="0.6"/>'
                )
        return out
    raise ValueError(f"Band.orient must be 'h' or 'v', got {b.orient!r}")


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


def _emit_circle(c: Circle, sx, sy, clip_id) -> list[str]:
    # radii follow each axis scale independently → faithful to the transform;
    # with equal_aspect the two are equal, so it looks round.
    cx, cy = sx(c.cx), sy(c.cy)
    rx = abs(sx(c.cx + c.r) - cx)
    ry = abs(sy(c.cy + c.r) - cy)
    dash = ' stroke-dasharray="5,3"' if c.dashed else ""
    return [
        f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}"'
        f' fill="none" stroke="{c.color}" stroke-width="{c.width}"'
        f'{dash} clip-path="url(#{clip_id})"/>'
    ]


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
            out.append(_text(sx(cl.value), mt + 9, cl.label, size=13, fill=cl.color))
        else:
            out.append(
                _text(
                    ml + pw - 2,
                    sy(cl.value) - 3,
                    cl.label,
                    size=13,
                    fill=cl.color,
                    anchor="end",
                )
            )
    return out


def _emit_point(pt: Point, sx, sy, ax_x, ax_y, placer):
    """Emit the drop-lines and dot now (respecting declared z-order) and register the
    dot as an obstacle. The label is deferred: returns (svg_now, defer) where `defer`
    is `(pt, dot_svg)` or None — build_scene places every deferred label last so it can
    dodge the fixed labels and dots already on the scene."""
    px, py = sx(pt.x), sy(pt.y)
    # dot + drop-lines are neutral dark so they read on top of the blue curve; the
    # coordinate label carries the data colour (pt.color). Matches the geometry
    # renderer's dark dots / coloured value-labels convention.
    out: list[str] = []
    if pt.droplines:
        out.append(
            f'<line x1="{px:.1f}" y1="{py:.1f}" x2="{px:.1f}" y2="{ax_y:.1f}"'
            f' stroke="{_AXIS_COLOR}" stroke-width="1" stroke-dasharray="3,2"'
            f' opacity="0.55"/>'
        )
        out.append(
            f'<line x1="{px:.1f}" y1="{py:.1f}" x2="{ax_x:.1f}" y2="{py:.1f}"'
            f' stroke="{_AXIS_COLOR}" stroke-width="1" stroke-dasharray="3,2"'
            f' opacity="0.55"/>'
        )
    dot = f'<circle cx="{px:.1f}" cy="{py:.1f}" r="2.6" fill="{_AXIS_COLOR}"/>'
    # the dot is an obstacle for every label placed afterwards
    placer.block((px - 3, py - 3, px + 3, py + 3))
    if pt.label is None:
        out.append(dot)
        return out, None
    # defer just the label+dot so its placement sees every later dot too
    return out, (pt, dot)
