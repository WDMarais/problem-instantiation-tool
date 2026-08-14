# Gig brief (STUB) — human acceptance QA on generated worksheets/papers

> **Status: STUB — activates as generation coverage grows.** Right now there are
> only a handful of built generators (~10% corpus coverage; see
> [../corpus-crosswalk.md](../corpus-crosswalk.md)), so there isn't yet a rich set
> of generated papers to QA. A small calibration pass over the existing worksheet
> HTML is possible today; the real volume opens up once more archetype families
> land ([../family-build-specs.md](../family-build-specs.md)).

**What this is:** paid, math-*light* acceptance checking of the generated output —
does it *look* like a real exam question, does it render correctly, is anything
visibly broken. **You are not checking whether the maths is correct** (see the fence
below). No programming; the value is a careful, dogged eye.

---

## The split — what you check vs what a script / Wynand checks

Three layers of validation; this brief is only the third:

| Layer | Who | Examples |
|---|---|---|
| **Structural** | a **script** (the gate) | mark totals sum to 140–160; no crash when a paper is generated/filled; schema valid |
| **Math-semantic** | **Wynand** | is the memo actually correct; are the answers right |
| **Perceptual / presentational** | **you (this brief)** | does it look like a real question; does it render right; is anything visually broken or ambiguous |

> **PREREQUISITE (TODO for Wynand before this activates):** the structural layer must
> exist as an automated gate script (generate N papers → assert mark totals in range,
> assert no exceptions, assert schema valid). Don't pay a human to eyeball mark-sums —
> that's a checksum a script does perfectly and for free. This brief assumes that gate
> already runs, so a human only ever sees output that already passed it.

---

## The fence (read this twice)

**You are NOT judging whether the maths is right.** If you're unsure whether an
answer or a step is mathematically correct, that is *not your call* — leave it. Only
flag things that look **structurally or visually off**. When in doubt, flag it as a
question, don't try to decide it.

---

## Workflow

1. Open a generated worksheet/paper alongside a **real past paper as the gold
   reference** (`nsc_papers/transcriptions/maths/*.md` — Wynand will point you at the
   right one to compare against).
2. Go through it side by side and look for anything off (checklist below).
3. Log each issue in the bug log with a screenshot and a one-line "this looks wrong
   because …".

## What to look for (perceptual / structural only)

- **Shape mismatch** vs the real paper: wildly different number of questions, weird
  mark distribution, a question that's laid out unlike anything in a real paper.
- **Rendering problems:** broken maths formatting, overlapping text, missing symbols,
  raw code/markup showing through, a diagram that didn't load.
- **Surface implausibility:** a question phrased in a way no real exam would, obvious
  nonsense numbers, duplicated or empty questions.
- **Interaction breakage:** an answer field that won't accept input, a button that
  does nothing, a page error while filling the paper in.

## Definition of done (per pass)

- A time-boxed pass completed over the assigned build.
- A bug log with each issue: screenshot + one-line description + which paper/question.
- Nothing math-correctness-related decided (only flagged as a question, if at all).

---

## Pay

- **Rate:** time-boxed hourly, **R100/hr** (QA output is exploratory — we pay for a
  thorough pass, *not* per bug, which would just reward noise).
- **Shape:** scoped sessions, e.g. "a 2-hour pass over this build." Time-boxed so it
  can't sprawl.
