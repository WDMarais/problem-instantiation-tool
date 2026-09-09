"""
Exponential scene builder — a single-asymptote CartesianScene consumer.

Turns ``y = a·b^x + q`` into a display-only sketch: the curve, its single
horizontal asymptote ``y = q`` (a dashed ``ConstantLine``), and the labelled
points a determine-the-equation problem states as given (the y-intercept and one
more point). No discontinuity — simpler than the hyperbola; the only new-ish bit
is clamping the fast-growing tail so pixel coordinates stay bounded.

Display-only: the caller (a generator) already baked the answer. This module only
*shows* the asymptote and points the problem states as given.
"""

from __future__ import annotations

from render.cartesian import (
    _REFERENCE_COLOR,
    CartesianScene,
    ConstantLine,
    Point,
    Polyline,
)

_N_SAMPLES = 120
_ASYMPTOTE_COLOR = _REFERENCE_COLOR


def exponential_scene(
    a: int,
    b: int,
    q: int,
    *,
    points: tuple[tuple[int, int], ...] = (),
    show_asymptote: bool = True,
    width_pad: float = 0.5,
) -> CartesianScene:
    """Scene for ``y = a·b^x + q`` (horizontal asymptote ``y = q``).

    ``points`` marks the labelled lattice points (typically the y-intercept and
    one neighbour). The window spans a few units either side of the labelled xs so
    the asymptote-hugging tail is visible; the growing tail runs off the top /
    bottom edge (clamped + clip-path), which is the correct picture.
    """
    ya = q

    def f(x: float) -> float:
        return a * (b**x) + q

    xs = [0.0] + [float(px) for px, _ in points]
    x_lo = min(xs) - 2.0 - width_pad  # extra room on the asymptote-hugging side
    x_hi = max(xs) + 1.0 + width_pad

    y_feat = [0.0, float(ya)] + [float(py) for _, py in points]
    y_lo_data, y_hi_data = min(y_feat), max(y_feat)
    y_pad = max((y_hi_data - y_lo_data) * 0.2, 1.0)
    y_lo, y_hi = y_lo_data - y_pad, y_hi_data + y_pad
    yspan = y_hi - y_lo
    clamp_lo, clamp_hi = y_lo - yspan, y_hi + yspan

    pts: list[tuple[float, float] | None] = []
    for i in range(_N_SAMPLES + 1):
        x = x_lo + (x_hi - x_lo) * i / _N_SAMPLES
        y = min(max(f(x), clamp_lo), clamp_hi)
        pts.append((x, y))
    items: list[object] = [Polyline(points=tuple(pts))]

    if show_asymptote:
        items.append(
            ConstantLine("h", float(ya), color=_ASYMPTOTE_COLOR, label=f"y = {ya}")
        )

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
    y_ticks = sorted({0, ya} | {py for _, py in points})

    return CartesianScene(
        x_min=x_lo,
        x_max=x_hi,
        y_min=y_lo,
        y_max=y_hi,
        items=tuple(items),
        x_ticks=tuple(float(t) for t in x_ticks),
        y_ticks=tuple(float(t) for t in y_ticks),
    )
