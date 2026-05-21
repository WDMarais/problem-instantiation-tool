"""
SVG renderer for trig graph encodings.

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

_CURVE_COLORS = ["#2563EB", "#DC2626", "#16A34A", "#9333EA"]
_AXIS_COLOR = "#333333"
_GRID_COLOR = "#e0e0e0"
_K_LINE_COLOR = "#16A34A"

_counter = 0


def render_trig_graph(
    graph: dict,
    *,
    range_band: tuple[float, float] | None = None,
    highlight_x: tuple[float, float] | None = None,
    width: int = 320,
    height: int = 200,
) -> str:
    """Return an inline SVG string for the given trig graph encoding."""
    global _counter
    _counter += 1
    clip_id = f"tgc{_counter}"

    curves = graph["curves"]
    x_min = float(graph["x_domain_deg"][0])
    x_max = float(graph["x_domain_deg"][1])
    k_line: float | None = graph.get("k_line")
    if k_line is not None:
        k_line = float(k_line)

    # ── y-axis extent ──────────────────────────────────────────────────────────
    y_extremes: list[float] = [0.0]
    for c in curves:
        off = float(c.get("offset", 0))
        amp = float(c["amplitude"])
        y_extremes += [off + amp, off - amp]
    if k_line is not None:
        y_extremes.append(k_line)
    if range_band is not None:
        y_extremes += list(range_band)

    y_data_max = max(y_extremes)
    y_data_min = min(y_extremes)
    span = max(y_data_max - y_data_min, 1.0)
    pad = span * 0.18
    y_max = y_data_max + pad
    y_min = y_data_min - pad

    # ── plot geometry ─────────────────────────────────────────────────────────
    ml, mr, mt, mb = 34, 26, 12, 26  # margins: left, right, top, bottom
    pw = width - ml - mr
    ph = height - mt - mb

    def sx(xd: float) -> float:
        return ml + (xd - x_min) / (x_max - x_min) * pw

    def sy(yv: float) -> float:
        return mt + (y_max - yv) / (y_max - y_min) * ph

    # axis intercepts, clamped to plot area
    ax_y = min(max(sy(0.0), mt), mt + ph)
    ax_x = min(max(sx(0.0), ml), ml + pw)

    # ── tick positions ────────────────────────────────────────────────────────
    first_period = float(curves[0]["period_deg"])
    x_step = first_period / 4.0
    # snap to nearest nice integer step
    for nice in [15, 30, 45, 90, 180]:
        if abs(nice - x_step) < x_step * 0.6:
            x_step = float(nice)
            break

    x_ticks: list[float] = []
    t = math.ceil(x_min / x_step - 1e-9) * x_step
    while t <= x_max + 1e-9:
        x_ticks.append(t)
        t += x_step

    y_tick_set: set[float] = {0.0}
    for c in curves:
        off = float(c.get("offset", 0))
        amp = float(c["amplitude"])
        y_tick_set.update([off + amp, off - amp])
        if off != 0.0:
            y_tick_set.add(off)
    if k_line is not None:
        y_tick_set.add(k_line)
    if range_band is not None:
        y_tick_set.update(range_band)
    y_ticks = sorted(v for v in y_tick_set if y_min <= v <= y_max)

    # ── assemble SVG ──────────────────────────────────────────────────────────
    out: list[str] = []

    out.append(
        f'<svg xmlns="http://www.w3.org/2000/svg"'
        f' width="{width}" height="{height}"'
        f' viewBox="0 0 {width} {height}"'
        f' style="display:block;max-width:100%;height:auto">'
    )
    out.append(
        f"<defs>"
        f'<clipPath id="{clip_id}">'
        f'<rect x="{ml}" y="{mt}" width="{pw}" height="{ph}"/>'
        f"</clipPath>"
        f"</defs>"
    )

    # shaded bands (drawn before grid so they sit underneath)
    if range_band is not None:
        ry1 = sy(range_band[1])
        ry2 = sy(range_band[0])
        out.append(
            f'<rect x="{ml}" y="{ry1:.1f}" width="{pw}" height="{ry2 - ry1:.1f}"'
            f' fill="#2563EB" opacity="0.10"/>'
        )
    if highlight_x is not None:
        hx1 = sx(highlight_x[0])
        hx2 = sx(highlight_x[1])
        out.append(
            f'<rect x="{hx1:.1f}" y="{mt}" width="{hx2 - hx1:.1f}" height="{ph}"'
            f' fill="#DC2626" opacity="0.09"/>'
        )

    # grid
    for xt in x_ticks:
        xi = sx(xt)
        out.append(
            f'<line x1="{xi:.1f}" y1="{mt}" x2="{xi:.1f}" y2="{mt + ph}"'
            f' stroke="{_GRID_COLOR}" stroke-width="1"/>'
        )
    for yt in y_ticks:
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

    # k-line
    if k_line is not None:
        kyi = sy(k_line)
        out.append(
            f'<line x1="{ml}" y1="{kyi:.1f}" x2="{ml + pw}" y2="{kyi:.1f}"'
            f' stroke="{_K_LINE_COLOR}" stroke-width="1.5" stroke-dasharray="5,3"/>'
        )
        k_label = (
            f"{int(round(k_line))}"
            if abs(k_line - round(k_line)) < 0.01
            else f"{k_line:.1f}"
        )
        out.append(
            f'<text x="{ml + pw + 4:.1f}" y="{kyi + 3:.1f}"'
            f' font-size="9" fill="{_K_LINE_COLOR}" font-family="sans-serif">{k_label}</text>'
        )

    # x-axis tick marks + labels
    for xt in x_ticks:
        xi = sx(xt)
        out.append(
            f'<line x1="{xi:.1f}" y1="{ax_y - 3:.1f}" x2="{xi:.1f}" y2="{ax_y + 3:.1f}"'
            f' stroke="{_AXIS_COLOR}" stroke-width="1"/>'
        )
        out.append(
            f'<text x="{xi:.1f}" y="{mt + ph + 17:.1f}"'
            f' font-size="9" text-anchor="middle" fill="#555" font-family="sans-serif">{int(round(xt))}°</text>'
        )

    # y-axis tick marks + labels
    for yt in y_ticks:
        yi = sy(yt)
        out.append(
            f'<line x1="{ax_x - 3:.1f}" y1="{yi:.1f}" x2="{ax_x + 3:.1f}" y2="{yi:.1f}"'
            f' stroke="{_AXIS_COLOR}" stroke-width="1"/>'
        )
        y_label = f"{int(round(yt))}" if abs(yt - round(yt)) < 0.01 else f"{yt:.1f}"
        out.append(
            f'<text x="{ax_x - 6:.1f}" y="{yi + 3:.1f}"'
            f' font-size="9" text-anchor="end" fill="#555" font-family="sans-serif">{y_label}</text>'
        )

    # range band edge lines (dashed, drawn over grid but under curves)
    if range_band is not None:
        for band_y in range_band:
            byi = sy(band_y)
            out.append(
                f'<line x1="{ml}" y1="{byi:.1f}" x2="{ml + pw}" y2="{byi:.1f}"'
                f' stroke="#2563EB" stroke-width="1.2" stroke-dasharray="4,3" opacity="0.6"/>'
            )

    # curves (clipped)
    n_samples = 400
    multi = len(curves) > 1

    for idx, curve in enumerate(curves):
        color = _CURVE_COLORS[idx % len(_CURVE_COLORS)]
        func = curve["func"]
        amp = float(curve["amplitude"])
        period = float(curve["period_deg"])
        phase = float(curve.get("phase_shift_deg", 0))
        offset = float(curve.get("offset", 0))

        pts: list[str] = []
        for i in range(n_samples + 1):
            xd = x_min + (x_max - x_min) * i / n_samples
            angle = 2 * math.pi * xd / period + math.radians(phase)
            yv = amp * (math.sin(angle) if func == "sin" else math.cos(angle)) + offset
            pts.append(f"{sx(xd):.1f},{sy(yv):.1f}")

        out.append(
            f'<polyline points="{" ".join(pts)}"'
            f' fill="none" stroke="{color}" stroke-width="2"'
            f' stroke-linejoin="round" stroke-linecap="round"'
            f' clip-path="url(#{clip_id})"/>'
        )

        # curve label at right edge (only when multiple curves)
        if multi:
            xd_end = x_max
            angle = 2 * math.pi * xd_end / period + math.radians(phase)
            yv_end = (
                amp * (math.sin(angle) if func == "sin" else math.cos(angle)) + offset
            )
            label = curve.get("id", f"f{idx + 1}")
            out.append(
                f'<text x="{sx(xd_end) + 4:.1f}" y="{sy(yv_end) + 4:.1f}"'
                f' font-size="10" fill="{color}" font-style="italic"'
                f' font-family="sans-serif">{label}</text>'
            )

    out.append("</svg>")
    return "\n".join(out)
