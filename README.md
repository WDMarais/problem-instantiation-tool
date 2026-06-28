# problem-instantiation-tool

A generic engine that sits between **content definitions** and downstream
**consumers** (spaced-repetition, PDF worksheets, practice mode, Manim, MCP/agent
tooling). It instantiates a problem from a spec — fresh, seeded, or reconstructed
from stored params — and rates submitted answers. It is a **pure data layer**: no
rendering, no input parsing, no presentation concerns live in the engine.

Primary consumer is `nsc_papers` (South African NSC / CAPS maths); `cq` (Chinese
vocabulary cards) is a second consumer kept in view as a cross-domain check.

## Layout

| Path | What it is |
|---|---|
| `problem_instantiation_tool/` | The engine (pure data). `schemas.py` (`Problem`, `ProblemInstance`, attempts), `engine.py` (`instantiate` / `rate`), `verifier.py` (verifier kinds: mcq, exact/numeric/symbolic/set equality, self-graded), `registry.py`, `normalizers/`, `exceptions.py`. |
| `content/` | Content definitions. `examples/` — per-topic `Problem`s and acquisition-sheet entry points; `generators/` — acquisition-sheet builders producing `SheetData`; `sheet.py` — the sheet dataclasses; `renderers/a4.py` — A4 HTML renderer. |
| `render/` | Figures → SVG (presentation, kept out of the engine). `graph.py` (trig curves), `geometry.py` (`GeometryFigure` for Euclidean figures), demo/acquisition-sheet scripts. See `render/DESIGN.md`. |
| `worksheets/generate.py` | Assembles instantiated problems into an HTML worksheet. |
| `tests/` | The behavioural test harness (red tests derived from `spec.md`). |
| `main.py` | Smoke test exercising the engine against real content. |

## Quickstart

Uses [uv](https://docs.astral.sh/uv/).

```bash
uv sync                                   # create .venv, install deps
uv run pytest                             # run the test suite
uv run python main.py                     # engine smoke test
uv run python worksheets/generate.py 10   # -> worksheet.html
```

Render previews (output HTML is git-ignored):

```bash
uv run python render/geometry_demo.py                    # figure variety
uv run python render/acquisition_triangle_angle_sum.py   # acquisition sheet
uv run python render/acquisition_parallel_line_angles.py # acquisition sheet
```

## Development

Lint and format with [ruff](https://docs.astral.sh/ruff/) (rules `E`/`F`/`I`,
line length 88):

```bash
uv run ruff check .          # lint
uv run ruff format .         # format
```

A pre-commit hook (`.githooks/pre-commit`) runs both on staged Python files and
blocks the commit on any violation. Activate it once per clone:

```bash
git config core.hooksPath .githooks
```

Bypass a single commit with `git commit --no-verify`.

## Design docs

- `spec.md` — behavioural spec; the source of truth for *intent*.
- `ARCHITECTURE.md` — design decisions, derived from the spec and tests.
- `render/DESIGN.md` — the rendering layer (Cartesian vs. Euclidean split,
  display-only rule, acquisition-vs-drill figures).
