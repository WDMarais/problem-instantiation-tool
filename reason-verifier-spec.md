# Reason-verifier spec — the Tier-3 unlock (`value_and_reason`)

**For:** the pit engine session. **From:** the strategy/design track (srs-tool curriculum-analysis).
**Status:** design handoff, not code. **Priority rationale:** `build-priority-map.md` Tier 3 — the
single highest-leverage *new verifier* on the board (vs. any single new generator): one build
converts ~15–19 P2 marks from "apparent wall" into gradeable.

**Sources (don't re-derive; read if you want the why):**
- `~/coding-projects/srs-tool/curriculum-analysis/siyavula-graph-probe-geometry.md` §1–3 — the
  three-layer structure and why the reason is a first-class gradeable object.
- `~/coding-projects/srs-tool/curriculum-analysis/build-priority-map.md` Tier 3 — yield + placement.
- `content/examples/parallelogram_angles.py` — **already generates reason-bearing angle-chases**;
  the reason currently lives in display-only worked steps. This archetype is the zero-risk pilot.

---

## 0. The one-paragraph version

DBE geometry marks an angle-chase step as **value + reason**: an angle size with no cited theorem
loses the mark (reason-fusion — probe §0). Today pit grades only the value (`symbolic_equality` on
the angle) and leaves the reason as ungraded prose. Tier-3 adds a **compound step kind
`value_and_reason`** that grades both jointly, where the reason is checked against a **bounded,
curated set of theorem names** (set-membership, *not* NLP). The comparison primitives already exist
in `verifier.py` — this is a compound-step + fused-marking + a curated reason-set data structure,
**not a new grading algorithm.** That is exactly why it is "smaller than a proof-grader" and
strictly bigger than `symbolic_equality`.

---

## 1. Why it's cheap: the primitives already exist

| Need | Already in `verifier.py` |
|---|---|
| grade the **value** (angle / ratio) | `symbolic_equality`, `numeric_equality` (with `rel_tol`) |
| grade the **reason** against a bounded set | `exact_equality` (`_normalize_string`: NFC + lower + whitespace) — this *is* bounded-string membership; `mcq` if the UI offers reasons as a picker |
| per-step marks + `MistakeType` | `_rate_submitted_step` → `(MistakeType, marks)` |
| resolve canonical from params | `_compute_canonicals` |

The genuinely new parts are only three, all small:
1. a **compound student value** carrying both `value` and `reason`;
2. **fused marking semantics** (one step, two facets, configurable partial credit);
3. the **reason-set** as a curated, closed data structure with aliases.

**If the UI presents the reason as a multiple-choice picker, the reason half reduces exactly to the
existing `mcq` kind** — then `value_and_reason` is literally `symbolic_equality ∘ mcq`. Consider
shipping the MCQ-reason variant first (lowest risk); free-text-reason (alias matching) is the
harder, deferrable half.

---

## 2. The `verifier_spec` shape (drop-in, matches existing step dicts)

```python
verifier_spec=[
    {
        "kind": "value_and_reason",
        "marks_possible": 2,          # DBE two-column S/R: 1 value + 1 reason
        "partial_credit": True,       # True → value & reason mark independently (S/R marking)
                                      # False → fused all-or-nothing (both required for the 1 mark)
        "value_key": "answer",        # canonical value param (as symbolic_equality's param_key)
        "value_kind": "symbolic_equality",   # reuse an existing comparator for the value facet
        "value_marks": 1,             # split of marks_possible when partial_credit (default: 1)
        "reason_key": "reason",       # param holding the canonical reason *id*
        "reason_set": "PARALLELOGRAM_REASONS",  # name of a bounded reason set (see §4)
        "reason_marks": 1,            # remaining marks_possible (default: marks_possible - value_marks)
        "normalize": ["whitespace"],  # applied to free-text reason before alias lookup
    }
]
```

Generator emits, alongside the existing `answer`, a `reason` param = the **canonical reason id**
(e.g. `"opp_angles_parallelogram"`), not free text. Example, migrating `parallelogram_opposite`:

```python
return {
    ...,
    "answer": sympy.Integer(given),
    "reason": "opp_angles_parallelogram",   # NEW — the canonical theorem id
}
```

## 3. Student attempt shape + marking

Compound student value on the `SubmittedStep` — a dict (keep it explicit; don't overload a tuple):

```python
SolutionAttempt(steps=[SubmittedStep({"value": 118, "reason": "opposite angles of a parallelogram"})])
```

Rating logic (new branch in `_rate_submitted_step`; canonical is a `{"value","reason"}` dict built
by a new branch in `_compute_canonicals`):

```
value_ok  = <compare student["value"] vs canonical["value"] using value_kind>
reason_ok = normalize(student["reason"]) in accepted_surfaces(canonical["reason"], reason_set)

if partial_credit and marks_possible > 1:
    marks = value_ok*value_marks + reason_ok*reason_marks
    mistake = correct        if (value_ok and reason_ok)
              semantic_error if (value_ok and not reason_ok)   # knows the number, not the why
              computation_error otherwise
else:  # fused, all-or-nothing
    if value_ok and reason_ok: return correct, marks_possible
    if value_ok:               return semantic_error, 0        # unjustified → no mark (DBE rider)
    return computation_error, 0
```

**The `MistakeType` mapping is a diagnostic deliverable, not bookkeeping** (probe §3a,
graph-as-diagnostic):

| value | reason | MistakeType | what the graph should do |
|---|---|---|---|
| ✓ | ✓ | `correct` | — |
| ✓ | ✗ | `semantic_error` | **comprehension-edge gap** — route to the theorem node; the arithmetic is fine, the *why* is missing. This is the signal the whole reason-verifier exists to capture. |
| ✗ | ✓ | `computation_error` | right theorem, slipped the arithmetic — a class-a drill, not a geometry gap |
| ✗ | ✗ | `computation_error` | — |

## 4. The reason-set: keep it a closed set, or it degrades into NLP

This is the one place the design can rot. **Rule: the reason-set is a closed dict of
`canonical_id → [accepted surface strings]`, matched by exact-after-normalization membership. No
fuzzy/edit-distance/embedding matching in v1.** A student phrasing not in the alias list is *wrong*,
and the fix is to **extend the alias list** — a bounded curation task, not a model. This is what
keeps it "smaller than a proof-grader."

```python
PARALLELOGRAM_REASONS = {
    "opp_angles_parallelogram":  ["opposite angles of a parallelogram", "opp angles of a parm",
                                  "opp ∠s of parm"],
    "cointerior_angles":         ["co-interior angles", "cointerior angles",
                                  "co-int angles; AD∥BC"],
    "alternate_angles":          ["alternate angles", "alt angles", "z angles"],
}
```

**The other members of the set are load-bearing distractors** (anti-gaming spine): the set for a
parallelogram configuration must hold ≥2–3 *plausible* reasons so a student who always writes the
same reason is penalised, and so surface features can't make one reason perennially correct. This is
why the bounded set is a *feature*, not just a grading convenience — it is the reason analogue of
the numeric-distractor discipline already in the repo.

**Bounded reason-sets to author (standard CAPS reason-phrases — common mathematical truth, safe to
enumerate):**
- `PARALLELOGRAM_REASONS` — above (pilot; archetype already exists).
- `CIRCLE_THEOREM_REASONS` — angle at centre = 2× at circumference; angle in semicircle = 90°;
  angles in same segment; opposite angles of cyclic quad supplementary; tangent-chord; tangent ⊥
  radius; equal chords. (Tier-3 target: circle-geometry angle-chase w/ reasons, ~8–11/P2.)
- `PROPORTION_REASONS` — line ∥ one side of triangle divides the other two proportionally (BPT);
  equiangular triangles are similar; corresponding sides of similar triangles are in proportion.
  (Tier-3 target: proportionality / BPT, ~6–7/P2.)

## 5. Scope cuts (v1 — flag if you disagree)

1. **Theorem-name only.** v1 grades the cited theorem, **not** the configuration citation ("…;
   AD∥BC"). The probe (§3b) says the minimum operational payload is the citable *statement*; the
   parallel-lines citation is a v2 extension (a second bounded facet, same machinery).
2. **No free-text NLP** — closed alias set only (§4). MCQ-reason variant is the safest first ship.
3. **Does not touch the wall.** This unlocks *single-step apply-with-reason* (class-b). Multi-step
   riders/proofs (class-c, non-canonical) stay scaffold-only — do **not** try to grow this into a
   chain-grader (build-map Tier 5).

## 6. Build path (lowest-risk first)

1. **Pilot on `parallelogram_angles.py`** — already shipped, reason already known and currently
   display-only. Add the `reason` param + switch the `verifier_spec` to `value_and_reason`. Zero new
   maths, proves the verifier end-to-end (engine + rating + `MistakeType` + worksheet render of the
   reason facet). This is the whole verifier de-risked against an existing archetype.
2. **Circle-theorem angle-chase archetype** on the proven verifier (~8–11/P2).
3. **BPT / proportionality archetype** (~6–7/P2).

## 7. Test expectations (mirror `test_parallelogram_labels.py` style)

- value ✓ reason ✓ → `is_correct`, full marks.
- value ✓ reason ✗ (a *distractor* from the same set) → `semantic_error`; marks = `value_marks`
  under partial credit, `0` under fused.
- value ✗ reason ✓ → `computation_error`; marks = `reason_marks` / `0`.
- reason phrased via an **alias** → graded ✓ (locks the alias list as the contract).
- reason **not in the set at all** → wrong (no silent pass; proves it's closed, not fuzzy).
- fused vs partial_credit produce the documented mark splits on the same attempt.
```
```

---

*Off the September MVP critical path (build-map: MVP stays the P1 symbolic slice). This is the
highest-leverage build for the P2 "resistant wall" when P2 comes into scope — surfaced now because
the weekend's Tier-1 progress (sequences + finance) means Tier-1 is no longer the only board.*
