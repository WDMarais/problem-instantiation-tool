"""
Circle scene builder — the analytic-geometry CartesianScene consumer.

Turns ``(x - a)^2 + (y - b)^2 = r^2`` into a display-only sketch: the circle, its
centre ``(a, b)``, and (optionally) one labelled point on it with the radius drawn
in. This is the first *analytic-geometry* consumer promised in ``render/DESIGN.md``
(analytic geometry rides on the same Cartesian schema as the function plots). The
only new mechanic is ``equal_aspect``: a circle only reads as round when the two
axis scales match, so the scene asks the emitter to square the units.

Display-only: the caller (a generator) already baked the answer. This module only
*shows* the centre, radius and point the problem states as given.
"""

from __future__ import annotations

from math import sqrt

from render.cartesian import (
    _REFERENCE_COLOR,
    CartesianScene,
    Circle,
    Point,
    Polyline,
)

_RADIUS_COLOR = _REFERENCE_COLOR


def circle_scene(
    a: int,
    b: int,
    r2: int,
    *,
    point: tuple[int, int] | None = None,
    show_centre: bool = True,
    width_pad: float = 1.0,
) -> CartesianScene:
    """Scene for ``(x - a)^2 + (y - b)^2 = r^2`` (``r2`` is r², kept integer).

    ``point`` marks one labelled lattice point on the circle; a thin radius segment
    joins it to the centre. The window is a square around the centre padded past the
    radius, and ``equal_aspect`` makes the emitter match the pixel scales so the
    circle renders round rather than as an ellipse.
    """
    r = sqrt(r2)
    half = r + width_pad
    x_lo, x_hi = a - half, a + half
    y_lo, y_hi = b - half, b + half

    items: list[object] = [Circle(float(a), float(b), r)]

    if point is not None:
        px, py = point
        # radius segment centre → point (drawn under the dots)
        items.append(
            Polyline(
                points=((float(a), float(b)), (float(px), float(py))),
                color=_RADIUS_COLOR,
                width=1.3,
            )
        )

    if show_centre:
        items.append(Point(float(a), float(b), label=f"({a}; {b})"))

    if point is not None:
        px, py = point
        items.append(
            Point(
                float(px),
                float(py),
                label=f"({px}; {py})",
                droplines=True,
            )
        )

    x_ticks = sorted({0, a} | ({point[0]} if point else set()))
    y_ticks = sorted({0, b} | ({point[1]} if point else set()))

    return CartesianScene(
        x_min=x_lo,
        x_max=x_hi,
        y_min=y_lo,
        y_max=y_hi,
        items=tuple(items),
        x_ticks=tuple(float(t) for t in x_ticks),
        y_ticks=tuple(float(t) for t in y_ticks),
        equal_aspect=True,
    )
