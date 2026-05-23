#!/usr/bin/env python3
"""
Dense worked-example sheet: a/x = b (x in the denominator).

Two A4 pages:
  Page 1 — Study:
    Section A: 6 detailed 4-step worked examples (integers → fraction RHS → symbols)
    Section B: 12 collapsed 1-step examples
  Page 2 — Practice:
    Section C: 16 own-work problems; starred problems have answers at the bottom

Key conceptual move: multiply both sides by x (an unknown variable).
x clears from the denominator on the left, leaving a = bx — then divide (2a).

The caption calls back to the previous sheet: students have already multiplied
both sides by p, r, m — x follows the same rule.

Four steps (not three) because the operation always produces an intermediate
a = bx before the final divide:
  1. equation
  2. × x on both sides
  3. a = bx          (intermediate — a known 2a form)
  4. x = a/b         (result)

Usage:
    .venv/bin/python content/examples/linear_xdenom.py
    .venv/bin/python content/examples/linear_xdenom.py --output xdenom.html
"""

from __future__ import annotations

import argparse
from pathlib import Path

_KATEX = """\
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"
  onload="renderMathInElement(document.body,{delimiters:[{left:'$$',right:'$$',display:true},{left:'$',right:'$',display:false}],throwOnError:false})">
</script>"""

_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: Georgia, "Times New Roman", serif; background: #ddd; color: #111; }

.page {
    width: 210mm; height: 297mm;
    margin: 8mm auto; padding: 16mm 22mm 14mm;
    background: #fff;
    display: flex; flex-direction: column;
    overflow: hidden;
    page-break-after: always; break-after: page;
}

.page-header {
    border-bottom: 1.5px solid #444;
    padding-bottom: 3mm; margin-bottom: 4mm;
    display: flex; justify-content: space-between; align-items: baseline;
    flex-shrink: 0;
}
.page-header h1 { font-size: 12pt; font-weight: bold; }
.page-header span { font-size: 9pt; color: #666; }

.balance-caption {
    font-size: 9pt; color: #444; font-style: italic;
    border-left: 3px solid #2563EB; padding-left: 5px;
    margin-bottom: 5mm; flex-shrink: 0; line-height: 1.5;
}

.section-label {
    font-size: 7.5pt; font-weight: bold; text-transform: uppercase;
    letter-spacing: 0.07em; color: #888;
    margin-bottom: 2mm; padding-bottom: 1mm; border-bottom: 1px solid #ececec;
    flex-shrink: 0;
}

/* Section A: 4-step worked examples — 2 columns, fewer rows than previous sheets */
.examples-grid {
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 2.5mm 10mm; margin-bottom: 5mm; flex-shrink: 0;
}
.worked-ex {
    display: flex; flex-direction: column; gap: 1.5mm;
    padding: 2mm 3mm; border-left: 2px solid #ddd;
}
.worked-step { font-size: 9.5pt; line-height: 1.4; }
.worked-step.intermediate {
    color: #888; font-style: italic; font-size: 8.5pt;
    display: flex; align-items: baseline; gap: 3mm;
}
.model-ref {
    font-size: 7pt; font-style: normal; color: #bbb;
    white-space: nowrap; flex-shrink: 0;
}
.worked-step.result {
    font-weight: bold;
    border-top: 1px solid #eee; margin-top: 1mm; padding-top: 1mm;
}

.collapsed-grid {
    display: grid; grid-template-columns: 1fr 1fr 1fr;
    gap: 1.5mm 6mm; flex-shrink: 0;
}
.collapsed-ex { font-size: 9.5pt; line-height: 1.55; }

.practice-intro {
    font-size: 8.5pt; color: #555; margin-bottom: 3mm; flex-shrink: 0;
}
.practice-grid {
    display: grid; grid-template-columns: repeat(4, 1fr);
    gap: 4mm 7mm; flex-shrink: 0;
}
.practice-item { display: flex; flex-direction: column; gap: 1mm; }
.practice-num { font-size: 7.5pt; font-weight: bold; color: #bbb; }
.practice-num.starred { color: #2563EB; }
.practice-eq { font-size: 10.5pt; line-height: 1.35; }
.answer-box {
    height: 9mm; border: 1px solid #bbb; border-radius: 1px;
    margin-top: 1.5mm; background: #fafafa;
}

.answers-block {
    margin-top: auto; padding-top: 3.5mm; border-top: 1px dashed #ccc;
    flex-shrink: 0;
}
.answers-label {
    font-size: 7.5pt; font-weight: bold; color: #888;
    text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 2mm;
}
.answers-grid {
    display: grid; grid-template-columns: repeat(4, 1fr);
    gap: 1.5mm 6mm;
}
.answer-entry { font-size: 9pt; display: flex; gap: 2mm; align-items: baseline; }
.answer-entry .n { font-weight: bold; color: #bbb; min-width: 5mm; }

@media print {
    body { background: none; }
    .page { margin: 0; }
}
"""

_TITLE = "a / x = b  —  Multiply Both Sides by x"

# (equation, multiply-step, intermediate a=bx, result)
# The intermediate step is styled lighter — it's a known form (2a), not a new idea.
_DETAILED: list[tuple[str, str, str, str]] = [
    (
        r"\tfrac{5}{x} = 2",
        r"\tfrac{5}{x} \times x = 2 \times x",
        r"5 = 2x",
        r"x = \tfrac{5}{2}",
    ),
    (
        r"\tfrac{6}{x} = 3",
        r"\tfrac{6}{x} \times x = 3 \times x",
        r"6 = 3x",
        r"x = 2",
    ),
    (
        r"\tfrac{6}{x} = \tfrac{3}{4}",
        r"\tfrac{6}{x} \times x = \tfrac{3}{4} \times x",
        r"6 = \tfrac{3x}{4}",
        r"x = 8",
    ),
    (
        r"\tfrac{1}{x} = \tfrac{1}{5}",
        r"\tfrac{1}{x} \times x = \tfrac{1}{5} \times x",
        r"1 = \tfrac{x}{5}",
        r"x = 5",
    ),
    (
        r"\tfrac{a}{x} = b",
        r"\tfrac{a}{x} \times x = b \times x",
        r"a = bx",
        r"x = \tfrac{a}{b}",
    ),
    (
        r"\tfrac{p}{x} = \tfrac{q}{r}",
        r"\tfrac{p}{x} \times x = \tfrac{q}{r} \times x",
        r"p = \tfrac{qx}{r}",
        r"x = \tfrac{pr}{q}",
    ),
]

_COLLAPSED: list[tuple[str, str]] = [
    (r"\tfrac{4}{x} = 2", r"x = 2"),
    (r"\tfrac{9}{x} = 3", r"x = 3"),
    (r"\tfrac{7}{x} = 2", r"x = \tfrac{7}{2}"),
    (r"\tfrac{8}{x} = 5", r"x = \tfrac{8}{5}"),
    (r"\tfrac{2}{x} = \tfrac{1}{3}", r"x = 6"),
    (r"\tfrac{5}{x} = \tfrac{2}{3}", r"x = \tfrac{15}{2}"),
    (r"\tfrac{k}{x} = m", r"x = \tfrac{k}{m}"),
    (r"\tfrac{a}{x} = \tfrac{1}{b}", r"x = ab"),
    (r"\tfrac{c}{x} = \tfrac{d}{e}", r"x = \tfrac{ce}{d}"),
    (r"\tfrac{n}{x} = n", r"x = 1"),
    (r"\tfrac{p}{x} = \tfrac{p}{q}", r"x = q"),
    (r"\tfrac{ab}{x} = c", r"x = \tfrac{ab}{c}"),
]

# (equation, answer or None); None = student works it out
_PRACTICE: list[tuple[str, str | None]] = [
    (r"\tfrac{4}{x} = 2", r"x = 2"),
    (r"\tfrac{10}{x} = 5", None),
    (r"\tfrac{7}{x} = 3", r"x = \tfrac{7}{3}"),
    (r"\tfrac{9}{x} = 6", None),
    (r"\tfrac{5}{x} = \tfrac{1}{2}", r"x = 10"),
    (r"\tfrac{3}{x} = \tfrac{3}{4}", None),
    (r"\tfrac{a}{x} = 5", r"x = \tfrac{a}{5}"),
    (r"\tfrac{k}{x} = m", None),
    (r"\tfrac{p}{x} = \tfrac{1}{q}", r"x = pq"),
    (r"\tfrac{c}{x} = \tfrac{d}{e}", None),
    (r"\tfrac{6}{x} = \tfrac{3}{4}", r"x = 8"),
    (r"\tfrac{n}{x} = n", None),
    (r"\tfrac{1}{x} = \tfrac{1}{7}", r"x = 7"),
    (r"\tfrac{r}{x} = \tfrac{s}{t}", None),
    (r"\tfrac{8}{x} = 5", r"x = \tfrac{8}{5}"),
    (r"\tfrac{ab}{x} = c", None),
]


def _page1_html() -> str:
    detailed_items = "".join(
        '<div class="worked-ex">'
        f'<div class="worked-step">${eq}$</div>'
        f'<div class="worked-step">${mult}$</div>'
        f'<div class="worked-step intermediate">${inter}$'
        f'<span class="model-ref">&#8594; ax&nbsp;=&nbsp;b</span></div>'
        f'<div class="worked-step result">${result}$</div>'
        "</div>"
        for eq, mult, inter, result in _DETAILED
    )
    collapsed_items = "".join(
        f'<div class="collapsed-ex">${eq} \\;\\Rightarrow\\; {ans}$</div>'
        for eq, ans in _COLLAPSED
    )
    return (
        '<section class="page">'
        '<div class="page-header">'
        f"<h1>{_TITLE}</h1>"
        "<span>Page 1 of 2</span>"
        "</div>"
        '<div class="balance-caption">'
        "In the previous sheet you multiplied both sides by p, r, m — x follows the same rule. "
        "Multiplying by x clears it from the denominator, leaving a&nbsp;=&nbsp;bx. "
        "You then solve that as before: divide both sides by b."
        "</div>"
        '<div class="section-label">A &mdash; Method: four steps</div>'
        f'<div class="examples-grid">{detailed_items}</div>'
        '<div class="section-label">B &mdash; Shorthand: same idea in one step</div>'
        f'<div class="collapsed-grid">{collapsed_items}</div>'
        "</section>\n"
    )


def _page2_html() -> str:
    practice_items = []
    for i, (eq, ans) in enumerate(_PRACTICE, 1):
        starred = ans is not None
        num_class = "practice-num starred" if starred else "practice-num"
        label = f"{i}.*" if starred else f"{i}."
        practice_items.append(
            f'<div class="practice-item">'
            f'<div class="{num_class}">{label}</div>'
            f'<div class="practice-eq">${eq}$</div>'
            f'<div class="answer-box"></div>'
            f"</div>"
        )

    answer_entries = []
    for i, (_, ans) in enumerate(_PRACTICE, 1):
        if ans is not None:
            answer_entries.append(
                f'<div class="answer-entry">'
                f'<span class="n">{i}.</span>'
                f"<span>${ans}$</span>"
                f"</div>"
            )

    return (
        '<section class="page">'
        '<div class="page-header">'
        f"<h1>{_TITLE}</h1>"
        "<span>Page 2 of 2</span>"
        "</div>"
        '<div class="section-label">C &mdash; Your turn</div>'
        '<div class="practice-intro">'
        "Solve for $x$. Write your answer in the box. "
        "Problems marked * have answers at the bottom of this page."
        "</div>"
        f'<div class="practice-grid">{"".join(practice_items)}</div>'
        '<div class="answers-block">'
        '<div class="answers-label">Answers &mdash; starred problems</div>'
        f'<div class="answers-grid">{"".join(answer_entries)}</div>'
        "</div>"
        "</section>\n"
    )


def build_html() -> str:
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="UTF-8">\n'
        f"<title>{_TITLE}</title>\n"
        f"{_KATEX}\n"
        f"<style>{_CSS}</style>\n"
        "</head>\n<body>\n" + _page1_html() + _page2_html() + "</body>\n</html>\n"
    )


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Generate a/x=b worked-example sheet.")
    ap.add_argument("--output", default="linear_xdenom.html")
    args = ap.parse_args()

    html = build_html()
    Path(args.output).write_text(html, encoding="utf-8")
    print(f"Wrote → {args.output}")
