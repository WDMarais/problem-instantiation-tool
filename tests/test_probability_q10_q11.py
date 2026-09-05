"""
Probability & counting — the NSC Q10/Q11 generators.

Q10 is two independent sub-parts: ``prob_mutually_exclusive`` (10.1, the addition
rule) and ``game_expected_payout`` (10.2, win probability × profit target → max
payout). Q11 is a shared-stem compound ``digit_count_exactly_one`` (count with exactly
one given digit, then the complement probability). Every answer is re-derived
independently — the digit count against a brute-force enumeration — the verifiers
round-trip, and each shipped source instance is reproduced.
"""

import sympy

from content.examples.digit_count_exactly_one import digit_count_exactly_one
from content.examples.game_expected_payout import game_expected_payout
from content.examples.prob_mutually_exclusive import prob_mutually_exclusive
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep


def _eng(problem):
    return Engine(registry=InMemoryRegistry({problem.id: problem}))


def _rate(inst, answers):
    return inst.verifier.rate(
        SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
    )


# --- 10.1 mutually exclusive -------------------------------------------------


def test_mutually_exclusive_answer_is_the_addition_rule():
    eng = _eng(prob_mutually_exclusive)
    for seed in range(120):
        p = eng.instantiate(prob_mutually_exclusive.id, seed=seed).params
        # P(A∪B) = P(A) + P(B) for mutually exclusive events, so P(B) = P(A∪B) − P(A)
        assert p["answer"] == p["p_aub"] - p["p_a"]
        assert 0 < p["answer"] < 1 and p["p_aub"] <= 1


def test_mutually_exclusive_grades_whole_two_marks():
    inst = _eng(prob_mutually_exclusive).instantiate(prob_mutually_exclusive.id, seed=3)
    r = _rate(inst, [inst.params["answer"]])
    assert r.is_correct and r.marks_awarded == 2
    # a calculator decimal for the same probability also lands
    approx = sympy.Float(round(float(inst.params["answer"]), 2))
    assert _rate(inst, [approx]).marks_awarded == 2
    assert (
        _rate(inst, [inst.params["answer"] + sympy.Rational(1, 10)]).marks_awarded == 0
    )


def test_mutually_exclusive_variety():
    eng = _eng(prob_mutually_exclusive)
    seen = {
        eng.instantiate(prob_mutually_exclusive.id, seed=s).params["answer"]
        for s in range(120)
    }
    assert len(seen) >= 20


# --- 10.2 game expected payout ----------------------------------------------


def test_game_win_probability_is_two_thirteenths():
    eng = _eng(game_expected_payout)
    for seed in range(120):
        p = eng.instantiate(game_expected_payout.id, seed=seed).params
        assert p["p_win"] == sympy.Rational(2, 13)
        # the expected winner count is a whole number (the memo divides by it)
        assert p["expected_winners"] == p["players"] * sympy.Rational(2, 13)
        # max payout = pool / winners, re-derived from the money parameters
        assert p["max_payout"] == p["payout_pool"] / p["expected_winners"]
        assert p["max_payout"] == (1 - p["profit"]) * p["price"] * sympy.Rational(13, 2)


def test_game_payout_is_a_clean_two_decimal_rand():
    eng = _eng(game_expected_payout)
    for seed in range(120):
        p = eng.instantiate(game_expected_payout.id, seed=seed).params
        cents = p["max_payout"] * 100
        assert cents == int(cents)  # terminates within two decimals


def test_game_grades_both_checkpoints():
    inst = _eng(game_expected_payout).instantiate(game_expected_payout.id, seed=7)
    p = inst.params
    assert _rate(inst, [p["p_win"], p["max_payout"]]).marks_awarded == 2
    # right probability, wrong final payout → only the P(win) mark
    r = _rate(inst, [p["p_win"], p["max_payout"] + 1])
    assert r.marks_awarded == 1 and not r.is_correct


def test_game_reproduces_source_instance():
    # NSC 2025 M/J P1 Q10.2: 260 players × R10, 70% profit → R19,50 per winner
    eng = _eng(game_expected_payout)
    for seed in range(600):
        p = eng.instantiate(game_expected_payout.id, seed=seed).params
        if (
            p["players"] == 260
            and p["price"] == 10
            and p["profit"] == sympy.Rational(7, 10)
        ):
            assert p["expected_winners"] == 40
            assert p["payout_pool"] == 780
            assert p["max_payout"] == sympy.Rational(39, 2)  # R19,50
            return
    raise AssertionError("source instance (260, R10, 70%) not reachable in 600 seeds")


# --- Q11 digit count (shared-stem compound) ---------------------------------


def _brute_count(t: int, start: int) -> int:
    return sum(1 for n in range(start, 1000) if str(n).count(str(t)) == 1)


def test_digit_count_matches_brute_force():
    eng = _eng(digit_count_exactly_one)
    for seed in range(120):
        p = eng.instantiate(digit_count_exactly_one.id, seed=seed).params
        assert p["answer_11_1"] == _brute_count(p["t"], p["start"])
        assert p["total"] == p["end"] - p["start"] + 1


def test_digit_complement_probability():
    eng = _eng(digit_count_exactly_one)
    for seed in range(120):
        p = eng.instantiate(digit_count_exactly_one.id, seed=seed).params
        assert p["answer_11_2"] == sympy.Rational(
            p["total"] - p["answer_11_1"], p["total"]
        )


def test_digit_variety():
    eng = _eng(digit_count_exactly_one)
    seen = {
        eng.instantiate(digit_count_exactly_one.id, seed=s).params["t"]
        for s in range(120)
    }
    assert len(seen) >= 5  # six target digits in the pool


def test_digit_all_correct_scores_full_two():
    inst = _eng(digit_count_exactly_one).instantiate(digit_count_exactly_one.id, seed=1)
    p = inst.params
    r = _rate(inst, [p["answer_11_1"], p["answer_11_2"]])
    assert r.is_correct and r.marks_awarded == 2


def test_digit_partial_credit():
    inst = _eng(digit_count_exactly_one).instantiate(digit_count_exactly_one.id, seed=1)
    p = inst.params
    # wrong count, right probability → only the probability mark
    assert _rate(inst, [p["answer_11_1"] + 1, p["answer_11_2"]]).marks_awarded == 1


def test_digit_reproduces_source_instance():
    # NSC 2025 M/J P1 Q11: numbers 501–999, exactly one 5 → 152; P(not) = 347/499
    eng = _eng(digit_count_exactly_one)
    for seed in range(200):
        p = eng.instantiate(digit_count_exactly_one.id, seed=seed).params
        if p["t"] == 5:
            assert (p["start"], p["end"]) == (501, 999)
            assert p["answer_11_1"] == 152
            assert p["answer_11_2"] == sympy.Rational(347, 499)
            return
    raise AssertionError("source instance t=5 not reachable in 200 seeds")


# --- templates + registration -----------------------------------------------


def test_templates_build_and_are_registered():
    from worksheets.generate import (
        PROBLEMS,
        template_digit_count_exactly_one,
        template_game_expected_payout,
        template_prob_mutually_exclusive,
    )

    me = _eng(prob_mutually_exclusive).instantiate(prob_mutually_exclusive.id, seed=2)
    gm = _eng(game_expected_payout).instantiate(game_expected_payout.id, seed=2)
    dc = _eng(digit_count_exactly_one).instantiate(digit_count_exactly_one.id, seed=2)

    for detail in ("full", "short"):
        assert template_prob_mutually_exclusive(me.params, detail=detail).worked_steps
        assert template_game_expected_payout(gm.params, detail=detail).worked_steps
        card = template_digit_count_exactly_one(dc.params, detail=detail)
        assert [sp.suffix for sp in card.subparts] == ["1", "2"]
        assert card.graph_svg is None  # no diagram
        assert all(sp.memo_steps for sp in card.subparts)

    # the Q11 compound's sub-part auto split sums to the canonical total (2),
    # and its headline marks to the slot's 7
    full = template_digit_count_exactly_one(dc.params)
    assert sum(sp.auto_marks for sp in full.subparts) == 2
    assert sum(sp.marks for sp in full.subparts) == 7

    for pid in (
        prob_mutually_exclusive.id,
        game_expected_payout.id,
        digit_count_exactly_one.id,
    ):
        assert pid in PROBLEMS
