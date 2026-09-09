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

The paper is built up one question at a time: the pipeline (manifest →
instantiate → NSC-numbered render + margin marks + self-checked memo, incl.
resistant passthroughs) runs over every render-free question before the plotter
builders unlock the graph-dependent ones.
"""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass, field
from pathlib import Path

from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from render.euclid_theorems import svg_for as _theorem_svg
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
    figure_svg: str = ""  # optional inline SVG (e.g. a theorem-proof diagram)


@dataclass(frozen=True)
class StaticPool:
    """A small pool of hand-authored variants for one resistant slot; build_paper
    picks one per seed. The content is still fixed and hand-marked (a proof has no
    auto-grader) — the pool only removes the "this part is canned" tell across the
    several papers we ship, by rotating which fixed variant appears. Not a
    generator: no numeric instantiation, nothing engine-graded."""

    variants: tuple[StaticContent, ...]

    def __post_init__(self) -> None:
        if not self.variants:
            raise ValueError("StaticPool needs at least one variant")

    def choose(self, rng: random.Random) -> StaticContent:
        return rng.choice(self.variants)


@dataclass(frozen=True)
class PaperSlot:
    """One numbered exam item. Exactly one of ``problem_id`` / ``static`` is set.

    ``marks`` is the paper's headline part-mark — the number the page prints. The
    generator's own ``verifier_spec`` total is the *canonical* marking scheme: the
    answer-value marks a verifier step actually covers. When a paper allots more
    than that (an NSC slot's method/setup lines with no verifier behind them — our
    generators grade answer-values only, so those fall outside verifier coverage
    and are marked by hand), the author declares the covered portion via
    ``auto_marks``; the remainder (``marks − auto_marks``) is manual marks, rendered
    honestly as such. A declared ``auto_marks`` must equal the generator's canonical
    total (it's a checkable claim about verifier coverage) and cannot exceed
    ``marks`` — build_paper enforces both. Leaving it ``None`` on a slot whose marks
    match the generator is the common, fully-covered case; leaving it ``None`` on a
    *divergent* slot is a loud, unacknowledged calibration gap (project house rule:
    never silently reconciled).
    """

    number: str  # NSC dotted number, e.g. "1.1.1", "1.2", "1.3"
    marks: int  # the paper's part-mark — authoritative for what the page prints
    topic: str  # short human label (facts only, not the exam's wording)
    problem_id: str | None = (
        None  # generated slot → key in worksheets.generate.PROBLEMS
    )
    static: StaticContent | StaticPool | None = None  # resistant passthrough (or pool)
    auto_marks: int | None = None  # engine-graded portion; None → = generator total

    def __post_init__(self) -> None:
        if (self.problem_id is None) == (self.static is None):
            raise ValueError(
                f"slot {self.number}: set exactly one of problem_id / static"
            )
        if self.auto_marks is not None:
            if self.static is not None:
                raise ValueError(
                    f"slot {self.number}: auto_marks is meaningless on a static slot"
                )
            if not 0 <= self.auto_marks <= self.marks:
                raise ValueError(
                    f"slot {self.number}: auto_marks {self.auto_marks} must be in "
                    f"0..{self.marks} (a slot can't auto-grade more than it is worth)"
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
    auto_marks: int | None = None  # resolved engine-graded marks (None for static)
    mark_warning: str | None = None  # loud when a divergence is left unacknowledged
    warnings: list[str] = field(default_factory=list)
    is_stem: bool = False  # compound shared stem: instruction + diagram, no marks/memo

    @property
    def manual_marks(self) -> int:
        """Paper marks with no verifier step behind them — marked by hand. These are
        typically NSC method/setup lines (e.g. 'squared both sides'); our generators
        grade answer-values only, so these fall outside verifier coverage."""
        if self.auto_marks is None:
            return 0
        return self.slot.marks - self.auto_marks


def _expand_compound(slot, card, gen_marks: int | None) -> list[RenderedSlot]:
    """Expand one compound (shared-stem) slot into a stem RenderedSlot (instruction +
    diagram, no marks) followed by one RenderedSlot per sub-part, all from the single
    instantiation ``card``. The honest mark split is enforced across the sub-parts:
    every sub-part's ``auto_marks`` sums to the generator's canonical verifier total
    (a checkable claim about what the engine grades), and the headline ``marks`` sum
    to the slot's declared total — the compound analogue of the per-slot check."""
    auto_sum = sum(sp.auto_marks for sp in card.subparts)
    marks_sum = sum(sp.marks for sp in card.subparts)
    if gen_marks is not None and auto_sum != gen_marks:
        raise ValueError(
            f"slot {slot.number}: sub-part auto_marks sum {auto_sum} ≠ generator's "
            f"canonical total {gen_marks} ({slot.problem_id}) — the sub-part split is "
            f"a claim about what the engine grades and must match it"
        )
    if marks_sum != slot.marks:
        raise ValueError(
            f"slot {slot.number}: sub-part marks sum {marks_sum} ≠ slot marks "
            f"{slot.marks} ({slot.problem_id}) — the headline total must reconcile"
        )
    stem = RenderedSlot(
        slot=PaperSlot(slot.number, 0, slot.topic, problem_id=slot.problem_id),
        instruction=card.instruction,
        display_math=card.display_math,
        memo_steps=[],
        graph_svg=card.graph_svg,
        generated=True,
        is_stem=True,
    )
    rendered = [stem]
    for sp in card.subparts:
        rendered.append(
            RenderedSlot(
                slot=PaperSlot(
                    f"{slot.number}.{sp.suffix}",
                    sp.marks,
                    slot.topic,
                    problem_id=slot.problem_id,
                    auto_marks=sp.auto_marks,
                ),
                instruction=sp.instruction,
                display_math=sp.display_math,
                memo_steps=list(sp.memo_steps),
                generated=True,
                auto_marks=sp.auto_marks,
            )
        )
    return rendered


def build_paper(spec: PaperSpec, *, seed: int | None = None) -> list[RenderedSlot]:
    """Instantiate every slot of *spec*. Generated slots are drawn from the engine
    (fresh per seed); static slots pass through.

    The paper's declared ``marks`` are what the page prints; the generator's own
    ``verifier_spec`` total is the canonical marking scheme — the answer-value marks
    a verifier step covers. A slot reconciles the two via ``auto_marks``:

    - ``auto_marks`` set → it must equal the generator total (a checkable claim
      about verifier coverage); the gap ``marks − auto_marks`` is manual marks (no
      verifier behind them; marked by hand). A wrong claim is a misconfiguration and
      raises (project house rule: loud, never silently reconciled).
    - ``auto_marks`` unset and the generator total already equals ``marks`` → the
      common fully-covered case.
    - ``auto_marks`` unset but the generator total diverges from ``marks`` → an
      *unacknowledged* calibration gap, surfaced as a loud warning for the author
      to resolve (declare ``auto_marks``, or remap the slot)."""
    engine = Engine(registry=InMemoryRegistry(REGISTRY))
    rng = random.Random(seed)
    out: list[RenderedSlot] = []
    for slot in spec.slots:
        if slot.problem_id is not None:
            entry = PROBLEMS[slot.problem_id]
            card = _generate_cards(engine, entry, rng, 1, 1)[0]
            gen_marks = _problem_marks(entry.problem)
            if card.subparts:  # compound (shared stem) → expand into stem + sub-slots
                out.extend(_expand_compound(slot, card, gen_marks))
                continue
            warn = None
            if slot.auto_marks is not None:
                if gen_marks is not None and slot.auto_marks != gen_marks:
                    raise ValueError(
                        f"slot {slot.number}: auto_marks {slot.auto_marks} ≠ "
                        f"generator's canonical total {gen_marks} "
                        f"({slot.problem_id}) — auto_marks is a claim about what the "
                        f"engine grades and must match it; fix the declaration or "
                        f"recalibrate the generator"
                    )
                resolved_auto = slot.auto_marks
            else:
                resolved_auto = gen_marks
                if gen_marks is not None and gen_marks != slot.marks:
                    warn = (
                        f"slot {slot.number}: paper marks {slot.marks} ≠ generator "
                        f"marks {gen_marks} ({slot.problem_id}) — declare auto_marks "
                        f"to acknowledge the method-mark gap, or remap the slot"
                    )
            out.append(
                RenderedSlot(
                    slot=slot,
                    instruction=card.instruction,
                    display_math=card.display_math,
                    memo_steps=list(card.worked_steps),
                    graph_svg=card.graph_svg,
                    generated=True,
                    auto_marks=resolved_auto,
                    mark_warning=warn,
                    warnings=[warn] if warn else [],
                )
            )
        else:
            s = slot.static
            assert s is not None
            if isinstance(s, StaticPool):  # rotate which fixed variant this seed gets
                s = s.choose(rng)
            out.append(
                RenderedSlot(
                    slot=slot,
                    instruction=s.instruction,
                    display_math=s.display_math,
                    memo_steps=list(s.memo_steps),
                    graph_svg=s.figure_svg or None,
                    generated=False,
                )
            )
    return out


# ── renderer ──────────────────────────────────────────────────────────────────

_PAPER_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: Georgia, 'Times New Roman', serif; color: #1a1a1a;
       background: #e8e8e8; }

/* screen: a readable centred column — not a fake A4 sheet */
.doc { max-width: 210mm; margin: 8mm auto 24mm; padding: 14mm 16mm 20mm;
       background: #fff; box-shadow: 0 1px 4px rgba(0,0,0,.15); }
.paper-header { text-align: center; border-bottom: 2px solid #1a1a1a;
                padding-bottom: 6px; margin-bottom: 4mm; }
.paper-title { font-size: 15pt; font-weight: bold; letter-spacing: .3px; }
.paper-sub { font-size: 9.5pt; color: #555; margin-top: 2px; }
.disclaimer { font-size: 8pt; font-style: italic; color: #666; text-align: center;
              border: 1px solid #ddd; background: #fafafa; padding: 4px 8px;
              margin-bottom: 6mm; }

/* notebook tabs (screen only); with JS off the tabs are plain jump links and
   every question stays visible — i.e. it degrades to continuous scroll */
.qnav { position: sticky; top: 0; z-index: 5; display: flex; flex-wrap: wrap;
        gap: 4px; padding: 6px 10px; background: #fff; border-bottom: 1px solid #ccc; }
.qnav a { font-family: 'Segoe UI', system-ui, sans-serif; font-size: 9.5pt;
          text-decoration: none; color: #333; padding: 3px 10px;
          border: 1px solid #ccc; border-radius: 4px; }
.qnav a.active { background: #1a1a1a; color: #fff; border-color: #1a1a1a; }
body.tabbed .qsection { display: none; }
body.tabbed .qsection.active { display: block; }

.qsection { margin-bottom: 8mm; }
.q-head { display: flex; justify-content: space-between; align-items: baseline;
          border-bottom: 1px solid #999; padding-bottom: 2px; margin-bottom: 4mm; }
.q-title { font-size: 12pt; font-weight: bold; letter-spacing: .5px; }
.q-marks { font-size: 10pt; font-weight: bold; }

/* slots: number/marks absolutely placed so the block is a clean fragmentation
   unit (grid/flex children are unreliable across page breaks in Chrome) */
.slot { position: relative; padding: 3mm 14mm 3mm 17mm; }
.slot + .slot { border-top: 1px solid #e3e3e3; }
.slot.depth-3 { margin-left: 7mm; }
.slot-num { position: absolute; left: 0; top: 3mm; font-weight: bold;
            font-size: 10.5pt; white-space: nowrap; }
.slot-marks { position: absolute; right: 0; top: 3mm; font-size: 10pt;
              white-space: nowrap; }
.slot-instruction { font-size: 10.5pt; line-height: 1.35; }
.slot-eq { margin: 1.5mm 0; }
.slot-graph { margin: 1.5mm 0; }
.work-space { border-bottom: 1px dotted #ccc; }

.memo h2 { font-size: 13pt; border-bottom: 2px solid #1a1a1a; padding-bottom: 3px;
           margin-bottom: 4mm; }
.memo-row { position: relative; padding: 1.5mm 34mm 1.5mm 17mm;
            border-bottom: 1px solid #eee; }
.memo-num { position: absolute; left: 0; top: 1.5mm; font-weight: bold;
            font-size: 10pt; }
.memo-steps { font-size: 10pt; line-height: 1.6; }
/* a step wider than its column (e.g. a long \\text{} that math won't wrap) scrolls
   inside its own box rather than bleeding right under the marks/badges gutter.
   overflow-y is pinned to visible-via-clip: setting only overflow-x:auto would let
   CSS coerce overflow-y to auto, and MathJax's few px of extra height would then
   raise a spurious vertical scrollbar on every line. */
.memo-steps > div { margin: .5mm 0; overflow-x: auto; overflow-y: hidden; }
.memo-meta { position: absolute; right: 0; top: 1.5mm; white-space: nowrap; }
.memo-marks { font-weight: bold; font-size: 9.5pt; }
.memo-badge { font-size: 7.5pt; text-transform: uppercase; letter-spacing: .5px;
              padding: 1px 4px; border-radius: 3px; margin-left: 2mm; }
.memo-badge.auto { background: #dcfce7; color: #166534; }
.memo-badge.manual { background: #e0e7ff; color: #3730a3; }
.memo-badge.static { background: #fef3c7; color: #92400e; }

/* print / PDF: native paged media owns the breaks — one question per page,
   slots kept whole. No height estimation, no clipping. */
@media print {
    body { background: #fff; }
    .qnav { display: none; }
    .doc { max-width: none; margin: 0; padding: 0; box-shadow: none; }
    body.tabbed .qsection { display: block; }
    .qsection { margin-bottom: 0; break-before: page; }
    .qsection:first-of-type { break-before: avoid; }
    .slot, .memo-row { break-inside: avoid; }
    @page { size: A4; margin: 18mm 16mm; }
}
"""

# Screen-only progressive enhancement: turn the question list into notebook tabs.
# With JS disabled (or under a CSP that blocks it) the body never gets `.tabbed`,
# so every .qsection stays visible and the page is a plain vertical scroll.
_TABS_JS = """
<script>
(function () {
  var nav = document.querySelector('.qnav');
  var secs = Array.prototype.slice.call(document.querySelectorAll('.qsection'));
  if (!nav || !secs.length) return;
  var links = Array.prototype.slice.call(nav.querySelectorAll('a'));
  document.body.classList.add('tabbed');
  function show(id) {
    if (!secs.some(function (s) { return s.id === id; })) id = secs[0].id;
    secs.forEach(function (s) { s.classList.toggle('active', s.id === id); });
    links.forEach(function (a) {
      a.classList.toggle('active', a.getAttribute('data-target') === id);
    });
    window.scrollTo(0, 0);
  }
  links.forEach(function (a) {
    a.addEventListener('click', function (e) {
      e.preventDefault();
      show(a.getAttribute('data-target'));
    });
  });
  show((location.hash || '').replace('#', '') || secs[0].id);
})();
</script>
"""


def _slot_html(rs: RenderedSlot) -> str:
    depth = rs.slot.number.count(".") + 1
    eq = (
        f'<div class="slot-eq">$${_tex_html(rs.display_math)}$$</div>'
        if rs.display_math
        else ""
    )
    graph = f'<div class="slot-graph">{rs.graph_svg}</div>' if rs.graph_svg else ""
    if rs.is_stem:
        # shared stem of a compound question: the narrative + f + diagram, shown once
        # above the sub-parts. No mark allocation and no answer space of its own.
        return (
            f'<div class="slot stem depth-{depth}">'
            f'<div class="slot-content">'
            f'<div class="slot-instruction">{rs.instruction}</div>'
            f"{eq}{graph}"
            f"</div></div>"
        )
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


def _memo_step_html(s: str) -> str:
    """One memo line. A bare-LaTeX step (the common case) is the whole line's math,
    wrapped in ``$…$``. A step that already carries ``$…$`` delimiters is mixed
    prose + inline math: the prose is left as HTML so it *wraps* (proof "Given:" /
    "Construction:" lines would otherwise be one non-wrapping ``\\text{}`` box that
    overflows the column), and KaTeX renders the ``$…$`` islands in place."""
    if "$" in s:
        return s
    return f"${_tex_html(s)}$"


def _memo_row_html(rs: RenderedSlot) -> str:
    steps = "".join(f"<div>{_memo_step_html(s)}</div>" for s in rs.memo_steps)
    if not rs.generated:
        badges = '<span class="memo-badge static">static</span>'
    elif rs.manual_marks > 0:
        # honest split: a verifier step backs the value marks; the rest have no
        # verifier behind them (NSC method/setup lines) and are marked by hand.
        badges = (
            f'<span class="memo-badge auto">{rs.auto_marks} auto</span>'
            f'<span class="memo-badge manual">{rs.manual_marks} manual</span>'
        )
    else:
        badges = '<span class="memo-badge auto">auto</span>'
    return (
        f'<div class="memo-row">'
        f'<span class="memo-num">{rs.slot.number}</span>'
        f'<div class="memo-steps">{steps}</div>'
        f'<span class="memo-meta">'
        f'<span class="memo-marks">[{rs.slot.marks}]</span>'
        f"{badges}"
        f"</span>"
        f"</div>"
    )


def _qhead_html(head: str, q_marks: int) -> str:
    return (
        f'<div class="q-head">'
        f'<span class="q-title">QUESTION {head}</span>'
        f'<span class="q-marks">[{q_marks}]</span>'
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

    masthead = (
        '<div class="paper-header">'
        f'<div class="paper-title">{spec.title}</div>'
        f'<div class="paper-sub">Variable instantiation of {spec.source} '
        f"· {spec.total_marks} marks</div>"
        "</div>"
        f'<p class="disclaimer">{spec.disclaimer}</p>'
    )

    # One continuous document: masthead, then a section per question, then the
    # memo. Native paged media (print) or the notebook tabs (screen) decide how
    # this flow is chunked — the renderer never estimates a single height.
    nav_links: list[str] = []
    sections: list[str] = []
    for head, slots in groups:
        q_marks = sum(rs.slot.marks for rs in slots)
        nav_links.append(f'<a href="#q{head}" data-target="q{head}">Q{head}</a>')
        body = "".join(_slot_html(rs) for rs in slots)
        sections.append(
            f'<section class="qsection" id="q{head}">'
            f"{_qhead_html(head, q_marks)}{body}</section>"
        )

    nav_links.append('<a href="#memo" data-target="memo">Memo</a>')
    memo_rows = "".join(_memo_row_html(rs) for rs in rendered if not rs.is_stem)
    sections.append(
        '<section class="qsection" id="memo">'
        '<div class="memo"><h2>Marking Memorandum</h2>'
        f"{memo_rows}</div></section>"
    )

    nav = f'<nav class="qnav">{"".join(nav_links)}</nav>'
    doc = f'<div class="doc">{masthead}{"".join(sections)}</div>'
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n<head>\n<meta charset="UTF-8">\n'
        f"<title>{spec.title}</title>\n"
        f"{inline_style()}\n"
        f"<style>{_PAPER_CSS}</style>\n"
        "</head>\n<body>\n"
        + prerender_body(nav + doc)
        + _TABS_JS
        + "</body>\n</html>\n"
    )


# ── 2025 May/June P1 (accumulating, render-free questions) ────────────────────

# The P1 paper is built up one question at a time; the renderer groups slots by
# their leading number, so each question becomes its own block. Mark allocations
# follow the paper skeleton (corpus-crosswalk.md). Where a generator's own marks
# differ, build_paper() emits a loud calibration warning — a real gap for a
# scoring-identical product, never silently reconciled.
#
# Q1 — render-free algebra (numbering, margin marks, memo, one resistant
# passthrough at 1.3). Q2 — Sequences & Series, fully addressable (class a/b),
# no plotter needed.
_MJ2025_P1 = PaperSpec(
    title="Mathematics P1 — Practice",
    source="2025 May/June P1",
    slots=(
        # Question 1 — equations & inequalities
        # auto_marks = the two roots a verifier step covers; the 3rd is the
        # factorising method line, marked by hand (no verifier behind it).
        PaperSlot(
            "1.1.1",
            3,
            "quadratic — factorise",
            problem_id="quadratic_factor",
            auto_marks=2,
        ),
        # auto_marks = the two roots (to 2 dp); the 3rd is the formula-substitution
        # method line, marked by hand. Non-factorisable discriminant forces the
        # formula — a different skill from 1.1.1's factorise (see quadratic_formula).
        PaperSlot(
            "1.1.2",
            3,
            "quadratic — formula",
            problem_id="quadratic_formula",
            auto_marks=2,
        ),
        # auto_marks = simplified power a^x = a^n (1) + exponent x = n (1); the 3rd
        # is the factoring line a^x(a^k+1), marked by hand. (The real 1.1.3 is a
        # common-base factoring solve, not the harder quadratic-in-u substitution —
        # that is exponential_equation, a 1.1.4-type slot; see audit.)
        PaperSlot(
            "1.1.3",
            3,
            "exponential — common-base solve",
            problem_id="exponential_common_base",
            auto_marks=2,
        ),
        PaperSlot(
            "1.1.4", 3, "quadratic inequality", problem_id="quadratic_inequality"
        ),
        # auto_marks = candidates (2) + valid (1); the 4th is the squaring-setup
        # method line, marked by hand (documented in surd_equation.py).
        PaperSlot(
            "1.1.5", 4, "surd equation", problem_id="surd_equation", auto_marks=3
        ),
        # auto_marks = x-values (2) + complete pairs (2); the 5th/6th are the
        # substitution-setup method lines, marked by hand (documented in
        # nonlinear_simultaneous.py).
        PaperSlot(
            "1.2",
            6,
            "nonlinear simultaneous",
            problem_id="nonlinear_simultaneous",
            auto_marks=4,
        ),
        # 1.3 was a STATIC proof (the same 8/3 identity every seed) — the one frozen
        # slot in the paper. Now generated: the source's "prove = 8/3" is posed as a
        # gradable "simplify to a constant" over a varying base and exponent offsets
        # (a proof's target value is given, so nothing is left to grade). auto_marks =
        # the simplified value (2); the factor-and-cancel set-up line is hand-marked.
        PaperSlot(
            "1.3",
            3,
            "exponent-algebra — simplify a same-base ratio to a constant",
            problem_id="exponent_simplify_constant",
            auto_marks=2,
        ),
        # Question 2 — sequences & series (arithmetic 2.1, geometric 2.2)
        PaperSlot(
            "2.1.1",
            2,
            "arithmetic — nth-term formula",
            problem_id="arith_seq_nth_term_formula",
        ),
        PaperSlot("2.1.2", 2, "arithmetic — find n", problem_id="arith_seq_find_n"),
        PaperSlot("2.1.3", 3, "arithmetic — series sum", problem_id="arith_series_sum"),
        PaperSlot(
            "2.2.1",
            2,
            "geometric — nth-term formula",
            problem_id="geo_seq_nth_term_formula",
        ),
        PaperSlot("2.2.2", 3, "geometric — find n", problem_id="geo_seq_find_n"),
        PaperSlot(
            "2.2.3", 3, "geometric — finite series", problem_id="geo_series_finite"
        ),
        PaperSlot(
            "2.2.4",
            3,
            "geometric — infinite series",
            problem_id="geo_series_infinite",
        ),
        # Question 3 — quadratic sequences. 3.1 derive Tₙ (generator recalibrated
        # to the NSC 3-mark allocation, fully covered). 3.2 the first-difference →
        # larger-term skill (new generator, 1 + 2 = 3). 3.3 the shift-to-negative
        # range — a half-open interval answer, now graded by the set_solution kind
        # (2 thresholds + interval), so it is live rather than a static passthrough.
        PaperSlot(
            "3.1",
            3,
            "quadratic sequence — general term",
            problem_id="quad_seq_nth_term_formula",
        ),
        PaperSlot(
            "3.2",
            3,
            "quadratic sequence — consecutive-term difference",
            problem_id="quad_seq_consecutive_diff",
        ),
        PaperSlot(
            "3.3",
            3,
            "quadratic sequence — shift-to-negative range",
            problem_id="quad_seq_shift_negative",
        ),
        # Question 4 — hyperbola. The tool's first COMPOUND slot: one f is
        # instantiated once and its six coupled sub-parts (4.1–4.6) are read off a
        # single shared stem + diagram, so 4.6 genuinely uses 4.5's A. The paper
        # layer expands this into a stem slot + six sub-slots; the 15 headline marks
        # split into 9 engine-graded (M, D, t, f≤0 via set_solution, A, AA′) + 6
        # hand-marked method lines.
        PaperSlot(
            "4",
            15,
            "hyperbola — read coupled properties off the equation",
            problem_id="hyperbola_properties",
        ),
        # Question 5 — parabola. A second COMPOUND slot (shared stem: one f, three
        # coupled sub-parts). 5.1 finds f from the turning point + a point; 5.2 the
        # no-real-roots k region; 5.3 reflects f and asks for a *sketch* of the cubic
        # g — a hand-drawn deliverable. The 9 headline marks split into 3 engine-
        # graded (a + expansion via 5.1, the k-set via 5.2) + 6 hand-marked (the
        # show-that setup, the discriminant line, and the whole 5.3 sketch).
        PaperSlot(
            "5",
            9,
            "parabola — determine the equation, then reflect and sketch",
            problem_id="parabola_properties",
        ),
        # Question 6 — exponential & inverse. A third COMPOUND slot, and the first
        # with TWO functions on one shared stem: an exponential f = p^x + q and a
        # line g = mx + c meeting at A, coupled through the g⁻¹ hook (6.3 reads B off
        # f). All four sub-parts are engine-gradable (no sketch): the 11 headline
        # marks split into 6 engine-graded (p, q, range via set_solution, g's slope +
        # equation, g⁻¹'s equation) + 5 hand-marked method lines.
        PaperSlot(
            "6",
            11,
            "exponential + line + inverse off one shared stem",
            problem_id="exponential_inverse",
        ),
        # Question 7 — finance. Three INDEPENDENT problems (different people /
        # accounts), so three ordinary slots, not a compound: 7.1 effective rate,
        # 7.2 present-value annuity (how many withdrawals — reuses the purpose-built
        # finance_pv_annuity_n), 7.3 lump sum + a deferred monthly annuity. Each is a
        # single numeric answer graded whole (money to the cent), the finance-family
        # convention: generator canonical total = the NSC part marks, no manual split.
        PaperSlot(
            "7.1",
            2,
            "effective annual rate from a nominal rate",
            problem_id="finance_effective_rate",
        ),
        PaperSlot(
            "7.2",
            5,
            "present-value annuity — number of withdrawals",
            problem_id="finance_pv_annuity_n",
        ),
        PaperSlot(
            "7.3",
            6,
            "lump sum + deferred monthly annuity — total at valuation date",
            problem_id="finance_lump_plus_annuity",
        ),
        # Question 8 — calculus: derivatives. Four INDEPENDENT sub-parts (different
        # functions, no shared stem), so four ordinary slots grouped under Q8 by
        # the leading number: 8.1 first principles (quadratic), 8.2.1 plain power
        # rule, 8.2.2 surd × squared-binomial (expand to powers first), 8.3 common
        # tangent to two parabolas (solve a, b). The three differentiations grade
        # their whole answer-value (fully engine-graded); 8.3 grades only the two
        # answers a, b (2 of its 6 marks) — the differentiation + system setup are
        # hand-marked method (auto_marks=2).
        PaperSlot(
            "8.1",
            5,
            "differentiate a quadratic from first principles",
            problem_id="derivative_first_principles",
        ),
        PaperSlot(
            "8.2.1",
            2,
            "differentiate a plain polynomial (power rule)",
            problem_id="derivative_polynomial",
        ),
        PaperSlot(
            "8.2.2",
            4,
            "differentiate a surd × squared-binomial product",
            problem_id="derivative_surd_product",
        ),
        PaperSlot(
            "8.3",
            6,
            "common tangent to two parabolas — solve a and b",
            problem_id="common_tangent_parabolas",
            auto_marks=2,
        ),
        # Question 9 — cubic functions. A COMPOUND (shared-stem) slot: one cubic
        # f = (x−p)(x−k)² with a repeated root drives five coupled sub-parts (find k,
        # the turning points, the concavity at a point, the sketch, the maximum gap
        # to h = −2f′). No stem diagram — 9.4 asks the student to draw it. The 18
        # headline marks split 6 engine-graded (k; x₂, y₂; concavity tag; d_max=2) +
        # 12 hand-marked (every method line, plus 9.4's sketch in full).
        PaperSlot(
            "9",
            18,
            "cubic with a repeated root — k, turning points, concavity, max gap",
            problem_id="cubic_shared_analysis",
        ),
        # Question 10 — probability. Two INDEPENDENT sub-parts (different contexts,
        # no shared stem) → two ordinary slots grouped under Q10 by the leading
        # number: 10.1 the mutually-exclusive addition rule (single answer, fully
        # engine-graded), 10.2 a fun-park game (win probability × profit target →
        # max payout per winner). 10.2 grades two checkpoints — P(win) and the final
        # payout (2 of its 6 marks) — the revenue/pool/expected-winner method lines
        # are hand-marked (auto_marks=2).
        PaperSlot(
            "10.1",
            2,
            "mutually exclusive events — find P(B) from the addition rule",
            problem_id="prob_mutually_exclusive",
        ),
        PaperSlot(
            "10.2",
            6,
            "fun-park game — max payout per winner (win probability × profit target)",
            problem_id="game_expected_payout",
            auto_marks=2,
        ),
        # Question 11 — counting & probability. A COMPOUND (shared-stem) slot: one
        # range of three-digit numbers drives both sub-parts (11.1 count those with
        # exactly one given digit; 11.2 the complement probability, which reuses the
        # 11.1 count). No diagram. The 7 headline marks split 2 engine-graded (the
        # count; the probability) + 5 hand-marked (the casework and the complement
        # setup).
        PaperSlot(
            "11",
            7,
            "three-digit numbers with exactly one given digit — count and complement",
            problem_id="digit_count_exactly_one",
        ),
    ),
)

# Question 6 (P2) — prove a trig identity. A resistant slot: a free-form deductive
# proof has no auto-grader (and none is feasible — the same wall as the Euclidean
# proof block), so it is hand-marked StaticContent. To avoid the identical proof
# recurring across the several papers we ship, it is a StaticPool of five standard
# Grade-12 identities (our own wording, standard textbook results — nothing copied
# from any exam), one drawn per seed. Each carries a full worked memo; the whole
# slot is hand-marked (the "static" badge says so).
_Q6_IDENTITY_PROOFS = StaticPool(
    (
        StaticContent(
            instruction="Prove the following identity:",
            display_math=r"\dfrac{1-\cos^2 x}{\sin x\,\cos x}=\tan x",
            memo_steps=(
                r"\text{LHS}=\dfrac{1-\cos^2 x}{\sin x\,\cos x}"
                r"=\dfrac{\sin^2 x}{\sin x\,\cos x}",
                r"=\dfrac{\sin x}{\cos x}=\tan x=\text{RHS}",
            ),
        ),
        StaticContent(
            instruction="Prove the following identity:",
            display_math=(
                r"\dfrac{\sin x}{1+\cos x}+\dfrac{1+\cos x}{\sin x}=\dfrac{2}{\sin x}"
            ),
            memo_steps=(
                r"\text{LHS}=\dfrac{\sin^2 x+(1+\cos x)^2}{\sin x\,(1+\cos x)}"
                r"=\dfrac{\sin^2 x+1+2\cos x+\cos^2 x}{\sin x\,(1+\cos x)}",
                r"=\dfrac{2+2\cos x}{\sin x\,(1+\cos x)}"
                r"=\dfrac{2(1+\cos x)}{\sin x\,(1+\cos x)}"
                r"=\dfrac{2}{\sin x}=\text{RHS}",
            ),
        ),
        StaticContent(
            instruction="Prove the following identity:",
            display_math=r"\dfrac{\cos x}{1-\sin x}=\dfrac{1+\sin x}{\cos x}",
            memo_steps=(
                r"\text{LHS}=\dfrac{\cos x}{1-\sin x}\cdot\dfrac{1+\sin x}{1+\sin x}"
                r"=\dfrac{\cos x\,(1+\sin x)}{1-\sin^2 x}",
                r"=\dfrac{\cos x\,(1+\sin x)}{\cos^2 x}=\dfrac{1+\sin x}{\cos x}"
                r"=\text{RHS}",
            ),
        ),
        StaticContent(
            instruction="Prove the following identity:",
            display_math=r"(\sin x+\cos x)^2=1+2\sin x\cos x",
            memo_steps=(
                r"\text{LHS}=\sin^2 x+2\sin x\cos x+\cos^2 x",
                r"=(\sin^2 x+\cos^2 x)+2\sin x\cos x=1+2\sin x\cos x=\text{RHS}",
            ),
        ),
        StaticContent(
            instruction="Prove the following identity:",
            display_math=r"\dfrac{1}{\cos^2 x}-\tan^2 x=1",
            memo_steps=(
                r"\text{LHS}=\dfrac{1}{\cos^2 x}-\dfrac{\sin^2 x}{\cos^2 x}"
                r"=\dfrac{1-\sin^2 x}{\cos^2 x}",
                r"=\dfrac{\cos^2 x}{\cos^2 x}=1=\text{RHS}",
            ),
        ),
    )
)


# The Euclidean-geometry proof blocks (P2 Q9.3 / Q10.3 / Q11.3). The real paper's
# Q9–Q10 are ~40 marks of circle-theorem and similarity PROOFS — the resistant wall
# (a free-form deductive proof has no auto-grader). Our live angle-chase archetypes
# (9.1/9.2, 10.1/10.2, 11.1/11.2) are the variable substitute; these hand-marked
# static proof pools carry the proof marks the substitute doesn't, so P2 reconciles
# to the NSC 150. Standard Grade-12 bookwork proofs — our own wording, standard
# results, nothing copied from any exam; one drawn per seed. Each geometry question
# draws from its own pool so no proof repeats within a paper.
_Q9_CIRCLE_PROOFS = StaticPool(
    (
        StaticContent(
            instruction=(
                "Prove the theorem which states that the angle subtended by an arc "
                "at the centre of a circle is twice the angle the arc subtends at the "
                "circumference."
            ),
            figure_svg=_theorem_svg("angle_at_centre"),
            memo_steps=(
                r"Given: $O$ the centre; $A\hat{O}B$ (centre) and $A\hat{C}B$ "
                r"(circumference) subtend arc $AB$.",
                r"Construction: join $CO$ and produce to $D$.",
                r"$OA=OC$ (radii), so $\hat{C}_1=\hat{A}_1$, and "
                r"$\hat{O}_1=\hat{C}_1+\hat{A}_1=2\hat{C}_1$ (exterior angle of "
                r"$\triangle OAC$).",
                r"Similarly $\hat{O}_2=2\hat{C}_2$. Adding: "
                r"$A\hat{O}B=\hat{O}_1+\hat{O}_2=2(\hat{C}_1+\hat{C}_2)=2\,A\hat{C}B$.",
            ),
        ),
        StaticContent(
            instruction=(
                "Prove the theorem which states that the opposite angles of a cyclic "
                "quadrilateral are supplementary."
            ),
            figure_svg=_theorem_svg("cyclic_quad_opposite"),
            memo_steps=(
                r"Given: cyclic quadrilateral $ABCD$ with centre $O$.",
                r"$\hat{O}_1=2\hat{A}$ (angle at centre $=2\times$ angle at "
                r"circumference, on arc $BCD$).",
                r"$\hat{O}_2=2\hat{C}$ (on arc $BAD$), and "
                r"$\hat{O}_1+\hat{O}_2=360^\circ$ (angles about $O$).",
                r"So $2\hat{A}+2\hat{C}=360^\circ$, giving "
                r"$\hat{A}+\hat{C}=180^\circ$.",
            ),
        ),
        StaticContent(
            instruction=(
                "Prove the theorem which states that the line drawn from the "
                "centre of a circle perpendicular to a chord bisects the chord."
            ),
            figure_svg=_theorem_svg("perp_from_centre_bisects_chord"),
            memo_steps=(
                r"Given: $O$ the centre and $OM\perp$ chord $AB$, with $M$ on "
                r"$AB$.",
                r"Construction: join $OA$ and $OB$.",
                r"In $\triangle OMA$ and $\triangle OMB$: $OA=OB$ (radii), "
                r"$OM$ is common, and $O\hat{M}A=O\hat{M}B=90^\circ$ (given).",
                r"$\triangle OMA\equiv\triangle OMB$ (RHS), so $AM=MB$ and "
                r"$OM$ bisects $AB$.",
            ),
        ),
        StaticContent(
            instruction=(
                "Prove the theorem which states that two tangents drawn to a "
                "circle from a point outside the circle are equal in length."
            ),
            figure_svg=_theorem_svg("two_tangents_equal"),
            memo_steps=(
                r"Given: tangents $PA$ and $PB$ from an external point $P$, "
                r"touching the circle (centre $O$) at $A$ and $B$.",
                r"Construction: join $OA$, $OB$ and $OP$.",
                r"$O\hat{A}P=O\hat{B}P=90^\circ$ (tangent $\perp$ radius), "
                r"$OA=OB$ (radii), and $OP$ is common.",
                r"$\triangle OAP\equiv\triangle OBP$ (RHS), so $PA=PB$.",
            ),
        ),
    )
)

_Q10_CIRCLE_PROOFS = StaticPool(
    (
        StaticContent(
            instruction=(
                "Prove the theorem which states that the angle between a tangent to a "
                "circle and a chord drawn from the point of contact equals the angle "
                "in the alternate segment."
            ),
            figure_svg=_theorem_svg("tangent_chord"),
            memo_steps=(
                r"Given: tangent $SAT$ at $A$, chord $AB$, and $C$ on the major arc.",
                r"Construction: draw diameter $AOD$ and join $BD$.",
                r"$D\hat{A}T=90^\circ$ (tangent $\perp$ radius) and "
                r"$A\hat{B}D=90^\circ$ (angle in semicircle).",
                r"$\hat{D}=A\hat{C}B$ (same segment, arc $AB$), so "
                r"$B\hat{A}T=90^\circ-D\hat{A}B=\hat{D}=A\hat{C}B$.",
            ),
        ),
        StaticContent(
            instruction=(
                "Prove that the exterior angle of a cyclic quadrilateral equals the "
                "interior opposite angle."
            ),
            figure_svg=_theorem_svg("cyclic_quad_exterior"),
            memo_steps=(
                r"Given: cyclic quadrilateral $ABCD$ with side $BC$ produced to $E$.",
                r"$B\hat{C}D+\hat{A}=180^\circ$ (opposite angles of a cyclic "
                r"quadrilateral).",
                r"$D\hat{C}E+B\hat{C}D=180^\circ$ (angles on a straight line).",
                r"Therefore $D\hat{C}E=\hat{A}$.",
            ),
        ),
        StaticContent(
            instruction=(
                "Prove the theorem which states that angles subtended by a "
                "chord of a circle, on the same side of the chord, are equal."
            ),
            figure_svg=_theorem_svg("angles_same_segment"),
            memo_steps=(
                r"Given: chord $AB$ subtends $A\hat{C}B$ and $A\hat{D}B$ at "
                r"$C$ and $D$ in the same segment; $O$ the centre.",
                r"$A\hat{O}B=2\,A\hat{C}B$ (angle at centre $=2\times$ angle "
                r"at circumference, on arc $AB$).",
                r"$A\hat{O}B=2\,A\hat{D}B$ (same, on arc $AB$).",
                r"So $2\,A\hat{C}B=2\,A\hat{D}B$, giving "
                r"$A\hat{C}B=A\hat{D}B$.",
            ),
        ),
        StaticContent(
            instruction=(
                "Prove the theorem which states that the angle subtended by a "
                "diameter at the circumference of a circle is a right angle."
            ),
            figure_svg=_theorem_svg("angle_in_semicircle"),
            memo_steps=(
                r"Given: $AB$ a diameter of the circle (centre $O$), and $C$ "
                r"a point on the circle.",
                r"Construction: join $OC$.",
                r"$OA=OC=OB$ (radii), so $\triangle OAC$ and $\triangle OBC$ "
                r"are isosceles: $\hat{A}=\hat{C}_1$ and $\hat{B}=\hat{C}_2$.",
                r"$A\hat{C}B=\hat{C}_1+\hat{C}_2=\hat{A}+\hat{B}$, and "
                r"$\hat{A}+\hat{B}+A\hat{C}B=180^\circ$ in $\triangle ABC$, "
                r"so $2\,A\hat{C}B=180^\circ$ and $A\hat{C}B=90^\circ$.",
            ),
        ),
    )
)

_Q11_SIMILARITY_PROOFS = StaticPool(
    (
        StaticContent(
            instruction=(
                "Prove the theorem which states that if two triangles are "
                "equiangular, their corresponding sides are in proportion."
            ),
            figure_svg=_theorem_svg("equiangular_triangles"),
            memo_steps=(
                r"Given: $\triangle ABC$ and $\triangle DEF$ with $\hat{A}=\hat{D}$, "
                r"$\hat{B}=\hat{E}$, $\hat{C}=\hat{F}$.",
                r"Construction: mark $P$ on $AB$ and $Q$ on $AC$ with $AP=DE$, "
                r"$AQ=DF$; join $PQ$.",
                r"$\triangle APQ\equiv\triangle DEF$ (SAS), so $A\hat{P}Q=\hat{E}"
                r"=\hat{B}$, giving $PQ\parallel BC$.",
                r"Then $\dfrac{AB}{AP}=\dfrac{AC}{AQ}$ (line parallel to a side), so "
                r"$\dfrac{AB}{DE}=\dfrac{AC}{DF}=\dfrac{BC}{EF}$.",
            ),
        ),
        StaticContent(
            instruction=(
                "Prove the theorem which states that a line drawn parallel to one "
                "side of a triangle divides the other two sides in proportion."
            ),
            figure_svg=_theorem_svg("basic_proportionality"),
            memo_steps=(
                r"Given: $\triangle ABC$ with $DE\parallel BC$, $D$ on $AB$ and $E$ "
                r"on $AC$.",
                r"Construction: join $BE$ and $CD$.",
                r"$\dfrac{\text{area }\triangle ADE}{\text{area }\triangle BDE}"
                r"=\dfrac{AD}{DB}$ and $\dfrac{\text{area }\triangle ADE}"
                r"{\text{area }\triangle CED}=\dfrac{AE}{EC}$ (equal heights).",
                r"$\triangle BDE$ and $\triangle CED$ have equal areas (same base "
                r"$DE$, $DE\parallel BC$), so $\dfrac{AD}{DB}=\dfrac{AE}{EC}$.",
            ),
        ),
    )
)


# Paper 2 — statistics, analytical geometry, trigonometry, Euclidean geometry.
# Being wired render-free-first: the statistics/trig questions land now; the
# analytical-geometry (cartesian renderer) and Euclidean-geometry (figure IS the
# problem — a true render gate) questions follow as those surfaces are built.
_MJ2025_P2 = PaperSpec(
    title="Mathematics P2 — Practice",
    source="2025 May/June P2",
    slots=(
        # Question 1 — statistics. A COMPOUND (shared-stem) slot: one dataset of 15
        # monthly premiums drives all four sub-parts (mean, standard deviation, the
        # count within one σ, and a weighted-increase inverse for k). No diagram. The
        # 9 headline marks split 4 engine-graded (x̄; σ; the count; k) + 5 hand-marked.
        PaperSlot(
            "1",
            9,
            "premium data — mean, standard deviation, within-one-σ count, weighted k%",
            problem_id="premium_increase_analysis",
        ),
        # Question 2 — statistics: regression. A COMPOUND (shared-stem) slot: one
        # bivariate dataset (items vs packing time) drives all five sub-parts (the
        # scatter plot, the least-squares line, the correlation r, a prediction, and
        # the "why the intercept is meaningless" reason). No diagram. The 10 headline
        # marks split 4 engine-graded (gradient; intercept; r; prediction) + 6
        # hand-marked (the scatter draw and the intercept explanation).
        PaperSlot(
            "2",
            10,
            "regression — scatter, least-squares line, correlation, predict, reason",
            problem_id="regression_line",
        ),
        # Question 3 — analytical geometry: ΔSRT. A COMPOUND (shared-stem) slot: one
        # instance (R on the x-axis, T on the y-axis, S(m;s) left of R, line RT) drives
        # six chained sub-parts (R, length RT in surd form, m from a given RT²:SR²
        # ratio, the equation of VR ⊥ ST, the foot V, and the reflected-quadrilateral
        # area RVTR′). No diagram — every part follows from the line equation and the
        # given facts. The 21 headline marks split 12 engine-graded (each final value)
        # + 9 hand-marked (the intercept/distance/ratio/perp/shoelace derivations).
        PaperSlot(
            "3",
            21,
            "triangle SRT — intercepts, length, ratio for m, ⊥ foot, reflected area",
            problem_id="analytic_geometry_srt",
        ),
        # Question 4 — analytical geometry: circle & tangent. A COMPOUND (shared-stem)
        # slot: one circle centred at M(a;0) with a lattice point E on it, the tangent
        # at E and a point C on that tangent drive seven sub-parts (the tangent-radius
        # angle, the tangent's equation, DM, the value p, the parallelogram point S,
        # an inside/outside test after the radius grows, and the isosceles angle ÊTM).
        # A schematic diagram (letters only). The 20 headline marks split 11 engine-
        # graded (each final value, incl. the inside/outside tag and the numeric angle)
        # + 9 hand-marked (the derivations and the "show that p" step).
        PaperSlot(
            "4",
            20,
            "circle & tangent — angle, tangent eqn, DM, p, parallelogram, region, ÊTM",
            problem_id="circle_tangent_chain",
        ),
        # Question 5.1 — trigonometry: special ratios. A COMPOUND (shared-stem) slot:
        # one given ratio (cos θ) plus the quadrant drives three sub-parts (sin²θ, a
        # reduction-formula ratio, a compound-angle value). No diagram. The 9 headline
        # marks split 3 engine-graded (the final value of each) + 6 hand-marked (the
        # Pythagoras/quadrant/expansion method).
        PaperSlot(
            "5.1",
            9,
            "special ratios — sin²θ, a reduction ratio, a compound-angle value",
            problem_id="trig_given_ratio",
        ),
        # Question 5.2 — trig simplify (identity). A flat slot: a quotient of
        # reduction/co-function terms in an unknown x collapses to a single ratio
        # (±sin x, ±cos x, ±tan x, ±1). The final ratio is engine-graded (3 of the 6
        # headline marks) via symbolic_equality; the reduction lines are hand-marked
        # method. Faithful by construction — the printed expression is simplified to
        # get the graded answer.
        PaperSlot(
            "5.2",
            6,
            "trig simplify — reduction/co-function expression to a single ratio",
            problem_id="trig_simplify_reduce",
            auto_marks=3,
        ),
        # Question 5.3 — trig simplify (special-angle product). A flat slot: a numeric
        # product of trig ratios at reducible special angles (120°…330°) evaluates to
        # an exact constant in ℚ[√2, √3]. The value is engine-graded (2 of the 4
        # headline marks); rewriting each ratio at its reference angle is hand-marked.
        PaperSlot(
            "5.3",
            4,
            "trig simplify — special-angle product to an exact value",
            problem_id="trig_simplify_product",
            auto_marks=2,
        ),
        # Question 6.1 — prove a trig identity (hand-marked static pool; see above).
        PaperSlot(
            "6.1",
            6,
            "prove a trig identity (hand-marked — outside the variable set)",
            static=_Q6_IDENTITY_PROOFS,
        ),
        # Question 6.2 — hence/otherwise solve a trig equation. A live slot: a general
        # trig equation solved for the reference angle. Standalone (not literally
        # chained off 6.1's identity) — the engine grades the answer value (1 of the
        # 7 marks) via symbolic_equality; the reference-angle / quadrant / general-
        # solution method lines are hand-marked.
        PaperSlot(
            "6.2",
            7,
            "hence solve a trig equation (reference angle)",
            problem_id="trig_equation",
            auto_marks=1,
        ),
        # Question 7 — trigonometric graphs. A COMPOUND (shared-stem) slot: two curves
        # f = a·cos x + q and g = sin(bx) drive six read-off-the-equation sub-parts
        # (range, period, increasing interval, two sign-inequality sets, a right shift).
        # No diagram — the properties follow from the equations. All 10 marks are
        # engine-graded (4 interval sets via set_solution, the period, the shifted eqn).
        PaperSlot(
            "7",
            10,
            "trig graphs — range, period, increasing, sign intervals, a right shift",
            problem_id="trig_graph_analysis",
        ),
        # Question 8 — 3-D trigonometry. A COMPOUND (shared-stem) slot: a vertical
        # tower FT over a horizontal triangle AFB drives three sub-parts — AF by the
        # sine rule, the "show that TF = AF·tan θ" relation, and the height TF. First
        # consumer of the 3-D wireframe renderer (render/scene3d.py, cabinet-oblique).
        # The 8 headline marks split 6 engine-graded (AF, TF) + 2 hand-marked (8.2,
        # a "show that" whose relation is given, so nothing for the engine to grade).
        PaperSlot(
            "8",
            8,
            "3-D trig — AF by sine rule, show TF = AF·tan θ, the tower height TF",
            problem_id="trig_3d_tower",
        ),
        # Question 9 — Euclidean geometry: circle angle-chase. A COMPOUND (shared-stem)
        # slot: O is the centre, A/B/C/D lie on the circle, and the given inscribed
        # angle AĈB drives two two-column sub-parts — the same-segment angle x = AD̂B
        # and the central angle y = AÔB. First Euclidean circle-theorem consumer of the
        # figure renderer (render/geometry.py Circle primitive); the figure IS the
        # problem. All 4 headline marks are engine-graded via value_and_reason (1 value
        # + 1 reason per part). The formal proof block (the literal 2025 Q9–Q11) stays
        # out of scope — no proof-structure verifier — so this is the angle-chase
        # archetype that fans across years, not the one-off proof.
        PaperSlot(
            "9",
            4,
            "circle geometry — same-segment angle x = AD̂B, central angle y = AÔB",
            problem_id="circle_geometry_angle_chase",
        ),
        # Question 9.3 — a circle-theorem proof (hand-marked static pool; see above).
        # Carries the proof marks the live angle-chase (9.1/9.2) doesn't.
        PaperSlot(
            "9.3",
            10,
            "prove a circle theorem (hand-marked — outside the variable set)",
            static=_Q9_CIRCLE_PROOFS,
        ),
        # Question 10 — Euclidean geometry: tangent-chord angle-chase. A COMPOUND
        # (shared-stem) slot and the second circle-theorem consumer of the figure
        # renderer, the first to draw a tangent. A tangent touches at A; the given
        # tangent-chord angle drives two two-column sub-parts — the alternate-segment
        # inscribed angle x = AĈB (tan-chord angle) and the central angle y = AÔB
        # (∠ centre = 2 ∠ circ.). The figure is faithful: the drawn tan-chord angle,
        # AĈB and AÔB all equal their values. All 4 headline marks are engine-graded
        # via value_and_reason (1 value + 1 reason per part).
        PaperSlot(
            "10",
            4,
            "circle geometry — tangent-chord angle x = AĈB, central angle y = AÔB",
            problem_id="tangent_chord_angle_chase",
        ),
        # Question 10.3 — a circle-theorem proof (hand-marked static pool; see above).
        PaperSlot(
            "10.3",
            8,
            "prove a circle theorem (hand-marked — outside the variable set)",
            static=_Q10_CIRCLE_PROOFS,
        ),
        # Question 11 — Euclidean geometry: cyclic-quadrilateral angle-chase. A
        # COMPOUND (shared-stem) slot and the third circle-theorem consumer of the
        # figure renderer. A/B/C/D lie on a circle (a cyclic quad) with side BC
        # produced to E; the given interior angle at A drives two sub-parts using two
        # DISTINCT cyclic-quad theorems — the opposite interior angle x = BĈD
        # (opp ∠s of cyclic quad = 180°) and the exterior angle y = DĈE
        # (ext ∠ of cyclic quad = interior opposite). The figure is faithful: the
        # drawn ∠DAB, BĈD and DĈE all equal their values. All 4 headline marks are
        # engine-graded via value_and_reason (1 value + 1 reason per part).
        PaperSlot(
            "11",
            4,
            "circle geometry — cyclic quad: opposite angle x = BĈD, exterior y = DĈE",
            problem_id="cyclic_quad_opposite_angles",
        ),
        # Question 11.3 — a similarity / proportion proof (hand-marked static pool;
        # see above). The similarity (BPT) strand of the real paper's proof block.
        PaperSlot(
            "11.3",
            10,
            "prove a similarity theorem (hand-marked — outside the variable set)",
            static=_Q11_SIMILARITY_PROOFS,
        ),
    ),
)

PAPERS: dict[str, PaperSpec] = {
    "2025_mj_p1": _MJ2025_P1,
    "2025_mj_p2": _MJ2025_P2,
}


# ── CLI ───────────────────────────────────────────────────────────────────────


def main() -> None:
    ap = argparse.ArgumentParser(description="Render a variable NSC-style paper.")
    ap.add_argument("--paper", default="2025_mj_p1", choices=list(PAPERS))
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
