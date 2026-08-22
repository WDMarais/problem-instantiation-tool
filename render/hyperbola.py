"""
Hyperbola scene builder — the discontinuity-split CartesianScene consumer.

Turns ``y = a/(x + p) + q`` into a display-only sketch: two branches split at the
vertical asymptote ``x = -p``, the horizontal asymptote ``y = q``, and (optionally)
one labelled point on the curve — the "given" information of a determine-the-
equation problem. This is the one genuinely new plotting mechanic in the render
design (``render/DESIGN.md``): the curve is emitted as a single Polyline whose two
branches are separated by a ``None`` break, so no false segment streaks across the
asymptote. The asymptotes themselves are dashed ``ConstantLine`` reference lines.

Display-only: the caller (a generator) already baked the answer. This module only
*shows* the asymptotes and point the problem states as given.
"""

from __future__ import annotations

from render.cartesian import CartesianScene, ConstantLine, Point, Polyline

_N_SAMPLES = 90
_ASYMPTOTE_COLOR = "#6B7280"


def hyperbola_scene(
    a: int,
    p: int,
    q: int,
    *,
    point: tuple[int, int] | None = None,
    show_asymptotes: bool = True,
    width_pad: float = 1.5,
) -> CartesianScene:
    """Scene for ``y = a/(x + p) + q`` (vertical asymptote ``x = -p``, horizontal
    ``y = q``). ``point`` marks one labelled lattice point on the curve.

    The window is centred on the asymptote intersection ``(-p, q)`` so the two
    branches show symmetrically; near the asymptote the curve runs off the top /
    bottom edge (clipped by the emitter), which is the correct picture.
    """
    xa = -p  # vertical asymptote
    ya = q  # horizontal asymptote

    def f(x: float) -> float:
        return a / (x + p) + q

    # ── window: centre on (xa, ya), hold the origin and the labelled point ──
    x_feat = [0.0, float(xa)] + ([float(point[0])] if point else [])
    y_feat = [0.0, float(ya)] + ([float(point[1])] if point else [])
    half_x = max(max(abs(v - xa) for v in x_feat), 2.0) + width_pad
    half_y = max(max(abs(v - ya) for v in y_feat), 2.0) + 1.0
    x_lo, x_hi = xa - half_x, xa + half_x
    y_lo, y_hi = ya - half_y, ya + half_y
    yspan = y_hi - y_lo
    clamp_lo, clamp_hi = y_lo - yspan, y_hi + yspan  # keep pixel coords bounded

    # ── curve: two branches, split by a None break at the asymptote ──
    def branch(x_from: float) -> list[tuple[float, float]]:
        # sample from a window edge toward the asymptote (excluding it)
        pts: list[tuple[float, float]] = []
        for i in range(_N_SAMPLES + 1):
            x = x_from + (xa - x_from) * i / _N_SAMPLES
            if abs(x - xa) < 1e-6:
                continue
            y = min(max(f(x), clamp_lo), clamp_hi)
            pts.append((x, y))
        return pts

    curve: list[tuple[float, float] | None] = []
    curve.extend(branch(x_lo))  # left branch: x_lo → xa⁻
    curve.append(None)  # break across the asymptote
    curve.extend(branch(x_hi))  # right branch: x_hi → xa⁺
    items: list[object] = [Polyline(points=tuple(curve))]

    if show_asymptotes:
        items.append(
            ConstantLine("v", float(xa), color=_ASYMPTOTE_COLOR, label=f"x = {xa}")
        )
        items.append(
            ConstantLine("h", float(ya), color=_ASYMPTOTE_COLOR, label=f"y = {ya}")
        )

    if point is not None:
        px, py = point
        items.append(
            Point(
                float(px),
                float(py),
                label=f"({px}; {py})",
                droplines=True,
                color="#DC2626",
            )
        )

    x_ticks = sorted({0, xa} | ({point[0]} if point else set()))
    y_ticks = sorted({0, ya} | ({point[1]} if point else set()))

    return CartesianScene(
        x_min=x_lo,
        x_max=x_hi,
        y_min=y_lo,
        y_max=y_hi,
        items=tuple(items),
        x_ticks=tuple(float(t) for t in x_ticks),
        y_ticks=tuple(float(t) for t in y_ticks),
    )
