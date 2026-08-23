"""
Trig graph rendering — now a *builder* over the shared ``CartesianScene`` spine.

This used to be a standalone SVG emitter; it now translates a trig graph encoding
into a ``CartesianScene`` (window + primitives) and defers all pixel work to
``render/cartesian.py``'s ``render_scene``. The domain knowledge that stays here is
exactly the trig-specific part: the y-extent from amplitude/offset, the degree-based
x-tick step, and sampling each sinusoid. Everything generic (axes, grid, clip, tick
marks, the window→pixel transform) lives in the emitter — DRY at the emitter, as
``render/DESIGN.md`` intends.

Graph encoding format (as stored in params["graph"] by trig_graph_properties.py):
    {
        "curves": [
            {
                "id": str,              # label shown on graph when multiple curves
                "func": "sin" | "cos",
                "amplitude": float,
                "period_deg": float,    # 360 for n=1, 180 for n=2
                "phase_shift_deg": float,  # optional, default 0; added to argument
                "offset": float,           # optional, default 0; vertical shift
            },
            ...
        ],
        "x_domain_deg": [x_min, x_max],
        "k_line": float,    # optional horizontal line (for solve problems)
    }

Optional overlays (passed to render_trig_graph):
    range_band     (y_lo, y_hi)  — horizontal shaded strip showing the range
    highlight_x    (x_lo, x_hi)  — vertical shaded strip (e.g. decreasing interval)
"""

from __future__ import annotations

import math

from render.cartesian import (
    Band,
    CartesianScene,
    ConstantLine,
    Label,
    Polyline,
    render_scene,
)

_CURVE_COLORS = ["#2563EB", "#DC2626", "#16A34A", "#9333EA"]
_K_LINE_COLOR = "#16A34A"
_RANGE_COLOR = "#2563EB"
_HIGHLIGHT_COLOR = "#DC2626"

_TRIG_MARGINS = (34, 26, 12, 26)  # roomier than the default: degree + edge labels
_N_SAMPLES = 400


def _fmt_num(v: float) -> str:
    return f"{int(round(v))}" if abs(v - round(v)) < 0.01 else f"{v:.1f}"


def _sample_curve(curve: dict, x_min: float, x_max: float) -> tuple:
    func = curve["func"]
    amp = float(curve["amplitude"])
    period = float(curve["period_deg"])
    phase = float(curve.get("phase_shift_deg", 0))
    offset = float(curve.get("offset", 0))

    def y_at(xd: float) -> float:
        angle = 2 * math.pi * xd / period + math.radians(phase)
        wave = math.sin(angle) if func == "sin" else math.cos(angle)
        return amp * wave + offset

    pts = []
    for i in range(_N_SAMPLES + 1):
        xd = x_min + (x_max - x_min) * i / _N_SAMPLES
        pts.append((xd, y_at(xd)))
    return tuple(pts), y_at(x_max)


def trig_scene(
    graph: dict,
    *,
    range_band: tuple[float, float] | None = None,
    highlight_x: tuple[float, float] | None = None,
) -> CartesianScene:
    """Translate a trig graph encoding into a ``CartesianScene``."""
    curves = graph["curves"]
    x_min = float(graph["x_domain_deg"][0])
    x_max = float(graph["x_domain_deg"][1])
    k_line = graph.get("k_line")
    k_line = float(k_line) if k_line is not None else None

    # ── y-extent from amplitude/offset (+ k-line, band), padded ──
    y_extremes = [0.0]
    for c in curves:
        off, amp = float(c.get("offset", 0)), float(c["amplitude"])
        y_extremes += [off + amp, off - amp]
    if k_line is not None:
        y_extremes.append(k_line)
    if range_band is not None:
        y_extremes += list(range_band)
    span = max(max(y_extremes) - min(y_extremes), 1.0)
    pad = span * 0.18
    y_max, y_min = max(y_extremes) + pad, min(y_extremes) - pad

    # ── x ticks: quarter-period, snapped to a nice degree step ──
    x_step = float(curves[0]["period_deg"]) / 4.0
    for nice in (15, 30, 45, 90, 180):
        if abs(nice - x_step) < x_step * 0.6:
            x_step = float(nice)
            break
    x_ticks = []
    t = math.ceil(x_min / x_step - 1e-9) * x_step
    while t <= x_max + 1e-9:
        x_ticks.append(t)
        t += x_step

    # ── y ticks: 0, each curve's max/min/offset, k-line, band edges ──
    y_tick_set = {0.0}
    for c in curves:
        off, amp = float(c.get("offset", 0)), float(c["amplitude"])
        y_tick_set.update([off + amp, off - amp])
        if off != 0.0:
            y_tick_set.add(off)
    if k_line is not None:
        y_tick_set.add(k_line)
    if range_band is not None:
        y_tick_set.update(range_band)
    y_ticks = sorted(v for v in y_tick_set if y_min <= v <= y_max)

    # ── items: bands (under) → k-line → curves → curve labels (over) ──
    items: list[object] = []
    if range_band is not None:
        items.append(
            Band("h", range_band[0], range_band[1], color=_RANGE_COLOR, edges=True)
        )
    if highlight_x is not None:
        items.append(
            Band(
                "v",
                highlight_x[0],
                highlight_x[1],
                color=_HIGHLIGHT_COLOR,
                opacity=0.09,
            )
        )
    if k_line is not None:
        items.append(
            ConstantLine("h", k_line, color=_K_LINE_COLOR, label=_fmt_num(k_line))
        )

    multi = len(curves) > 1
    labels: list[object] = []
    for idx, curve in enumerate(curves):
        color = _CURVE_COLORS[idx % len(_CURVE_COLORS)]
        pts, y_end = _sample_curve(curve, x_min, x_max)
        items.append(Polyline(points=pts, color=color))
        if multi:
            labels.append(
                Label(
                    x_max,
                    y_end,
                    curve.get("id", f"f{idx + 1}"),
                    color=color,
                    anchor="start",
                    italic=True,
                )
            )
    items.extend(labels)

    return CartesianScene(
        x_min=x_min,
        x_max=x_max,
        y_min=y_min,
        y_max=y_max,
        items=tuple(items),
        x_ticks=tuple(x_ticks),
        y_ticks=tuple(y_ticks),
        x_label="",  # trig graphs don't carry the italic x/y axis captions
        y_label="",
        x_tick_suffix="°",
        edge_ticks=True,
    )


def render_trig_graph(
    graph: dict,
    *,
    range_band: tuple[float, float] | None = None,
    highlight_x: tuple[float, float] | None = None,
    width: int = 320,
    height: int = 200,
) -> str:
    """Return an inline SVG string for the given trig graph encoding."""
    scene = trig_scene(graph, range_band=range_band, highlight_x=highlight_x)
    return render_scene(scene, width=width, height=height, margins=_TRIG_MARGINS)
