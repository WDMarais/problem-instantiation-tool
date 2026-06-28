"""
Tests for the named exception hierarchy and all engine failure modes.

Spec section: ## Section 3 — Failure modes
"""

import pytest
from pydantic import ValidationError

from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.exceptions import (
    AttemptValidationError,
    CanonicalResolutionError,
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
        verifier_spec={"kind": "symbolic_equality", "marks_possible": 1},
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
    """Stored params with a renamed field raise ParamsIncompatibleError
    on reconstruction."""
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
    """Engine raises, never silently falls back to a fresh instantiation
    on param mismatch."""
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
    """srs_card + SelfGraded raises ValidationError at Problem() construction,
    not at instantiate().

    This is the exact example from spec Section 3. The error must surface at
    construction so authoring mistakes are caught immediately, not deferred to
    runtime.
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


# ---------------------------------------------------------------------------
# CanonicalResolutionError — the verifier refuses to guess a canonical
# ---------------------------------------------------------------------------
#
# These mirror main.py's smoke-test gap markers as proper pytest cases: when a
# verifier step cannot resolve its canonical answer (no param_key, no answer key,
# ambiguous params) the engine must raise at instantiate, never silently pick an
# arbitrary param.


def _instantiate(problem_spec, verifier_spec, seed=1):
    problem = Problem(
        id="p",
        type_id="algebra",
        name="p",
        artifact_type="practice",
        problem_spec=problem_spec,
        verifier_spec=verifier_spec,
    )
    engine = Engine(registry=InMemoryRegistry({"p": problem}))
    return engine.instantiate("p", seed=seed)


@pytest.mark.failure_modes
def test_canonical_resolution_error_is_subclass_of_problem_engine_error():
    """CanonicalResolutionError inherits from ProblemEngineError."""
    assert issubclass(CanonicalResolutionError, ProblemEngineError)


@pytest.mark.failure_modes
def test_ambiguous_symbolic_canonical_raises():
    """symbolic_equality with several params and no 'answer'/param_key cannot pick
    a canonical and must raise rather than guess the first param."""
    with pytest.raises(CanonicalResolutionError):
        _instantiate(
            {"kind": "x", "a_range": [1, 9], "b_range": [1, 9]},
            {"kind": "symbolic_equality", "marks_possible": 1},
        )


@pytest.mark.failure_modes
def test_ambiguous_numeric_canonical_raises():
    """numeric_equality resolves via 'answer' like the symbolic path; ambiguous
    params raise."""
    with pytest.raises(CanonicalResolutionError):
        _instantiate(
            {"kind": "x", "a_range": [1, 9], "b_range": [1, 9]},
            {"kind": "numeric_equality", "tolerance": 0.01, "marks_possible": 1},
        )


@pytest.mark.failure_modes
def test_ambiguous_set_equality_canonical_raises():
    """set_equality with no root* params must not sweep every field into the
    answer set — it raises instead."""
    with pytest.raises(CanonicalResolutionError):
        _instantiate(
            {"kind": "x", "a_range": [1, 9], "b_range": [1, 9]},
            {"kind": "set_equality", "marks_possible": 1},
        )


@pytest.mark.failure_modes
def test_missing_param_key_raises():
    """A param_key the generator never produced raises (no silent default to 0)."""
    with pytest.raises(CanonicalResolutionError):
        _instantiate(
            {"kind": "x", "a_range": [1, 9]},
            {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "answer"},
        )


@pytest.mark.failure_modes
def test_canonical_resolution_error_carries_kind_and_keys():
    """The exception names the verifier kind and the params it had to choose from,
    so the authoring fix is obvious."""
    with pytest.raises(CanonicalResolutionError) as exc_info:
        _instantiate(
            {"kind": "x", "a_range": [1, 9], "b_range": [1, 9]},
            {"kind": "symbolic_equality", "marks_possible": 1},
        )
    assert exc_info.value.kind == "symbolic_equality"
    assert set(exc_info.value.available_keys) == {"a", "b"}


@pytest.mark.failure_modes
def test_sole_param_is_unambiguous_and_does_not_raise():
    """A single generated param is the answer by elimination — kept as a
    convenience, so this must NOT raise."""
    inst = _instantiate(
        {"kind": "x", "a_range": [3, 3]},  # sole param a == 3
        {"kind": "symbolic_equality", "marks_possible": 1},
    )
    assert inst.verifier.canonicals == [3]


@pytest.mark.failure_modes
def test_explicit_answer_param_does_not_raise():
    """An explicit 'answer' param resolves the canonical even amid other fields."""
    inst = _instantiate(
        {"kind": "x", "a_range": [1, 9], "answer": 7},
        {"kind": "symbolic_equality", "marks_possible": 1},
    )
    assert inst.verifier.canonicals == [7]


@pytest.mark.failure_modes
def test_root_params_resolve_set_equality_without_raising():
    """The root* convention resolves set_equality even with extra fields present."""
    inst = _instantiate(
        {"kind": "x", "root_range": [-9, 9], "leading_coeff_range": [1, 3]},
        {"kind": "set_equality", "marks_possible": 1},
    )
    (canonical,) = inst.verifier.canonicals
    assert isinstance(canonical, frozenset)
    assert "leading_coeff" not in canonical  # extra field excluded from the set


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
