"""General labelled figures for the six examinable Euclidean-geometry theorem
proofs shown on P2 Q9.3 / Q10.3 / Q11.3.

Unlike the live angle-chase figures (which a generator instantiates per seed), these
are *static* diagrams: one canonical, general configuration per theorem, matching the
lettering of the hand-authored proof memo in ``worksheets/paper.py`` exactly. NSC
"prove the theorem" questions provide such a diagram — the student's proof references
its labelled points — so each static proof slot needs one.

Display-only, like every figure: the drawing is not to scale and nothing is measured
off it. Each builder returns a :class:`GeometryFigure`; ``svg_for(name)`` renders one
to an inline SVG string for embedding in a ``StaticContent.figure_svg``.
"""

from __future__ import annotations

import math

from render.geometry import (
    Angle,
    Circle,
    GeometryFigure,
    Point,
    Segment,
    circle_point,
    render_figure,
    tangent_point,
)

_R = 1.0  # unit circle in layout space; the renderer fits it to the viewport


def angle_at_centre() -> GeometryFigure:
    """∠ at centre = 2 × ∠ at circumference. C at the top sees chord AB; O is the
    centre; CO is produced to D so the exterior-angle step applies to △OAC, △OBC."""
    o = Point("O", 0.0, 0.0, label_dir=(-0.6, 0.5))
    c = circle_point("C", 0, 0, _R, 90, label_dir=(0, 1))
    d = circle_point("D", 0, 0, _R, 270, label_dir=(0, -1))
    a = circle_point("A", 0, 0, _R, 214, label_dir=(-1, -0.4))
    b = circle_point("B", 0, 0, _R, 326, label_dir=(1, -0.4))
    return GeometryFigure(
        points=[o, a, b, c, d],
        segments=[
            Segment("C", "D"),  # CO produced to D (through the centre)
            Segment("O", "A"),
            Segment("O", "B"),  # radii OA, OB → the central angle AÔB
            Segment("C", "A"),
            Segment("C", "B"),  # chords → the circumference angle AĈB
            Segment("A", "B"),  # the subtended chord
        ],
        circles=[Circle("O", _R)],
        width=250,
        height=240,
    )


def cyclic_quad_opposite() -> GeometryFigure:
    """Opposite angles of a cyclic quadrilateral are supplementary. O is the centre;
    radii OB, OD show the two central angles Ô₁ = 2Â, Ô₂ = 2Ĉ used in the proof."""
    o = Point("O", 0.0, 0.0, label_dir=(0.5, -0.5))
    a = circle_point("A", 0, 0, _R, 132, label_dir=(-1, 0.4))
    b = circle_point("B", 0, 0, _R, 58, label_dir=(1, 0.4))
    c = circle_point("C", 0, 0, _R, 340, label_dir=(1, -0.3))
    d = circle_point("D", 0, 0, _R, 212, label_dir=(-1, -0.4))
    return GeometryFigure(
        points=[o, a, b, c, d],
        segments=[
            Segment("A", "B"),
            Segment("B", "C"),
            Segment("C", "D"),
            Segment("D", "A"),
            Segment("O", "B"),
            Segment("O", "D"),
        ],
        circles=[Circle("O", _R)],
        width=250,
        height=240,
    )


def tangent_chord() -> GeometryFigure:
    """Tangent-chord angle = angle in the alternate segment. Tangent SAT touches at A;
    chord AB; C on the major arc; construction diameter AD (through O) and chord BD."""
    o = Point("O", 0.0, 0.0, label_dir=(0.55, 0.2))
    a = circle_point("A", 0, 0, _R, 270, label_dir=(0, -1))
    s = tangent_point("S", 0, 0, _R, 270, -1.25, label_dir=(-1, 0))
    t = tangent_point("T", 0, 0, _R, 270, 1.25, label_dir=(1, 0))
    d = circle_point("D", 0, 0, _R, 90, label_dir=(0, 1))
    b = circle_point("B", 0, 0, _R, 202, label_dir=(-1, 0.1))
    c = circle_point("C", 0, 0, _R, 44, label_dir=(1, 0.5))
    return GeometryFigure(
        points=[o, a, s, t, b, c, d],
        segments=[
            Segment("S", "T"),  # the tangent, touching at A
            Segment("A", "B"),  # the chord
            Segment("A", "D"),  # construction: diameter through O
            Segment("B", "D"),  # construction: join BD
            Segment("C", "A"),
            Segment("C", "B"),  # alternate-segment angle AĈB
        ],
        circles=[Circle("O", _R)],
        width=250,
        height=250,
    )


def cyclic_quad_exterior() -> GeometryFigure:
    """Exterior angle of a cyclic quadrilateral = interior opposite angle. Cyclic
    quad ABCD with side BC produced to E; DĈE (exterior) equals Â (interior opp.)."""
    o = Point("O", 0.0, 0.0, dot=False, label="")  # centre only anchors the circle
    a = circle_point("A", 0, 0, _R, 165, label_dir=(-1, 0.2))
    b = circle_point("B", 0, 0, _R, 92, label_dir=(0, 1))
    c = circle_point("C", 0, 0, _R, 16, label_dir=(0.7, 0.6))
    d = circle_point("D", 0, 0, _R, 248, label_dir=(-0.5, -1))
    # BC produced beyond C to E (along the ray B→C)
    bx, by = b.x, b.y
    cx, cy = c.x, c.y
    ux, uy = cx - bx, cy - by
    e = Point("E", cx + 0.62 * ux, cy + 0.62 * uy, label_dir=(1, -0.2))
    return GeometryFigure(
        points=[o, a, b, c, d, e],
        segments=[
            Segment("A", "B"),
            Segment("B", "C"),
            Segment("C", "D"),
            Segment("D", "A"),
            Segment("C", "E"),  # BC produced to E
        ],
        circles=[Circle("O", _R)],
        width=260,
        height=240,
    )


def equiangular_triangles() -> GeometryFigure:
    """Equiangular triangles have proportional sides. △ABC (with the construction
    P on AB, Q on AC, PQ ∥ BC) alongside the smaller equiangular △DEF."""
    a = Point("A", 0.0, 1.6, label_dir=(0, 1))
    b = Point("B", -1.05, 0.0, label_dir=(-1, -0.4))
    c = Point("C", 1.2, 0.0, label_dir=(1, -0.4))
    f = 0.55  # AP:AB = AQ:AC, so PQ ∥ BC
    p = Point("P", a.x + f * (b.x - a.x), a.y + f * (b.y - a.y), label_dir=(-1, 0.2))
    q = Point("Q", a.x + f * (c.x - a.x), a.y + f * (c.y - a.y), label_dir=(1, 0.2))
    # smaller equiangular triangle DEF, to the right (similar to ABC, scale 0.6)
    ox, s = 3.1, 0.6
    d = Point("D", ox + s * a.x, s * a.y, label_dir=(0, 1))
    e = Point("E", ox + s * b.x, s * b.y, label_dir=(-1, -0.4))
    g = Point("F", ox + s * c.x, s * c.y, label_dir=(1, -0.4))
    return GeometryFigure(
        points=[a, b, c, p, q, d, e, g],
        segments=[
            Segment("A", "B"),
            Segment("B", "C"),
            Segment("C", "A"),
            Segment("P", "Q", dashed=True),  # construction PQ ∥ BC
            Segment("D", "E"),
            Segment("E", "F"),
            Segment("F", "D"),
        ],
        angles=[
            Angle("A", "B", "C", arcs=1),
            Angle("D", "E", "F", arcs=1),  # Â = D̂
            Angle("B", "C", "A", arcs=2),
            Angle("E", "F", "D", arcs=2),  # B̂ = Ê
            Angle("C", "A", "B", arcs=3),
            Angle("F", "D", "E", arcs=3),  # Ĉ = F̂
        ],
        width=340,
        height=210,
    )


def basic_proportionality() -> GeometryFigure:
    """A line parallel to one side of a triangle divides the other two in proportion.
    △ABC with DE ∥ BC (D on AB, E on AC); construction cevians BE and CD."""
    a = Point("A", 0.0, 1.7, label_dir=(0, 1))
    b = Point("B", -1.15, 0.0, label_dir=(-1, -0.4))
    c = Point("C", 1.15, 0.0, label_dir=(1, -0.4))
    f = 0.45
    d = Point("D", a.x + f * (b.x - a.x), a.y + f * (b.y - a.y), label_dir=(-1, 0.2))
    e = Point("E", a.x + f * (c.x - a.x), a.y + f * (c.y - a.y), label_dir=(1, 0.2))
    return GeometryFigure(
        points=[a, b, c, d, e],
        segments=[
            Segment("A", "B"),
            Segment("A", "C"),
            Segment("B", "C", arrows=1),
            Segment("D", "E", arrows=1),  # DE ∥ BC (single chevrons on both)
            Segment("B", "E", dashed=True),
            Segment("C", "D", dashed=True),  # construction cevians
        ],
        width=250,
        height=210,
    )


def perp_from_centre_bisects_chord() -> GeometryFigure:
    """The line drawn from the centre of a circle perpendicular to a chord bisects
    the chord. Centre O; chord AB; M the foot of OM ⊥ AB; radii OA, OB give the two
    congruent right triangles (RHS)."""
    depth = 0.55  # how far below O the chord sits
    half = math.sqrt(_R * _R - depth * depth)  # half-chord AM = MB
    o = Point("O", 0.0, 0.0, label_dir=(-0.5, 0.6))
    a = Point("A", -half, -depth, label_dir=(-1, -0.2))
    b = Point("B", half, -depth, label_dir=(1, -0.2))
    m = Point("M", 0.0, -depth, label_dir=(0, -1))
    return GeometryFigure(
        points=[o, a, b, m],
        segments=[
            Segment("O", "A"),
            Segment("O", "B"),  # radii
            Segment("O", "M"),  # the perpendicular from the centre
            Segment("A", "M", ticks=1),
            Segment("M", "B", ticks=1),  # the chord, shown bisected at M
        ],
        angles=[Angle("M", "O", "A", right=True)],  # OM ⊥ AB
        circles=[Circle("O", _R)],
        width=250,
        height=230,
    )


def two_tangents_equal() -> GeometryFigure:
    """Two tangents drawn to a circle from a common external point are equal. Tangents
    PA, PB touch at A, B; radii OA, OB meet them at right angles; the line OP gives the
    two congruent right triangles (RHS), so PA = PB."""
    d = 2.3  # OP, the external point's distance from the centre
    touch = math.degrees(math.acos(_R / d))  # ∠AOP at the contact
    o = Point("O", 0.0, 0.0, label_dir=(-1, 0))
    p = Point("P", d, 0.0, label_dir=(1, 0))
    a = circle_point("A", 0, 0, _R, touch, label_dir=(0.2, 1))
    b = circle_point("B", 0, 0, _R, -touch, label_dir=(0.2, -1))
    return GeometryFigure(
        points=[o, a, b, p],
        segments=[
            Segment("P", "A", ticks=1),
            Segment("P", "B", ticks=1),  # the two tangents, shown equal
            Segment("O", "A"),
            Segment("O", "B"),  # radii to the contacts
            Segment("O", "P", dashed=True),  # construction: join OP
        ],
        angles=[
            Angle("A", "O", "P", right=True),  # radius ⊥ tangent at A
            Angle("B", "O", "P", right=True),  # radius ⊥ tangent at B
        ],
        circles=[Circle("O", _R)],
        width=260,
        height=230,
    )


def angles_same_segment() -> GeometryFigure:
    """Angles subtended by a chord (arc) in the same segment are equal. Chord AB
    subtends AĈB and AD̂B at C, D on the major arc; radii OA, OB give the central
    angle AÔB = 2AĈB = 2AD̂B used in the proof."""
    o = Point("O", 0.0, 0.0, label_dir=(0.6, -0.2))
    a = circle_point("A", 0, 0, _R, 215, label_dir=(-1, -0.2))
    b = circle_point("B", 0, 0, _R, 325, label_dir=(1, -0.2))
    c = circle_point("C", 0, 0, _R, 74, label_dir=(0.7, 0.7))
    d = circle_point("D", 0, 0, _R, 116, label_dir=(-0.7, 0.7))
    return GeometryFigure(
        points=[o, a, b, c, d],
        segments=[
            Segment("A", "B"),  # the subtended chord
            Segment("A", "C"),
            Segment("B", "C"),  # AĈB
            Segment("A", "D"),
            Segment("B", "D"),  # AD̂B
            Segment("O", "A", dashed=True),
            Segment("O", "B", dashed=True),  # construction: radii to the chord
        ],
        angles=[
            Angle("C", "A", "B", arcs=1),
            Angle("D", "A", "B", arcs=1),  # equal angles in the same segment
        ],
        circles=[Circle("O", _R)],
        width=260,
        height=250,
    )


def angle_in_semicircle() -> GeometryFigure:
    """The angle subtended by a diameter at the circumference is a right angle.
    Diameter AB through the centre O; C on the circle; radius OC gives the two
    isosceles triangles whose base angles sum to AĈB = 90°."""
    o = Point("O", 0.0, 0.0, label_dir=(0, -1))
    a = Point("A", -_R, 0.0, label_dir=(-1, 0))
    b = Point("B", _R, 0.0, label_dir=(1, 0))
    c = circle_point("C", 0, 0, _R, 68, label_dir=(0.3, 1))
    return GeometryFigure(
        points=[o, a, b, c],
        segments=[
            Segment("A", "B"),  # the diameter, through O
            Segment("A", "C"),
            Segment("B", "C"),  # the inscribed angle AĈB
            Segment("O", "C", dashed=True),  # construction: the radius OC
        ],
        angles=[Angle("C", "A", "B", right=True)],  # AĈB = 90°
        circles=[Circle("O", _R)],
        width=250,
        height=205,
    )


_FIGURES = {
    "angle_at_centre": angle_at_centre,
    "cyclic_quad_opposite": cyclic_quad_opposite,
    "tangent_chord": tangent_chord,
    "cyclic_quad_exterior": cyclic_quad_exterior,
    "equiangular_triangles": equiangular_triangles,
    "basic_proportionality": basic_proportionality,
    "perp_from_centre_bisects_chord": perp_from_centre_bisects_chord,
    "two_tangents_equal": two_tangents_equal,
    "angles_same_segment": angles_same_segment,
    "angle_in_semicircle": angle_in_semicircle,
}


def svg_for(name: str) -> str:
    """Render the named theorem figure to an inline SVG string."""
    try:
        builder = _FIGURES[name]
    except KeyError:
        raise KeyError(
            f"unknown theorem figure {name!r}; have {sorted(_FIGURES)}"
        ) from None
    return render_figure(builder())
