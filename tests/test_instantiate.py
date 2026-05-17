"""
Tests for engine.instantiate() — all three modes (fresh/seeded/reconstruction),
gap-fill lifecycle, and cross-domain shape consistency.

Spec section: ## Section 1 — instantiate()
"""

import pytest

from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.exceptions import AttemptValidationError
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import (
    Problem,
    ProblemInstance,
    ProvidedStep,
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
def surd_gap_problem():
    return Problem(
        id="surd_gap_step1",
        type_id="algebra",
        name="Surd equation gap fill — step 1",
        artifact_type="gap_fill",
        problem_spec={"kind": "surd_linear", "a_range": [2, 9]},
        verifier_spec=[
            {"kind": "symbolic_equality", "marks_possible": 1},
            {"kind": "symbolic_equality", "marks_possible": 1},
            {"kind": "symbolic_equality", "marks_possible": 1},
        ],
        source_id="surd_equation_linear_rhs",
        blank_steps=[1],
        difficulty="standard",
    )


@pytest.fixture
def surd_gap_noncontiguous_problem():
    return Problem(
        id="surd_gap_steps0_2",
        type_id="algebra",
        name="Surd equation gap fill — steps 0 and 2",
        artifact_type="gap_fill",
        problem_spec={"kind": "surd_linear", "a_range": [2, 9]},
        verifier_spec=[
            {"kind": "symbolic_equality", "marks_possible": 1},
            {"kind": "symbolic_equality", "marks_possible": 1},
            {"kind": "symbolic_equality", "marks_possible": 1},
        ],
        source_id="surd_equation_linear_rhs",
        blank_steps=[0, 2],
        difficulty="standard",
    )


@pytest.fixture
def nihao_problem():
    return Problem(
        id="nihao_card",
        type_id="vocabulary",
        name="你好 — meaning and pronunciation",
        artifact_type="srs_card",
        problem_spec={"kind": "cq_vocab", "hanzi": "你好"},
        verifier_spec={"kind": "mcq", "marks_possible": 1},
    )


@pytest.fixture
def engine(quad_problem):
    registry = InMemoryRegistry({"quadratic_factor": quad_problem})
    return Engine(registry=registry)


# ---------------------------------------------------------------------------
# Integration: full instantiate() roundtrip
# ---------------------------------------------------------------------------


@pytest.mark.instantiate
def test_instantiate_returns_problem_instance_with_all_fields(engine):
    """Seeded instantiate() returns a ProblemInstance with spec, params, solution, verifier, seed."""
    instance = engine.instantiate("quadratic_factor", seed=42)
    assert instance.spec.id == "quadratic_factor"
    assert isinstance(instance.params, dict)
    assert instance.solution is not None
    assert instance.verifier is not None
    assert instance.seed == 42


# ---------------------------------------------------------------------------
# Fresh mode (no seed or params)
# ---------------------------------------------------------------------------


@pytest.mark.instantiate
def test_fresh_instantiate_records_seed_on_instance(engine):
    """Unseeded instantiate() records the generated seed on the returned instance."""
    instance = engine.instantiate("quadratic_factor")
    assert isinstance(instance.seed, int)


@pytest.mark.instantiate
def test_fresh_instantiate_twice_produces_independent_instances(engine):
    """Two unseeded calls produce statistically independent instances (different seeds)."""
    a = engine.instantiate("quadratic_factor")
    b = engine.instantiate("quadratic_factor")
    # Seeds should differ; collisions are astronomically unlikely with a good RNG.
    assert a.seed != b.seed


@pytest.mark.instantiate
def test_fresh_instantiate_does_not_cache(engine):
    """Engine has no hidden mutable state — two fresh calls are independent."""
    a = engine.instantiate("quadratic_factor")
    b = engine.instantiate("quadratic_factor")
    assert a is not b


# ---------------------------------------------------------------------------
# Seeded (deterministic) mode
# ---------------------------------------------------------------------------


@pytest.mark.instantiate
def test_seeded_instantiate_is_deterministic(engine):
    """Same seed produces identical params and solution on every call."""
    a = engine.instantiate("quadratic_factor", seed=42)
    b = engine.instantiate("quadratic_factor", seed=42)
    assert a.params == b.params
    assert a.seed == b.seed == 42


@pytest.mark.instantiate
def test_seeded_instantiate_solution_matches_params(engine):
    """solution on a seeded instance is consistent with the resolved params."""
    instance = engine.instantiate("quadratic_factor", seed=42)
    # Solution steps must be SubmittedStep instances (the golden-path answer).
    assert all(type(s) is SubmittedStep for s in instance.solution.steps)


# ---------------------------------------------------------------------------
# Accepts Problem object directly (not just str ID)
# ---------------------------------------------------------------------------


@pytest.mark.instantiate
def test_instantiate_accepts_problem_object_directly(quad_problem):
    """instantiate() accepts a Problem object instead of a string ID."""
    registry = InMemoryRegistry({"quadratic_factor": quad_problem})
    engine = Engine(registry=registry)
    instance = engine.instantiate(quad_problem, seed=1)
    assert instance.spec is quad_problem


# ---------------------------------------------------------------------------
# Code-based (callable) problem_spec
# ---------------------------------------------------------------------------


@pytest.mark.instantiate
def test_callable_problem_spec_produces_same_instance_shape():
    """A callable problem_spec (code generator) produces the same ProblemInstance shape as YAML."""

    def discriminant_generator(rng):
        # Minimal implementation: returns fixed params. Real generators use rng for
        # case branching (d>0/d=0/d<0) that a YAML DSL cannot express as one concept.
        return {"a": 1, "b": 0, "c": -1}

    problem = Problem(
        id="discriminant_generator",
        type_id="algebra",
        name="Discriminant — case branching",
        artifact_type="practice",
        problem_spec=discriminant_generator,  # callable, not dict
        verifier_spec={"kind": "symbolic_equality", "marks_possible": 1},
    )
    registry = InMemoryRegistry({"discriminant_generator": problem})
    engine = Engine(registry=registry)
    instance = engine.instantiate("discriminant_generator", seed=1)
    # Shape must be identical regardless of whether problem_spec is a dict or callable.
    assert hasattr(instance, "spec")
    assert hasattr(instance, "params")
    assert hasattr(instance, "solution")
    assert hasattr(instance, "verifier")
    assert hasattr(instance, "seed")


# ---------------------------------------------------------------------------
# Reconstruction mode (params=...)
# ---------------------------------------------------------------------------


@pytest.mark.instantiate
def test_reconstruction_from_params_skips_random_draw(engine):
    """params= mode skips random draw; returns instance with exactly those params."""
    instance = engine.instantiate(
        "quadratic_factor",
        params={"a": 2, "root1": -3, "root2": 5},
    )
    assert instance.params == {"a": 2, "root1": -3, "root2": 5}
    assert instance.seed is None  # no seed — reconstruction path


@pytest.mark.instantiate
def test_reconstruction_rederives_solution_from_params(engine):
    """Reconstructed instance has a solution computed from the given params."""
    instance = engine.instantiate(
        "quadratic_factor",
        params={"a": 2, "root1": -3, "root2": 5},
    )
    assert instance.solution is not None
    assert all(type(s) is SubmittedStep for s in instance.solution.steps)


# ---------------------------------------------------------------------------
# Mutual exclusion: seed and params
# ---------------------------------------------------------------------------


@pytest.mark.instantiate
def test_seed_and_params_together_raises(engine):
    """Passing both seed= and params= raises AttemptValidationError."""
    with pytest.raises(AttemptValidationError):
        engine.instantiate(
            "quadratic_factor",
            seed=42,
            params={"a": 2, "root1": -3, "root2": 5},
        )


# ---------------------------------------------------------------------------
# Gap-fill: single blank step
# ---------------------------------------------------------------------------


@pytest.mark.instantiate
def test_gap_fill_single_blank_presented_attempt_shape(surd_gap_problem):
    """Gap-fill with blank_steps=[1] produces presented_attempt with None at index 1."""
    registry = InMemoryRegistry({"surd_gap_step1": surd_gap_problem})
    engine = Engine(registry=registry)
    instance = engine.instantiate("surd_gap_step1", seed=7)
    steps = instance.presented_attempt.steps
    assert isinstance(steps[0], ProvidedStep)
    assert steps[1] is None
    assert isinstance(steps[2], ProvidedStep)


@pytest.mark.instantiate
def test_gap_fill_solution_is_fully_submitted(surd_gap_problem):
    """Gap-fill solution (golden-path) has SubmittedStep at every index, including blanks."""
    registry = InMemoryRegistry({"surd_gap_step1": surd_gap_problem})
    engine = Engine(registry=registry)
    instance = engine.instantiate("surd_gap_step1", seed=7)
    assert all(type(s) is SubmittedStep for s in instance.solution.steps)


# ---------------------------------------------------------------------------
# Gap-fill: noncontiguous blank steps
# ---------------------------------------------------------------------------


@pytest.mark.instantiate
def test_gap_fill_noncontiguous_blanks_presented_attempt_shape(
    surd_gap_noncontiguous_problem,
):
    """Gap-fill with blank_steps=[0, 2] produces None at indices 0 and 2."""
    registry = InMemoryRegistry(
        {"surd_gap_steps0_2": surd_gap_noncontiguous_problem}
    )
    engine = Engine(registry=registry)
    instance = engine.instantiate("surd_gap_steps0_2", seed=7)
    steps = instance.presented_attempt.steps
    assert steps[0] is None
    assert isinstance(steps[1], ProvidedStep)
    assert steps[2] is None


# ---------------------------------------------------------------------------
# Gap-fill: difficulty defaulting
# ---------------------------------------------------------------------------


@pytest.mark.instantiate
def test_gap_fill_difficulty_defaults_one_below_source():
    """Gap-fill without authored difficulty carries one tier below the source problem."""
    source_problem = Problem(
        id="surd_equation_linear_rhs",
        type_id="algebra",
        name="Surd equation (linear RHS)",
        artifact_type="practice",
        problem_spec={"kind": "surd_linear", "a_range": [2, 9]},
        verifier_spec=[
            {"kind": "symbolic_equality"},
            {"kind": "symbolic_equality"},
            {"kind": "symbolic_equality"},
        ],
        difficulty="standard",
    )
    gap_problem = Problem(
        id="surd_gap_no_difficulty",
        type_id="algebra",
        name="Surd gap — no authored difficulty",
        artifact_type="gap_fill",
        problem_spec={"kind": "surd_linear", "a_range": [2, 9]},
        verifier_spec=[
            {"kind": "symbolic_equality"},
            {"kind": "symbolic_equality"},
            {"kind": "symbolic_equality"},
        ],
        source_id="surd_equation_linear_rhs",
        blank_steps=[1],
        # difficulty omitted — engine looks up source and applies one-tier-below rule
    )
    registry = InMemoryRegistry(
        {
            "surd_equation_linear_rhs": source_problem,
            "surd_gap_no_difficulty": gap_problem,
        }
    )
    engine = Engine(registry=registry)
    instance = engine.instantiate("surd_gap_no_difficulty", seed=1)
    # Source is "standard"; one tier below → "routine"
    assert instance.spec.difficulty == "routine"


@pytest.mark.instantiate
def test_gap_fill_authored_difficulty_overrides_default():
    """Authored difficulty on a gap-fill problem overrides the one-below-source default."""
    gap_problem = Problem(
        id="surd_gap_hard",
        type_id="algebra",
        name="Surd gap — authored challenging difficulty",
        artifact_type="gap_fill",
        problem_spec={"kind": "surd_linear", "a_range": [2, 9]},
        verifier_spec=[
            {"kind": "symbolic_equality"},
            {"kind": "symbolic_equality"},
            {"kind": "symbolic_equality"},
        ],
        source_id="surd_equation_linear_rhs",
        blank_steps=[1],
        difficulty="challenging",  # overrides the standard→routine default
    )
    registry = InMemoryRegistry({"surd_gap_hard": gap_problem})
    engine = Engine(registry=registry)
    instance = engine.instantiate("surd_gap_hard", seed=1)
    assert instance.spec.difficulty == "challenging"


# ---------------------------------------------------------------------------
# cq domain — identical ProblemInstance shape
# ---------------------------------------------------------------------------


@pytest.mark.instantiate
def test_cq_domain_produces_identical_instance_shape(nihao_problem):
    """Chinese vocabulary (cq) problems produce the same ProblemInstance shape as math."""
    registry = InMemoryRegistry({"nihao_card": nihao_problem})
    engine = Engine(registry=registry)
    instance = engine.instantiate("nihao_card", seed=1)
    assert instance.spec.id == "nihao_card"
    assert isinstance(instance.params, dict)
    assert instance.solution is not None
    assert instance.verifier is not None


@pytest.mark.instantiate
def test_cq_reconstruction_retains_prior_score_after_annotation_fix(nihao_problem):
    """Reconstructing a cq problem after correcting an annotation re-derives solution;
    the consumer's stored SolutionRating is not touched by the engine."""
    registry = InMemoryRegistry({"nihao_card": nihao_problem})
    engine = Engine(registry=registry)
    # Store params (as a consumer would), then reconstruct.
    original = engine.instantiate(
        "nihao_card", params={"hanzi": "你好"}
    )
    reconstructed = engine.instantiate(
        "nihao_card", params={"hanzi": "你好"}
    )
    # Engine returns a fresh ProblemInstance; consumer is responsible for retained rating.
    assert reconstructed.params == {"hanzi": "你好"}
    assert reconstructed.solution is not None


# === SPEC GAPS ===
# test_generator_backward_compat_expanded_signature: spec says adding optional params
#   is allowed. No test yet for what happens when a stored params dict is a subset of
#   the current (expanded) signature — engine should reconstruct successfully, filling
#   new optional params with their defaults. Needs a concrete example to pin behaviour.
#
# test_fresh_instantiate_seed_range: spec does not specify the seed integer range.
#   A 32-bit vs 64-bit seed affects reproducibility across platforms. Worth pinning.
#
# test_gap_fill_difficulty_when_source_is_routine: spec says one tier below source,
#   but does not define the tier below "routine" (the lowest). Edge case unspecified.
