"""
The classification atom (identify arithmetic/geometric/neither) and the unlabelled
mixed-solving mode it composes into.

Rationale: solving a sequence problem is ``classify ∘ apply-method``. Labelled
problems only ever drill the second half; these drill the first in isolation and
then compose it back in via an unlabelled, mixed bundle.
"""

import pytest

from content.examples.arithmetic_sequence import nth_term_formula as arith_nth
from content.examples.sequence_classification import (
    admissible_types,
    identify_sequence_type,
    is_arithmetic,
    is_geometric,
    is_quadratic,
    possible_sequence_types,
)
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep
from worksheets.generate import (
    BUNDLES,
    PROBLEMS,
    template_arith_nth_term_formula,
    template_identify_sequence_type,
    template_possible_sequence_types,
)


def _eng():
    return Engine(
        registry=InMemoryRegistry({identify_sequence_type.id: identify_sequence_type})
    )


def _terms(params):
    return [params["t1"], params["t2"], params["t3"], params["t4"]]


@pytest.mark.parametrize("seed", range(30))
def test_generated_label_matches_the_terms(seed):
    """The stated answer is honest: the terms actually are that type, and are not
    simultaneously another named type."""
    inst = _eng().instantiate(identify_sequence_type.id, seed=seed)
    p = inst.params
    ans = p["answer"]
    t = _terms(p)
    assert ans in {"arithmetic", "geometric", "quadratic", "neither"}
    if ans == "arithmetic":
        assert is_arithmetic(t) and not is_geometric(t)
    elif ans == "geometric":
        assert is_geometric(t) and not is_arithmetic(t)
    elif ans == "quadratic":
        # genuine quadratic: constant non-zero 2nd difference, and NOT also a
        # simpler named type (arithmetic ⇒ 2nd diff 0, so these are exclusive).
        assert is_quadratic(t)
        assert not is_arithmetic(t)
        assert not is_geometric(t)
    else:
        assert not is_arithmetic(t)
        assert not is_geometric(t)
        assert not is_quadratic(t)


def test_all_four_types_appear_across_seeds():
    eng = _eng()
    seen = {
        eng.instantiate(identify_sequence_type.id, seed=s).params["answer"]
        for s in range(80)
    }
    assert seen == {"arithmetic", "geometric", "quadratic", "neither"}


def test_correct_word_scores_full():
    inst = _eng().instantiate(identify_sequence_type.id, seed=1)
    ans = inst.params["answer"]
    rating = inst.verifier.rate(SolutionAttempt(steps=[SubmittedStep(ans)]))
    assert rating.is_correct
    assert rating.steps[0].mistake_type == "correct"
    assert rating.steps[0].verifier_type == "exact_equality"


def test_wrong_word_scores_zero():
    inst = _eng().instantiate(identify_sequence_type.id, seed=1)
    ans = inst.params["answer"]
    wrong = "geometric" if ans != "geometric" else "arithmetic"
    rating = inst.verifier.rate(SolutionAttempt(steps=[SubmittedStep(wrong)]))
    assert not rating.is_correct
    assert rating.steps[0].marks_awarded == 0


def test_case_insensitive_match():
    inst = _eng().instantiate(identify_sequence_type.id, seed=2)
    ans = inst.params["answer"]
    rating = inst.verifier.rate(SolutionAttempt(steps=[SubmittedStep(ans.upper())]))
    assert rating.is_correct


def test_identify_template_does_not_pre_reveal_the_type():
    inst = _eng().instantiate(identify_sequence_type.id, seed=3)
    card = template_identify_sequence_type(inst.params)
    assert "arithmetic, geometric, quadratic or neither" in card.instruction
    # the worked reason concludes with the actual answer word
    assert inst.params["answer"] in " ".join(card.worked_steps)


def test_unlabelled_solving_template_drops_the_type_word():
    eng = Engine(registry=InMemoryRegistry({arith_nth.id: arith_nth}))
    params = eng.instantiate(arith_nth.id, seed=4).params
    labelled = template_arith_nth_term_formula(params, labeled=True)
    unlabelled = template_arith_nth_term_formula(params, labeled=False)
    assert "arithmetic sequence" in labelled.instruction
    assert "arithmetic" not in unlabelled.instruction
    assert "the sequence" in unlabelled.instruction


def test_mixed_bundle_registered_and_wires_real_problems():
    assert "sequences_mixed" in BUNDLES
    ids = [pid for pid, _ in BUNDLES["sequences_mixed"]]
    assert "identify_sequence_type" in ids
    assert any(pid.endswith("unlabeled") for pid in ids)
    for pid in ids:
        assert pid in PROBLEMS


# ── possible_sequence_types: "which types could it still be?" ───────────────────


def _poss_eng():
    return Engine(
        registry=InMemoryRegistry({possible_sequence_types.id: possible_sequence_types})
    )


def _poss(params):
    return [params["t1"], params["t2"], params["t3"]]


@pytest.mark.parametrize("seed", range(40))
def test_possible_answer_set_is_read_off_the_three_terms(seed):
    """The answer set is exactly the discriminators applied to the shown terms —
    re-derived here independently of the generator's construction."""
    p = _poss_eng().instantiate(possible_sequence_types.id, seed=seed).params
    t = _poss(p)
    assert p["answer_set"] == admissible_types(t)
    # answer is a non-empty subset of the three named types (never "neither")
    assert p["answer_set"]
    assert p["answer_set"] <= {"arithmetic", "geometric", "quadratic"}
    # arithmetic and quadratic are mutually exclusive on three terms
    assert not {"arithmetic", "quadratic"} <= p["answer_set"]


def test_three_terms_never_pin_geometric_alone():
    """A geometric start (2, 4, 8, …) is equally a quadratic until a 4th term — so a
    set containing 'geometric' must also contain 'quadratic'. This is the whole point
    of the type; assert the ambiguity actually occurs and is never resolved wrongly."""
    eng = _poss_eng()
    saw_geo_quad = False
    for s in range(80):
        ans = eng.instantiate(possible_sequence_types.id, seed=s).params["answer_set"]
        if "geometric" in ans:
            assert "quadratic" in ans
            saw_geo_quad = ans == {"geometric", "quadratic"} or saw_geo_quad
    assert saw_geo_quad, "expected some {geometric, quadratic} ambiguous draws"


def test_all_reachable_answer_sets_appear():
    eng = _poss_eng()
    seen = {
        frozenset(
            eng.instantiate(possible_sequence_types.id, seed=s).params["answer_set"]
        )
        for s in range(80)
    }
    assert seen == {
        frozenset({"arithmetic"}),
        frozenset({"quadratic"}),
        frozenset({"geometric", "quadratic"}),
    }


def test_exact_set_scores_full_and_subset_scores_partial():
    eng = _poss_eng()
    # find a two-element answer so partial credit is observable
    inst = None
    for s in range(80):
        cand = eng.instantiate(possible_sequence_types.id, seed=s)
        if cand.params["answer_set"] == {"geometric", "quadratic"}:
            inst = cand
            break
    assert inst is not None
    full = inst.verifier.rate(
        SolutionAttempt(steps=[SubmittedStep(frozenset({"geometric", "quadratic"}))])
    )
    assert full.is_correct and full.marks_awarded == 2
    partial = inst.verifier.rate(
        SolutionAttempt(steps=[SubmittedStep(frozenset({"quadratic"}))])
    )
    assert not partial.is_correct and partial.marks_awarded == 1
    wrong = inst.verifier.rate(
        SolutionAttempt(steps=[SubmittedStep(frozenset({"arithmetic"}))])
    )
    assert wrong.marks_awarded == 0


def test_possible_template_concludes_with_the_admissible_set():
    inst = _poss_eng().instantiate(possible_sequence_types.id, seed=3)
    card = template_possible_sequence_types(inst.params, detail="full")
    conclusion = card.worked_steps[-1]
    for name in inst.params["answer_set"]:
        assert name in conclusion
    assert "could be" in " ".join(card.worked_steps)


def test_possible_types_in_classification_bundles():
    for bundle in ("sequences_mixed", "sequences_full"):
        ids = {pid for pid, _ in BUNDLES[bundle]}
        assert "possible_sequence_types" in ids
