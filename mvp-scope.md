# MVP Scope — September 2026 slice

**Anchor:** individual Paper-1 *algebra* practice problems with trustworthy per-problem
memos, delivered SRS/worksheet style (~50 problems / 5 days), for private matric tutees,
by September 2026. The engine (`instantiate`/`rate`, verifier kinds, CA chain) is fixed
substrate and is not re-scoped here.

**Fenced OUT (do not let creep in):** paper assembly; Paper 2 entirely (Euclidean
geometry, trig, analytic geometry, stats); the leaf-solver / operation-validity upgrade.

---

## 1. Trustworthy memo — the property set + how each is tested

### 1a. The memo artifact

A memo is a finely-grained **up-to-5-step** worked sequence. Granularity is deliberate:

```
x + 5 = 6   →   [ write the equation , add -5 to both sides , evaluate (5-5) and (6-5) ]
                = 3 steps
```

Prior worksheets earlier in the DAG may be treated as **worked substeps** — shown for
context, not scored on this sheet.

### 1b. Two marking regimes (a real design output)

| Mode | Context | Full marks require | Basis |
|---|---|---|---|
| **discrete-issue** | tutee practice (default) | correct **shape AND value** on the ~1–2 essential steps, OR the **presumptive shape given the student's own earlier values** | CA chain (carry steps b–f on an incorrect a via SymPy); a step-1 slip is not 0/6 |
| **exam-marker** | exam simulation | steps **correspond strongly to the NSC memo** | tighter; NSC-memo alignment |

- Only the ~1–2 **essential** steps score; the rest are uncounted scaffolding.
- discrete-issue ≈ `ValidationMode.LENIENT` + CA carry-on. exam-marker ≈ stricter
  correspondence (relationship to `ValidationMode.STRICT` TBD in interview).

### 1c. Memo failure modes → checkable properties

**Key structural insight:** construction may run forward, backward, or a mix — and the
direction is immaterial, because the hard part is the **same range-limiting problem**
either way. Pick the answer → you must constrain inputs so nice inputs produce it. Pick
the inputs → you must constrain the draw so a nice answer comes out. The arithmetic is
internally consistent regardless of direction; **it is not the risk**. The risk is the
*joint constraint* that both the problem and its answer land in the intended "nice" band
(integers, in-scope, solvable). Value-wrong memos essentially don't occur; **scope-wrong
memos are the failure mode**.

| # | Failure mode | Nature | Caught where (today) |
|---|---|---|---|
| F1 | **Out-of-scope / unsolvable draw** — mathematically valid but pedagogically wrong instance: non-integer params, quadratic with imaginary roots (range not constrained), difficulty above intended band. This is the range-limiting constraint failing at one end. | generator parameter-domain constraint | *only human eyeball* — the real gap |
| F2 | **Aesthetic / render / alignment** — value right, LaTeX garbled or ugly (`\quadx` class) | rendering | *only human eyeball* |
| — | ~~Value / arithmetic wrong~~ | precluded: construction is internally consistent | n/a |
| — | ~~Step non-sequitur / leaf-skipping~~ | trusted: author-declared step chain | out of scope (not an ITS) |

**Adjacent (marking tolerance, not memo generation):** notational forms the author finds
sloppy but NSC would mark right — e.g. `(x²−5x+6)=0 → (x−2)(x−3)` dropping the `= 0`.
This is about what the *verifier accepts from the student* (discrete-issue vs exam-marker),
not about the memo being mis-generated. Tracked under §1b.

### 1d. How F1 (scope) is tested — the in-scope predicate

Every generator declares a **per-type in-scope predicate**. One predicate, two consumers:

- **Per-draw guard** — the generator asserts the predicate on every instance and raises
  loudly on violation (consistent with "exceptions over quiet errors"). Makes it
  impossible to *ship* a bad draw.
- **Test-time sweep** — pytest instantiates the generator across the param space and
  asserts the predicate holds for every instance. A guard that fires in production is
  itself a failure; the sweep proves it never fires under normal operation.

**Coverage:** most P1-algebra generators have **small finite integer param grids** (roots
in `[−9, 9]` = 361 pairs), so the sweep is **exhaustive over the declared grid**, not
sampled. Fall back to bounded-random sampling only where a param is continuous or the grid
is combinatorially large.

**The predicate must be non-tautological.** A guard that re-derives what the generator
constructed proves nothing: a root-picking quadratic generator makes `b²−4ac` a perfect
square *by construction*, so asserting it is vacuous. The predicate earns its keep only
when expressed on the **presented problem** (the coefficients/structure the tutee sees)
and checked **independently of construction**. Non-tautological checks for a root-picking
quadratic: roots distinct (unless deduped), `|coeffs| ≤ bound`, no degenerate `root = 0`
if excluded, roots within the intended magnitude band.

F2 (render) remains human-eyeball for September unless promoted in §4.

### 1e. Instruction ambiguity / multi-valued answers (Area-1, Q4)

Evidence: survey of NSC P1 memos 2023–2025 (`nsc_papers/transcriptions/maths/`). **Finding:
single-canonical-value answers are the *minority* in P1 algebra.** 7 of 8 hard answer
shapes occur *commonly*; only trig general-solutions (`+180°n`) are absent (they are P2).

So instruction-ambiguity is **not** something you designed away by luck — it is intrinsic
to the domain. The MVP's defence is **shape selection** (§2): only ship problem types
whose answer shape the closed verifier set marks trustworthily, and author narrow prompts
("state all roots", "correct to 2 decimal places") that pin the accepted form.

---

## 2. P1-algebra coverage checklist (in / out for September)

**Reframe forced by the NSC survey:** scope by **answer shape the engine can trustworthily
mark**, not by curriculum sub-strand. A sub-strand is IN only where its dominant answer
shape falls inside the closed verifier set. Shapes the engine handles well pull a strand
in; shapes it can't pull it out (or restrict it to worked-example / self-graded).

### 2a. Answer shape × verifier competence

| Answer shape | Freq in P1 algebra | Verifier support today | Verdict |
|---|---|---|---|
| Single value / two-root **set** | common | `set_equality`, `symbolic_equality` | **IN** |
| **Expression-valued** (Tₙ, f′, inverse, tangent line) | dominant Q2–Q10 | `symbolic_equality` (SymPy) — the engine's strength | **IN** |
| Multiple equivalent **forms** (factored≡expanded) | common | SymPy `simplify` handles algebraic equivalence | **IN** |
| **Rounded numeric** (finance, 2-dp irrational roots) | common | `numeric_equality` + `tolerance` (implemented) | **IN**, needs tolerance authored per problem |
| **Interval / inequality** answer (`x<−1 or x>3`) | **near-ubiquitous** | **NONE** — `IntervalCheck` was deferred to v2 | **GAP → decision** |
| Multiple whole **methods**, each mark-scored | common | one authored path only (not an ITS) | **OUT** as multi-path; OK if we score only the *answer value* (discrete-issue mode) |
| **"Show that" / proof** (target given) | common (4–5/paper) | `self_graded` only | **worked_example / self_graded**, not auto-scored |
| **Reject-root with reason mark** (surds/exp) | common | `self_graded` / structural | **PARTIAL** — memo shows the reject; scoring the *reason* is self_graded |
| Restriction / excluded value (`x ≠ 3`) attached to answer | common | — | **DEFER** (answer-plus-condition composite) |

**Escape hatch that makes this tractable:** discrete-issue mode scores only the ~1–2
essential steps (§1b). Choose those to be **value/expression** steps and the multi-method,
reason-mark, and excluded-value complications fall away — they live in the shown scaffolding
(memo), not in what's auto-scored. The MVP scores the shape it can and *presents* the rest.

### 2b. Sub-strand checklist (driven by 2a)

| Sub-strand | Built today | Dominant answer shape | Sept verdict |
|---|---|---|---|
| Equations: linear | deep | single value | **IN** |
| Equations: quadratic (factorise/roots) | factorise/roots/zero-product | root **set**, expression | **IN** |
| **Inequalities** (quadratic) | — | **interval** | **blocked on the interval decision (§2a)** |
| Number patterns: **arithmetic** | yes | expression (Tₙ), single value | **IN** |
| Number patterns: geometric / series | — | expression | **stretch** — near-clone of arithmetic |
| Functions: eval / inverse | yes | value, expression | **IN** |
| Functions: **graph reading** (domain/range/intercepts) | — | value + interval | **DEFER** — needs renderer + interval support |
| Exponents & surds | stub | value, **reject-root** | **partial IN** — pure solve IN; reject-reason to memo only |
| Finance / growth | stub | **rounded numeric** | **candidate IN** — rides `numeric_equality`+tolerance; formula-heavy authoring |
| Calculus (P1) | — | expression (derivative) | **OUT** — new strand, no substrate (though f′ rides SymPy) |
| Probability (P1) | stub | value / proof | **OUT** — not algebra-shaped |

### 2c. Open decisions for the user

- **D1 — Interval verifier.** Inequalities + domain/range are near-ubiquitous but have no
  verifier. Options: (i) build a small `IntervalCheck` (single high-value verifier kind,
  scoped to unions of intervals over ℝ) → unlocks inequalities *and* graph-reading later;
  (ii) defer all interval-answer problems to post-September. Pick one.
- **D2 — Anchor strand.** Which single sub-strand, shipped cold, makes you comfortable
  putting this in front of a tutee? Anchors the acceptance bar on depth over breadth.
- **D3 — Finance in or out.** It's the cleanest new strand (tolerance-numeric answers,
  no interval/proof), but it's stub-only and formula-heavy. Cheap-IN or defer?

## 3. Delivery artifact & session format

**User priority (2026-07-11):** *coverage/breadth* over single-strand depth; Probability,
Exponents+Surds, Finance judged comparatively easy generation-ins. Explicit fallback: "if
coverage needs a fully general solver, simplify assumptions and pivot to a good SRS glossary
deck instead" — horizon **~4 weeks** (≈ 2026-08-08), tighter than the Sept go/no-go.

**Key distinction that governs everything:** *topic coverage ≠ auto-marking coverage.* A
general solver is only needed to auto-grade every shape. As **shown memo** (worked answer
key the tutee self-checks), the hard shapes (intervals, reject-reasons, multi-method,
proofs) are free — `generate.py` already ships this. The three delivery spines:

| Spine | What tutee gets | Trust gate | Solver needed? | Build state |
|---|---|---|---|---|
| **A. Worksheet + worked memo** (self-check) | printed problems + worked answer key | **F1 (scope) only** — no marking | **no** | ~80% built (`generate.py`) |
| **B. Interactive SRS auto-marking** | attempt → machine rating per step | F1 **+** answer-shape marking (survey complexity bites) | partial (per shape) | engine ready; verifier gaps at interval/proof shapes |
| **C. Glossary/vocabulary SRS deck** | term ⇄ definition drill | term-pair correctness | none (sidesteps generation) | design exists (see memory); not built |

*(spine choice pending — see Q6)*

### 3b. Coverage snapshot — worksheet spine (A), P1 + P2

Inventory (2026-07-11) of `content/` against NSC P1+P2. **Critical correction: there are no
true stubs.** Every `content/examples` file is a real, verifier-backed `Problem`. The
"stub" strands are **engine-ready but not worksheet-wired** — they lack only a `template_*`
in `generate.py`. **Coverage is a wiring problem, not a solver problem** — so the
general-solver fear that would trigger the glossary pivot does *not* apply to spine A.

| State | What's there |
|---|---|
| **Worksheet-wired now** (21 problems) | Quadratic factorise/zero-product (P1); trig graphs + R-form (P2); △/∥m angle-chase (P2) |
| **Engine-ready, one wiring weekend away** | Linear equations/inequalities/simultaneous, arithmetic sequences, exponents & surds, finance (3), probability-Venn (numeric), trig ratios/equations/special-angles, analytic geometry (text answers), stats one-var (numeric) |
| **Medium (new generator, rides existing infra)** | Series (Σ/Sₙ), geometric sequences (clone of arithmetic), trig-identity proofs, algebraic derivative (power-rule/first-principles) |
| **Expensive (new `render/` machinery)** | Function-graph *sketching* (needs general Cartesian plotter — today: sin/cos only); circle theorems (needs circle primitive — today: straight segments only); similarity figures; statistics *drawing* (histogram/ogive/box-plot) |
| **Genuinely absent (zero generator)** | Differential calculus, function-graph sketching, series, circle theorems, similarity |

Render machinery: `render/graph.py` = sin/cos sinusoids only; `render/geometry.py` = straight
segments/angles/pose, **no circle primitive**. These two gaps gate the expensive tier.

### 3c. Delivery logistics & the scaffolded sheet shape

**Distribution channel (undecided, both feasible — not a build blocker):**
- (i) **Generate + email** the HTML/PDF sheet per tutee, or
- (ii) **website access** in principle (hosted; tutee logs in).
A September call, downstream of the sheets; either works with the same generated artifact.

**Sheet internal structure — the real pedagogy (a scaffolded acquisition ladder, not a flat
problem set).** A single day's sheet targets *one concept to mastery* via:
- **~10 full worked examples** — every step explicitly listed (`detail="full"`),
- **~10 compressed worked examples** — same steps, not spelled out (`detail="short"`) — the
  compression serves fast catchers,
- **~32 graded practice problems** — mechanically identical, difficulty rising by *feature
  addition*: `+1` → `+var` → `+(two args)`, so by end of sheet the tutee owns e.g.
  `x − a·f(y) = 0 → x = a·f(y)`.

This is the **acquisition-sheet pipeline** (`content/renderers/a4.py`, Sections A worked /
B collapsed / C practice; `generate.py --long N`) — **already built**. But it is only the
*acquisition* mode — see §3d; whether it is the right whole-product shape is **open**.

### 3d. Acquisition vs retention — open pedagogical axis (UNRESOLVED)

The scaffolded ladder (blocked practice: one shape, ~50 variations) is mechanically the
easiest thing to ship, and good for *first contact*. It is **not obviously the right
whole-product shape** — retention likely needs **interleaving + spacing** ("guitar-drill
revision"), e.g. *"2 new sheets/week + 3 interleaved sheets with all past problems up for
grabs."* Block-vs-interleave, and each side already has a mechanism:

| Mode | Purpose | Mechanism (all present) | September cost |
|---|---|---|---|
| **Blocked acquisition ladder** | first contact with a shape | acquisition pipeline (`a4.py`, `--long`) | built |
| **Interleaved revision sheet** | mix across introduced shapes | `exam.py` mixed shuffle → printed sheet | built; a **composition policy** |
| **Spaced scheduling** ("which shapes, when") | retention over time | `srs-tool` (per-student SRS state) | rides deferred **spine B** |

**The cost hinge — does interleaving need per-student memory?** The phrasing "all past
problems up for grabs" implies **no**: a revision sheet that is a *uniform sample over
everything introduced to date* is just a composition policy over the existing shuffle, needs
no per-student SRS state, and stays spine A (printed self-check). "2 new + 3 interleaved /
week" is then cheap for September — 2 acquisition ladders + 3 growing-pool mixed sheets.
*True* spaced repetition (forgetting curves, per-student intervals) is the part that needs
SRS state and defers with spine B. See memory: glossary layer, DAG diagnostic vision.

**Answer-key timing:** the worked examples *are* the key, deliberately **front-loaded** as
scaffolding — "peeking" is by design in Sections A/B. Only the Section-C practice tail is
where check-after-attempt matters; the worked block above it already models every step.

## 4. September acceptance bar + prioritized build list

**Spine assumption:** worksheet + worked memo (A). Marking is *tutee self-check against the
shown memo*, so the answer-shape complexity (§2a) does not bite — nothing is auto-graded.
The trust gate reduces to **F1 (scope) + F2 (render)**. The CA verifier/chain work is not
wasted: it powers the round-trip trust check (smoke test) today and is the substrate for an
interactive spine-B fast-follow later.

**The honest cost of "cheap wiring":** each newly-wired generator multiplies the F1 surface.
"Trustworthy wiring" per generator = (a) declare its in-scope predicate + green exhaustive/
sampled sweep (§1d); (b) smoke-test round-trip — canonical accepted, wrong answer rejected;
(c) one human eyeball of a generated sheet (F2). Budget this per generator, not just the
`template_*` boilerplate.

### 4a. Prioritized build list (3 weekends)

**Weekend 1 — wire the built, highest ROI (no new render code).** Wire existing
`content/examples` Problems into `template_*` + memo: linear equations/inequalities/
simultaneous, arithmetic sequences (+ geometric clone), exponents & surds, finance (3),
probability-Venn (numeric), trig ratios/equations/special-angles, analytic geometry (text),
stats one-var (numeric). Apply the per-generator trust gate to each.
→ **Lifts P1 to near-complete except calculus & graph-sketching; fills P2 trig-algebra +
analytic + stats-numeric.**

**Weekend 2 — medium (rides existing infra).** Series (Σ/Sₙ) generator; **algebraic
calculus — derivatives from first principles + power rule, text-only memo (DECIDED IN);
tangent-line graph deferred**; trig-identity proofs (memo already presents step chains);
an axes+points plotter reused for analytic geometry; optional Venn SVG.

**Weekend 3 — expensive (DECIDED: Cartesian function plotter).** Build a general Cartesian
plotter (axes, intercepts, asymptotes, parabola/hyperbola/exponential/line families) in
`render/graph.py`. → unlocks **all of P1 functions & graphs**. Circle theorems (P2) are
*not* taken this window — deferred.

### 4b. The "50 over 5 days" delivery object (Area 3)

No paper-assembly logic needed. The "50 / 5 days" object is **5 concept-ladders** (one
scaffolded acquisition sheet per day, ~50 graded items each — see §3c), *not* a flat 50-item
shuffle. Each day is produced by the already-built acquisition-sheet pipeline
(`content/renderers/a4.py` Sections A/B/C; `generate.py --long N`). Assembly = pick 5
concepts + set the per-section counts; strictly downstream of individual problems. (`exam.py`
`EXAM_MIX` remains available for a mixed-revision variant, but the daily object is a ladder.)

### 4c. September acceptance bar ("done-ish")

- **Coverage:** all Weekend-1 strands wired = **P1 worksheet-complete except calculus &
  graph-sketching**, plus P2 trig + angle-chase geometry + analytic + stats-numeric.
- **Per generator, non-negotiable:** in-scope predicate declared + sweep green (F1);
  round-trip smoke test green; one human render eyeball (F2). A generator without all three
  does not ship.
- **Quantity:** ~15–20 wired problem *types*, each an unlimited instance source → a 50-
  problem / 5-day mix is a trivial selection over them.
- **Go/no-go (early Sept, from strategy memory):** if the F1 sweeps and round-trips are
  green across the wired set, the memos are trustworthy → chargeable. If not solid,
  soft-launch free to tutees. Free-to-tutees is an acceptable success state.

### 4d. Decisions (resolved 2026-07-11)

- **D-A. Weekend-3 pick → Cartesian function plotter.** Unlocks all P1 functions & graphs;
  higher exam frequency and closer to the P1 anchor than circle theorems. Circle theorems
  (P2) deferred.
- **D-B. Calculus → IN as text-only.** Algebraic derivatives (first principles + power rule)
  as a Weekend-2 generator with a text memo. Tangent-line *graph* deferred.
- **D-C. Interactive marking (spine B) → DEFERRED, post-September fast-follow.** The CA
  verifier stays a substrate (round-trip trust check + future spine-B base), not a shipped
  September surface. Answer-shape marking complexity (§2a) therefore does not gate September.

### 4e. Post-September backlog (explicitly deferred, not dropped)

Circle-theorem geometry (circle primitive); Euclidean similarity figures; statistics drawing
(histogram/ogive/box-plot); tangent-line graphs; **interactive auto-marking (spine B)** incl.
an `IntervalCheck` verifier for inequality/domain-range answers; paper assembly; the
leaf-solver / operation-validity upgrade.

---

## 5. Recommendation — build sequencing (the load-bearing choice)

The stack is fixed substrate (Python 3.11 + Pydantic v2 + SymPy + MathJSON), so the real
recommendation is *order of work*, and it follows directly from the interview:

1. **Build the F1 trust harness FIRST, before any Weekend-1 wiring.** The interview
   established that the memo's *value* is trustworthy by construction (§1c) and the only
   mathematical failure mode is the out-of-scope draw (F1). A shared **in-scope-predicate +
   exhaustive-sweep** harness (§1d) is therefore the actual product spine — it is what makes
   "trustworthy memo" a *checked* property rather than a hope. Wiring 15 generators *without*
   it just multiplies untested surface. This harness is the highest-leverage first move and
   is a day, not a weekend.

2. **Sequence Weekend-1 wiring by (exam-frequency × trust-cheapness).** Do the
   single-value / expression / root-set answer shapes first — linear, quadratics, sequences,
   finance, exponents — because their F1 predicates are trivial (integer/bounded/nice). Leave
   interval-answer types (double-inequality) for last: their memos need the most care and, in
   spine A, are *presented* not marked, so they carry no verifier urgency.

3. **Give F2 (render) a lightweight ritual, not machinery.** Keep it human-eyeball, but make
   it a per-generator checklist item: generate one sheet, open via `wslview`, scan for LaTeX
   corruption. Cheap, catches the `\quadx` class, no build cost.

4. **Do not gold-plate the "50/5" object.** It is `list[(problem_id, count)]` + seed + a
   per-day split over `generate.py`. Anything more is paper-assembly creep (fenced out).

**The one real risk is discipline, not capability.** Coverage is reachable (§3b) and the
engine is done. The failure mode is skipping the per-generator trust gate under time
pressure and shipping a plausible-but-out-of-scope memo — which, in an education market, is
fatal (strategy memory: "wrong memo = instant death"). §4c's bar — *no generator ships
without predicate + sweep + round-trip + eyeball* — is the guardrail; treat it as the
definition of done, not a nice-to-have.
