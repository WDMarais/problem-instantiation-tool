#!/usr/bin/env python3
"""
Minimal HTML worksheet generator.

Usage (from project root):
    .venv/bin/python worksheets/generate.py 10
    .venv/bin/python worksheets/generate.py 10 --seed 42 --title "Revision: Quadratics"
    .venv/bin/python worksheets/generate.py 10 --per-page 3 --output out.html

Extensibility:
  - Add a problem type: write template_<id>(params) -> ProblemCard, register in
    TEMPLATES and REGISTRY.
  - When you have 3+ generators, split into _templates.py + _renderer.py;
    the ProblemCard dataclass and build_html() signature stay the same.
"""

from __future__ import annotations

import argparse
import math
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import sympy

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from content.examples.monic_factorise import problem as monic_factorise_problem
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry


# ── data model ────────────────────────────────────────────────────────────────


@dataclass
class ProblemCard:
    instruction: str  # plain text; inline math in $...$
    display_math: str  # LaTeX body for the display equation (without $$ delimiters)
    worked_steps: list[
        str
    ]  # LaTeX bodies for each solution step (without $ delimiters)


# ── problem templates ─────────────────────────────────────────────────────────


def _poly_latex(b: int, c: int) -> str:
    """LaTeX for x^2 + bx + c, handling signs and unit coefficients."""
    b_term = (
        ""
        if b == 0
        else "+ x"
        if b == 1
        else "- x"
        if b == -1
        else f"+ {b}x"
        if b > 0
        else f"- {abs(b)}x"
    )
    c_term = "" if c == 0 else f"+ {c}" if c > 0 else f"- {abs(c)}"
    return f"x^2 {b_term} {c_term}".strip()


def _factor_eq(r: int) -> str:
    """'x ± |r| = 0' with sign normalised (avoids 'x - -4 = 0')."""
    return f"x - {r} = 0" if r >= 0 else f"x + {abs(r)} = 0"


def template_monic_factorise(params: dict, detail: str = "full") -> ProblemCard:
    b, c = params["b"], params["c"]
    r1, r2 = sorted([params["root1"], params["root2"]])
    factor_sum = r1 + r2  # = -b
    factor_prod = c  # = mn

    factored_eq = sympy.latex(params["answer"]) + " = 0"
    solutions = rf"x = {r1} \quad \text{{or}} \quad x = {r2}"

    if detail == "full":
        # "-(m+n) = b ⟹ m+n = -b" makes the one sign flip in the method explicit.
        step_conditions = (
            rf"-(m+n) = {b} \;\Rightarrow\; m+n = {factor_sum}"
            rf", \quad mn = {factor_prod}"
        )
        # Zero-product property: show each factor = 0 so the root is transparent.
        # Note: space before {_factor_eq(...)} is required — \quad followed directly
        # by a letter is parsed as an unknown command (e.g. \quadx).
        zero_step = (
            rf"{_factor_eq(r1)} \;\Rightarrow\; x = {r1}"
            rf" \quad \text{{or}} \quad "
            rf"{_factor_eq(r2)} \;\Rightarrow\; x = {r2}"
        )
        steps = [
            r"(x-m)(x-n) = x^2 - (m+n)x + mn",
            step_conditions,
            rf"m = {r1}, \quad n = {r2}",
            factored_eq,
            zero_step,
            solutions,
        ]
    else:  # short — conditions + zero-product, skip the derivation scaffolding
        zero_step = (
            rf"{_factor_eq(r1)} \;\Rightarrow\; x = {r1}"
            rf" \quad \text{{or}} \quad "
            rf"{_factor_eq(r2)} \;\Rightarrow\; x = {r2}"
        )
        steps = [
            rf"m+n = {factor_sum}, \quad mn = {factor_prod}",
            factored_eq,
            zero_step,
            solutions,
        ]

    return ProblemCard(
        instruction="Factorise completely, then solve for $x$:",
        display_math=_poly_latex(b, c) + " = 0",
        worked_steps=steps,
    )


TEMPLATES: dict[str, Callable[[dict], ProblemCard]] = {
    monic_factorise_problem.id: template_monic_factorise,
}

REGISTRY: dict = {
    monic_factorise_problem.id: monic_factorise_problem,
}


# ── HTML / CSS ────────────────────────────────────────────────────────────────

# $$ for display, $ for inline — works cleanly in controlled content with no
# prose dollar signs.  List $$ first so auto-render greedily matches it before $.
_KATEX = """\
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"
  onload="renderMathInElement(document.body,{delimiters:[{left:'$$',right:'$$',display:true},{left:'$',right:'$',display:false}],throwOnError:false})">
</script>"""

_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }

body {
    font-family: Georgia, "Times New Roman", serif;
    background: #ddd;
    color: #111;
}

/* ── page shell: fixed A4 size, generous fixed padding ── */
.page {
    width: 210mm;
    height: 297mm;
    margin: 8mm auto;
    padding: 22mm 24mm 18mm;
    background: #fff;
    display: flex;
    flex-direction: column;
    overflow: hidden;           /* nothing spills past the page boundary */
    page-break-after: always;
    break-after: page;
}

.page-header {
    border-bottom: 1.5px solid #444;
    padding-bottom: 3.5mm;
    margin-bottom: 6mm;
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    flex-shrink: 0;
}
.page-header h1   { font-size: 12.5pt; font-weight: bold; }
.page-header span { font-size: 9pt; color: #666; }

/* problems flex-fills all remaining page height after the header */
.problems {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 5mm;
    min-height: 0;
}

.problem {
    flex: 1;
    display: flex;
    flex-direction: column;
    border: 1px solid #bbb;
    border-radius: 2px;
    padding: 4.5mm 5.5mm 3.5mm;
    min-height: 0;
}

.problem-label {
    font-size: 8.5pt;
    font-weight: bold;
    color: #777;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 2mm;
    flex-shrink: 0;
}

.problem-instruction {
    font-size: 10.5pt;
    margin-bottom: 3mm;
    flex-shrink: 0;
}

.problem-equation {
    font-size: 1.2em;
    padding: 0 3mm 3.5mm;
    flex-shrink: 0;
}

/* ruled working space: takes all remaining height inside the problem box */
.working-space {
    flex: 1;
    min-height: 55mm;
    background-image: repeating-linear-gradient(
        to bottom,
        transparent 0, transparent 8.5mm,
        #ccc 8.5mm, #ccc 9mm
    );
}

/* ── answer key: not a fixed-height page, just a trailing block ── */
.answer-key {
    width: 210mm;
    margin: 8mm auto;
    padding: 22mm 24mm 18mm;
    background: #fff;
}
.answer-key h2 {
    font-size: 12.5pt;
    font-weight: bold;
    border-bottom: 1.5px solid #444;
    padding-bottom: 3.5mm;
    margin-bottom: 7mm;
}
.answer-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(80mm, 1fr));
    gap: 5mm 8mm;
}
.answer-row {
    display: flex;
    align-items: flex-start;
    gap: 2.5mm;
    font-size: 11pt;
}
.answer-num { font-weight: bold; color: #777; min-width: 7mm; padding-top: 0.15em; }
.answer-steps { display: flex; flex-direction: column; gap: 1.5mm; }

@media print {
    body        { background: none; }
    .page       { margin: 0; }
    .answer-key { margin: 0; }
}
"""


def _problem_html(n: int, card: ProblemCard) -> str:
    return (
        '<div class="problem">'
        f'<div class="problem-label">Question {n}</div>'
        f'<div class="problem-instruction">{card.instruction}</div>'
        f'<div class="problem-equation">$${card.display_math}$$</div>'
        '<div class="working-space"></div>'
        "</div>"
    )


def _page_html(
    cards: list[ProblemCard],
    offset: int,
    page_n: int,
    total_pages: int,
    title: str,
) -> str:
    problems = "".join(_problem_html(offset + i + 1, c) for i, c in enumerate(cards))
    return (
        '<section class="page">'
        '<div class="page-header">'
        f"<h1>{title}</h1>"
        f"<span>Page {page_n} of {total_pages}</span>"
        "</div>"
        f'<div class="problems">{problems}</div>'
        "</section>\n"
    )


def _answer_key_html(cards: list[ProblemCard]) -> str:
    def _steps_html(steps: list[str]) -> str:
        return "".join(f"<div>${s}$</div>" for s in steps)

    rows = "".join(
        f'<div class="answer-row">'
        f'<span class="answer-num">{i + 1}.</span>'
        f'<div class="answer-steps">{_steps_html(c.worked_steps)}</div>'
        f"</div>"
        for i, c in enumerate(cards)
    )
    return (
        '<section class="answer-key">'
        "<h2>Worked Answers</h2>"
        f'<div class="answer-grid">{rows}</div>'
        "</section>\n"
    )


def build_html(title: str, cards: list[ProblemCard], per_page: int = 2) -> str:
    n_pages = math.ceil(len(cards) / per_page)
    pages = [
        _page_html(
            cards[p * per_page : (p + 1) * per_page],
            p * per_page,
            p + 1,
            n_pages,
            title,
        )
        for p in range(n_pages)
    ]
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="UTF-8">\n'
        f"<title>{title}</title>\n"
        f"{_KATEX}\n"
        f"<style>{_CSS}</style>\n"
        "</head>\n<body>\n"
        + "".join(pages)
        + _answer_key_html(cards)
        + "</body>\n</html>\n"
    )


# ── CLI ───────────────────────────────────────────────────────────────────────


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate an HTML practice worksheet.")
    ap.add_argument("n", type=int, help="Number of problems")
    ap.add_argument("--problem", default="monic_factorise", choices=list(TEMPLATES))
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--title", default="Factorisation Practice")
    ap.add_argument("--per-page", type=int, default=2, dest="per_page")
    ap.add_argument("--output", default="worksheet.html")
    ap.add_argument(
        "--long",
        type=int,
        default=None,
        dest="long_count",
        metavar="N",
        help="First N problems get full 6-step worked answer; rest use 3-step short form.",
    )
    args = ap.parse_args()

    engine = Engine(registry=InMemoryRegistry(REGISTRY))
    rng = random.Random(args.seed)
    template_fn = TEMPLATES[args.problem]
    long_count = args.long_count if args.long_count is not None else args.n

    cards = [
        template_fn(
            engine.instantiate(args.problem, seed=rng.randint(0, 2**31)).params,
            detail="full" if i < long_count else "short",
        )
        for i in range(args.n)
    ]

    html = build_html(args.title, cards, per_page=args.per_page)
    Path(args.output).write_text(html, encoding="utf-8")
    print(f"Wrote {args.n} problems ({args.problem}) → {args.output}")


if __name__ == "__main__":
    main()
