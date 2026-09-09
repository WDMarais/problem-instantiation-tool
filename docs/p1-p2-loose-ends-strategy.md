# P1 & P2 loose-ends strategy (2026-09-09)

How we close out the two 2025 M/J variable papers. Grounded in the *current*
manifests (`worksheets/paper.py`) and `corpus-crosswalk.md`, not memory.

## Where the two papers actually stand

Introspected both `PaperSpec`s: **every slot present is live (engine-generated) —
there are no present-but-unfilled or static-passthrough slots.** So "loose ends"
means **missing slots** (gaps in the numbering), not half-built ones.

### P1 — structurally complete
Renders contiguously Q1…Q11 (31 slots, ~103 marks), all live. The real paper's
RESISTANT items were each either **folded into a compound generated slot** or
**substituted with a calculate-version**:
- 1.3 exponent-algebra *proof* (c) → `exponent_simplify_constant` (simplify-to-constant)
- 3.1 quad-seq *"show that"* (c) → `quad_seq_nth_term_formula` (calculate)
- 5.1 parabola *"show that"* + 5.3 *sketch from g′* (c) → one compound `parabola_properties`
- 9.1 cubic *"show that"* (c) → inside compound `cubic_shared_analysis`

**P1 has no build work.** Its only loose end is a **fidelity audit**: confirm each
substitute is an honest, non-trivial replacement (not a give-away), and that the
render-dependent sketch parts (Q5 reflect/sketch, Q9 sketch) read correctly. This
is a review pass, possibly a no-op — NOT new archetypes.

### P2 — three genuine gaps (all trig, the middle third)
Renders `… 5.1.3 → 7 …` — a **visible hole**: no 5.2, no 5.3, no Q6. Crosswalk
(`corpus-crosswalk.md:303`) says what belongs there:

| slot | topic | marks | class | buildable? |
|---|---|---|---|---|
| **5.2–5.3** | trig **simplify / product-trick** (reduction + co-function to a single ratio / constant) | ~10 | **b** | **yes** — needs one new `trig_simplify` archetype |
| **6.1–6.2.1** | **prove identity ×2** | 6 | **c** RESISTANT | no — proof wall (no proof verifier) |
| **6.2.2–6.2.3** | *hence* simplify / solve | 7 | **b** | **yes** — `trig_equation` / `trig_graph_solve` exist |

Everything else in P2 is already a live compound slot (Q1 stats, Q2 regression,
Q3 analytic-geom, Q4 circle-tangent, Q5.1 ratios, Q7 graphs, Q8 3-D, Q9/10/11 the
circle-theorem archetypes we just shipped).

## The one recurring decision: the proof wall

Q6.1 (identity proofs) is the same RESISTANT wall as the Euclidean proof block —
free-form deductive proof, no auto-grader, none feasible. Three ways to treat a
resistant stem, in preference order:
1. **Substitute a buildable archetype** at that slot (what we did for geometry
   Q9–11). Keeps the paper fully live + variable. **Preferred.**
2. **Hence-solve-only**: drop the proof, keep just the buildable 6.2.2–6.2.3 tail
   as the Q6 slot. Simple, honest, loses the "prove" flavour.
3. **StaticContent passthrough** (hand-authored proof + memo, auto_marks=0). Fills
   the number but carries **no variability** — barely our product. Last resort.

## Recommended sequence

Do the buildable trig, decide Q6 pragmatically, leave P1 to an audit:

1. **`trig_simplify` archetype → wire P2 Q5.2 + Q5.3.** One new generator covering
   reduction-formula simplification and the product-to-single-ratio/constant trick
   (e.g. `sin(180°−x)·cos(90°+x)·… → −sin²x` style). Grade with `symbolic_equality`
   (expression answer) — no new verifier kind needed. Compound shared-stem or two
   flat slots. Biggest single win: closes 10 marks and the most glaring hole.
2. **Q6 = hence-solve slot (option 2), or substitute (option 1).** Recommend
   **option 2** first pass: wire `trig_equation` as Q6 (general-solution / interval
   solve), 7 marks, fully live. Revisit as a compound with a static identity stem
   only if the paper reads thin without the "prove" step. This removes the last
   visible gap so P2 renders contiguously 1→11.
3. **P1 fidelity audit.** Eyeball the four substitute slots + the two sketch slots
   across a few seeds; fix only if a substitute is a give-away or a sketch misreads.
   Expected outcome: no change, or one small generator tweak.

## Definition of done

- P2 renders **contiguously** (no 5.1.3→7 jump); every slot live, or explicitly
  static-with-memo if we accept option 3 anywhere.
- `build_paper` for both papers: **no calibration warnings**; marks reconcile.
- New generators each get a test file (variety + grading teeth + faithfulness where
  a figure/answer relation exists), mirroring the circle-theorem archetype tests.
- Full suite green; ruff clean.
- Per-question flow unchanged: **render → user eyeball → wire → commit**, one
  question at a time. Nothing wired or committed before visual sign-off.

## Explicitly out of scope (unchanged)

Identity/Euclidean **proofs** (no proof verifier — the resistant floor); the formal
2025 Q9–Q11 proof block; renderer HLR/occlusion + interactive drag-rotate.
