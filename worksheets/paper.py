"""
Paper-assembly layer — instantiate a real NSC paper's question skeleton with
fresh variable values, as a self-marking practice paper.

A :class:`PaperSpec` is an ordered manifest of numbered slots mirroring a real
paper's structure (Q-number + part-marks + topic). Each slot is either:

- **generated** — references a wired generator (``worksheets.generate.PROBLEMS``).
  The engine instantiates it and the verifier can mark it, so the slot is *live*:
  it respawns with fresh numbers on every seed and its memo is machine-checked.
- **static** — a fixed passthrough for a *resistant* item (a "prove / interpret /
  draw" question we cannot auto-generate or auto-mark), carrying its own stem and
  worked memo, authored by us.

The manifest **is** the product object ("2025 May/June P1") and the thing later
mixed and matched. It stores only facts — Q-number, marks, topic, and a citation
— never the exam's wording (project corpus-provenance rule): generated slots get
their wording from our own generator; static slots are authored by us. Every
rendered paper carries a "not an official DBE/NSC paper" disclaimer, and the
mathematical skeleton (topics, mark allocation) is the only thing mirrored — never
the paper's text or figures.

This is the Q1 spine: it proves the whole pipeline (manifest → instantiate →
NSC-numbered render + margin marks + self-checked memo, incl. one resistant
passthrough) on render-free algebra, before breadth and the plotter builders.
"""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass, field
from pathlib import Path

from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from worksheets.generate import (
    PROBLEMS,
    REGISTRY,
    _generate_cards,
    _problem_marks,
    _tex_html,
    _working_height_mm,
    html_to_pdf,
    inline_style,
    prerender_body,
)

_DISCLAIMER = (
    "Practice worksheet — not an official DBE/NSC paper. Question numbers and mark "
    "allocations mirror the structure of a past paper for revision only; all wording "
    "and numeric values are independently generated."
)


# ── manifest (pure data) ──────────────────────────────────────────────────────


@dataclass(frozen=True)
class StaticContent:
    """A fixed, hand-authored item — used for a resistant slot the tool cannot
    generate or auto-mark. Wording is ours; nothing is copied from the exam."""

    instruction: str  # plain text; inline math in $…$
    memo_steps: tuple[str, ...]  # LaTeX bodies (no $ delimiters) — the fixed memo
    display_math: str = ""  # optional givens, LaTeX body (no $$ delimiters)


@dataclass(frozen=True)
class PaperSlot:
    """One numbered exam item. Exactly one of ``problem_id`` / ``static`` is set."""

    number: str  # NSC dotted number, e.g. "1.1.1", "1.2", "1.3"
    marks: int  # the paper's part-mark — authoritative for what the page prints
    topic: str  # short human label (facts only, not the exam's wording)
    problem_id: str | None = (
        None  # generated slot → key in worksheets.generate.PROBLEMS
    )
    static: StaticContent | None = None  # resistant passthrough

    def __post_init__(self) -> None:
        if (self.problem_id is None) == (self.static is None):
            raise ValueError(
                f"slot {self.number}: set exactly one of problem_id / static"
            )


@dataclass(frozen=True)
class PaperSpec:
    """An ordered manifest mirroring a real paper's skeleton."""

    title: str  # what the page prints, e.g. "Mathematics P1 — Practice"
    source: str  # citation, provenance only, e.g. "2025 May/June P1"
    slots: tuple[PaperSlot, ...]
    disclaimer: str = _DISCLAIMER

    @property
    def total_marks(self) -> int:
        return sum(s.marks for s in self.slots)


# ── driver (manifest → instantiated slots) ────────────────────────────────────


@dataclass
class RenderedSlot:
    slot: PaperSlot
    instruction: str
    display_math: str
    memo_steps: list[str]
    graph_svg: str | None = None
    generated: bool = False
    mark_warning: str | None = None  # loud when paper marks ≠ generator marks
    warnings: list[str] = field(default_factory=list)


def build_paper(spec: PaperSpec, *, seed: int | None = None) -> list[RenderedSlot]:
    """Instantiate every slot of *spec*. Generated slots are drawn from the engine
    (fresh per seed); static slots pass through. The paper's declared marks are
    what the page prints; a mismatch with the generator's own ``marks_possible`` is
    recorded as a loud warning — a real calibration gap for a scoring-identical
    product, never silently reconciled (project house rule)."""
    engine = Engine(registry=InMemoryRegistry(REGISTRY))
    rng = random.Random(seed)
    out: list[RenderedSlot] = []
    for slot in spec.slots:
        if slot.problem_id is not None:
            entry = PROBLEMS[slot.problem_id]
            card = _generate_cards(engine, entry, rng, 1, 1)[0]
            gen_marks = _problem_marks(entry.problem)
            warn = None
            if gen_marks is not None and gen_marks != slot.marks:
                warn = (
                    f"slot {slot.number}: paper marks {slot.marks} ≠ generator "
                    f"marks {gen_marks} ({slot.problem_id})"
                )
            out.append(
                RenderedSlot(
                    slot=slot,
                    instruction=card.instruction,
                    display_math=card.display_math,
                    memo_steps=list(card.worked_steps),
                    graph_svg=card.graph_svg,
                    generated=True,
                    mark_warning=warn,
                    warnings=[warn] if warn else [],
                )
            )
        else:
            s = slot.static
            assert s is not None
            out.append(
                RenderedSlot(
                    slot=slot,
                    instruction=s.instruction,
                    display_math=s.display_math,
                    memo_steps=list(s.memo_steps),
                    generated=False,
                )
            )
    return out


# ── renderer ──────────────────────────────────────────────────────────────────

_PAPER_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: Georgia, 'Times New Roman', serif; color: #1a1a1a;
       background: #f4f4f4; padding: 12mm 0; }
.paper, .memo {
    width: 210mm; min-height: 297mm; margin: 0 auto 10mm; padding: 18mm 16mm;
    background: #fff; box-shadow: 0 1px 4px rgba(0,0,0,.15); }
.paper-header { text-align: center; border-bottom: 2px solid #1a1a1a;
                padding-bottom: 6px; margin-bottom: 4mm; }
.paper-title { font-size: 15pt; font-weight: bold; letter-spacing: .3px; }
.paper-sub { font-size: 9.5pt; color: #555; margin-top: 2px; }
.disclaimer { font-size: 8pt; font-style: italic; color: #666; text-align: center;
              border: 1px solid #ddd; background: #fafafa; padding: 4px 8px;
              margin-bottom: 6mm; }
.question { margin-bottom: 7mm; }
.q-head { display: flex; justify-content: space-between; align-items: baseline;
          border-bottom: 1px solid #999; padding-bottom: 2px; margin-bottom: 3mm; }
.q-title { font-size: 12pt; font-weight: bold; letter-spacing: .5px; }
.q-marks { font-size: 10pt; font-weight: bold; }
.slot { display: grid; grid-template-columns: 16mm 1fr 14mm; column-gap: 3mm;
        margin-bottom: 3mm; align-items: start; }
.slot.depth-2 { padding-left: 0; }
.slot.depth-3 { padding-left: 8mm; }
.slot-num { font-weight: bold; font-size: 10.5pt; white-space: nowrap; }
.slot-content { min-width: 0; }
.slot-instruction { font-size: 10.5pt; line-height: 1.35; }
.slot-eq { margin: 1.5mm 0; }
.slot-graph { margin: 1.5mm 0; }
.work-space { border-bottom: 1px dotted #ccc; }
.slot-marks { text-align: right; font-size: 10pt; white-space: nowrap; }
.memo h2 { font-size: 13pt; border-bottom: 2px solid #1a1a1a; padding-bottom: 3px;
           margin-bottom: 4mm; }
.memo-row { display: grid; grid-template-columns: 16mm 1fr auto auto; column-gap: 3mm;
            align-items: baseline; padding: 1.5mm 0; border-bottom: 1px solid #eee; }
.memo-num { font-weight: bold; font-size: 10pt; }
.memo-steps { font-size: 10pt; line-height: 1.5; }
.memo-steps > div { margin: .5mm 0; }
.memo-marks { font-weight: bold; font-size: 9.5pt; }
.memo-badge { font-size: 7.5pt; text-transform: uppercase; letter-spacing: .5px;
              padding: 1px 5px; border-radius: 3px; margin-left: 4mm; }
.memo-badge.auto { background: #dcfce7; color: #166534; }
.memo-badge.static { background: #fef3c7; color: #92400e; }
@media print { body { background: #fff; padding: 0; }
    .paper, .memo { box-shadow: none; margin: 0; page-break-after: always; } }
"""


def _slot_html(rs: RenderedSlot) -> str:
    depth = rs.slot.number.count(".") + 1
    eq = (
        f'<div class="slot-eq">$${_tex_html(rs.display_math)}$$</div>'
        if rs.display_math
        else ""
    )
    graph = f'<div class="slot-graph">{rs.graph_svg}</div>' if rs.graph_svg else ""
    h = _working_height_mm(rs.slot.marks)
    return (
        f'<div class="slot depth-{depth}">'
        f'<span class="slot-num">{rs.slot.number}</span>'
        f'<div class="slot-content">'
        f'<div class="slot-instruction">{rs.instruction}</div>'
        f"{eq}{graph}"
        f'<div class="work-space" style="height:{h}mm"></div>'
        f"</div>"
        f'<span class="slot-marks">({rs.slot.marks})</span>'
        f"</div>"
    )


def _memo_row_html(rs: RenderedSlot) -> str:
    steps = "".join(f"<div>${_tex_html(s)}$</div>" for s in rs.memo_steps)
    badge = "auto" if rs.generated else "static"
    return (
        f'<div class="memo-row">'
        f'<span class="memo-num">{rs.slot.number}</span>'
        f'<div class="memo-steps">{steps}</div>'
        f'<span class="memo-marks">[{rs.slot.marks}]</span>'
        f'<span class="memo-badge {badge}">{badge}</span>'
        f"</div>"
    )


def render_paper_html(spec: PaperSpec, rendered: list[RenderedSlot]) -> str:
    # group consecutive slots by their leading question number ("1" of "1.1.1")
    groups: list[tuple[str, list[RenderedSlot]]] = []
    for rs in rendered:
        head = rs.slot.number.split(".")[0]
        if not groups or groups[-1][0] != head:
            groups.append((head, []))
        groups[-1][1].append(rs)

    questions = []
    for head, slots in groups:
        q_marks = sum(rs.slot.marks for rs in slots)
        body = "".join(_slot_html(rs) for rs in slots)
        questions.append(
            f'<div class="question">'
            f'<div class="q-head">'
            f'<span class="q-title">QUESTION {head}</span>'
            f'<span class="q-marks">[{q_marks}]</span>'
            f"</div>"
            f'<div class="q-body">{body}</div>'
            f"</div>"
        )

    memo = "".join(_memo_row_html(rs) for rs in rendered)
    paper = (
        '<section class="paper">'
        '<div class="paper-header">'
        f'<div class="paper-title">{spec.title}</div>'
        f'<div class="paper-sub">Variable instantiation of {spec.source} '
        f"· {spec.total_marks} marks</div>"
        "</div>"
        f'<p class="disclaimer">{spec.disclaimer}</p>'
        + "".join(questions)
        + "</section>\n"
        '<section class="memo">'
        "<h2>Marking Memorandum</h2>"
        f"{memo}"
        "</section>\n"
    )
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n<head>\n<meta charset="UTF-8">\n'
        f"<title>{spec.title}</title>\n"
        f"{inline_style()}\n"
        f"<style>{_PAPER_CSS}</style>\n"
        "</head>\n<body>\n" + prerender_body(paper) + "</body>\n</html>\n"
    )


# ── the first spine: 2025 May/June P1, Question 1 ─────────────────────────────

# Q1 is all render-free algebra: it proves the pipeline (numbering, margin marks,
# memo, and one resistant passthrough at 1.3) without waiting on the plotter.
# Mark allocations follow the paper skeleton (corpus-crosswalk.md). Where a
# generator's own marks differ, build_paper() emits a loud calibration warning.
_MJ2025_P1_Q1 = PaperSpec(
    title="Mathematics P1 — Practice",
    source="2025 May/June P1",
    slots=(
        PaperSlot("1.1.1", 3, "quadratic — factorise", problem_id="quadratic_factor"),
        # TODO(1.1.2): needs a non-monic quadratic-formula (2-dp) variant; the
        # factorise generator stands in for now so the spine renders end-to-end.
        PaperSlot("1.1.2", 3, "quadratic — formula", problem_id="quadratic_factor"),
        PaperSlot(
            "1.1.3", 3, "exponential equation", problem_id="exponential_equation"
        ),
        PaperSlot(
            "1.1.4", 3, "quadratic inequality", problem_id="quadratic_inequality"
        ),
        PaperSlot("1.1.5", 4, "surd equation", problem_id="surd_equation"),
        PaperSlot(
            "1.2", 6, "nonlinear simultaneous", problem_id="nonlinear_simultaneous"
        ),
        PaperSlot(
            "1.3",
            3,
            "exponent-algebra proof (resistant)",
            static=StaticContent(
                instruction=(
                    "Prove, without using a calculator, that "
                    r"$\dfrac{3^{x+2} - 3^{x}}{3^{x+1}} = \dfrac{8}{3}$ "
                    "for every integer $x$."
                ),
                memo_steps=(
                    r"\dfrac{3^{x+2} - 3^{x}}{3^{x+1}} "
                    r"= \dfrac{3^{x}\left(3^{2} - 1\right)}{3^{x}\cdot 3}",
                    r"= \dfrac{9 - 1}{3}",
                    r"= \dfrac{8}{3}",
                ),
            ),
        ),
    ),
)

PAPERS: dict[str, PaperSpec] = {
    "2025_mj_p1_q1": _MJ2025_P1_Q1,
}


# ── CLI ───────────────────────────────────────────────────────────────────────


def main() -> None:
    ap = argparse.ArgumentParser(description="Render a variable NSC-style paper.")
    ap.add_argument("--paper", default="2025_mj_p1_q1", choices=list(PAPERS))
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--output", default="paper.html")
    ap.add_argument("--pdf", action="store_true", help="Also render a PDF")
    args = ap.parse_args()

    spec = PAPERS[args.paper]
    rendered = build_paper(spec, seed=args.seed)

    warnings = [w for rs in rendered for w in rs.warnings]
    if warnings:
        print(f"calibration warnings ({len(warnings)}):")
        for w in warnings:
            print(f"  ! {w}")

    html = render_paper_html(spec, rendered)
    html_path = Path(args.output)
    html_path.write_text(html, encoding="utf-8")
    print(
        f"Wrote {spec.source} ({len(rendered)} slots, {spec.total_marks} marks) "
        f"→ {args.output}"
    )

    if args.pdf:
        pdf_path = html_path.with_suffix(".pdf")
        html_to_pdf(html_path, pdf_path)
        print(f"Wrote PDF → {pdf_path}")


if __name__ == "__main__":
    main()
