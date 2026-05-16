# problem-instantiation-tool — Behavioral Spec

A generic engine sitting between content definitions and downstream consumers (SRS, PDF,
practice mode, Manim, MCP/agent tooling, etc.). Pure data layer — no rendering, no input
parsing, no presentation concerns.

---

## Ecosystem context

- `srs-tool` — shared scheduling/state package (SRSState, SM-2, check_unlocks). Stable, exists.
- `problem-instantiation-tool` — this engine. Does not exist yet.
- `nsc_papers` — NSC math content: YAML concept definitions + scripted generators. Primary consumer.
- `cq` — Chinese vocabulary card pipeline. Second consumer. Cross-domain validation lens throughout.

---

## Design principles

- **Spec is the source of truth for intent.** Code is an implementation of the spec, not a
  supplement to it. You should not need spec + code to understand what a problem looks like.
- **YAML and code generators are two syntaxes for the same contract.** YAML: parameter ranges
  are independent and structure is fixed. Code: generation logic requires real computation
  (backward-engineering, conditional branching, discriminant constraints). Engine dispatches
  uniformly; both produce identical `ProblemInstance` shape. No special-casing.
- **Explicit over inferred.** Authored fields state intent directly; the engine validates
  consistency at construction time. Inferred-only values are reserved for computed outputs
  (e.g. `SolutionRating` totals) where explicit authoring would create a sync surface.
- **Pure data layer.** No rendering (LaTeX etc.), no input parsing. Consumers handle presentation.
- **All boundary types are serializable.** No live SymPy objects or callables cross the
  engine's external surface. Expression trees use MathJSON format. Required for MCP/agent
  tooling (a first-class consumer).
- **Catalogue lives in the content layer.** Engine resolves IDs via an injected `ContentRegistry`;
  it does not own the catalogue. Engine surface: `instantiate(id, seed, params)` only.
- **v1 user model: good-faith/driven users.** Solutions are not hidden. Adverse-user hardening
  (solution gating, tamper detection) is explicitly deferred.
- **Exceptions are loud by design.** Failures in `instantiate()` and `verifier.rate()` raise
  named exceptions — never silently return None. Frequent recurrence of the same exception is
  a signal to fix the root cause, not a reason to suppress it.

---

## Core object schemas

### ContentRegistry (protocol — implemented by each content project)

```python
class ContentRegistry(Protocol):
    def get(self, problem_id: str) -> Problem: ...
    def version(self) -> str: ...    # included in ParamsIncompatibleError reports
```

Each content project (`nsc_papers`, `cq`, etc.) provides its own registry implementation
adhering to this versioned protocol. The engine is constructed with a registry instance;
no global registry exists. Tests inject an `InMemoryRegistry` that accepts `Problem` objects
directly — no file I/O, no YAML parsing, problems defined inline.

```python
# production
engine = Engine(registry=NSCRegistry(content_dir="./content"))

# tests
engine = Engine(registry=InMemoryRegistry({
    "quadratic_factor": Problem(id="quadratic_factor", ...)
}))
```

### Problem (the spec — immutable, authored)

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | str | yes | unique identifier |
| `type_id` | str | yes | references a `concept_type` |
| `name` | str | yes | human-readable label |
| `artifact_type` | enum | yes | `srs_card \| practice \| worked_example \| gap_fill` |
| `problem_spec` | dict or callable | yes | YAML: `{kind, ...param ranges}`; code: the generator itself |
| `verifier_spec` | dict or list[dict] | yes | single dict for atomics; list parallel to steps for composites |
| `problem_structure` | dict or None | composites only | `{kind: sequential, steps: [{role, ...}, ...]}` |
| `required_slots` | list or None | composites only | soft suggested-order constraints (not hard gates) |
| `difficulty` | enum or None | no | `routine \| standard \| challenging \| non_routine` |
| `source_id` | str or None | gap_fill only | ID of the source composite |
| `blank_steps` | list[int] or None | gap_fill only | step indices to blank (0-based; may be noncontiguous) |

**`artifact_type` semantics:**
- `srs_card` — ≤2 steps, all machine-gradeable verifiers. Engine validates at construction;
  violation is an authoring error.
- `practice` — standalone machine-gradeable problem, not SRS-scheduled.
- `worked_example` — problem + full solution artifact; SelfGraded or human-marked.
- `gap_fill` — must have `source_id` + `blank_steps`. Engine validates both present.

**`required_slots` / `min_tier`:** soft suggested ordering — not an access gate. Consumers
decide whether to enforce. Users can attempt any problem at any time and backpropagate along
the soft-DAG.

**`difficulty`:** authored enum, relative within a chain and roughly across chains. Not
objectively comparable across domains. Gap-fill defaults to one step below source difficulty;
authored value overrides. Separate from `min_tier` (prerequisite suggestion vs cognitive load).

**`verifier_spec` format:**

```yaml
# atomic — one verifier, no inter-step dependency
verifier_spec:
  kind: set_equality
  marks_possible: 1          # default 1; omittable

# composite — list parallel to problem_structure.steps
verifier_spec:
  - kind: set_equality
    marks_possible: 1
    # step 0: no depends_on
  - kind: numeric_approx
    tolerance: 0.005
    marks_possible: 2
    depends_on: [0]
    symbolic_expr: "2 * step0_result"
    # canonical answer expressed symbolically in terms of prior step result variables;
    # engine substitutes student's step 0 value for CA evaluation
```

`symbolic_expr` is required on any step with `depends_on`. For code generators, it is a
callable rather than a string expression.

### ProblemInstance (output of instantiate — immutable snapshot)

| Field | Type | Notes |
|---|---|---|
| `spec` | Problem | original spec, unmodified |
| `params` | dict | resolved concrete values, e.g. `{a: 2, root1: -3, root2: 5}` |
| `solution` | SolutionAttempt | golden-path answer, computed eagerly at instantiation |
| `verifier` | VerifierChain | live, ready to call `.rate()` |
| `seed` | int or None | seed used; enables replay |
| `presented_attempt` | SolutionAttempt or None | gap_fill only: pre-filled attempt with blank steps as None |

`solution` is computed eagerly — generator has all params in scope, cost is negligible, every
consumer needs it. Not hidden from consumers (good-faith user model).

`presented_attempt` is pre-computed eagerly for gap-fill instances. Contains `ProvidedStep`
for pre-filled context steps and `None` for blank slots the student must fill.

### SolutionAttempt

```
SolutionAttempt:
  steps: list[ProvidedStep | SubmittedStep | None]
```

**Step types — explicit tagged union:**

| Type | Meaning | Verifier behaviour |
|---|---|---|
| `ProvidedStep(value)` | Pre-filled context (engine-provided) | Skip — not marked |
| `SubmittedStep(value)` | Student-submitted answer | Mark this step |
| `None` | Blank slot not yet filled | Only valid in `presented_attempt`; raises `AttemptValidationError` if present at `rate()` time |

`StepValue` (the `value` inside either wrapper) is one of:
- `dict` — named outputs, e.g. `{"x": expr, "y": expr}` (order irrelevant within step)
- scalar — single-output step: MathJSON expression, MCQ choice key (str), or bool (SelfGraded)

**Gap-fill lifecycle:**

```
# Engine produces:
presented_attempt.steps = [ProvidedStep(v1), None, ProvidedStep(v3)]
  # consumer shows this to student; None marks what they must fill in

# Student fills step 1; consumer constructs:
submitted_attempt.steps = [ProvidedStep(v1), SubmittedStep(student_val), ProvidedStep(v3)]
  # None replaced with SubmittedStep; ProvidedSteps pass through unchanged

# verifier.rate(submitted_attempt):
  # ProvidedStep → skip
  # SubmittedStep → mark
  # None → AttemptValidationError (incomplete submission)
```

`Solution` is structurally identical to `SolutionAttempt` (all steps are `SubmittedStep`);
it is the guaranteed-valid case. No metadata on the attempt itself — `problem_id`, `timestamp`,
`attempt_number` are the consumer's concern.

**Expression trees** use MathJSON — a purpose-built, serializable, language-agnostic format
with existing tooling (conversion to/from SymPy, LaTeX, JS SDK). No SymPy dependency at
engine boundaries; consumers convert internally as needed.

```json
["Add", "x", 5]
["Multiply", 2, ["Symbol", "a"]]
["Power", "x", 2]
```

### SolutionRating (output of verifier.rate — computed, not authored)

```
SolutionRating:
  steps: list[StepRating]     # authoritative; ordered
  marks_awarded: int          # sum across steps (computed convenience)
  marks_possible: int         # max marks for submitted steps only (computed convenience)
  is_correct: bool            # marks_awarded == marks_possible (SRS pass/fail shortcut)

StepRating:
  index: int                  # 0-based
  marks_awarded: int          # marks for this step
  marks_possible: int         # from verifier_spec; default 1
  mistake_type: enum          # correct | ca_correct | semantic_error | computation_error
  verifier_type: str          # which StepVerifier judged this step
```

**`mistake_type` semantics:**

| Value | Meaning | SRS signal |
|---|---|---|
| `correct` | Matches canonical answer | Pass |
| `ca_correct` | Wrong vs canonical; correct given student's own prior value | Arithmetic slip; light penalty |
| `semantic_error` | Wrong vs CA-canonical (step has a prior dependency; student did not apply the correct formula to their own prior values — this includes a coincidental match with canonical, e.g. using the canonical prior value instead of their own) | Conceptual gap; heavy penalty |
| `computation_error` | Step 0 only (no prior); simply wrong | Standard fail |

SRS scheduling should weight `semantic_error` more heavily than `ca_correct` or
`computation_error`. `ca_correct` means the student understood the method but made an
earlier arithmetic slip; `semantic_error` means they applied the wrong approach regardless.

`marks_possible` on `SolutionRating` covers submitted steps only — partial attempts do not
penalise for unsubmitted steps. `is_correct` is a computed convenience; not authored.

### VerifierChain

Built at instantiation time from `verifier_spec`. Atomics: one-element chain. Composites:
one `StepVerifier` per `verifier_spec` entry, parallel to `problem_structure.steps`.

CA marking via **two-pass evaluation:**

**Pass 1 — symbolic tree (at instantiation):**
Chain builds each step's answer as a symbolic expression parameterised by prior step result
variables, not resolved constants. This is the "what should this step be, given whatever
came before" function.

**Pass 2 — student value substitution (at rate()):**
Chain walks steps in order. At each `SubmittedStep`, it:
1. Evaluates student value vs concrete canonical answer → is it `correct`?
2. Evaluates student value vs CA-canonical (symbolic_expr with student's prior values
   substituted) → determines full `mistake_type`
3. Threads the student's value forward as input to the next step's symbolic_expr

```
# canonical: a=5, x=2a=10, z=2x=20
# student:   a=10, x=10, z=20

step 0: canonical=5,  student=10
          → computation_error  (no prior step; just wrong)

step 1: canonical=10, ca_canonical=2×10=20, student=10
          student==canonical(10) but ≠ ca_canonical(20)
          → semantic_error  (formula correct but applied against canonical a, not their a=10)

step 2: canonical=20, ca_canonical=2×10=20, student=20
          student==ca_canonical  → ca_correct
```

CA does not apply across noncontiguous gap-fill blanks — `ProvidedStep` values break the
causal chain and reset to canonical for the next student-submitted step.

**StepVerifier types (closed set, v1):**

| Type | Student submits | Notes |
|---|---|---|
| `SymPyEquivalence` | MathJSON expression | Converted to SymPy internally; not exposed at boundary |
| `MCQ` | choice key (str) | Objectively gradeable; preferred for language/non-math |
| `ExactMatch` | str | Case-insensitive by default; authored normalization options (strip accents, whitespace, tone marks) |
| `SelfGraded` | bool | Human marks pass/fail; deprioritised in v1; valid for teacher-marked exams |

---

## Section 1 — instantiate()

### Signature

```python
engine = Engine(registry=my_registry)
engine.instantiate(spec_or_id, seed=None, params=None)
# seed and params are mutually exclusive
```

Three modes:
1. **Fresh (random):** no seed or params — random draw; seed recorded on instance for replay.
2. **Deterministic:** `seed=42` — identical instance on every call.
3. **Reconstruction:** `params={...}` — skip random draw; re-derive solution and verifier from
   stored params. Engine validates params against current generator signature.

### Cases

```
engine.instantiate("quadratic_factor", seed=42)
  → ProblemInstance {
      spec: Problem("quadratic_factor"),
      params: {a: 2, root1: -3, root2: 5},
      solution: SolutionAttempt(steps=[SubmittedStep({"roots": ["-3", "5"]})]),
      verifier: VerifierChain([SetEqualityVerifier(marks_possible=1)]),
      seed: 42,
      presented_attempt: None   # not a gap_fill
    }

engine.instantiate("quadratic_factor", seed=42)  [called again]
  → identical ProblemInstance
  # no hidden mutable state in the engine

engine.instantiate("quadratic_factor")  [called twice, no seed]
  → two statistically independent ProblemInstances
  # engine does not cache or deduplicate unseeded calls

engine.instantiate(Problem(...))
  → ProblemInstance as above
  # accepts str ID (resolved via registry) or already-constructed Problem object

engine.instantiate("discriminant_generator")  [code-based spec]
  → ProblemInstance with identical shape to YAML-based instantiation
  # d>0/d=0/d<0 branching handled internally; YAML alternative needs three concepts
  # with frequency weights — code is the right tool when DSL would encode computation

engine.instantiate("quadratic_factor", params={"a": 2, "root1": -3, "root2": 5})
  → ProblemInstance reconstructed from stored params
  # random draw skipped; solution and verifier re-derived
  # unit tests are the primary safeguard against incompatibility ever reaching this path

engine.instantiate("quadratic_factor", seed=42, params={...})
  → raises AttemptValidationError  # mutually exclusive
```

### Gap-fill cases

```
engine.instantiate("surd_gap_step1", seed=7)
  # spec: {artifact_type: gap_fill, source_id: "surd_equation_linear_rhs", blank_steps: [1]}
  → ProblemInstance {
      params: {a: 3, ...},
      solution: SolutionAttempt(steps=[SubmittedStep(s0), SubmittedStep(s1), SubmittedStep(s2)]),
      presented_attempt: SolutionAttempt(steps=[ProvidedStep(s0), None, ProvidedStep(s2)]),
      verifier: VerifierChain checking only SubmittedStep positions
    }

engine.instantiate("surd_gap_steps0_2", seed=7)
  # blank_steps: [0, 2] — noncontiguous
  → presented_attempt.steps = [None, ProvidedStep(s1), None]
  # verifier checks steps 0 and 2 independently; ProvidedStep(s1) breaks CA chain

gap-fill difficulty defaults
  # source difficulty: standard → gap-fill carries: routine
  # source difficulty: standard, spec has difficulty: challenging → gap-fill carries: challenging
```

### Persistence model

Consumer stores: `(problem_id, params, SolutionRating)` — no seed required.

**Generator backward-compatibility contract:** call signature can only be retained or expanded,
never narrowed. Adding optional params is fine; removing or renaming existing params is a
breaking change requiring a new problem ID. Params reconstruct the problem display stably;
solution is re-derived on reconstruction and may reflect improvements. Stored SolutionRating
is retained regardless of solution changes — students keep old scores.

### cq lens

```
engine.instantiate("nihao_card")
  → ProblemInstance {
      params: {hanzi: "你好"},
      solution: SolutionAttempt(steps=[SubmittedStep({"gloss": "hello", "pinyin": "nǐ hǎo"})]),
      verifier: VerifierChain([MCQVerifier(...)]),
      ...
    }
  # engine is domain-agnostic; identical shape to math problems
  # persistence: store (problem_id: "nihao_card", params: {hanzi: "你好"}, rating)
  # corrected pinyin annotation surfaced on next reconstruction; prior score retained
```

---

## Section 2 — verifier.rate()

### Cases

```
# 1-step SRS card — correct
verifier.rate(SolutionAttempt(steps=[SubmittedStep({"roots": {-3, 5}})]))
  → SolutionRating {
      steps: [StepRating {index:0, marks_awarded:1, marks_possible:1,
                          mistake_type:correct, verifier_type:"set_equality"}],
      marks_awarded:1, marks_possible:1, is_correct:True
    }

# 1-step SRS card — wrong answer
verifier.rate(SolutionAttempt(steps=[SubmittedStep({"roots": {-3, 4}})]))
  → SolutionRating {
      steps: [StepRating {index:0, marks_awarded:0, marks_possible:1,
                          mistake_type:computation_error, verifier_type:"set_equality"}],
      marks_awarded:0, marks_possible:1, is_correct:False
    }

# 2-step: student wrong on step 0, ca_correct on step 1
# canonical: a=5, x=2a=10  |  student: a=10, x=20
verifier.rate(SolutionAttempt(steps=[SubmittedStep(10), SubmittedStep(20)]))
  → SolutionRating {
      steps: [
        StepRating {index:0, marks_awarded:0, marks_possible:1, mistake_type:computation_error},
        StepRating {index:1, marks_awarded:1, marks_possible:1, mistake_type:ca_correct}
      ],
      marks_awarded:1, marks_possible:2, is_correct:False
    }

# 2-step: semantic error on step 1
# canonical: a=5, x=2a=10  |  student: a=10, x=10 (applied formula to canonical a, not theirs)
verifier.rate(SolutionAttempt(steps=[SubmittedStep(10), SubmittedStep(10)]))
  → StepRating {index:1, mistake_type:semantic_error, marks_awarded:0}
  # student matched canonical x=10 but not ca_canonical x=20; conceptual gap flagged

# partial attempt — 1 of 2 steps submitted
verifier.rate(SolutionAttempt(steps=[SubmittedStep(5)]))
  → SolutionRating {marks_awarded:1, marks_possible:1, is_correct:True}
  # marks_possible covers submitted steps only; pure function, no "incomplete" error

# gap-fill: ProvidedSteps skipped; only SubmittedStep at index 1 marked
verifier.rate(SolutionAttempt(steps=[ProvidedStep(s0), SubmittedStep(student_val), ProvidedStep(s2)]))
  → SolutionRating covering index 1 only; marks_possible=1

# None in submitted attempt
verifier.rate(SolutionAttempt(steps=[None]))
  → raises AttemptValidationError(step_index=0, reason="None only valid in presented_attempt")

# insight step with higher mark weight
# verifier_spec: {kind: sympy_equivalence, marks_possible: 2}
verifier.rate(SolutionAttempt(steps=[SubmittedStep(correct_expr)]))
  → StepRating {mistake_type:correct, marks_awarded:2, marks_possible:2}

# MCQ
verifier.rate(SolutionAttempt(steps=[SubmittedStep("B")]))
  → StepRating {mistake_type:correct/computation_error, verifier_type:"mcq", ...}

# ExactMatch — pinyin with tone-mark normalisation
# verifier_spec: {kind: exact_match, normalize: [case, accents, whitespace]}
verifier.rate(SolutionAttempt(steps=[SubmittedStep("ni hao")]))   # missing tone marks
  → StepRating {mistake_type:correct, verifier_type:"exact_match", ...}
  # "ni hao" normalises to match "nǐ hǎo" when normalize includes accents

verifier.rate(SolutionAttempt(steps=[SubmittedStep("Tanzania")]))
  → StepRating {mistake_type:correct, verifier_type:"exact_match", ...}
verifier.rate(SolutionAttempt(steps=[SubmittedStep("tanzania")]))
  → StepRating {mistake_type:correct, ...}  # case_insensitive is always on by default
verifier.rate(SolutionAttempt(steps=[SubmittedStep("Zambia")]))
  → StepRating {mistake_type:computation_error, marks_awarded:0, ...}

# SelfGraded
verifier.rate(SolutionAttempt(steps=[SubmittedStep(True)]))
  → StepRating {mistake_type:correct, marks_awarded:marks_possible, verifier_type:"self_graded"}
  # engine trusts the boolean; good-faith user model
```

### Language / non-math (cq lens)

Chinese vocabulary uses MCQ (choose gloss from options) or fill-in-the-word (type pinyin).
Both map to existing verifier types without modification. Rough chengyu definition → SelfGraded.
No new verifier type needed for cq in v1.

---

## Section 3 — Failure modes

```python
ProblemEngineError                               # base; catch-all for callers that don't need specifics
  ├── ProblemNotFoundError(problem_id)
  │     # unknown ID; caller error; loud failure in dev, should not reach prod
  ├── InstantiationError(problem_id, cause)
  │     # generator raised — overconstrained spec, authoring bug; wraps underlying exception
  ├── ParamsIncompatibleError(problem_id, stored_params, current_signature)
  │     # reconstruction path; stored params don't match current generator signature
  │     # resolution: explicit migration of stored records, not silent fallback
  └── AttemptValidationError(step_index, reason)
        # wrong type at a step; None in submitted attempt; etc.
```

### Cases

```
engine.instantiate("nonexistent_id")
  → raises ProblemNotFoundError("nonexistent_id")

engine.instantiate("overconstrained_generator")
  → raises InstantiationError("overconstrained_generator", cause=<underlying>)

engine.instantiate("quadratic_factor", params={"a": 2, "old_field": 5})
  # "old_field" was renamed in a generator update
  → raises ParamsIncompatibleError(
        problem_id="quadratic_factor",
        stored_params={"a": 2, "old_field": 5},
        current_signature={"a", "root1", "root2"}
    )
  # resolution: explicit migration, not silent fallback

verifier.rate(SolutionAttempt(steps=[SubmittedStep("not_a_bool")]))  # SelfGraded expects bool
  → raises AttemptValidationError(step_index=0, reason="SelfGraded expects bool, got str")

Problem(
    id="circle_area",
    type_id="geometry",
    name="Find the area of a circle",
    artifact_type="srs_card",
    problem_spec={"kind": "circle_area", "radius_range": [1, 10]},
    verifier_spec=[
        {"kind": "self_graded", "marks_possible": 1},
        {"kind": "self_graded", "marks_possible": 1},
    ],
)
  # artifact_type srs_card requires all verifiers to be machine-gradeable
  # (SymPyEquivalence or MCQ); SelfGraded is not
  → raises ValidationError at construction: "srs_card artifact_type incompatible
    with SelfGraded verifier at step 0"
  # authoring error surfaced immediately — not deferred to instantiate() or rate()
```

---

## Explicitly out of scope (v1)

- **Multi-step machine grading (3+ steps).** SRS = 1–2 steps. Complex worked examples →
  `worked_example` artifact type → human/SelfGraded. Ops-tree alignment (split steps,
  reordered parallel steps, partial credit for skipped steps) is the v2 direction.
- **Intelligent Tutoring System behaviour.** Equivalence checking stays shallow; problems are
  authored for a specific solution path.
- **Rendering / presentation.** No LaTeX, no display formatting. Consumers handle all output.
- **Input parsing.** No string-to-expression parsing. Expression inputs are
  valid-by-construction MathJSON from the consumer's UI.
- **Adverse-user hardening.** Solution gating, tamper detection, hashing deferred. v1 targets
  good-faith/driven users.
- **Additional StepVerifier types.** `SymPyEquivalence`, `MCQ`, `ExactMatch`, `SelfGraded`
  are the closed set for v1. `IntervalCheck` (inequalities) is a noted v2 candidate.
- **Catalogue / discovery.** Lives in the content layer. Engine does not own it.

---

## Technology recommendation

### Constraints that drove this recommendation

Specific cases from the interview that put pressure on technology choices:

1. **MCP/agent tooling as first-class consumer** → all boundary types must be JSON-serializable.
   No live objects, no Python-specific formats at the surface.
2. **Authoring errors should fail at construction, not at `instantiate()` time** → schema
   enforcement needs to be structural and automatic, not a pile of manual `if` checks.
3. **Two-pass CA evaluation requires symbolic computation** → a CAS is load-bearing, not optional.
4. **Per-project registry, tests as first-class citizens** → the content layer interface must
   be injectable with zero friction.
5. **YAML has real expressiveness limits** (encoding computation in DSL form) → the canonical
   spec format should not be YAML; YAML can remain as a human-authored input format.

### Recommendation

**Python 3.11+** throughout. The entire ecosystem (`srs-tool`, `nsc_papers`, `cq`, SymPy) is
Python. No axis pushes toward a different language; diverging here buys nothing.

**Pydantic v2** for all schema objects (`Problem`, `ProblemInstance`, `SolutionAttempt`,
`SolutionRating`, and their sub-types). The "explicit over inferred" principle becomes
mechanical: illegal `Problem` states raise `ValidationError` at model construction, not
downstream at `instantiate()` time. `.model_dump()` and `.model_validate()` give JSON
serialization and deserialization for free — satisfying the MCP boundary requirement without
extra work.

**Python `Protocol`** (PEP 544, structural subtyping) for `ContentRegistry`. No inheritance
required; any object with `get(id) -> Problem` and `version() -> str` satisfies the contract.
Test registries implement the protocol with an in-memory dict — pure injection, zero boilerplate.

**Pydantic models as the canonical spec format, not YAML.** Authors define `Problem` instances
as Python objects (Pydantic model instantiation). Code generators are Python callables
registered with the registry. YAML becomes an optional human-authored import format: parsed,
validated against the Pydantic schema on load, rejected with a clear error if invalid. This
eliminates YAML DSL limitations, keeps the entire stack in one typed language, and means
YAML and code generators truly are two syntaxes for the same contract — they both produce
the same Pydantic `Problem` model.

**MathJSON** for expression trees at all boundaries. Purpose-built for serializable
mathematical expressions; has existing implementations and tooling (conversion to/from SymPy,
LaTeX, a JavaScript SDK). Prefer over a bespoke dict schema — the format already exists and
is maintained. Internally, the `SymPyEquivalenceVerifier` converts MathJSON to SymPy
expressions for equivalence checking; this conversion never crosses the engine boundary.

**SymPy** for the `SymPyEquivalenceVerifier` and the symbolic dependency graph used in
two-pass CA evaluation. SymPy is the right call: Python-native, handles symbolic
simplification and equivalence checking, lightweight enough for this use case. The symbolic
expressions built during Pass 1 (CA setup) live entirely inside the engine; they are never
serialized or exposed.

### Tension named and resolved

**Pydantic-as-canonical vs YAML-for-human-authoring.** Pydantic requires Python literacy
from content authors; YAML is more accessible. Resolution: Pydantic is the canonical
representation; YAML is a validated import format. Authors who want YAML can write it and
get immediate feedback on schema violations at load time. Authors writing complex generators
use Python directly. Both paths produce the same Pydantic `Problem`. This is not a
compromise — it is strictly better than making YAML canonical, because it removes the class
of bugs where YAML and code generator assumptions silently diverge.
