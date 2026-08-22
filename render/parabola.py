"""
Parabola scene builder — the first CartesianScene consumer.

Turns a parabola ``f(x) = a(x - r1)(x - r2)`` into a display-only sketch: the
curve, its intercepts, and (optionally) its turning point, on a window sized to
hold every key feature. All the maths (vertex, y-intercept, sampling, window
padding, integer ticks) lives here; ``render/cartesian.py`` just draws.

Display-only: the caller (a generator) already baked the answer. This module only
*shows* points the problem states as given — it never invents an answer.
"""

from __future__ import annotations

from render.cartesian import CartesianScene, Label, Point, Polyline

_N_SAMPLES = 120


def parabola_scene(
    a: int,
    r1: int,
    r2: int,
    *,
    show_intercepts: bool = True,
    show_vertex: bool = False,
    width_pad: float = 1.0,
) -> CartesianScene:
    """Scene for ``y = a(x - r1)(x - r2)`` with distinct integer roots.

    ``show_intercepts`` labels the two x-intercepts (by x-value) and the
    y-intercept (as a coordinate) — the "given" information of a determine-the-
    equation problem. ``show_vertex`` marks the turning point (never labelled with
    its coordinates, which would give away a compute-the-vertex answer).
    """
    lo, hi = sorted((r1, r2))
    vx = (r1 + r2) / 2.0
    vy = a * (vx - r1) * (vx - r2)
    yint = a * r1 * r2  # f(0)

    def f(x: float) -> float:
        return a * (x - r1) * (x - r2)

    # ── window: hold both roots, the vertex, the y-intercept and the origin ──
    x_lo = min(lo, vx) - width_pad
    x_hi = max(hi, vx) + width_pad
    y_vals = [0.0, float(vy), float(yint)]
    y_lo_data, y_hi_data = min(y_vals), max(y_vals)
    y_pad = max((y_hi_data - y_lo_data) * 0.15, 1.0)
    y_lo = y_lo_data - y_pad
    y_hi = y_hi_data + y_pad

    # ── curve ────────────────────────────────────────────────────────────────
    pts: list[tuple[float, float] | None] = []
    for i in range(_N_SAMPLES + 1):
        x = x_lo + (x_hi - x_lo) * i / _N_SAMPLES
        pts.append((x, f(x)))
    items: list[object] = [Polyline(points=tuple(pts))]

    # ── ticks: only meaningful integer positions get a gridline + label ──
    x_ticks = sorted({0, lo, hi} | ({int(vx)} if vx == int(vx) else set()))
    y_ticks = sorted({0, int(yint)} | ({int(vy)} if vy == int(vy) else set()))

    if show_intercepts:
        items.append(Point(float(lo), 0.0, label=_fmt_int(lo), color="#DC2626"))
        items.append(Point(float(hi), 0.0, label=_fmt_int(hi), color="#DC2626"))
        items.append(
            Point(
                0.0,
                float(yint),
                label=f"(0; {_fmt_int(yint)})",
                droplines=False,
                color="#DC2626",
            )
        )

    if show_vertex:
        items.append(Point(vx, float(vy), droplines=True, color="#16A34A"))
        items.append(Label(vx, y_hi, "turning point", color="#16A34A", anchor="middle"))

    return CartesianScene(
        x_min=x_lo,
        x_max=x_hi,
        y_min=y_lo,
        y_max=y_hi,
        items=tuple(items),
        x_ticks=tuple(float(t) for t in x_ticks),
        y_ticks=tuple(float(t) for t in y_ticks),
    )


def _fmt_int(v: float) -> str:
    return f"{int(round(v))}"
