"""
A4 print renderer for acquisition sheets.

Takes a SheetData and returns a complete HTML string (two pages, print-ready).
Section B accepts an optional note for renderer-level label annotations.
"""

from __future__ import annotations

from content.sheet import (
    CollapsedEx,
    FiveStep,
    FourStep,
    PracticeEx,
    SheetData,
    SixStep,
    ThreeStep,
)

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


def _render_three(ex: ThreeStep) -> str:
    return (
        '<div class="worked-ex">'
        f'<div class="worked-step">${ex.equation}$</div>'
        f'<div class="worked-step">${ex.operation}$</div>'
        f'<div class="worked-step result">${ex.result}$</div>'
        "</div>"
    )


def _render_four(ex: FourStep) -> str:
    ref_html = f'<span class="model-ref">&#8594; {ex.model_ref}</span>'
    return (
        '<div class="worked-ex">'
        f'<div class="worked-step">${ex.equation}$</div>'
        f'<div class="worked-step">${ex.operation}$</div>'
        f'<div class="worked-step intermediate">${ex.intermediate}${ref_html}</div>'
        f'<div class="worked-step result">${ex.result}$</div>'
        "</div>"
    )


def _render_five(ex: FiveStep) -> str:
    return (
        '<div class="worked-ex">'
        f'<div class="worked-step">${ex.equation}$</div>'
        f'<div class="worked-step">${ex.op1}$</div>'
        f'<div class="worked-step intermediate">${ex.mid}$</div>'
        f'<div class="worked-step">${ex.op2}$</div>'
        f'<div class="worked-step result">${ex.result}$</div>'
        "</div>"
    )


def _render_six(ex: SixStep) -> str:
    return (
        '<div class="worked-ex">'
        f'<div class="worked-step">${ex.equation}$</div>'
        f'<div class="worked-step">${ex.op1}$</div>'
        f'<div class="worked-step intermediate">${ex.mid1}$</div>'
        f'<div class="worked-step">${ex.op2}$</div>'
        f'<div class="worked-step intermediate">${ex.mid2}$</div>'
        f'<div class="worked-step result">${ex.result}$</div>'
        "</div>"
    )


def _render_detailed(ex: ThreeStep | FourStep | FiveStep | SixStep) -> str:
    if isinstance(ex, SixStep):
        return _render_six(ex)
    if isinstance(ex, FiveStep):
        return _render_five(ex)
    if isinstance(ex, FourStep):
        return _render_four(ex)
    return _render_three(ex)


def _render_collapsed(ex: CollapsedEx) -> str:
    return (
        f'<div class="collapsed-ex">'
        f"${ex.equation} \\;\\Rightarrow\\; {ex.answer}$"
        f"</div>"
    )


def _render_practice_item(i: int, ex: PracticeEx) -> str:
    starred = ex.answer is not None
    num_class = "practice-num starred" if starred else "practice-num"
    label = f'{i}.<span class="star">*</span>' if starred else f"{i}."
    return (
        f'<div class="practice-item">'
        f'<div class="{num_class}">{label}</div>'
        f'<div class="practice-eq">${ex.equation}$</div>'
        f'<div class="answer-box"></div>'
        f"</div>"
    )


def _render_answer_entry(i: int, ex: PracticeEx) -> str:
    if ex.answer is None:
        return ""
    return (
        f'<div class="answer-entry">'
        f'<span class="n">{i}.</span>'
        f"<span>${ex.answer}$</span>"
        f"</div>"
    )


_STEP_LABEL = {ThreeStep: "three", FourStep: "four", FiveStep: "five", SixStep: "six"}


def _section_a_label(data: SheetData) -> str:
    steps = _STEP_LABEL[type(data.detailed[0])]
    return f"A &mdash; Method: {steps} steps"


def _section_b_label(note: str) -> str:
    base = "B &mdash; Shorthand: same idea in one step"
    if not note:
        return base
    styled = (
        f'<span style="font-weight:normal;text-transform:none;'
        f'letter-spacing:0;color:#aaa">({note})</span>'
    )
    return f"{base} {styled}"


def _page1(data: SheetData, section_b_note: str) -> str:
    detailed_html = "".join(_render_detailed(d) for d in data.detailed)
    collapsed_html = "".join(_render_collapsed(c) for c in data.collapsed)
    return (
        '<section class="page">'
        '<div class="page-header">'
        f"<h1>{data.title}</h1>"
        "<span>Page 1 of 2</span>"
        "</div>"
        f'<div class="balance-caption">{data.caption}</div>'
        f'<div class="section-label">{_section_a_label(data)}</div>'
        f'<div class="examples-grid">{detailed_html}</div>'
        f'<div class="section-label">{_section_b_label(section_b_note)}</div>'
        f'<div class="collapsed-grid">{collapsed_html}</div>'
        "</section>\n"
    )


def _page2(data: SheetData) -> str:
    practice_html = "".join(
        _render_practice_item(i, ex) for i, ex in enumerate(data.practice, 1)
    )
    answers_html = "".join(
        _render_answer_entry(i, ex) for i, ex in enumerate(data.practice, 1)
    )
    return (
        '<section class="page">'
        '<div class="page-header">'
        f"<h1>{data.title}</h1>"
        "<span>Page 2 of 2</span>"
        "</div>"
        '<div class="section-label">C &mdash; Your turn</div>'
        '<div class="practice-intro">'
        "Solve for $x$. Show your working on a separate sheet and write only your final answer in the box. "
        'Problems marked <span class="star">*</span> have answers at the bottom. '
        "Some answers are negative &mdash; check your sign."
        "</div>"
        f'<div class="practice-grid">{practice_html}</div>'
        '<div class="answers-block">'
        '<div class="answers-label">Answers &mdash; starred problems</div>'
        f'<div class="answers-grid">{answers_html}</div>'
        "</div>"
        "</section>\n"
    )


def build_html(data: SheetData, *, section_b_note: str = "") -> str:
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="UTF-8">\n'
        f"<title>{data.title}</title>\n"
        f"{_KATEX}\n"
        f"<style>{_CSS}</style>\n"
        "</head>\n<body>\n"
        + _page1(data, section_b_note)
        + _page2(data)
        + "</body>\n</html>\n"
    )
