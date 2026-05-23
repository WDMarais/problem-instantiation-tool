#!/usr/bin/env python3
"""
Dense worked-example sheet: x ± a = b (non-zero RHS).

Prerequisites: linear_balance.py (1a/b) — student can already do x ± a = 0.

Two A4 pages:
  Page 1 — Study:
    Section A: 8 detailed 3-step worked examples (integers → fractions → symbols)
    Section B: 12 collapsed 1-step examples
  Page 2 — Practice:
    Section C: 16 own-work problems; starred problems have answers at the bottom

New challenge vs 1a/b: the RHS is not zero, so subtracting a leaves b on the
right (not 0). The student must carry b through: x + a = b → x = b − a.

Important cases to cover:
  - b < a: result is negative — students often panic here; include explicitly
  - negative b: x − a = −c is common in practice
  - fraction arithmetic: result requires adding/subtracting fractions

Usage:
    .venv/bin/python content/examples/linear_shift.py
    .venv/bin/python content/examples/linear_shift.py --output shift.html
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

.examples-grid {
    display: grid; grid-template-columns: 1fr 1fr;
    align-items: start;
    gap: 2.5mm 10mm; margin-bottom: 5mm; flex-shrink: 0;
}
.worked-ex {
    display: flex; flex-direction: column; gap: 1.5mm;
    padding: 2mm 3mm; border-left: 2px solid #ddd;
}
.worked-step { font-size: 9.5pt; line-height: 1.4; }
.worked-step.result {
    font-weight: bold;
    border-top: 1px solid #eee; margin-top: 0.5mm; padding-top: 0.5mm;
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
.practice-num { font-size: 8.5pt; font-weight: bold; color: #bbb; }
.practice-num.starred { color: #2563EB; }
.star { font-size: 11pt; }
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

_TITLE = "x ± a = b  —  Non-Zero Right-Hand Side"

# (equation, operation step, result)
_DETAILED: list[tuple[str, str, str]] = [
    (
        r"x + 3 = 7",
        r"x + 3 - 3 = 7 - 3",
        r"x = 4",
    ),
    (
        r"x - 5 = 2",
        r"x - 5 + 5 = 2 + 5",
        r"x = 7",
    ),
    (
        r"x + 8 = 3",
        r"x + 8 - 8 = 3 - 8",
        r"x = -5",
    ),
    (
        r"x - 2 = -6",
        r"x - 2 + 2 = -6 + 2",
        r"x = -4",
    ),
    (
        r"x + \tfrac{1}{2} = \tfrac{3}{4}",
        r"x + \tfrac{1}{2} - \tfrac{1}{2} = \tfrac{3}{4} - \tfrac{1}{2}",
        r"x = \tfrac{1}{4}",
    ),
    (
        r"x - \tfrac{1}{3} = \tfrac{1}{6}",
        r"x - \tfrac{1}{3} + \tfrac{1}{3} = \tfrac{1}{6} + \tfrac{1}{3}",
        r"x = \tfrac{1}{2}",
    ),
    (
        r"x + a = b",
        r"x + a - a = b - a",
        r"x = b - a",
    ),
    (
        r"x - p = q",
        r"x - p + p = q + p",
        r"x = p + q",
    ),
]

_COLLAPSED: list[tuple[str, str]] = [
    (r"x + 4 = 9", r"x = 5"),
    (r"x - 3 = 8", r"x = 11"),
    (r"x + 7 = 2", r"x = -5"),
    (r"x - 6 = -2", r"x = 4"),
    (r"x + 10 = 4", r"x = -6"),
    (r"x - 9 = -5", r"x = 4"),
    (r"x + \tfrac{1}{4} = \tfrac{3}{4}", r"x = \tfrac{1}{2}"),
    (r"x - \tfrac{2}{3} = \tfrac{1}{3}", r"x = 1"),
    (r"x + a = b", r"x = b - a"),
    (r"x - m = n", r"x = m + n"),
    (r"x + p = q", r"x = q - p"),
    (r"x - r = s", r"x = r + s"),
]

# (equation, answer or None)
# Negative results are included deliberately — students must not assume x > 0.
_PRACTICE: list[tuple[str, str | None]] = [
    (r"x + 5 = 9", r"x = 4"),
    (r"x - 3 = 7", None),
    (r"x + 6 = 2", r"x = -4"),
    (r"x - 4 = -1", None),
    (r"x + 9 = 4", r"x = -5"),
    (r"x - 8 = 5", None),
    (r"x + \tfrac{1}{2} = \tfrac{3}{2}", r"x = 1"),
    (r"x - \tfrac{1}{4} = \tfrac{3}{4}", None),
    (r"x + \tfrac{2}{3} = \tfrac{1}{3}", r"x = -\tfrac{1}{3}"),
    (r"x - \tfrac{1}{6} = \tfrac{5}{6}", None),
    (r"x + a = 2b", r"x = 2b - a"),
    (r"x - m = n + 1", None),
    (r"x + p = q", r"x = q - p"),
    (r"x - r = s", None),
    (r"x + 7 = -3", r"x = -10"),
    (r"x - k = j", None),
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
        "The 3 does not simply disappear from the left and reappear as $-3$ on the right. "
        "You subtract 3 from both sides: on the left it cancels to zero; "
        "on the right, 7 becomes $7 - 3 = 4$. "
        "The right-hand side is always affected too."
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
        label = f'{i}.<span class="star">*</span>' if starred else f"{i}."
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
        'Problems marked <span class="star">*</span> have answers at the bottom. '
        "Some answers are negative &mdash; check your sign."
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
        description="Generate x±a=b non-zero RHS worked-example sheet."
    )
    ap.add_argument("--output", default="linear_shift.html")
    args = ap.parse_args()

    html = build_html()
    Path(args.output).write_text(html, encoding="utf-8")
    print(f"Wrote → {args.output}")
