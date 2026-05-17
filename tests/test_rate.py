"""
Tests for verifier.rate() — all mistake_type cases, CA marking, partial attempts,
gap-fill skipping, and each StepVerifier type.

Spec section: ## Section 2 — verifier.rate()
"""

import pytest

# Stubs — one block for all unimplemented production imports.
# As each module is implemented: move its imports above this block as bare imports,
# delete the corresponding stub classes from the except clause.
# When the except clause is empty, delete the whole try/except.
try:
    from problem_instantiation_tool.schemas import (
        Problem,
        SolutionAttempt,
        SolutionRating,
        StepRating,
        ProvidedStep,
        SubmittedStep,
        ValidationMode,
    )
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.exceptions import AttemptValidationError
except ImportError:

    class Problem:
        def __init__(self, **kwargs):
            raise NotImplementedError

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

    class ValidationMode:
        LENIENT = "lenient"
        STRICT = "strict"

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

    class AttemptValidationError(Exception):
        def __init__(self, step_index, reason=""):
            super().__init__(step_index, reason)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def srs_instance():
    """1-step SRS card: set_equality verifier. Canonical roots: {-3, 5}."""
    problem = Problem(  # TODO: wire up
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
    registry = InMemoryRegistry({"quadratic_factor": problem})  # TODO: wire up
    engine = Engine(registry=registry)  # TODO: wire up
    # Use reconstruction so canonical answer is deterministic in tests.
    return engine.instantiate(  # TODO: wire up
        "quadratic_factor",
        params={"a": 1, "root1": -3, "root2": 5},
    )


@pytest.fixture
def two_step_ca_instance():
    """2-step problem: step0=a, step1=2*a. Canonical: a=5, x=10."""
    problem = Problem(  # TODO: wire up
        id="two_step_linear",
        type_id="algebra",
        name="Find a, then x=2a",
        artifact_type="practice",
        problem_spec={"kind": "fixed", "a": 5},
        verifier_spec=[
            {"kind": "sympy_equivalence", "marks_possible": 1},
            {
                "kind": "sympy_equivalence",
                "marks_possible": 1,
                "depends_on": [0],
                "symbolic_expr": "2 * step0_result",
            },
        ],
        problem_structure={
            "kind": "sequential",
            "steps": [{"role": "find_a"}, {"role": "find_x"}],
        },
    )
    registry = InMemoryRegistry({"two_step_linear": problem})  # TODO: wire up
    engine = Engine(registry=registry)  # TODO: wire up
    return engine.instantiate("two_step_linear", params={"a": 5})  # TODO: wire up


@pytest.fixture
def mcq_instance():
    """MCQ verifier: canonical answer is choice key 'B'."""
    problem = Problem(  # TODO: wire up
        id="mcq_geo",
        type_id="geography",
        name="Capital of France",
        artifact_type="srs_card",
        problem_spec={
            "kind": "mcq_fixed",
            "choices": {"A": "Berlin", "B": "Paris", "C": "Rome", "D": "Madrid"},
            "correct": "B",
        },
        verifier_spec={"kind": "mcq", "marks_possible": 1},
    )
    registry = InMemoryRegistry({"mcq_geo": problem})  # TODO: wire up
    engine = Engine(registry=registry)  # TODO: wire up
    return engine.instantiate("mcq_geo", params={"correct": "B"})  # TODO: wire up


@pytest.fixture
def exact_match_geo_instance():
    """ExactMatch verifier: canonical answer is 'Tanzania' (case-insensitive by default)."""
    problem = Problem(  # TODO: wire up
        id="country_flag",
        type_id="geography",
        name="Name the country",
        artifact_type="srs_card",
        problem_spec={"kind": "fixed_answer", "answer": "Tanzania"},
        verifier_spec={"kind": "exact_match", "marks_possible": 1},
    )
    registry = InMemoryRegistry({"country_flag": problem})  # TODO: wire up
    engine = Engine(registry=registry)  # TODO: wire up
    return engine.instantiate(
        "country_flag", params={"answer": "Tanzania"}
    )  # TODO: wire up


@pytest.fixture
def exact_match_pinyin_instance():
    """ExactMatch with accents normalization: canonical 'nǐ hǎo', normalize=[accents]."""
    problem = Problem(  # TODO: wire up
        id="pinyin_nihao",
        type_id="vocabulary",
        name="Pinyin for 你好",
        artifact_type="srs_card",
        problem_spec={"kind": "fixed_answer", "answer": "nǐ hǎo"},
        verifier_spec={
            "kind": "exact_match",
            "marks_possible": 1,
            "normalize": ["accents"],
        },
    )
    registry = InMemoryRegistry({"pinyin_nihao": problem})  # TODO: wire up
    engine = Engine(registry=registry)  # TODO: wire up
    return engine.instantiate(
        "pinyin_nihao", params={"answer": "nǐ hǎo"}
    )  # TODO: wire up


@pytest.fixture
def self_graded_instance():
    """SelfGraded verifier: student submits bool."""
    problem = Problem(  # TODO: wire up
        id="worked_example_check",
        type_id="algebra",
        name="Check your worked example",
        artifact_type="worked_example",
        problem_spec={"kind": "fixed", "expression": "x^2 - 4"},
        verifier_spec={"kind": "self_graded", "marks_possible": 2},
    )
    registry = InMemoryRegistry({"worked_example_check": problem})  # TODO: wire up
    engine = Engine(registry=registry)  # TODO: wire up
    return engine.instantiate("worked_example_check", seed=1)  # TODO: wire up


@pytest.fixture
def gap_fill_instance():
    """Gap-fill with blank at step 1: [ProvidedStep, blank, ProvidedStep]. Canonical: s0, s1, s2."""
    problem = Problem(  # TODO: wire up
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
    registry = InMemoryRegistry({"surd_gap": problem})  # TODO: wire up
    engine = Engine(registry=registry)  # TODO: wire up
    return engine.instantiate("surd_gap", params={"a": 3})  # TODO: wire up


@pytest.fixture
def ca_gap_noncontiguous_instance():
    """3-step CA gap-fill with blank_steps=[0, 2]. Step 2 CA-depends on step 1 (provided).

    Canonical: a=5, step1=2*a=10, step2=step1+5=15.
    """
    problem = Problem(  # TODO: wire up
        id="three_step_ca_gap",
        type_id="algebra",
        name="Three-step chain, noncontiguous blanks",
        artifact_type="gap_fill",
        problem_spec={"kind": "fixed", "a": 5},
        verifier_spec=[
            {"kind": "sympy_equivalence", "marks_possible": 1},
            {
                "kind": "sympy_equivalence",
                "marks_possible": 1,
                "depends_on": [0],
                "symbolic_expr": "2 * step0_result",
            },
            {
                "kind": "sympy_equivalence",
                "marks_possible": 1,
                "depends_on": [1],
                "symbolic_expr": "step1_result + 5",
            },
        ],
        problem_structure={
            "kind": "sequential",
            "steps": [
                {"role": "find_a"},
                {"role": "find_2a"},
                {"role": "find_2a_plus_5"},
            ],
        },
        source_id="three_step_chain",
        blank_steps=[0, 2],
    )
    registry = InMemoryRegistry({"three_step_ca_gap": problem})  # TODO: wire up
    engine = Engine(registry=registry)  # TODO: wire up
    return engine.instantiate("three_step_ca_gap", params={"a": 5})  # TODO: wire up


@pytest.fixture
def high_marks_instance():
    """SymPyEquivalence verifier with marks_possible=2 (insight step)."""
    problem = Problem(  # TODO: wire up
        id="circle_insight",
        type_id="geometry",
        name="Circle area derivation",
        artifact_type="practice",
        problem_spec={"kind": "fixed", "radius": 1},
        verifier_spec={"kind": "sympy_equivalence", "marks_possible": 2},
    )
    registry = InMemoryRegistry({"circle_insight": problem})  # TODO: wire up
    engine = Engine(registry=registry)  # TODO: wire up
    return engine.instantiate("circle_insight", params={"radius": 1})  # TODO: wire up


# ---------------------------------------------------------------------------
# Integration: instantiate then rate
# ---------------------------------------------------------------------------


@pytest.mark.rate
def test_rate_correct_answer_returns_full_solution_rating(srs_instance):
    """Correct answer on 1-step SRS card returns SolutionRating with is_correct=True."""
    attempt = SolutionAttempt(
        steps=[SubmittedStep({"roots": {-3, 5}})]
    )  # TODO: wire up
    rating = srs_instance.verifier.rate(attempt)  # TODO: wire up
    assert isinstance(rating, SolutionRating)
    assert rating.is_correct is True
    assert rating.marks_awarded == 1
    assert rating.marks_possible == 1


# ---------------------------------------------------------------------------
# 1-step: correct and computation_error
# ---------------------------------------------------------------------------


@pytest.mark.rate
def test_one_step_correct(srs_instance):
    """Correct 1-step attempt: mistake_type=correct, marks_awarded=1."""
    attempt = SolutionAttempt(
        steps=[SubmittedStep({"roots": {-3, 5}})]
    )  # TODO: wire up
    rating = srs_instance.verifier.rate(attempt)  # TODO: wire up
    step = rating.steps[0]
    assert step.index == 0
    assert step.mistake_type == "correct"
    assert step.marks_awarded == 1
    assert step.marks_possible == 1
    assert step.verifier_type == "set_equality"


@pytest.mark.rate
def test_one_step_wrong_is_computation_error(srs_instance):
    """Wrong 1-step attempt (no prior steps): mistake_type=computation_error."""
    attempt = SolutionAttempt(
        steps=[SubmittedStep({"roots": {-3, 4}})]
    )  # TODO: wire up
    rating = srs_instance.verifier.rate(attempt)  # TODO: wire up
    step = rating.steps[0]
    assert step.mistake_type == "computation_error"
    assert step.marks_awarded == 0
    assert rating.is_correct is False


# ---------------------------------------------------------------------------
# 2-step CA marking: ca_correct
# ---------------------------------------------------------------------------


@pytest.mark.rate
def test_two_step_ca_correct(two_step_ca_instance):
    """Step 0 wrong → computation_error; step 1 correct given student's step 0 → ca_correct.

    Canonical: a=5, x=2a=10.
    Student:   a=10, x=20  (wrong a, but x=2×their_a correctly applied).
    """
    attempt = SolutionAttempt(
        steps=[SubmittedStep(10), SubmittedStep(20)]
    )  # TODO: wire up
    rating = two_step_ca_instance.verifier.rate(attempt)  # TODO: wire up

    assert rating.steps[0].mistake_type == "computation_error"
    assert rating.steps[0].marks_awarded == 0

    assert rating.steps[1].mistake_type == "ca_correct"
    assert rating.steps[1].marks_awarded == 1

    assert rating.marks_awarded == 1
    assert rating.marks_possible == 2
    assert rating.is_correct is False


# ---------------------------------------------------------------------------
# 2-step CA marking: coincidental canonical match (lenient and strict)
# ---------------------------------------------------------------------------


@pytest.mark.rate
def test_two_step_coincidental_match_lenient_is_correct(two_step_ca_instance):
    """Coincidental canonical match in LENIENT mode (default) → correct.

    Canonical: a=5, x=2a=10.  Student: a=10, x=10.
    Student x=10 matches canonical(10) but not ca_canonical(20).
    LENIENT: a correct answer is correct regardless of path taken.
    """
    attempt = SolutionAttempt(
        steps=[SubmittedStep(10), SubmittedStep(10)]
    )  # TODO: wire up
    rating = two_step_ca_instance.verifier.rate(attempt)  # TODO: wire up

    assert rating.steps[0].mistake_type == "computation_error"
    assert rating.steps[1].mistake_type == "correct"
    assert rating.steps[1].marks_awarded == 1


@pytest.mark.rate
def test_two_step_coincidental_match_strict_is_semantic_error(two_step_ca_instance):
    """Coincidental canonical match in STRICT mode → semantic_error.

    Canonical: a=5, x=2a=10.  Student: a=10, x=10.
    Student x=10 matches canonical(10) but not ca_canonical(20).
    STRICT: coincidental match signals student did not apply method to their own prior value.
    """
    attempt = SolutionAttempt(
        steps=[SubmittedStep(10), SubmittedStep(10)]
    )  # TODO: wire up
    rating = two_step_ca_instance.verifier.rate(
        attempt, validation_mode=ValidationMode.STRICT
    )  # TODO: wire up

    assert rating.steps[0].mistake_type == "computation_error"
    assert rating.steps[1].mistake_type == "semantic_error"
    assert rating.steps[1].marks_awarded == 0
    assert rating.is_correct is False


# ---------------------------------------------------------------------------
# 2-step CA marking: genuine semantic_error (both modes agree)
# ---------------------------------------------------------------------------


@pytest.mark.rate
def test_two_step_genuine_semantic_error(two_step_ca_instance):
    """Genuine semantic_error: wrong vs canonical AND wrong vs CA-canonical. Both modes agree.

    Canonical: a=5, x=2a=10.  Student: a=10, x=7.
    Student x=7 ≠ canonical(10) and ≠ ca_canonical(20) → semantic_error in both modes.
    """
    attempt = SolutionAttempt(
        steps=[SubmittedStep(10), SubmittedStep(7)]
    )  # TODO: wire up
    rating = two_step_ca_instance.verifier.rate(attempt)  # TODO: wire up

    assert rating.steps[0].mistake_type == "computation_error"
    assert rating.steps[1].mistake_type == "semantic_error"
    assert rating.steps[1].marks_awarded == 0
    assert rating.marks_awarded == 0
    assert rating.is_correct is False


# ---------------------------------------------------------------------------
# Partial attempt: marks_possible covers submitted steps only
# ---------------------------------------------------------------------------


@pytest.mark.rate
def test_partial_attempt_marks_possible_covers_submitted_only(two_step_ca_instance):
    """Submitting only step 0 of a 2-step problem: marks_possible=1, not 2."""
    # Canonical a=5; student submits correct a=5 for step 0 only.
    attempt = SolutionAttempt(steps=[SubmittedStep(5)])  # TODO: wire up
    rating = two_step_ca_instance.verifier.rate(attempt)  # TODO: wire up
    assert rating.marks_possible == 1
    assert rating.marks_awarded == 1
    assert rating.is_correct is True  # vacuously correct over submitted steps


# ---------------------------------------------------------------------------
# Gap-fill: ProvidedStep skipped, only SubmittedStep at blank index marked
# ---------------------------------------------------------------------------


@pytest.mark.rate
def test_gap_fill_provided_steps_skipped_in_marking(gap_fill_instance):
    """ProvidedSteps pass through unmarked; only SubmittedStep at blank index is rated."""
    # Blank is at index 1. Student fills it with the canonical step 1 value.
    canonical_s1 = gap_fill_instance.solution.steps[1].value  # TODO: wire up
    s0_value = gap_fill_instance.presented_attempt.steps[0].value  # TODO: wire up
    s2_value = gap_fill_instance.presented_attempt.steps[2].value  # TODO: wire up

    attempt = SolutionAttempt(  # TODO: wire up
        steps=[
            ProvidedStep(s0_value),
            SubmittedStep(canonical_s1),
            ProvidedStep(s2_value),
        ]
    )
    rating = gap_fill_instance.verifier.rate(attempt)  # TODO: wire up

    # Only step 1 should appear in rating (ProvidedSteps skipped).
    assert len(rating.steps) == 1
    assert rating.steps[0].index == 1
    assert rating.steps[0].mistake_type == "correct"
    assert rating.marks_possible == 1


# ---------------------------------------------------------------------------
# Gap-fill CA chain: ProvidedStep resets CA to canonical
# ---------------------------------------------------------------------------


@pytest.mark.rate
def test_provided_step_breaks_ca_chain_in_noncontiguous_gap_fill(
    ca_gap_noncontiguous_instance,
):
    """ProvidedStep at step 1 resets the CA chain to canonical; student's wrong step 0
    does not propagate into the CA evaluation for step 2.

    Canonical: a=5, step1=10, step2=15.
    Student submits: step0=8 (wrong), step2=21.

    Without reset: step2 ca_canonical = 2*8+5 = 21 → student=21 is ca_correct.
    With reset:    ProvidedStep(10) breaks chain; step2 ca_canonical = 10+5 = 15.
                   Student step2=21 ≠ 15 → computation_error (not ca_correct).
    """
    provided_s1 = ca_gap_noncontiguous_instance.presented_attempt.steps[
        1
    ].value  # TODO: wire up

    attempt = SolutionAttempt(  # TODO: wire up
        steps=[
            SubmittedStep(8),  # wrong: canonical a=5
            ProvidedStep(provided_s1),  # canonical step1=10 breaks CA chain
            SubmittedStep(21),  # ca_correct WITHOUT reset, computation_error WITH reset
        ]
    )
    rating = ca_gap_noncontiguous_instance.verifier.rate(attempt)  # TODO: wire up

    assert len(rating.steps) == 2  # only the two SubmittedSteps are rated
    assert rating.steps[0].index == 0
    assert rating.steps[0].mistake_type == "computation_error"
    assert rating.steps[1].index == 2
    # Chain was reset by ProvidedStep(10): ca_canonical = 10+5 = 15, not 21.
    assert rating.steps[1].mistake_type == "computation_error"


# ---------------------------------------------------------------------------
# None in submitted attempt → AttemptValidationError
# ---------------------------------------------------------------------------


@pytest.mark.rate
def test_none_step_in_rate_raises_attempt_validation_error(srs_instance):
    """None at a step position in a submitted attempt raises AttemptValidationError."""
    attempt = SolutionAttempt(steps=[None])  # TODO: wire up
    with pytest.raises(AttemptValidationError) as exc_info:
        srs_instance.verifier.rate(attempt)  # TODO: wire up
    assert exc_info.value.step_index == 0


# ---------------------------------------------------------------------------
# High mark weight
# ---------------------------------------------------------------------------


@pytest.mark.rate
def test_high_marks_possible_awarded_in_full_on_correct(high_marks_instance):
    """Verifier with marks_possible=2 awards 2 marks on a correct answer."""
    canonical_value = high_marks_instance.solution.steps[0].value  # TODO: wire up
    attempt = SolutionAttempt(steps=[SubmittedStep(canonical_value)])  # TODO: wire up
    rating = high_marks_instance.verifier.rate(attempt)  # TODO: wire up
    assert rating.steps[0].marks_possible == 2
    assert rating.steps[0].marks_awarded == 2
    assert rating.marks_awarded == 2
    assert rating.is_correct is True


# ---------------------------------------------------------------------------
# MCQ verifier
# ---------------------------------------------------------------------------


@pytest.mark.rate
def test_mcq_correct_choice(mcq_instance):
    """Correct MCQ choice: mistake_type=correct, verifier_type='mcq'."""
    attempt = SolutionAttempt(steps=[SubmittedStep("B")])  # TODO: wire up
    rating = mcq_instance.verifier.rate(attempt)  # TODO: wire up
    assert rating.steps[0].mistake_type == "correct"
    assert rating.steps[0].verifier_type == "mcq"
    assert rating.is_correct is True


@pytest.mark.rate
def test_mcq_wrong_choice(mcq_instance):
    """Wrong MCQ choice: mistake_type=computation_error, marks_awarded=0."""
    attempt = SolutionAttempt(steps=[SubmittedStep("A")])  # TODO: wire up
    rating = mcq_instance.verifier.rate(attempt)  # TODO: wire up
    assert rating.steps[0].mistake_type == "computation_error"
    assert rating.steps[0].marks_awarded == 0
    assert rating.is_correct is False


# ---------------------------------------------------------------------------
# ExactMatch verifier
# ---------------------------------------------------------------------------


@pytest.mark.rate
def test_exact_match_correct_casing(exact_match_geo_instance):
    """Exact case match: 'Tanzania' → correct."""
    attempt = SolutionAttempt(steps=[SubmittedStep("Tanzania")])  # TODO: wire up
    rating = exact_match_geo_instance.verifier.rate(attempt)  # TODO: wire up
    assert rating.steps[0].mistake_type == "correct"
    assert rating.steps[0].verifier_type == "exact_match"


@pytest.mark.rate
def test_exact_match_case_insensitive_by_default(exact_match_geo_instance):
    """Lowercase submission 'tanzania' matches canonical 'Tanzania' (case-insensitive always on)."""
    attempt = SolutionAttempt(steps=[SubmittedStep("tanzania")])  # TODO: wire up
    rating = exact_match_geo_instance.verifier.rate(attempt)  # TODO: wire up
    assert rating.steps[0].mistake_type == "correct"


@pytest.mark.rate
def test_exact_match_wrong_answer(exact_match_geo_instance):
    """Wrong ExactMatch answer: mistake_type=computation_error, marks_awarded=0."""
    attempt = SolutionAttempt(steps=[SubmittedStep("Zambia")])  # TODO: wire up
    rating = exact_match_geo_instance.verifier.rate(attempt)  # TODO: wire up
    assert rating.steps[0].mistake_type == "computation_error"
    assert rating.steps[0].marks_awarded == 0


@pytest.mark.rate
def test_exact_match_accent_normalisation(exact_match_pinyin_instance):
    """'ni hao' (no tone marks) normalises to match 'nǐ hǎo' when normalize includes accents."""
    attempt = SolutionAttempt(steps=[SubmittedStep("ni hao")])  # TODO: wire up
    rating = exact_match_pinyin_instance.verifier.rate(attempt)  # TODO: wire up
    assert rating.steps[0].mistake_type == "correct"


# ---------------------------------------------------------------------------
# SelfGraded verifier
# ---------------------------------------------------------------------------


@pytest.mark.rate
def test_self_graded_true_is_correct(self_graded_instance):
    """SelfGraded True: mistake_type=correct, marks_awarded=marks_possible."""
    attempt = SolutionAttempt(steps=[SubmittedStep(True)])  # TODO: wire up
    rating = self_graded_instance.verifier.rate(attempt)  # TODO: wire up
    assert rating.steps[0].mistake_type == "correct"
    assert rating.steps[0].marks_awarded == rating.steps[0].marks_possible
    assert rating.steps[0].verifier_type == "self_graded"


@pytest.mark.rate
def test_self_graded_false_is_not_correct(self_graded_instance):
    """SelfGraded False: marks_awarded=0, is_correct=False."""
    attempt = SolutionAttempt(steps=[SubmittedStep(False)])  # TODO: wire up
    rating = self_graded_instance.verifier.rate(attempt)  # TODO: wire up
    assert rating.steps[0].marks_awarded == 0
    assert rating.is_correct is False


@pytest.mark.rate
def test_self_graded_non_bool_raises_attempt_validation_error(self_graded_instance):
    """SelfGraded with a non-bool submission raises AttemptValidationError."""
    attempt = SolutionAttempt(steps=[SubmittedStep("not_a_bool")])  # TODO: wire up
    with pytest.raises(AttemptValidationError) as exc_info:
        self_graded_instance.verifier.rate(attempt)  # TODO: wire up
    assert exc_info.value.step_index == 0


# === SPEC GAPS ===
# test_exact_match_whitespace_normalisation: spec lists "whitespace" as an authored
#   normalize option but gives no concrete example. Behaviour under leading/trailing
#   vs internal whitespace normalisation is unspecified.
