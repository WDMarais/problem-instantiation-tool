"""
Independent oracle for ``tree_probability``.

- The without-replacement draws are re-derived by enumerating the *entire ordered
  sample space* of distinct-item pairs with ``itertools.permutations`` and
  counting favourable outcomes — a different method than the branch-multiplying
  formula the generator uses.
- Total probability is re-derived through the **complementary paths**
  (1 − P(failure on either branch)), which never uses the p·q1 + (1−p)·q2 form.

All comparisons go through stdlib ``fractions.Fraction`` (a different arithmetic
path than SymPy).
"""

from __future__ import annotations

from fractions import Fraction
from itertools import permutations

import pytest
import sympy

from content.examples.tree_probability import (
    tree_draw_both,
    tree_draw_one_each,
    tree_total_probability,
)
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

_PROBLEMS = {
    p.id: p for p in [tree_total_probability, tree_draw_both, tree_draw_one_each]
}
_ENGINE = Engine(registry=InMemoryRegistry(_PROBLEMS))


def _frac(r: sympy.Rational) -> Fraction:
    return Fraction(int(sympy.numer(r)), int(sympy.denom(r)))


def _bag(params):
    """Labelled bag: colour_a items tagged 'A', colour_b items tagged 'B',
    each made distinct by an index so permutations treats them as individuals."""
    return [("A", i) for i in range(params["count_a"])] + [
        ("B", j) for j in range(params["count_b"])
    ]


def _enumerate_draw_prob(params, favourable) -> Fraction:
    bag = _bag(params)
    total = fav = 0
    for first, second in permutations(bag, 2):
        total += 1
        if favourable(first, second):
            fav += 1
    return Fraction(fav, total)


def test_draw_both_matches_enumeration():
    for seed in range(80):
        inst = _ENGINE.instantiate("tree_draw_both", seed=seed)
        p = inst.params
        tag = "A" if p["target_colour"] == p["colour_a"] else "B"
        counted = _enumerate_draw_prob(
            p, lambda a, b, tag=tag: a[0] == tag and b[0] == tag
        )
        assert _frac(p["answer"]) == counted, seed


def test_draw_one_each_matches_enumeration():
    for seed in range(80):
        inst = _ENGINE.instantiate("tree_draw_one_each", seed=seed)
        p = inst.params
        counted = _enumerate_draw_prob(p, lambda a, b: a[0] != b[0])
        assert _frac(p["answer"]) == counted, seed


def test_total_probability_matches_complementary_paths():
    for seed in range(80):
        inst = _ENGINE.instantiate("tree_total_probability", seed=seed)
        p = inst.params
        pb = _frac(p["p_branch1"])
        q1 = _frac(p["p_success_given1"])
        q2 = _frac(p["p_success_given2"])
        via_complement = 1 - (pb * (1 - q1) + (1 - pb) * (1 - q2))
        assert _frac(p["answer"]) == via_complement, seed


@pytest.mark.parametrize("pid", list(_PROBLEMS))
def test_answer_is_a_valid_probability(pid):
    for seed in range(40):
        inst = _ENGINE.instantiate(pid, seed=seed)
        ans = _frac(inst.params["answer"])
        assert 0 <= ans <= 1, (pid, seed)


def test_draw_bag_sizes_are_in_range():
    for pid in ("tree_draw_both", "tree_draw_one_each"):
        for seed in range(40):
            inst = _ENGINE.instantiate(pid, seed=seed)
            p = inst.params
            assert 2 <= p["count_a"] <= 5 and 2 <= p["count_b"] <= 5
            assert p["n_total"] == p["count_a"] + p["count_b"]


# --- verifier round-trips ----------------------------------------------------


@pytest.mark.parametrize("pid", list(_PROBLEMS))
def test_correct_scores_full_fraction_or_decimal(pid):
    inst = _ENGINE.instantiate(pid, seed=6)
    ans = inst.verifier.canonicals[0]
    for form in (ans, str(float(ans))):
        r = inst.verifier.rate(SolutionAttempt(steps=[SubmittedStep(form)]))
        assert r.marks_awarded == 1 and r.is_correct, (pid, form)


def test_with_replacement_slip_is_wrong():
    """Using N (not N−1) on the second draw is the archetypal error and must
    not score."""
    inst = _ENGINE.instantiate("tree_draw_both", seed=6)
    p = inst.params
    n = p["n_total"]
    t = p["count_a"] if p["target_colour"] == p["colour_a"] else p["count_b"]
    with_repl = sympy.Rational(t, n) ** 2
    r = inst.verifier.rate(SolutionAttempt(steps=[SubmittedStep(with_repl)]))
    assert r.marks_awarded == 0 and not r.is_correct
    assert with_repl != inst.verifier.canonicals[0]
