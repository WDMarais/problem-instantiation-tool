"""
Tests for the named exception hierarchy and all engine failure modes.

Spec section: ## Section 3 — Failure modes
"""

import pytest

from pydantic import ValidationError

from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.exceptions import (
    AttemptValidationError,
    InstantiationError,
    ParamsIncompatibleError,
    ProblemEngineError,
    ProblemNotFoundError,
)
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import (
    Problem,
    SolutionAttempt,
    SubmittedStep,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def quad_problem():
    return Problem(
        id="quadratic_factor",
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


@pytest.fixture
def engine(quad_problem):
    registry = InMemoryRegistry({"quadratic_factor": quad_problem})
    return Engine(registry=registry)


# ---------------------------------------------------------------------------
# Exception hierarchy — ProblemEngineError is the base catch-all
# ---------------------------------------------------------------------------


@pytest.mark.failure_modes
def test_problem_not_found_is_subclass_of_problem_engine_error():
    """ProblemNotFoundError inherits from ProblemEngineError."""
    assert issubclass(ProblemNotFoundError, ProblemEngineError)


@pytest.mark.failure_modes
def test_instantiation_error_is_subclass_of_problem_engine_error():
    """InstantiationError inherits from ProblemEngineError."""
    assert issubclass(InstantiationError, ProblemEngineError)


@pytest.mark.failure_modes
def test_params_incompatible_error_is_subclass_of_problem_engine_error():
    """ParamsIncompatibleError inherits from ProblemEngineError."""
    assert issubclass(ParamsIncompatibleError, ProblemEngineError)


@pytest.mark.failure_modes
def test_attempt_validation_error_is_subclass_of_problem_engine_error():
    """AttemptValidationError inherits from ProblemEngineError."""
    assert issubclass(AttemptValidationError, ProblemEngineError)


@pytest.mark.failure_modes
def test_problem_engine_error_catches_all_engine_failures(engine):
    """Catching ProblemEngineError is sufficient to catch any engine-level failure."""
    with pytest.raises(ProblemEngineError):
        engine.instantiate("nonexistent_id")


# ---------------------------------------------------------------------------
# ProblemNotFoundError
# ---------------------------------------------------------------------------


@pytest.mark.failure_modes
def test_unknown_id_raises_problem_not_found_error(engine):
    """instantiate() with an unknown ID raises ProblemNotFoundError."""
    with pytest.raises(ProblemNotFoundError) as exc_info:
        engine.instantiate("nonexistent_id")
    assert "nonexistent_id" in str(exc_info.value)


@pytest.mark.failure_modes
def test_problem_not_found_error_carries_problem_id(engine):
    """ProblemNotFoundError exposes the unknown problem_id."""
    with pytest.raises(ProblemNotFoundError) as exc_info:
        engine.instantiate("nonexistent_id")
    assert exc_info.value.problem_id == "nonexistent_id"


# ---------------------------------------------------------------------------
# InstantiationError
# ---------------------------------------------------------------------------


@pytest.mark.failure_modes
def test_overconstrained_generator_raises_instantiation_error():
    """A generator that raises internally is wrapped in InstantiationError."""

    def overconstrained(rng):
        raise ValueError("no valid discriminant found under constraints")

    problem = Problem(
        id="overconstrained_generator",
        type_id="algebra",
        name="Overconstrained",
        artifact_type="practice",
        problem_spec=overconstrained,
        verifier_spec={"kind": "sympy_equivalence", "marks_possible": 1},
    )
    registry = InMemoryRegistry({"overconstrained_generator": problem})
    engine = Engine(registry=registry)
    with pytest.raises(InstantiationError) as exc_info:
        engine.instantiate("overconstrained_generator", seed=1)
    assert exc_info.value.problem_id == "overconstrained_generator"
    assert exc_info.value.cause is not None  # wraps the underlying ValueError


# ---------------------------------------------------------------------------
# ParamsIncompatibleError
# ---------------------------------------------------------------------------


@pytest.mark.failure_modes
def test_renamed_param_raises_params_incompatible_error(engine):
    """Stored params with a renamed field raise ParamsIncompatibleError on reconstruction."""
    with pytest.raises(ParamsIncompatibleError) as exc_info:
        engine.instantiate(
            "quadratic_factor",
            params={"a": 2, "old_field": 5},  # "old_field" no longer in signature
        )
    assert exc_info.value.problem_id == "quadratic_factor"
    assert "old_field" in str(exc_info.value.stored_params)
    assert exc_info.value.current_signature == {"a", "root1", "root2"}


@pytest.mark.failure_modes
def test_params_incompatible_error_does_not_silently_fall_back(engine):
    """Engine raises, never silently falls back to a fresh instantiation on param mismatch."""
    # Verify the error is raised, not swallowed.
    raised = False
    try:
        engine.instantiate(
            "quadratic_factor",
            params={"a": 2, "old_field": 5},
        )
    except ParamsIncompatibleError:
        raised = True
    assert raised, "expected ParamsIncompatibleError, got quiet success"


# ---------------------------------------------------------------------------
# AttemptValidationError — wrong type at a step
# ---------------------------------------------------------------------------


@pytest.mark.failure_modes
def test_self_graded_non_bool_raises_attempt_validation_error(quad_problem):
    """SelfGraded verifier receiving a non-bool raises AttemptValidationError."""
    problem = Problem(
        id="sg_problem",
        type_id="algebra",
        name="Self-graded",
        artifact_type="worked_example",
        problem_spec={"kind": "fixed", "expression": "x^2"},
        verifier_spec={"kind": "self_graded", "marks_possible": 1},
    )
    registry = InMemoryRegistry({"sg_problem": problem})
    engine = Engine(registry=registry)
    instance = engine.instantiate("sg_problem", seed=1)
    attempt = SolutionAttempt(steps=[SubmittedStep("not_a_bool")])
    with pytest.raises(AttemptValidationError) as exc_info:
        instance.verifier.rate(attempt)
    assert exc_info.value.step_index == 0
    assert "bool" in exc_info.value.reason.lower()


# ---------------------------------------------------------------------------
# ValidationError at construction — authoring errors surface immediately
# ---------------------------------------------------------------------------


@pytest.mark.failure_modes
def test_srs_card_with_self_graded_verifier_raises_validation_error_at_construction():
    """srs_card + SelfGraded raises ValidationError at Problem() construction, not at instantiate().

    This is the exact example from spec Section 3. The error must surface at construction
    so authoring mistakes are caught immediately, not deferred to runtime.
    """
    with pytest.raises(ValidationError):
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


# === SPEC GAPS ===
# test_instantiation_error_cause_type: spec says InstantiationError wraps the
#   underlying exception as `cause`, but does not specify whether this is stored
#   as __cause__ (PEP 3134 chaining) or as an explicit .cause attribute. Both
#   are tested above; implementation should pick one and the test should be tightened.
#
# test_params_incompatible_current_signature_type: spec shows current_signature as
#   a set ({"a", "root1", "root2"}) but does not specify whether it reflects the
#   full signature or only the required params. Optional params with defaults are
#   ambiguous — are they in current_signature or not?
#
# test_empty_registry_error: spec does not specify what happens if the registry
#   itself raises during get() (network error, file not found, etc.). Should this
#   surface as ProblemNotFoundError, InstantiationError, or propagate as-is?
