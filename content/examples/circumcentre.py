"""
Analytic geometry (straight line), archetype 6 — ``circumcentre``.

Given three points A, B, C, find the coordinates of the point P that is
**equidistant** from all three — the circumcentre of triangle ABC (the centre of
the circle through A, B, C).

The skill is turning "equidistant" into algebra. |PA| = |PB| squared gives
|PA|² = |PB|², whose x² and y² terms cancel, leaving a *linear* equation — the
perpendicular bisector of AB. A second pair, |PB|² = |PC|², gives another line;
their intersection is P. Two coordinates, graded independently (1 mark each): a
student who sets up one bisector correctly but slips on the other loses only the
coordinate that depends on it.

**Construction** is backward from the answer, the house pattern: choose an
integer circumcentre (h, k) and a squared radius r² that is a sum of two squares
in at least three ways, then drop the three vertices onto lattice points of that
circle (P + integer offset vectors of length r). Every vertex is then exactly r
from (h, k) by construction, so (h, k) *is* the circumcentre — no equation is
solved in the generator, which is what makes the test's own solve an independent
check. r² is drawn from a fixed set of such values (25, 50, 65, …); that set
exists to guarantee three lattice vertices, not to prettify the answer — the
circumcentre is the plain integer (h, k) either way.
"""

from __future__ import annotations

import math
import random

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

# Squared radii that are a sum of two integer squares in ≥3 essentially distinct
# ways, so a circle of this radius carries enough lattice points to place three
# distinct vertices on it.
_LATTICE_RADII_SQ = (25, 50, 65, 85, 125, 130, 169)


def _lattice_offsets(r_sq: int) -> list[tuple[int, int]]:
    """All integer vectors (dx, dy) with dx² + dy² = r_sq."""
    lim = math.isqrt(r_sq)
    return [
        (dx, dy)
        for dx in range(-lim, lim + 1)
        for dy in range(-lim, lim + 1)
        if dx * dx + dy * dy == r_sq
    ]


def _gen(rng: random.Random) -> dict:
    r_sq = rng.choice(_LATTICE_RADII_SQ)
    offsets = _lattice_offsets(r_sq)  # every _LATTICE_RADII_SQ entry has ≥ 3

    h = rng.randint(-6, 6)
    k = rng.randint(-6, 6)

    (dax, day), (dbx, dby), (dcx, dcy) = rng.sample(offsets, 3)
    ax, ay = h + dax, k + day
    bx, by = h + dbx, k + dby
    cx, cy = h + dcx, k + dcy

    return {
        "ax": ax,
        "ay": ay,
        "bx": bx,
        "by": by,
        "cx": cx,
        "cy": cy,
        "centre_x": h,
        "centre_y": k,
        "radius_sq": r_sq,
        "points_latex": (
            rf"A({ax},\,{ay}),\ B({bx},\,{by})\text{{ and }}C({cx},\,{cy})"
        ),
    }


circumcentre = Problem(
    id="circumcentre",
    type_id="circumcentre",
    name="Point equidistant from three given points (circumcentre)",
    artifact_type="practice",
    problem_spec=_gen,
    verifier_spec=[
        {"kind": "numeric_equality", "marks_possible": 1, "param_key": "centre_x"},
        {"kind": "numeric_equality", "marks_possible": 1, "param_key": "centre_y"},
    ],
    corpus_anchor=CorpusAnchor(
        paper="2023 Nov P2",
        question="3.7",  # "equidistant point" — 3 method marks in the paper
        # The paper scores the two distance set-ups + solve as 3 method marks;
        # our answer-level scheme grades the two coordinates (2 marks), so the
        # standalone part-mark is left unset rather than forced to match.
    ),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(registry=InMemoryRegistry({circumcentre.id: circumcentre}))

    def show(label, inst, *answers):
        attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
        r = inst.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  "
            f"is_correct={r.is_correct}"
        )

    for seed in range(4):
        inst = engine.instantiate(circumcentre.id, seed=seed)
        p = inst.params
        print(f"=== seed {seed} ===")
        print(
            f"  A=({p['ax']},{p['ay']})  B=({p['bx']},{p['by']})  "
            f"C=({p['cx']},{p['cy']})  ->  P=({p['centre_x']},{p['centre_y']})"
        )
        show("equidistant P ", inst, p["centre_x"], p["centre_y"])
        # classic confusion: the centroid (mean of vertices) is not the
        # circumcentre unless the triangle is equilateral
        gx = (p["ax"] + p["bx"] + p["cx"]) / 3
        gy = (p["ay"] + p["by"] + p["cy"]) / 3
        show("centroid instead", inst, gx, gy)
