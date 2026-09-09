"""
Straight-line scene builder — the simplest CartesianScene consumer.

Turns ``y = mx + c`` into a display-only sketch: one straight segment spanning
the window, and (optionally) the labelled lattice points a determine-the-equation
problem states as given. No curve sampling and no asymptote — a line needs only
its two window-edge endpoints — so this is the plainest builder in the family; it
exists to reuse the same axes, ticks, drop-lines and point labels as the others.

Display-only: the caller (a generator) already baked the answer. This module only
*shows* the line and the points the problem states as given.
"""

from __future__ import annotations

from render.cartesian import CartesianScene, Point, Polyline


def line_scene(
    m: int,
    c: int,
    *,
    points: tuple[tuple[int, int], ...] = (),
    width_pad: float = 1.0,
) -> CartesianScene:
    """Scene for ``y = mx + c``. ``points`` marks the labelled lattice points the
    sketch calls out (typically the two points that fix the line).

    The window holds the origin, the y-intercept and every labelled point, with a
    little padding; the line is drawn as its two window-edge endpoints (the emitter
    clips to the plot area), which keeps it exactly straight.
    """

    def f(x: float) -> float:
        return m * x + c

    xs = [0.0] + [float(px) for px, _ in points]
    x_lo = min(xs) - width_pad
    x_hi = max(xs) + width_pad

    y_feat = [0.0, float(c)] + [float(py) for _, py in points]
    y_lo_data, y_hi_data = min(y_feat), max(y_feat)
    y_pad = max((y_hi_data - y_lo_data) * 0.2, 1.0)
    y_lo, y_hi = y_lo_data - y_pad, y_hi_data + y_pad

    # a straight line: just its two window-edge endpoints (emitter clips the rest)
    curve = ((x_lo, f(x_lo)), (x_hi, f(x_hi)))
    items: list[object] = [Polyline(points=curve)]

    for px, py in points:
        items.append(
            Point(
                float(px),
                float(py),
                label=f"({px}; {py})",
                droplines=True,
            )
        )

    x_ticks = sorted({0} | {px for px, _ in points})
    y_ticks = sorted({0, c} | {py for _, py in points})

    return CartesianScene(
        x_min=x_lo,
        x_max=x_hi,
        y_min=y_lo,
        y_max=y_hi,
        items=tuple(items),
        x_ticks=tuple(float(t) for t in x_ticks),
        y_ticks=tuple(float(t) for t in y_ticks),
    )
