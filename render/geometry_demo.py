#!/usr/bin/env python3
"""
Preview page for render/geometry.py figures.

Renders one instance of each parallelogram angle-chase variant (figure + question
+ worked reason) into a single HTML page for visual inspection of the marks:
angle arcs, parallel chevrons, vertex labels, and the diagonal transversal.

    .venv/bin/python render/geometry_demo.py            # -> geometry_demo.html
    .venv/bin/python render/geometry_demo.py --seed 11
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from worksheets.generate import PROBLEMS

_VARIANTS = [
    "parallelogram_cointerior",
    "parallelogram_opposite",
    "parallelogram_alternate",
]

_KATEX = """\
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"
  onload="renderMathInElement(document.body,{delimiters:[{left:'$$',right:'$$',display:true},{left:'$',right:'$',display:false}],throwOnError:false})">
</script>"""

_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: Georgia, serif; background: #eceff3; color: #111; padding: 24px; }
h1 { font-size: 16pt; margin-bottom: 4px; }
.sub { color: #666; font-size: 10pt; margin-bottom: 20px; }
.variant { background: #fff; border: 1px solid #ccc; border-radius: 4px;
           padding: 16px; margin-bottom: 18px; }
.variant h2 { font-size: 10pt; color: #2563EB; text-transform: uppercase;
              letter-spacing: 0.05em; margin-bottom: 4px; }
.variant .reason { font-size: 10pt; color: #444; margin-bottom: 12px; }
.row { display: grid; grid-template-columns: repeat(6, 1fr); gap: 10px; }
.cell { text-align: center; }
.cell svg { width: 100%; height: auto; }
.cap { font-size: 9.5pt; color: #555; margin-top: 2px; }
"""


def _cell(pid: str, engine: Engine, seed: int) -> str:
    entry = PROBLEMS[pid]
    inst = engine.instantiate(pid, seed=seed)
    card = entry.template(inst.params)
    given = inst.params["given_deg"]
    (ans,) = inst.verifier.canonicals
    return (
        '<div class="cell">'
        f"{card.graph_svg}"
        f'<div class="cap">given ${given}^\\circ$ &rarr; ${ans}^\\circ$</div>'
        "</div>"
    )


_REASON = {
    "parallelogram_cointerior": (
        r"adjacent: $\hat{B}=180^\circ-\hat{A}$"
        r" (co-interior $\angle$s; $AD\parallel BC$)"
    ),
    "parallelogram_opposite": (
        r"opposite: $\hat{C}=\hat{A}$"
        r" (opposite $\angle$s of a $\parallel^{\text{m}}$)"
    ),
    "parallelogram_alternate": (
        r"alternate (Z): $B\hat{A}C=D\hat{C}A$"
        r" (alt $\angle$s; $AB\parallel DC$)"
    ),
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=7, help="base seed for the row")
    ap.add_argument("--cols", type=int, default=6, help="instances per variant")
    ap.add_argument("--output", default="geometry_demo.html")
    args = ap.parse_args()

    engine = Engine(
        registry=InMemoryRegistry({p: PROBLEMS[p].problem for p in _VARIANTS})
    )
    sections = []
    for pid in _VARIANTS:
        cells = "".join(_cell(pid, engine, args.seed + i) for i in range(args.cols))
        sections.append(
            '<div class="variant">'
            f"<h2>{pid.replace('parallelogram_', '')}</h2>"
            f'<div class="reason">{_REASON[pid]}</div>'
            f'<div class="row">{cells}</div>'
            "</div>"
        )
    html = (
        "<!DOCTYPE html><html lang='en'><head><meta charset='UTF-8'>"
        "<title>Geometry figure preview</title>"
        f"{_KATEX}<style>{_CSS}</style></head><body>"
        "<h1>GeometryFigure preview — pose variety</h1>"
        "<div class='sub'>render/geometry.py &middot; each row is one variant "
        "across seeds: rotation, scale (70-100%), and reflection vary; the angle "
        "relationships and labels do not. Figures are not to scale.</div>"
        f"{''.join(sections)}"
        "</body></html>"
    )
    Path(args.output).write_text(html, encoding="utf-8")
    print(f"Wrote preview -> {args.output}")


if __name__ == "__main__":
    main()
