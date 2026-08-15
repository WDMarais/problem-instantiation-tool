# INCOMING — backlog inbox

Loose backlog items that don't yet have a home in a family spec or a build.
Newest at top. Move an item into the relevant spec / crosswalk when it graduates
from "noted" to "planned".

---

## Reason grading: the UI is a projection of the closed set; one engine seam is not

**Date:** 2026-08-15
**Context:** `value_and_reason` verifier shipped (engine `8457c4e`, parallelogram
pilot `1a79bfc`). Question raised: should reason answers be a **dropdown select**
(so students can't fail on a spelling mistake), and should we be able to
selectively review/override spelling misses?

**The framing (keep this — it's the reusable insight):** the reason-set is a
closed set of canonical ids, each with a list of accepted surface phrasings. Every
plausible UI is just a *different projection of that same set*, and none of them
need an engine change:

- **Dropdown / MCQ** — UI renders one option per canonical id and submits the id
  itself. Spelling becomes structurally impossible; grading is unchanged
  (membership in the closed set). Cost: priming (we show the options).
- **Free-text + alias match** (what's built) — student types, we normalize +
  membership-check. No priming; spelling misses outside the alias list lose the
  reason mark.
- The same set therefore supports an **SRS progression**: dropdown early
  (recognition, accept the priming) → free-text later (recall, no priming), same
  canonical ids underneath, no re-authoring. This is the desired hardening path.

**So the dropdown is genuinely UI-for-later** — defer it, we lose nothing, the set
already supports it.

**The one seam that is NOT UI (the actual backlog item):** "selectively review /
override spelling mistakes" needs a signal the engine doesn't currently expose.
Today two very different failures both collapse to `MistakeType.semantic_error`:

1. student cited a **distractor theorem** (a *different* canonical id's surface) —
   a *confident* wrong-reason; this is the comprehension-edge signal we want.
2. student wrote something in **no alias list at all** — could be a spelling miss
   of the *right* theorem, or genuinely unknown.

The data to separate these is already in hand at grading time (we hold the whole
reason-set), so a miss can be checked against the *other* canonical ids' aliases:
matches a distractor → confident wrong-theorem; matches nothing → "unrecognized",
the review-queue candidate. That distinction is what makes human override
*triageable*, and it's cheap (one extra lookup) — but it has to live in the engine
as a **third signal** (an `unrecognized_reason` flag, or a distinct MistakeType),
not folded into `semantic_error`.

**Recommendation / trigger:** don't build speculatively — there's no consumer yet
and the dropdown path never needs it. Build the unrecognized-vs-wrong distinction
the **first time we stand up a review / override queue** (or a free-text grader
where forgiving spelling matters). ~20-minute change; the trigger is what's
missing, not the design.

**Related:** `reason-verifier-spec.md`, memory `project-reason-verifier-backlog`,
memory `project-quadratic-inequality-region-signal` (set-answer / subset-reason
kinds still open).
