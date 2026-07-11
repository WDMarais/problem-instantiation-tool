# Case-interview: the September MVP slice

Invoke the **case-interviewer** skill. This is **not** a ground-up engine spec — the
engine already exists and is implemented. We are scoping one **product slice** on
top of it: an individual-problems practice product a private tutor can put in front
of matric tutees, shippable by **September 2026**.

## What already exists (the fixed substrate — do NOT re-interview it)

- **Engine** (`problem_instantiation_tool/`): pure data layer. `instantiate(spec)` /
  `rate(attempt)`. No rendering, no input parsing in the engine.
- **Verifier** (`verifier.py`): `VerifierChain` with **general multi-step CA**
  (Consistent-Accuracy / carried-error) two-pass evaluation — steps chain via
  `depends_on` + `symbolic_expr`; `MistakeType` = correct / ca_correct /
  semantic_error / computation_error; `ValidationMode` STRICT/LENIENT;
  `ProvidedStep` breaks the CA chain for gap-fill. Verifier kinds: symbolic /
  numeric / exact / set equality, mcq, self_graded. Recently hardened to **raise
  `CanonicalResolutionError` rather than guess** a canonical answer.
- **Content**: ~12 algebra generators (linear-equation family deep; quadratics
  factorise/roots/zero-product; arithmetic sequences; functions eval/inverse).
  Plus 6 geometry angle-chase generators (these are **Paper 2**, out of scope).
  Many `content/examples/` entries (finance, statistics, probability, analytic
  geometry, trig, exponents) are **stubs, not generators**.
- **Delivery**: `worksheets/generate.py` (HTML worksheet); `exam.py` (shuffle +
  count — a worksheet, not a real paper). SRS (`srs-tool`) is the *intended primary
  consumer*. Figures are **display-only** (answers baked by the generator, never
  read off the picture).

Read before interviewing: `spec.md` (historical context), `ARCHITECTURE.md`,
`problem_instantiation_tool/verifier.py`, `worksheets/generate.py`,
`~/.claude/projects/-home-sitrosi-coding-projects/memory/project_side_hustle_strategy.md`.

## The MVP to scope

**Individual Paper-1 *algebra* practice problems with trustworthy per-problem
memos, delivered SRS/worksheet style (e.g. ~50 problems across 5 days), for private
tutees, by September.** No full-paper assembly.

## Interview these, not the engine contract

1. **"Trustworthy memo" as a *checkable* property.** This is the crux and the whole
   value proposition. What must be true of a memo before a tutee sees it? How is
   each property *tested* (round-trip acceptance, wrong-answer rejection, working
   legibility, instruction unambiguity)? What are the memo failure modes and where
   is each caught? Enumerate them.
2. **P1-algebra coverage checklist.** Which sub-strands ship in September vs defer:
   equations/inequalities, number patterns & sequences, functions & graphs,
   exponents/surds, and the finance / calculus / probability P1 strands. In or out,
   and why. A generator that's trivially reachable from an existing pattern may be
   cheap in; one that isn't is deferred.
3. **Delivery artifact & session format.** What does the tutee actually receive —
   printed HTML? an SRS queue? What's the "50 over 5 days" object, and how is it
   assembled from individual problems without paper-assembly logic?
4. **The September acceptance bar.** Concretely: how many strands × how many
   problems each, memos verified how, "done-ish" defined as what.

## Explicit out-of-scope — fence these off, do not let them creep in

- **Paper assembly** (question hierarchy, per-subquestion marks, CAPS cognitive-
  level spread, memo-to-paper layout). Strictly later.
- **Paper 2** entirely: Euclidean geometry / circle theorems, trig, analytic
  geometry, statistics. The existing angle-chase generators do not serve this MVP.
- **The leaf-solver / operation-validity upgrade** ("detect that step 3 multiplies
  by 0"). This crosses the spec's explicit "not an ITS" line. The author-declared
  CA chain is sufficient for September. Named later candidate only.

## Deliverable

A scope doc (`mvp-scope.md`) with: the trustworthy-memo property set + how each is
tested, the in/out coverage checklist, the delivery-artifact definition, and a
prioritized build list from now to September with an explicit acceptance bar.
