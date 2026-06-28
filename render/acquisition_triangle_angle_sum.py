#!/usr/bin/env python3
"""
Acquisition sheet (vertical-slice prototype): the angle sum of a triangle.

This is the *upstream* of the triangle_angle_sum SRS drill. Instead of asserting
"angles of a triangle sum to 180° (because the rule says so)", it derives the
theorem once — the classic parallel-line construction — as a sequence of figure
states, each carrying its own claim and reason. Then it collapses the result to
the citable one-liner, and only then hands over a few apply-it problems (the same
drill figures, now meaningful).

Design notes:
  * Reuses render/geometry.py unchanged — each derivation step is just a
    GeometryFigure with one more mark than the last.
  * The derivation figures use NO pose: a fixed, canonical orientation is the
    point. (Random Pose variety is for the SRS drill, where the student already
    owns the method and needs visual exposure — not for first contact.)
  * Equal angles are marked with matching arc counts (1 = α, 2 = β, 3 = γ); the
    two alternate angles at C reuse α's and β's arc counts to *show* the equality.

Not yet a formalised schema: if this format lands, it graduates to a
content/sheet-style dataclass + a4 renderer. For now it is a standalone preview,
a sibling of render/geometry_demo.py.

    .venv/bin/python render/acquisition_triangle_angle_sum.py   # -> *.html
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from render.geometry import Angle, GeometryFigure, Point, Segment, render_figure

# ── canonical triangle + construction line ℓ through C parallel to AB ──────────
_A = Point("A", 0.0, 0.0)
_B = Point("B", 4.2, 0.0)
_C = Point("C", 1.5, 2.6)
_L = Point("Lc", _C.x - 1.7, _C.y, dot=False, label="")  # left end of ℓ (no dot/label)
_R = Point("ℓ", _C.x + 2.0, _C.y, dot=False)  # right end carries the line's name
_TRI = [Segment("A", "B"), Segment("B", "C"), Segment("C", "A")]

# interior-angle marks (always shown): α at A, β at B, γ at C
_INTERIOR = [
    Angle("A", "B", "C", label="α", arcs=1),
    Angle("B", "C", "A", label="β", arcs=2),
    Angle("C", "A", "B", label="γ", arcs=3),
]
# the two alternate angles at C, marked to match their partners
_ALT_A = Angle("C", "Lc", "A", label="α", arcs=1)  # vertex C, ray to L, ray to A
_ALT_B = Angle("C", "ℓ", "B", label="β", arcs=2)  # vertex C, ray to R, ray to B


def _figure(stage: int) -> str:
    """Progressive derivation figure. stage 1..4 reveals one idea at a time."""
    pts = [_A, _B, _C]
    segs = list(_TRI)
    angles = list(_INTERIOR)
    if stage >= 2:  # add the construction line
        pts += [_L, _R]
        segs += [Segment("Lc", "ℓ", dashed=(stage < 4))]  # solid once it's "the line"
    if stage >= 3:  # mark the two alternate angles
        angles += [_ALT_A, _ALT_B]
    return render_figure(GeometryFigure(points=pts, segments=segs, angles=angles))


# ── derivation steps: figure + claim + reason (the worked layer) ──────────────
_STEPS = [
    (
        "Label the angles",
        r"\text{Let } \hat{A}=\alpha,\ \hat{B}=\beta,\ \hat{C}=\gamma.",
        r"\text{Goal: show } \alpha+\beta+\gamma = 180^\circ.",
    ),
    (
        "Construct a parallel",
        r"\text{Draw } \ell \text{ through } C,\ \ell \parallel AB.",
        r"(\text{construction})",
    ),
    (
        "Alternate angles",
        r"L\hat{C}A=\alpha,\quad R\hat{C}B=\beta",
        r"(\text{alternate } \angle\text{s};\ \ell \parallel AB)",
    ),
    (
        "Angles on a line",
        r"\alpha+\gamma+\beta = 180^\circ",
        r"(\angle\text{s on a straight line } \ell)\ \therefore\ "
        r"\alpha+\beta+\gamma=180^\circ",
    ),
]


def _practice_cells(n: int = 3) -> str:
    """A few apply-it problems: the real SRS drill figures, with blanks for the
    value *and* the reason — so even the hand-off rehearses the 'why', not just
    the number."""
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from worksheets.generate import PROBLEMS

    entry = PROBLEMS["triangle_angle_sum"]
    engine = Engine(registry=InMemoryRegistry({"triangle_angle_sum": entry.problem}))
    cells = []
    for i in range(n):
        inst = engine.instantiate("triangle_angle_sum", seed=100 + i)
        card = entry.template(inst.params)
        cells.append(
            '<div class="pcell">'
            f"{card.graph_svg}"
            r'<div class="pq">$\hat{C} = $ <span class="box"></span></div>'
            '<div class="pr">reason: <span class="rule"></span></div>'
            "</div>"
        )
    return "".join(cells)


_KATEX = """\
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"
  onload="renderMathInElement(document.body,{delimiters:[{left:'$$',right:'$$',display:true},{left:'$',right:'$',display:false}],throwOnError:false})">
</script>"""

_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: Georgia, serif; background: #eceff3; color: #111; padding: 24px; }
.sheet { max-width: 1100px; margin: 0 auto; background: #fff; border: 1px solid #ccc;
         border-radius: 5px; padding: 26px 30px; }
h1 { font-size: 17pt; margin-bottom: 2px; }
.sub { color: #666; font-size: 10pt; margin-bottom: 18px; }
h2 { font-size: 10pt; color: #2563EB; text-transform: uppercase; letter-spacing: .06em;
     border-bottom: 1px solid #e3e3e3; padding-bottom: 3px; margin: 20px 0 12px; }
.steps { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }
.step { border: 1px solid #e6e6e6; border-radius: 4px; padding: 8px 8px 10px; }
.badge { display: inline-block; font-size: 8.5pt; font-weight: bold; color: #fff;
         background: #2563EB; border-radius: 10px; padding: 1px 8px;
         margin-bottom: 4px; }
.step .name { font-size: 9.5pt; color: #444; margin-bottom: 4px; }
.step svg { width: 100%; height: auto; }
.claim { font-size: 10pt; margin-top: 6px; }
.reason { font-size: 9pt; color: #555; margin-top: 2px; }
.theorem { background: #f4f8ff; border: 1px solid #cfe0ff; border-radius: 4px;
           padding: 12px 16px; margin-top: 6px; font-size: 11pt; }
.theorem .cite { color: #2563EB; font-weight: bold; }
.practice-intro { font-size: 9.5pt; color: #555; margin-bottom: 10px; }
.pgrid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.pcell { text-align: center; }
.pcell svg { width: 100%; height: auto; }
.pq { font-size: 10pt; margin-top: 4px; text-align: left; }
.pr { font-size: 9pt; color: #777; margin-top: 3px; text-align: left; }
.box { display: inline-block; width: 46px; border-bottom: 1.5px solid #333; }
.rule { display: inline-block; width: 150px; border-bottom: 1px solid #aaa; }
"""


def build_html() -> str:
    steps_html = ""
    for i, (name, claim, reason) in enumerate(_STEPS, start=1):
        steps_html += (
            '<div class="step">'
            f'<span class="badge">Step {i}</span>'
            f'<div class="name">{name}</div>'
            f"{_figure(i)}"
            f'<div class="claim">${claim}$</div>'
            f'<div class="reason">${reason}$</div>'
            "</div>"
        )
    theorem = (
        '<div class="theorem">'
        r"You derived it, so now you may cite it in one line: "
        r'<span class="cite">the angles of a triangle sum to $180^\circ$</span> '
        r"&mdash; reason tag <em>($\angle$s of a $\triangle$)</em>. "
        r"The chain was: $\ell \parallel AB \Rightarrow$ alternate $\angle$s "
        r"$\Rightarrow \alpha+\gamma+\beta$ lie on a straight line $=180^\circ$."
        "</div>"
    )
    return (
        "<!DOCTYPE html><html lang='en'><head><meta charset='UTF-8'>"
        "<title>Acquisition — angle sum of a triangle</title>"
        f"{_KATEX}<style>{_CSS}</style></head><body><div class='sheet'>"
        "<h1>Why do the angles of a triangle add to 180&deg;?</h1>"
        "<div class='sub'>Derive it once, then you never have to take it on "
        "faith. &middot; prototype geometry acquisition sheet</div>"
        "<h2>Derivation</h2>"
        f"<div class='steps'>{steps_html}</div>"
        "<h2>The theorem</h2>"
        f"{theorem}"
        "<h2>Your turn</h2>"
        "<div class='practice-intro'>Now apply it. Give $\\hat{C}$ <em>and</em> "
        "the reason &mdash; the reason is the part that matters.</div>"
        f"<div class='pgrid'>{_practice_cells()}</div>"
        "</div></body></html>"
    )


def main() -> None:
    out = Path("acquisition_triangle_angle_sum.html")
    out.write_text(build_html(), encoding="utf-8")
    print(f"Wrote → {out}")


if __name__ == "__main__":
    main()
