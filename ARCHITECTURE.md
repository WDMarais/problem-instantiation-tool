# Architecture — problem-instantiation-tool

Derived from the red test harness (`tests/`) and `spec.md`. All design decisions
recorded here were made before any implementation code was written.

---

## Design decisions

### Gap A — Gap-fill difficulty defaulting

Engine looks up the source problem from the registry at `instantiate()` time, computes
one tier below its `difficulty`, and returns a `spec.model_copy(update={"difficulty":
computed})`. The original `Problem` object is never mutated. `instance.spec` is this
copy. If the source is not in the registry, `ProblemNotFoundError` is raised for the
source ID.

Tier order: `routine < standard < challenging < non_routine`. Floor: `routine` stays
`routine` (gap-fill of a routine problem stays routine).

### Gap B — Callable `problem_spec` serialization

Custom Pydantic `@field_serializer` on `Problem.problem_spec`:

- `dict` → passes through as-is (already JSON-serializable)
- `callable` → serialized to:
  ```json
  {
    "__type__": "callable",
    "qualname": "module.function_name",
    "source":   "<inspect.getsource output>",
    "notes":    "<fn.__doc__ or empty string>"
  }
  ```

This keeps all `Problem` instances JSON-serializable at the MCP boundary while
preserving the callable's structure and intent for agent tooling.

### Gap C — `current_signature` for `ParamsIncompatibleError`

`Problem` has an explicit `param_names: frozenset[str] | None = None` field. When
set, the engine uses it directly as `current_signature`. When `None`, the engine
falls back to a seed-0 trial draw to derive the signature. Production problems should
always declare `param_names`; `None` is permitted for prototyping.

### `SolutionRating` computed fields

`marks_awarded`, `marks_possible`, and `is_correct` are regular Pydantic fields (not
`computed_field`). The verifier computes them before constructing `SolutionRating`. An
optional `model_validator(mode='after')` may assert consistency. This allows the schema
tests to construct `SolutionRating` directly with explicit values.

### `set_equality` verifier (5th type in v1 closed set)

`set_equality` is used throughout the test suite for SRS card root sets but was absent
from the spec's original StepVerifier list. It is added to the v1 closed set. Student
submits a set or dict of values; verifier checks unordered equality.

`numeric_approx` appears in the spec format example and one schema test but has no
grading tests. It is deferred to v2. `Problem` accepts it in `verifier_spec` without
error (no kind validation at construction), but no `StepVerifier` implementation exists
in v1.

---

## Module layout

```
problem_instantiation_tool/
├── __init__.py
├── exceptions.py        # ProblemEngineError hierarchy — no internal deps
├── schemas.py           # All shared types, enums, Verifier Protocol
├── registry.py          # ContentRegistry Protocol + InMemoryRegistry
├── verifier.py          # VerifierChain + StepVerifier types (internal)
└── engine.py            # Engine
```

`verifier.py` is never directly imported by consumers or tests. It is accessed only
via `instance.verifier.rate(attempt)`. All VerifierChain internals (SymPy, StepVerifier
subclasses, CA symbolic graph) are private implementation detail.

---

## Shared types

All shared types live in `schemas.py`. No separate types module.

`ProblemInstance.verifier` is typed against a `Verifier` Protocol defined in
`schemas.py` — this avoids a circular import (`verifier.py` imports from `schemas.py`;
if `schemas.py` imported `VerifierChain`, the import would cycle). `VerifierChain`
satisfies the protocol structurally (PEP 544).

---

## Implementation order (DAG)

1. `exceptions.py` — leaf; no internal dependencies
2. `schemas.py` — pydantic + exceptions
3. `registry.py` — schemas + exceptions *(parallel with 4)*
4. `verifier.py` — schemas + exceptions + sympy *(parallel with 3)*
5. `engine.py` — all of the above

---

## Per-module interface

### `exceptions.py`

```python
class ProblemEngineError(Exception): ...

class ProblemNotFoundError(ProblemEngineError):
    def __init__(self, problem_id: str) -> None
    problem_id: str

class InstantiationError(ProblemEngineError):
    def __init__(self, problem_id: str, cause: Exception) -> None
    problem_id: str
    cause: Exception          # explicit .cause attribute (not only __cause__)

class ParamsIncompatibleError(ProblemEngineError):
    def __init__(self, problem_id: str, stored_params: dict, current_signature: set[str]) -> None
    problem_id: str
    stored_params: dict
    current_signature: set[str]

class AttemptValidationError(ProblemEngineError):
    def __init__(self, step_index: int, reason: str = "") -> None
    step_index: int
    reason: str
```

No spec gaps. No open design decisions.

---

### `schemas.py`

**Enums** (`str, Enum` for Pydantic v2 serialization):

```python
class ArtifactType(str, Enum):
    srs_card = "srs_card"
    practice = "practice"
    worked_example = "worked_example"
    gap_fill = "gap_fill"

class Difficulty(str, Enum):
    routine = "routine"
    standard = "standard"
    challenging = "challenging"
    non_routine = "non_routine"

class MistakeType(str, Enum):
    correct = "correct"
    ca_correct = "ca_correct"
    semantic_error = "semantic_error"
    computation_error = "computation_error"

class ValidationMode(str, Enum):
    LENIENT = "lenient"    # coincidental canonical match → correct (default)
    STRICT  = "strict"     # coincidental canonical match → semantic_error
```

**Step wrappers:**

```python
class ProvidedStep(BaseModel):
    value: Any

class SubmittedStep(BaseModel):
    value: Any
# type(ProvidedStep(...)) is not type(SubmittedStep(...)) is guaranteed
```

**Attempt and rating:**

```python
class SolutionAttempt(BaseModel):
    steps: list[ProvidedStep | SubmittedStep | None]

class StepRating(BaseModel):
    index: int
    marks_awarded: int
    marks_possible: int
    mistake_type: MistakeType
    verifier_type: str

class SolutionRating(BaseModel):
    steps: list[StepRating]
    marks_awarded: int      # regular field — verifier computes before construction
    marks_possible: int     # regular field — verifier computes before construction
    is_correct: bool        # regular field — verifier computes before construction
    # Optional: model_validator(mode='after') asserts internal consistency
```

**`Verifier` Protocol** (in `schemas.py` to break circular import with `verifier.py`):

```python
class Verifier(Protocol):
    def rate(
        self,
        attempt: SolutionAttempt,
        *,
        validation_mode: ValidationMode = ValidationMode.LENIENT,
    ) -> SolutionRating: ...
```

**`Problem`:**

```python
class Problem(BaseModel):
    id: str
    type_id: str
    name: str
    artifact_type: ArtifactType
    problem_spec: dict | Callable      # @field_serializer handles callable (see Gap B)
    verifier_spec: dict | list[dict]
    problem_structure: dict | None = None
    required_slots: list[str] | None = None
    difficulty: Difficulty | None = None
    source_id: str | None = None
    blank_steps: list[int] | None = None
    param_names: frozenset[str] | None = None   # explicit signature (see Gap C)

    # Validators enforced at construction (model_validator or field_validator):
    # • srs_card + list verifier_spec → len(verifier_spec) ≤ 2
    # • srs_card + any {"kind": "self_graded"} entry → ValidationError
    # • gap_fill → source_id and blank_steps both required
    # • artifact_type and difficulty enum values enforced by Pydantic automatically
```

**`ProblemInstance`:**

```python
class ProblemInstance(BaseModel):
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    spec: Problem                    # model_copy() with filled difficulty for gap_fill
    params: dict[str, Any]
    solution: SolutionAttempt
    verifier: Verifier               # VerifierChain satisfies Verifier protocol
    seed: int | None
    presented_attempt: SolutionAttempt | None   # None for non-gap_fill
```

**Spec gaps:**
- Callable `problem_spec` serialization: design decided (Gap B); implementation-trivial.
- `test_srs_card_exactly_two_steps_is_valid`: add one passing test; no architecture impact.

---

### `registry.py`

```python
class ContentRegistry(Protocol):               # exported for type annotations
    def get(self, problem_id: str) -> Problem: ...
    def version(self) -> str: ...

class InMemoryRegistry:
    def __init__(self, problems: dict[str, Problem]) -> None: ...
    def get(self, problem_id: str) -> Problem: ...  # raises ProblemNotFoundError on miss
    def version(self) -> str: ...                   # returns a fixed string
```

No spec gaps. No open design decisions.

---

### `verifier.py`

**Public surface** (called only by `engine.py`):

```python
def build_verifier_chain(
    verifier_spec: dict | list[dict],
    params: dict[str, Any],
) -> VerifierChain:
    # Pass 1: builds symbolic SymPy expression per step that has depends_on + symbolic_expr.
    # Returns VerifierChain ready for rate() calls.
```

**`VerifierChain`** (satisfies `Verifier` protocol structurally):

```python
class VerifierChain:
    def rate(
        self,
        attempt: SolutionAttempt,
        *,
        validation_mode: ValidationMode = ValidationMode.LENIENT,
    ) -> SolutionRating: ...
```

**CA two-pass evaluation:**

Pass 1 (`build_verifier_chain`): for each step entry with `depends_on` and
`symbolic_expr`, parse the expression string into a SymPy expression parameterised by
`step{N}_result` symbols. Store per-step symbolic expressions on the chain.

Pass 2 (`rate()`): maintain `ca_values: dict[int, Any]` — accumulated step values
(student-submitted or canonical-provided). Walk steps in index order:

- `None` → raise `AttemptValidationError(step_index=i, reason="...")`
- `ProvidedStep(v)` → write `ca_values[i] = v` (canonical value; breaks CA propagation
  from prior student errors); skip rating; no `StepRating` emitted for this index.
- `SubmittedStep(v)`:
  - If no `depends_on`: `correct` vs `computation_error` (no CA).
  - If `depends_on` present:
    1. Compare `v` vs `canonical[i]` → `is_canonical_match`
    2. Substitute `ca_values` into symbolic expr → `ca_canonical`
    3. Determine `mistake_type`:
       - `v == canonical` and `v == ca_canonical` → `correct`
       - `v != canonical` and `v == ca_canonical` → `ca_correct`
       - `v == canonical` and `v != ca_canonical`:
         - `ValidationMode.LENIENT` → `correct`
         - `ValidationMode.STRICT` → `semantic_error`
       - `v != canonical` and `v != ca_canonical` → `semantic_error`
  - Write `ca_values[i] = v` (student value propagates forward to next step).

`marks_possible` on `SolutionRating` sums only `SubmittedStep` positions.

**StepVerifier closed set (v1):**

| Kind string | Class | Student submits | Notes |
|---|---|---|---|
| `sympy_equivalence` | `SymPyEquivalenceVerifier` | MathJSON expression | Converts to SymPy internally; never exposed at boundary |
| `set_equality` | `SetEqualityVerifier` | set or dict of values | Unordered equality |
| `mcq` | `MCQVerifier` | str (choice key) | Exact key match |
| `exact_match` | `ExactMatchVerifier` | str | Case-insensitive always; authored `normalize` options: `accents`, `whitespace`, `tone_marks` |
| `self_graded` | `SelfGradedVerifier` | bool | Non-bool → `AttemptValidationError` |

`numeric_approx` — accepted in `verifier_spec` schema without error; no verifier
implementation in v1; deferred to v2.

No spec gaps blocking this module.

---

### `engine.py`

```python
class Engine:
    def __init__(self, registry: ContentRegistry) -> None: ...

    def instantiate(
        self,
        spec_or_id: str | Problem,
        *,
        seed: int | None = None,
        params: dict[str, Any] | None = None,
    ) -> ProblemInstance: ...
```

**`instantiate()` logic:**

1. **Resolve spec**: `str` → `registry.get(id)` (raises `ProblemNotFoundError`);
   `Problem` → use directly (`instance.spec is problem_object` holds for direct pass).

2. **Mutual exclusion**: `seed` and `params` both non-None →
   `AttemptValidationError(step_index=0, reason="seed and params are mutually exclusive")`.

3. **Mode dispatch:**
   - *Fresh* (`seed=None, params=None`): draw `seed = random.randint(0, 2**31 - 1)`,
     call generator with seeded `random.Random(seed)`.
   - *Seeded*: call generator with `random.Random(seed)`.
   - *Reconstruction*: validate `params` against `current_signature` (from
     `spec.param_names` if set; otherwise seed-0 trial draw to derive it). Extra keys
     in `params` not in `current_signature` → `ParamsIncompatibleError`. Keys in
     `current_signature` missing from `params` and without defaults →
     `ParamsIncompatibleError`. New optional params (in signature, absent from `params`,
     have defaults) → filled with defaults silently.

4. **Generator call**: any exception from the generator →
   `InstantiationError(problem_id, cause=e)`.

5. **Gap-fill difficulty** (after successful generation, if `artifact_type == gap_fill`
   and `spec.difficulty is None`):
   ```python
   source = registry.get(spec.source_id)   # ProblemNotFoundError if missing
   computed = _one_tier_below(source.difficulty)   # floor: routine → routine
   spec = spec.model_copy(update={"difficulty": computed})
   ```

6. **Build verifier**: `build_verifier_chain(spec.verifier_spec, resolved_params)`.

7. **Build solution**: one `SubmittedStep` per step, values from generator output.

8. **Build `presented_attempt`** (gap_fill only): `ProvidedStep` at non-blank indices,
   `None` at `blank_steps` indices.

9. Return `ProblemInstance(spec=spec, params=..., solution=..., verifier=...,
   seed=..., presented_attempt=...)`.

**Spec gaps:**
- Backward-compat expanded signature: new optional params absent from stored `params`
  but present in current signature are filled with defaults; no error raised.
- Seed range: `random.randint(0, 2**31 - 1)`.

---

## Deferred test concerns

These are known test bugs that will produce false failures when the named module is
implemented. Fix before implementing the relevant module.

1. **`test_instantiate.py::test_gap_fill_difficulty_defaults_one_below_source`** —
   *Fixed.* Source problem `surd_equation_linear_rhs` (with `difficulty="standard"`)
   added to the `InMemoryRegistry`. Engine can now look it up at instantiate() time.

2. **`test_instantiate.py::test_callable_problem_spec_produces_same_instance_shape`** —
   *Fixed.* Callable `discriminant_generator` now returns a valid params dict instead
   of raising `NotImplementedError`.

3. **`test_schemas.py::test_engine_with_in_memory_registry_resolves_problem_by_id`** —
   Integration test cosmetically placed in the schema file. No behavioral issue; not
   worth moving.

---

## Tracer bullet recommendation

**None warranted.** Every inter-module seam is fully specified by the test suite:

- `schemas → verifier`: `SolutionAttempt` in, `SolutionRating` out — covered by all
  of `test_rate.py`.
- `engine → verifier`: `build_verifier_chain(spec, params) → VerifierChain` — the
  engine's construction path is always exercised by `test_rate.py` fixtures, which
  call `engine.instantiate()` then `instance.verifier.rate()`.
- `engine → registry`: `get(id) → Problem` — covered by `test_failure_modes.py` and
  `test_instantiate.py`.

Horizontal layering (exceptions → schemas → registry/verifier → engine) is safe here.
Each layer's contract is pinned by tests before the next layer is needed. The Pydantic-
as-source-of-truth approach means type contracts are enforced at construction, not
discovered at integration.
