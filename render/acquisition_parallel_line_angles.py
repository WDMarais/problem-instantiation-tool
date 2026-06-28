#!/usr/bin/env python3
"""
Acquisition sheet (vertical-slice prototype): angles on parallel lines (F / Z / co-int).

This sits one layer *below* the triangle-angle-sum sheet in the prerequisite DAG:
that proof cites "alternate ∠s", which this sheet grounds. The whole of parallel-
line angle work reduces to exactly two irreducibles —

    1. angles on a straight line = 180°   (a linear pair; gives vertically opposite)
    2. corresponding (F) angles equal      (the parallel postulate — the bedrock)

— and everything else is a theorem on top:

    alternate (Z)  = corresponding + vertically opposite
    co-interior    = corresponding + straight line

So F is the one thing you *accept* (it is what "parallel" means, via the slide /
translation picture); Z and co-interior you *prove*. This sheet marks the two
axioms, derives Z across the two crossings, and states co-interior as a corollary,
then hands over apply-it problems that demand the value *and* the reason.

Reuses render/geometry.py unchanged (now with dot=False / label="" on Point for
clean line endpoints). Derivation figures use NO pose — a fixed canonical layout.

    .venv/bin/python render/acquisition_parallel_line_angles.py   # -> *.html
"""

from __future__ import annotations

import argparse
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from render.geometry import (
    Angle,
    GeometryFigure,
    Point,
    Pose,
    Segment,
    render_figure,
)

_H = 2.2  # vertical gap between the two parallel lines (layout units)


def _points(theta_deg: float) -> list[Point]:
    """The configuration for a transversal meeting the lower line at angle θ.
    Lower line y=0, upper line y=_H (both horizontal → parallel); transversal up
    through Q=(0,0) at angle θ, crossing the upper line at P. θ is exactly the
    'above the lower line, right of the transversal' angle, so apply-problems can
    set it to the given value and the figure stays to-scale."""
    th = math.radians(theta_deg)
    dx, dy = math.cos(th), math.sin(th)
    px = _H / math.tan(th)  # x where the transversal meets the upper line
    return [
        # label_dir is figure-relative (layout y-up): keep labels clear of the
        # angle marks that cluster on the transversal's right, under any pose.
        Point(
            "P", px, _H, label_dir=(-0.55, 0.85)
        ),  # upper crossing, wide up-left wedge
        Point(
            "Q", 0.0, 0.0, label_dir=(-0.55, 0.85)
        ),  # lower crossing, wide up-left wedge
        Point("UL", -2.0, _H, dot=False, label=""),
        Point("UR", 2.9, _H, dot=False, label="ℓ"),  # name the upper line ℓ
        Point("LL", -2.4, 0.0, dot=False, label=""),
        Point("LR", 2.3, 0.0, dot=False, label="m"),  # name the lower line m
        Point("Tt", px + 0.55 * dx, _H + 0.55 * dy, dot=False, label=""),
        Point("Tb", -0.75 * dx, -0.75 * dy, dot=False, label=""),
    ]


_SEGS = [
    # both chevrons ride out to the same far end (p1 / left), clear of P, Q
    Segment("UL", "UR", arrows=1, mark_pos=0.2),  # ℓ, chevron near the left end
    Segment("LL", "LR", arrows=1, mark_pos=0.2),  # m, chevron near the left end
    Segment("Tt", "Tb"),  # the transversal
]


# the four angles we ever mark, by their position at each crossing
def _p_ar(lbl: str) -> Angle:  # at P, above ℓ, right of transversal
    return Angle("P", "UR", "Tt", label=lbl, arcs=1)


def _p_bl(lbl: str) -> Angle:  # at P, below ℓ (interior), left  — vert. opp. of _p_ar
    return Angle("P", "UL", "Q", label=lbl, arcs=1)


def _p_br(lbl: str) -> Angle:  # at P, below ℓ (interior), right — co-interior partner
    return Angle("P", "Q", "UR", label=lbl, arcs=1)


def _q_ar(lbl: str) -> Angle:  # at Q, above m (interior), right
    return Angle("Q", "LR", "P", label=lbl, arcs=1)


_DERIV_THETA = 63.0


def _deriv(stage: int) -> str:
    pts = _points(_DERIV_THETA)
    angles: list[Angle] = []
    if stage == 2:  # vertical angles: 1 and 2
        angles = [_p_ar("1"), _p_bl("2")]
    elif stage == 3:  # corresponding: 1 and 3
        angles = [_p_ar("1"), _q_ar("3")]
    elif stage == 4:  # alternate: 2 and 3
        angles = [_p_bl("2"), _q_ar("3")]
    return render_figure(GeometryFigure(points=pts, segments=_SEGS, angles=angles))


# ── derivation steps: figure + claim + reason ─────────────────────────────────
_STEPS = [
    (
        "The set-up",
        r"\ell \parallel m,\ \text{cut by a transversal at } P,\ Q.",
        r"\text{Two crossings. Name a few angles: } \hat{1},\hat{2}\ (\text{at }P),"
        r"\ \hat{3}\ (\text{at }Q).",
    ),
    (
        "Axiom — straight line",
        r"\hat{1} = \hat{2}",
        r"(\text{vertically opposite } \angle\text{s} -"
        r" \text{ each is } 180^\circ\!-\!\text{their shared neighbour})",
    ),
    (
        "Axiom — corresponding (F)",
        r"\hat{1} = \hat{3}",
        r"(\text{corresponding } \angle\text{s};\ \ell \parallel m)"
        r"\ \text{— slide } P \text{ onto } Q",
    ),
    (
        "Theorem — alternate (Z)",
        r"\hat{2} = \hat{1} = \hat{3}\ \Rightarrow\ \hat{2} = \hat{3}",
        r"(\text{vert. opp., then corresponding})\ \therefore\ "
        r"\text{alternate } \angle\text{s equal}",
    ),
]


# ── apply-it problems: one given angle + reason, to-scale, no answer key ───────
_APPLY = [
    # (theta, given-angle-builder, label for given, prompt, the relationship name)
    (58, _p_ar, "corresponding"),
    (64, _p_bl, "alternate"),
    (71, _p_br, "co-interior"),
]


def _random_pose(rng: random.Random) -> Pose:
    """Pure visual variety for the apply figures: a similarity transform (angle-
    preserving, so the given angle and answer are untouched). Rotation sets the
    angle of ingress; reflection flips the transversal between '/' and '\\'."""
    return Pose(
        rotate_deg=round(rng.uniform(0, 360), 1),
        scale=round(rng.uniform(0.82, 1.0), 3),
        reflect=rng.random() < 0.5,
    )


def _apply_cell(theta: int, given_builder, kind: str, pose: Pose) -> str:
    pts = _points(theta)
    angles = [given_builder(f"{theta}°"), _q_ar("x")]
    fig = GeometryFigure(points=pts, segments=_SEGS, angles=angles, pose=pose)
    svg = render_figure(fig)
    return (
        '<div class="pcell">'
        f"{svg}"
        r'<div class="pq">$x = $ <span class="box"></span></div>'
        f'<div class="pr">reason: <span class="rule"></span> '
        f'<span class="hint">({kind})</span></div>'
        "</div>"
    )


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
           padding: 12px 16px; margin-top: 6px; font-size: 11pt; line-height: 1.5; }
.theorem .cite { color: #2563EB; font-weight: bold; }
.practice-intro { font-size: 9.5pt; color: #555; margin-bottom: 10px; }
.pgrid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.pcell { text-align: center; }
.pcell svg { width: 100%; height: auto; }
.pq { font-size: 10pt; margin-top: 4px; text-align: left; }
.pr { font-size: 9pt; color: #777; margin-top: 3px; text-align: left; }
.hint { color: #aaa; font-style: italic; }
.box { display: inline-block; width: 46px; border-bottom: 1.5px solid #333; }
.rule { display: inline-block; width: 120px; border-bottom: 1px solid #aaa; }
"""


def build_html(seed: int = 0) -> str:
    steps_html = ""
    for i, (name, claim, reason) in enumerate(_STEPS, start=1):
        steps_html += (
            '<div class="step">'
            f'<span class="badge">Step {i}</span>'
            f'<div class="name">{name}</div>'
            f"{_deriv(i)}"
            f'<div class="claim">${claim}$</div>'
            f'<div class="reason">${reason}$</div>'
            "</div>"
        )
    theorem = (
        '<div class="theorem">'
        r"Two axioms only: <span class='cite'>∠s on a line $=180^\circ$</span> and "
        r"<span class='cite'>corresponding ∠s equal</span> (that one is the parallel "
        r"postulate — accept it). Everything else falls out:<br>"
        r"&bull; <b>Alternate (Z):</b> $\hat{2}=\hat{3}$ &mdash; vert. opp. then "
        r"corresponding. Tag <em>(alt $\angle$s; $\ell\parallel m$)</em>.<br>"
        r"&bull; <b>Co-interior:</b> $\hat{4}+\hat{3}=180^\circ$, since "
        r"$\hat{4}+\hat{1}=180^\circ$ ($\angle$s on a line) and $\hat{1}=\hat{3}$ "
        r"(corresponding). Tag <em>(co-int $\angle$s; $\ell\parallel m$)</em>."
        "</div>"
    )
    apply_html = "".join(
        _apply_cell(t, b, k, _random_pose(random.Random(seed + i)))
        for i, (t, b, k) in enumerate(_APPLY)
    )
    return (
        "<!DOCTYPE html><html lang='en'><head><meta charset='UTF-8'>"
        "<title>Acquisition — angles on parallel lines</title>"
        f"{_KATEX}<style>{_CSS}</style></head><body><div class='sheet'>"
        "<h1>Angles on parallel lines: where F and Z come from</h1>"
        "<div class='sub'>The two facts you accept, and the ones you can prove from "
        "them. &middot; prototype geometry acquisition sheet</div>"
        "<h2>Derivation</h2>"
        f"<div class='steps'>{steps_html}</div>"
        "<h2>The two axioms (everything else is a theorem)</h2>"
        f"{theorem}"
        "<h2>Your turn</h2>"
        "<div class='practice-intro'>Find $x$ <em>and</em> name the reason. The "
        "relationship is hinted; the citation (and the why) is yours.</div>"
        f"<div class='pgrid'>{apply_html}</div>"
        "</div></body></html>"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0, help="seed for apply-figure poses")
    ap.add_argument("--output", default="acquisition_parallel_line_angles.html")
    args = ap.parse_args()
    out = Path(args.output)
    out.write_text(build_html(args.seed), encoding="utf-8")
    print(f"Wrote → {out}")


if __name__ == "__main__":
    main()
