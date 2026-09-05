# Deployment / Distribution / Website-MVP — session brief

Seed doc for a **separate interactive session** (open a new tmux pane, `cd` to this
repo, run `claude`, then `@docs/deployment-session-brief.md`). Re-enter it later with
`claude --resume` (pick it from the list) or `claude --continue` (most recent in this
dir). This thread is design/planning + light infra — it should NOT touch the
content-generation code the main session is actively editing (worksheets/, content/).

## Product state (as of 2026-09-05)

- **P1 is complete**: `2025_mj_p1`, 51 slots, **150 marks** (the full NSC P1 headline
  total). Every slot re-rolls per seed except one static proof (1.3 — being genericised
  in the main session).
- The product is a **variable NSC paper generator**: one PaperSpec manifest instantiates
  a real exam's question skeleton with fresh numeric values per seed. The engine grades
  the auto portion of each slot; the rest is hand-marked (auto/manual split per slot).
- Current output path:
  `.venv/bin/python -m worksheets.paper --seed N --output paper.html [--pdf]`
  → one HTML page, tabs **Q1–Q11 + Memo**. `--pdf` already exists
  (`html_to_pdf` in worksheets/paper.py) and renders a single paper to PDF.
- Static-KaTeX pre-render via Deno is resolved for the a4 path; the **worksheet path
  is still TODO** (server-side KaTeX so a PDF has real typeset math, not client JS).

## What this session is for

1. **Website MVP** — how a teacher or student gets a fresh paper.
   - Explicitly **NOT** payment/login for the MVP (prior decision). Focus is *showable*:
     the tool can only be pitched by being shown, so the deliverable is a ~90-sec
     before/after demo + a URL that hands someone a fresh, unique paper.
   - Open questions: hosting choice; one-fresh-paper-per-visit vs pick-a-seed vs
     shareable per-seed URL; teacher entry (bulk / answer memo) vs student entry
     (single paper, maybe no memo); how the math renders server-side for a clean page.

2. **PDF / printout concessions** — the concrete near-term ask.
   - A **"convert everything to PDF in one shot"** command: batch the whole paper
     (all questions + memo) into a single printable PDF — and likely a batch across N
     seeds (a stack of distinct papers + memos) for a teacher who wants a class set.
   - The current tabbed Q1–Q11+Memo HTML needs a print/PDF layout (page breaks per
     question, memo as a separate section/booklet, no tab chrome).
   - Decide: extend `--pdf` into a batch/combined mode vs a new `worksheets.export`
     command; whether memo is a separate PDF or a back-of-booklet section.

3. **Distribution / spread** — reach term-4 audience.
   - SA school **term 4 starts ~October**, so real usage is ~3–4 weeks out; distribution
     has lead time and is the current critical path (content is already showable).
   - Open questions: who is the first channel (a specific school/teacher?), what format
     they actually want (printed class sets? a link?), free vs gated.

## Constraints / prior decisions (from memory)

- Showable-tooling pitch: can't be pitched verbally, only shown; the before/after demo
  (deck + the instantiator that generated it) is itself a deliverable.
- MVP scope is delivery/packaging, NOT payment/login.
- Open browser files with `wslview <file>` (WSL).
- Corpus-provenance rule: we ship OUR numbers/wording, never the exam's verbatim.

## First moves for that session

- Decide the PDF story (batch/combined command + print layout) — most concrete, unblocks
  handing someone something tangible.
- Sketch the website MVP surface (one page: "generate a fresh paper" → HTML + PDF).
- Name the first distribution channel and what format it needs.
