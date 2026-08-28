"""
Q1 Algebra, common-base exponential equation — ``exponential_common_base``.

The oracle is independent of the backward construction: the reported answer is
confirmed by evaluating the *original* equation  a^(x+k) + a^x  at x = n and
checking it equals N, and by checking a^x resolves to a^n. Distribution tests
guard that every base and more than one exponent gap are actually exercised.
"""

from content.examples.exponential_common_base import exponential_common_base
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep


def _eng():
    return Engine(
        registry=InMemoryRegistry({exponential_common_base.id: exponential_common_base})
    )


def _rate(inst, *answers):
    steps = [SubmittedStep(a) for a in answers]
    return inst.verifier.rate(SolutionAttempt(steps=steps))


# --- generator correctness (independent oracle) -----------------------------


def test_answer_solves_the_original_equation():
    eng = _eng()
    for seed in range(120):
        p = eng.instantiate(exponential_common_base.id, seed=seed).params
        a, k, n = p["base"], p["k"], p["n"]
        # the ORIGINAL equation must hold at x = n
        assert a ** (n + k) + a**n == p["total"], (seed, p["equation_latex"])
        # the two reported answer-values are the simplified power and the exponent
        assert p["power"] == a**n
        assert p["x_answer"] == n


def test_factored_constant_and_total_are_consistent():
    eng = _eng()
    for seed in range(120):
        p = eng.instantiate(exponential_common_base.id, seed=seed).params
        a, k = p["base"], p["k"]
        assert p["coeff"] == a**k + 1
        assert p["total"] == p["coeff"] * p["power"]
        # exact division — the whole point of the archetype
        assert p["total"] % p["coeff"] == 0


def test_numbers_stay_exam_sized():
    eng = _eng()
    for seed in range(200):
        p = eng.instantiate(exponential_common_base.id, seed=seed).params
        assert p["total"] < 100_000, (seed, p["total"])
        assert p["k"] >= 1 and p["n"] >= 1


def test_distribution_covers_bases_and_gaps():
    eng = _eng()
    bases, gaps = set(), set()
    for seed in range(200):
        p = eng.instantiate(exponential_common_base.id, seed=seed).params
        bases.add(p["base"])
        gaps.add(p["k"])
    assert bases == {2, 3, 5}
    assert len(gaps) >= 2  # not every item is a^(x+1)


# --- verifier round-trips ---------------------------------------------------


def test_full_marks_on_power_and_exponent():
    inst = _eng().instantiate(exponential_common_base.id, seed=7)
    p = inst.params
    r = _rate(inst, p["power"], p["x_answer"])
    assert r.is_correct and r.marks_awarded == 2


def test_partial_credit_right_power_wrong_exponent():
    inst = _eng().instantiate(exponential_common_base.id, seed=7)
    p = inst.params
    r = _rate(inst, p["power"], p["x_answer"] + 1)
    assert r.marks_awarded == 1 and not r.is_correct


def test_all_wrong_scores_zero():
    inst = _eng().instantiate(exponential_common_base.id, seed=7)
    p = inst.params
    r = _rate(inst, p["power"] + 1, p["x_answer"] + 1)
    assert r.marks_awarded == 0
