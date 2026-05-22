#!/usr/bin/env python3
"""
Dense worked-example sheet: x + a = 0 and x − a = 0 (balance method).

Two A4 pages:
  Page 1 — Study:
    Section A (top ~55%): 8 detailed 3-step worked examples
    Section B (bottom ~45%): 12 collapsed 1-step examples (more examples, less space)
  Page 2 — Practice:
    Section C: 16 own-work problems in a 4-column grid
    Answers for starred problems appear at the bottom of page 2.

Content scope: integers, simple fractions, single variables.
Both x + a = 0 and x − a = 0 forms are covered and interleaved.

Usage:
    .venv/bin/python content/examples/linear_balance.py
    .venv/bin/python content/examples/linear_balance.py --output balance.html
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

/* ── Section A: 3-step worked examples ───────────────────────── */
.examples-grid {
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 2.5mm 10mm; margin-bottom: 5mm; flex-shrink: 0;
}
.worked-ex {
    display: flex; flex-direction: column; gap: 0;
    padding: 2mm 3mm; border-left: 2px solid #ddd;
}
.worked-step { font-size: 9.5pt; line-height: 1.6; }
.worked-step.result { font-weight: bold; border-top: 1px solid #eee; margin-top: 1mm; padding-top: 1mm; }

/* ── Section B: collapsed 1-step examples ────────────────────── */
.collapsed-grid {
    display: grid; grid-template-columns: 1fr 1fr 1fr;
    gap: 1.5mm 6mm; flex-shrink: 0;
}
.collapsed-ex { font-size: 9.5pt; line-height: 1.55; }

/* ── Section C: practice grid ────────────────────────────────── */
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

/* ── Answers block ────────────────────────────────────────────── */
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

_TITLE = "x + a = 0 — Balance Method"

# Each entry: (equation, middle step showing both-sides operation, result)
_DETAILED: list[tuple[str, str, str]] = [
    (
        r"x - 5 = 0",
        r"x - 5 + 5 = 0 + 5",
        r"x = 5",
    ),
    (
        r"x + 6 = 0",
        r"x + 6 - 6 = 0 - 6",
        r"x = -6",
    ),
    (
        r"x - 12 = 0",
        r"x - 12 + 12 = 0 + 12",
        r"x = 12",
    ),
    (
        r"x + 8 = 0",
        r"x + 8 - 8 = 0 - 8",
        r"x = -8",
    ),
    (
        r"x - \tfrac{1}{2} = 0",
        r"x - \tfrac{1}{2} + \tfrac{1}{2} = 0 + \tfrac{1}{2}",
        r"x = \tfrac{1}{2}",
    ),
    (
        r"x + \tfrac{3}{4} = 0",
        r"x + \tfrac{3}{4} - \tfrac{3}{4} = 0 - \tfrac{3}{4}",
        r"x = -\tfrac{3}{4}",
    ),
    (
        r"x - p = 0",
        r"x - p + p = 0 + p",
        r"x = p",
    ),
    (
        r"x + k = 0",
        r"x + k - k = 0 - k",
        r"x = -k",
    ),
]

# Each entry: (equation, answer) — displayed as "equation  ⟹  answer"
_COLLAPSED: list[tuple[str, str]] = [
    (r"x - 3 = 0", r"x = 3"),
    (r"x + 7 = 0", r"x = -7"),
    (r"x + 2 = 0", r"x = -2"),
    (r"x - 9 = 0", r"x = 9"),
    (r"x - \tfrac{1}{3} = 0", r"x = \tfrac{1}{3}"),
    (r"x + \tfrac{2}{5} = 0", r"x = -\tfrac{2}{5}"),
    (r"x - \tfrac{5}{6} = 0", r"x = \tfrac{5}{6}"),
    (r"x + \tfrac{1}{4} = 0", r"x = -\tfrac{1}{4}"),
    (r"x - m = 0", r"x = m"),
    (r"x + n = 0", r"x = -n"),
    (r"x - \alpha = 0", r"x = \alpha"),
    (r"x + q = 0", r"x = -q"),
]

# Each entry: (equation, answer or None)
# answer is not None  ↔  starred; answer shown at bottom of page 2
_PRACTICE: list[tuple[str, str | None]] = [
    (r"x - 4 = 0", r"x = 4"),
    (r"x + 3 = 0", None),
    (r"x + 8 = 0", r"x = -8"),
    (r"x - 1 = 0", None),
    (r"x - 7 = 0", r"x = 7"),
    (r"x + 5 = 0", None),
    (r"x + \tfrac{1}{2} = 0", r"x = -\tfrac{1}{2}"),
    (r"x - \tfrac{3}{4} = 0", None),
    (r"x - \tfrac{2}{3} = 0", r"x = \tfrac{2}{3}"),
    (r"x + \tfrac{5}{8} = 0", None),
    (r"x - r = 0", r"x = r"),
    (r"x + t = 0", None),
    (r"x + \beta = 0", r"x = -\beta"),
    (r"x - \lambda = 0", None),
    (r"x + 11 = 0", r"x = -11"),
    (r"x - \tfrac{2}{5} = 0", None),
]


def _page1_html() -> str:
    detailed_items = "".join(
        '<div class="worked-ex">'
        f'<div class="worked-step">${eq}$</div>'
        f'<div class="worked-step">${step}$</div>'
        f'<div class="worked-step result">${result}$</div>'
        "</div>"
        for eq, step, result in _DETAILED
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
        "Principle: we add or subtract the same value on both sides to keep the equation balanced."
        "</div>"
        '<div class="section-label">A &mdash; Method: three steps</div>'
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
    ap = argparse.ArgumentParser(
        description="Generate x+a=0 balance-method worked-example sheet."
    )
    ap.add_argument("--output", default="linear_balance.html")
    args = ap.parse_args()

    html = build_html()
    Path(args.output).write_text(html, encoding="utf-8")
    print(f"Wrote → {args.output}")
