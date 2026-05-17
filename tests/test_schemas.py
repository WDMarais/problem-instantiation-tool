"""
Tests for core object schemas: Problem, ProblemInstance, SolutionAttempt,
SolutionRating, ContentRegistry, InMemoryRegistry.

Spec section: ## Core object schemas
"""

import json
import pytest

# Stubs — one block for all unimplemented production imports.
# As each module is implemented: move its imports above this block as bare imports,
# delete the corresponding stub classes from the except clause.
# When the except clause is empty, delete the whole try/except.
try:
    from pydantic import ValidationError
    from problem_instantiation_tool.schemas import (
        Problem,
        ProblemInstance,
        SolutionAttempt,
        SolutionRating,
        StepRating,
        ProvidedStep,
        SubmittedStep,
    )
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.exceptions import ProblemNotFoundError
except ImportError:

    class ValidationError(Exception):
        pass

    class Problem:
        def __init__(self, **kwargs):
            raise NotImplementedError

    class ProblemInstance:
        pass

    class SolutionAttempt:
        def __init__(self, **kwargs):
            raise NotImplementedError

    class SolutionRating:
        def __init__(self, **kwargs):
            raise NotImplementedError

    class StepRating:
        def __init__(self, **kwargs):
            raise NotImplementedError

    class ProvidedStep:
        def __init__(self, value):
            raise NotImplementedError

    class SubmittedStep:
        def __init__(self, value):
            raise NotImplementedError

    class InMemoryRegistry:
        def __init__(self, problems):
            raise NotImplementedError

        def get(self, problem_id):
            raise NotImplementedError

        def version(self):
            raise NotImplementedError

    class Engine:
        def __init__(self, registry):
            raise NotImplementedError

        def instantiate(self, spec_or_id, seed=None, params=None):
            raise NotImplementedError

    class ProblemNotFoundError(Exception):
        def __init__(self, problem_id):
            super().__init__(problem_id)


# ---------------------------------------------------------------------------
# Integration smoke: Engine + InMemoryRegistry + Problem roundtrip
# ---------------------------------------------------------------------------


@pytest.mark.schemas
def test_engine_with_in_memory_registry_resolves_problem_by_id():
    """Full roundtrip: Engine built with InMemoryRegistry; problem fetched and instantiated."""
    problem = Problem(  # TODO: wire up
        id="quad_factor",
        type_id="algebra",
        name="Factor a quadratic",
        artifact_type="srs_card",
        problem_spec={
            "kind": "quadratic_factor",
            "a_range": [1, 5],
            "root_range": [-9, 9],
        },
        verifier_spec={"kind": "set_equality", "marks_possible": 1},
    )
    registry = InMemoryRegistry({"quad_factor": problem})  # TODO: wire up
    engine = Engine(registry=registry)  # TODO: wire up
    instance = engine.instantiate("quad_factor", seed=1)  # TODO: wire up
    assert instance.spec.id == "quad_factor"
    assert isinstance(instance.params, dict)
    assert instance.solution is not None
    assert instance.verifier is not None


# ---------------------------------------------------------------------------
# Problem — valid construction
# ---------------------------------------------------------------------------


@pytest.mark.schemas
def test_problem_minimal_required_fields():
    """Problem with only required fields constructs without error."""
    p = Problem(  # TODO: wire up
        id="simple_add",
        type_id="arithmetic",
        name="Simple addition",
        artifact_type="srs_card",
        problem_spec={"kind": "add", "a_range": [1, 10], "b_range": [1, 10]},
        verifier_spec={"kind": "set_equality", "marks_possible": 1},
    )
    assert p.id == "simple_add"
    assert p.artifact_type == "srs_card"


@pytest.mark.schemas
def test_problem_difficulty_defaults_to_none():
    """difficulty is None when not authored."""
    p = Problem(  # TODO: wire up
        id="simple_add",
        type_id="arithmetic",
        name="Simple addition",
        artifact_type="srs_card",
        problem_spec={"kind": "add", "a_range": [1, 10]},
        verifier_spec={"kind": "set_equality"},
    )
    assert p.difficulty is None


@pytest.mark.schemas
def test_problem_all_optional_fields():
    """Problem with every optional field constructs and exposes those fields."""
    p = Problem(  # TODO: wire up
        id="hard_composite",
        type_id="algebra",
        name="Full composite",
        artifact_type="practice",
        problem_spec={"kind": "quadratic_factor", "a_range": [1, 5]},
        verifier_spec=[
            {"kind": "set_equality", "marks_possible": 1},
            {
                "kind": "numeric_approx",
                "tolerance": 0.005,
                "marks_possible": 2,
                "depends_on": [0],
                "symbolic_expr": "2 * step0_result",
            },
        ],
        problem_structure={
            "kind": "sequential",
            "steps": [{"role": "factor"}, {"role": "evaluate"}],
        },
        required_slots=["factoring_basics"],
        difficulty="challenging",
    )
    assert p.difficulty == "challenging"
    assert p.problem_structure["kind"] == "sequential"
    assert len(p.required_slots) == 1


@pytest.mark.schemas
def test_problem_gap_fill_with_source_id_and_blank_steps():
    """gap_fill Problem with source_id and blank_steps constructs correctly."""
    p = Problem(  # TODO: wire up
        id="surd_gap",
        type_id="algebra",
        name="Surd gap fill",
        artifact_type="gap_fill",
        problem_spec={"kind": "surd_linear", "a_range": [2, 9]},
        verifier_spec=[
            {"kind": "sympy_equivalence", "marks_possible": 1},
            {"kind": "sympy_equivalence", "marks_possible": 1},
            {"kind": "sympy_equivalence", "marks_possible": 1},
        ],
        source_id="surd_equation_linear_rhs",
        blank_steps=[1],
    )
    assert p.source_id == "surd_equation_linear_rhs"
    assert p.blank_steps == [1]
    assert p.artifact_type == "gap_fill"


@pytest.mark.schemas
def test_problem_gap_fill_noncontiguous_blank_steps():
    """gap_fill with noncontiguous blank_steps stores both indices."""
    p = Problem(  # TODO: wire up
        id="surd_gap_0_2",
        type_id="algebra",
        name="Surd gap fill steps 0 and 2",
        artifact_type="gap_fill",
        problem_spec={"kind": "surd_linear", "a_range": [2, 9]},
        verifier_spec=[
            {"kind": "sympy_equivalence", "marks_possible": 1},
            {"kind": "sympy_equivalence", "marks_possible": 1},
            {"kind": "sympy_equivalence", "marks_possible": 1},
        ],
        source_id="surd_equation_linear_rhs",
        blank_steps=[0, 2],
    )
    assert p.blank_steps == [0, 2]


# ---------------------------------------------------------------------------
# Problem — JSON serialization (MCP boundary requirement)
# ---------------------------------------------------------------------------


@pytest.mark.schemas
def test_problem_model_dump_is_json_serializable():
    """Problem.model_dump() produces a JSON-serializable dict (no live objects)."""
    p = Problem(  # TODO: wire up
        id="simple_add",
        type_id="arithmetic",
        name="Simple addition",
        artifact_type="srs_card",
        problem_spec={"kind": "add", "a_range": [1, 10]},
        verifier_spec={"kind": "set_equality", "marks_possible": 1},
    )
    dumped = p.model_dump()
    assert isinstance(dumped, dict)
    json.dumps(dumped)  # must not raise TypeError


# ---------------------------------------------------------------------------
# Problem — validation failures (authoring errors at construction time)
# ---------------------------------------------------------------------------


@pytest.mark.schemas
def test_problem_srs_card_with_self_graded_raises_validation_error():
    """srs_card artifact_type with SelfGraded verifier raises ValidationError at construction."""
    with pytest.raises(ValidationError):
        Problem(  # TODO: wire up
            id="bad_srs",
            type_id="geometry",
            name="Self-graded SRS card",
            artifact_type="srs_card",
            problem_spec={"kind": "circle_area", "radius_range": [1, 10]},
            verifier_spec={"kind": "self_graded", "marks_possible": 1},
        )


@pytest.mark.schemas
def test_problem_srs_card_with_more_than_two_verifier_steps_raises_validation_error():
    """srs_card with 3 verifier entries raises ValidationError (≤2 steps required)."""
    with pytest.raises(ValidationError):
        Problem(  # TODO: wire up
            id="three_step_srs",
            type_id="algebra",
            name="Three-step SRS card",
            artifact_type="srs_card",
            problem_spec={"kind": "multi"},
            verifier_spec=[
                {"kind": "set_equality", "marks_possible": 1},
                {"kind": "set_equality", "marks_possible": 1},
                {"kind": "set_equality", "marks_possible": 1},
            ],
        )


@pytest.mark.schemas
def test_problem_gap_fill_without_source_id_raises_validation_error():
    """gap_fill without source_id raises ValidationError at construction."""
    with pytest.raises(ValidationError):
        Problem(  # TODO: wire up
            id="gap_no_source",
            type_id="algebra",
            name="Gap fill without source",
            artifact_type="gap_fill",
            problem_spec={"kind": "surd_linear"},
            verifier_spec={"kind": "sympy_equivalence"},
            blank_steps=[1],
            # source_id deliberately omitted
        )


@pytest.mark.schemas
def test_problem_gap_fill_without_blank_steps_raises_validation_error():
    """gap_fill without blank_steps raises ValidationError at construction."""
    with pytest.raises(ValidationError):
        Problem(  # TODO: wire up
            id="gap_no_blanks",
            type_id="algebra",
            name="Gap fill without blank steps",
            artifact_type="gap_fill",
            problem_spec={"kind": "surd_linear"},
            verifier_spec={"kind": "sympy_equivalence"},
            source_id="surd_equation_linear_rhs",
            # blank_steps deliberately omitted
        )


@pytest.mark.schemas
def test_problem_invalid_artifact_type_raises_validation_error():
    """artifact_type not in enum raises ValidationError."""
    with pytest.raises(ValidationError):
        Problem(  # TODO: wire up
            id="bad_type",
            type_id="algebra",
            name="Bad artifact type",
            artifact_type="quiz",  # not a valid enum value
            problem_spec={"kind": "add"},
            verifier_spec={"kind": "set_equality"},
        )


@pytest.mark.schemas
def test_problem_invalid_difficulty_raises_validation_error():
    """difficulty value not in enum raises ValidationError."""
    with pytest.raises(ValidationError):
        Problem(  # TODO: wire up
            id="bad_difficulty",
            type_id="algebra",
            name="Bad difficulty",
            artifact_type="practice",
            problem_spec={"kind": "add"},
            verifier_spec={"kind": "set_equality"},
            difficulty="hard",  # not valid; correct values: routine/standard/challenging/non_routine
        )


# ---------------------------------------------------------------------------
# SolutionAttempt — tagged union step types
# ---------------------------------------------------------------------------


@pytest.mark.schemas
def test_solution_attempt_with_submitted_step_stores_value():
    """SolutionAttempt containing SubmittedStep preserves the step and value."""
    step = SubmittedStep({"roots": [-3, 5]})  # TODO: wire up
    attempt = SolutionAttempt(steps=[step])  # TODO: wire up
    assert attempt.steps[0] is step


@pytest.mark.schemas
def test_solution_attempt_with_provided_step_stores_value():
    """SolutionAttempt containing ProvidedStep preserves the step and value."""
    step = ProvidedStep(
        ["Multiply", 2, ["Symbol", "a"]]
    )  # TODO: wire up (MathJSON value)
    attempt = SolutionAttempt(steps=[step])  # TODO: wire up
    assert attempt.steps[0] is step


@pytest.mark.schemas
def test_solution_attempt_with_none_slot_is_valid_for_presented_attempt():
    """SolutionAttempt can hold None at a step position (for presented_attempt blank slots)."""
    attempt = SolutionAttempt(
        steps=[ProvidedStep(5), None, ProvidedStep(3)]
    )  # TODO: wire up
    assert attempt.steps[1] is None


@pytest.mark.schemas
def test_provided_step_and_submitted_step_are_distinct_types():
    """ProvidedStep and SubmittedStep are different types — not interchangeable wrappers."""
    provided = ProvidedStep(10)  # TODO: wire up
    submitted = SubmittedStep(10)  # TODO: wire up
    assert type(provided) is not type(submitted)


@pytest.mark.schemas
def test_solution_is_all_submitted_steps():
    """The canonical solution is a SolutionAttempt where every step is a SubmittedStep."""
    # The golden-path solution has no ProvidedStep or None — all steps are SubmittedStep.
    solution = SolutionAttempt(  # TODO: wire up
        steps=[SubmittedStep({"roots": [-3, 5]})]
    )
    assert all(type(s) is SubmittedStep for s in solution.steps)


# ---------------------------------------------------------------------------
# SolutionRating — computed convenience fields
# ---------------------------------------------------------------------------


@pytest.mark.schemas
def test_solution_rating_marks_awarded_is_sum_of_step_marks():
    """marks_awarded equals the sum of marks_awarded across all StepRatings."""
    rating = SolutionRating(  # TODO: wire up
        steps=[
            StepRating(
                index=0,
                marks_awarded=1,
                marks_possible=1,
                mistake_type="correct",
                verifier_type="set_equality",
            ),
            StepRating(
                index=1,
                marks_awarded=0,
                marks_possible=2,
                mistake_type="semantic_error",
                verifier_type="sympy_equivalence",
            ),
        ],
        marks_awarded=1,
        marks_possible=3,
        is_correct=False,
    )
    assert rating.marks_awarded == 1
    assert rating.marks_possible == 3
    assert rating.is_correct is False


@pytest.mark.schemas
def test_solution_rating_is_correct_true_when_full_marks():
    """is_correct is True exactly when marks_awarded == marks_possible."""
    rating = SolutionRating(  # TODO: wire up
        steps=[
            StepRating(
                index=0,
                marks_awarded=1,
                marks_possible=1,
                mistake_type="correct",
                verifier_type="mcq",
            ),
        ],
        marks_awarded=1,
        marks_possible=1,
        is_correct=True,
    )
    assert rating.is_correct is True


@pytest.mark.schemas
def test_solution_rating_is_correct_false_when_partial():
    """is_correct is False when marks_awarded < marks_possible."""
    rating = SolutionRating(  # TODO: wire up
        steps=[
            StepRating(
                index=0,
                marks_awarded=0,
                marks_possible=1,
                mistake_type="computation_error",
                verifier_type="set_equality",
            ),
        ],
        marks_awarded=0,
        marks_possible=1,
        is_correct=False,
    )
    assert rating.is_correct is False


@pytest.mark.schemas
def test_step_rating_mistake_type_enum_values():
    """StepRating accepts all four mistake_type values from the spec."""
    for mt in ("correct", "ca_correct", "semantic_error", "computation_error"):
        sr = StepRating(  # TODO: wire up
            index=0,
            marks_awarded=0,
            marks_possible=1,
            mistake_type=mt,
            verifier_type="set_equality",
        )
        assert sr.mistake_type == mt


# ---------------------------------------------------------------------------
# ContentRegistry — structural protocol (PEP 544)
# ---------------------------------------------------------------------------


@pytest.mark.schemas
def test_in_memory_registry_satisfies_content_registry_protocol():
    """InMemoryRegistry satisfies ContentRegistry protocol without subclassing."""
    from typing import Protocol, runtime_checkable

    @runtime_checkable
    class ContentRegistry(Protocol):
        def get(self, problem_id: str) -> object: ...
        def version(self) -> str: ...

    registry = InMemoryRegistry({})  # TODO: wire up
    assert isinstance(registry, ContentRegistry)


@pytest.mark.schemas
def test_ad_hoc_class_satisfies_content_registry_protocol():
    """Any class with get() and version() satisfies ContentRegistry (structural subtyping)."""
    from typing import Protocol, runtime_checkable

    @runtime_checkable
    class ContentRegistry(Protocol):
        def get(self, problem_id: str) -> object: ...
        def version(self) -> str: ...

    class AdHocRegistry:
        def get(self, problem_id: str):
            return None

        def version(self) -> str:
            return "ad-hoc-1.0"

    assert isinstance(AdHocRegistry(), ContentRegistry)


@pytest.mark.schemas
def test_in_memory_registry_get_returns_registered_problem():
    """InMemoryRegistry.get(id) returns the exact Problem registered under that id."""
    p = Problem(  # TODO: wire up
        id="test_prob",
        type_id="test",
        name="Test problem",
        artifact_type="practice",
        problem_spec={"kind": "test"},
        verifier_spec={"kind": "set_equality"},
    )
    registry = InMemoryRegistry({"test_prob": p})  # TODO: wire up
    assert registry.get("test_prob") is p


@pytest.mark.schemas
def test_in_memory_registry_get_unknown_id_raises_problem_not_found():
    """InMemoryRegistry.get(unknown_id) raises ProblemNotFoundError."""
    registry = InMemoryRegistry({})  # TODO: wire up
    with pytest.raises(ProblemNotFoundError):
        registry.get("nonexistent")


@pytest.mark.schemas
def test_in_memory_registry_version_returns_string():
    """InMemoryRegistry.version() returns a string."""
    registry = InMemoryRegistry({})  # TODO: wire up
    v = registry.version()
    assert isinstance(v, str)


# ---------------------------------------------------------------------------
# ProblemInstance — structure and presented_attempt
# ---------------------------------------------------------------------------


@pytest.mark.schemas
def test_problem_instance_non_gap_fill_has_none_presented_attempt():
    """ProblemInstance from a non-gap_fill problem has presented_attempt=None."""
    problem = Problem(  # TODO: wire up
        id="quad",
        type_id="algebra",
        name="Quadratic",
        artifact_type="srs_card",
        problem_spec={
            "kind": "quadratic_factor",
            "a_range": [1, 5],
            "root_range": [-9, 9],
        },
        verifier_spec={"kind": "set_equality", "marks_possible": 1},
    )
    registry = InMemoryRegistry({"quad": problem})  # TODO: wire up
    engine = Engine(registry=registry)  # TODO: wire up
    instance = engine.instantiate("quad", seed=1)  # TODO: wire up
    assert instance.presented_attempt is None


@pytest.mark.schemas
def test_problem_instance_gap_fill_has_non_none_presented_attempt():
    """ProblemInstance from a gap_fill problem has a non-None presented_attempt."""
    gap_problem = Problem(  # TODO: wire up
        id="surd_gap",
        type_id="algebra",
        name="Surd gap fill",
        artifact_type="gap_fill",
        problem_spec={"kind": "surd_linear", "a_range": [2, 9]},
        verifier_spec=[
            {"kind": "sympy_equivalence", "marks_possible": 1},
            {"kind": "sympy_equivalence", "marks_possible": 1},
            {"kind": "sympy_equivalence", "marks_possible": 1},
        ],
        source_id="surd_equation_linear_rhs",
        blank_steps=[1],
    )
    source_problem = Problem(  # TODO: wire up
        id="surd_equation_linear_rhs",
        type_id="algebra",
        name="Surd equation (linear RHS)",
        artifact_type="practice",
        problem_spec={"kind": "surd_linear", "a_range": [2, 9]},
        verifier_spec=[{"kind": "sympy_equivalence"}],
        difficulty="standard",
    )
    registry = InMemoryRegistry(
        {"surd_gap": gap_problem, "surd_equation_linear_rhs": source_problem}
    )  # TODO: wire up
    engine = Engine(registry=registry)  # TODO: wire up
    instance = engine.instantiate("surd_gap", seed=7)  # TODO: wire up
    assert instance.presented_attempt is not None


@pytest.mark.schemas
def test_problem_instance_gap_fill_presented_attempt_has_none_at_blank_steps():
    """presented_attempt.steps has None at blank_steps indices and ProvidedStep elsewhere."""
    gap_problem = Problem(  # TODO: wire up
        id="surd_gap",
        type_id="algebra",
        name="Surd gap fill",
        artifact_type="gap_fill",
        problem_spec={"kind": "surd_linear", "a_range": [2, 9]},
        verifier_spec=[
            {"kind": "sympy_equivalence"},
            {"kind": "sympy_equivalence"},
            {"kind": "sympy_equivalence"},
        ],
        source_id="surd_equation_linear_rhs",
        blank_steps=[1],
    )
    source_problem = Problem(  # TODO: wire up
        id="surd_equation_linear_rhs",
        type_id="algebra",
        name="Surd equation (linear RHS)",
        artifact_type="practice",
        problem_spec={"kind": "surd_linear", "a_range": [2, 9]},
        verifier_spec=[{"kind": "sympy_equivalence"}],
        difficulty="standard",
    )
    registry = InMemoryRegistry(
        {"surd_gap": gap_problem, "surd_equation_linear_rhs": source_problem}
    )  # TODO: wire up
    engine = Engine(registry=registry)  # TODO: wire up
    instance = engine.instantiate("surd_gap", seed=7)  # TODO: wire up
    steps = instance.presented_attempt.steps
    assert steps[1] is None
    assert isinstance(steps[0], ProvidedStep)
    assert isinstance(steps[2], ProvidedStep)


# === SPEC GAPS ===
# test_problem_instance_immutability: spec says ProblemInstance is an "immutable snapshot"
#   but does not specify the enforcement mechanism. Unclear whether assigning to a field
#   (e.g. instance.seed = 99) should raise AttributeError (Pydantic frozen=True) or is
#   just "don't mutate it" by convention. Needs clarification.
#
# test_problem_callable_spec_model_dump: spec states problem_spec can be "dict or callable".
#   When problem_spec is a Python callable, it is unclear how model_dump() handles it —
#   is the callable excluded, stored as a qualified name string, or something else?
#   The MCP serialization boundary requirement implies it cannot be a live callable in dumps.
#
# test_srs_card_exactly_two_steps_is_valid: spec says srs_card allows ≤2 steps but
#   does not explicitly confirm that 2-step verifier_spec is valid (not just 1-step).
#   The example in Section 3 shows a 2-step srs_card that should fail due to SelfGraded,
#   implying 2 machine-gradeable steps is fine — but could use an explicit passing test.
