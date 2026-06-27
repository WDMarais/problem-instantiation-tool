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
.grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; }
.card { background: #fff; border: 1px solid #ccc; border-radius: 4px; padding: 16px; }
.card h2 { font-size: 10pt; color: #2563EB; text-transform: uppercase;
           letter-spacing: 0.05em; margin-bottom: 10px; }
.instruction { font-size: 11pt; margin-bottom: 6px; line-height: 1.4; }
.given { font-size: 12pt; margin-bottom: 10px; }
.fig { text-align: center; margin: 6px 0 12px; }
.fig svg { width: 340px; height: auto; }
.reason { border-top: 1px dashed #ccc; padding-top: 10px; }
.reason .lbl { font-size: 8pt; color: #888; text-transform: uppercase;
               letter-spacing: 0.05em; margin-bottom: 6px; }
.reason div.step { font-size: 11pt; margin-bottom: 4px; }
"""


def _card(pid: str, engine: Engine, seed: int) -> str:
    entry = PROBLEMS[pid]
    inst = engine.instantiate(pid, seed=seed)
    card = entry.template(inst.params)
    steps = "".join(f'<div class="step">${s}$</div>' for s in card.worked_steps)
    return (
        '<div class="card">'
        f"<h2>{pid.replace('parallelogram_', '')}</h2>"
        f'<div class="instruction">{card.instruction}</div>'
        f'<div class="given">$${card.display_math}$$</div>'
        f'<div class="fig">{card.graph_svg}</div>'
        '<div class="reason"><div class="lbl">Worked reason</div>'
        f"{steps}</div>"
        "</div>"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--output", default="geometry_demo.html")
    args = ap.parse_args()

    engine = Engine(
        registry=InMemoryRegistry({p: PROBLEMS[p].problem for p in _VARIANTS})
    )
    cards = "".join(_card(pid, engine, args.seed) for pid in _VARIANTS)
    html = (
        "<!DOCTYPE html><html lang='en'><head><meta charset='UTF-8'>"
        "<title>Geometry figure preview</title>"
        f"{_KATEX}<style>{_CSS}</style></head><body>"
        "<h1>GeometryFigure preview — parallelogram angle-chases</h1>"
        "<div class='sub'>render/geometry.py &middot; figures are display-only, "
        "deliberately not to scale</div>"
        f"<div class='grid'>{cards}</div>"
        "</body></html>"
    )
    Path(args.output).write_text(html, encoding="utf-8")
    print(f"Wrote preview -> {args.output}")


if __name__ == "__main__":
    main()
