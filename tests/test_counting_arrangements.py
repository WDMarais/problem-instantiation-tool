"""
Independent oracle for ``counting_arrangements``: enumerate *every* permutation
of the n objects with ``itertools.permutations`` and count the ones satisfying
each restriction, then assert that brute-force count equals the generator's
closed-form factorial answer. Enumeration and the factorial formula are wholly
different methods, so agreement across many seeds is real corroboration, not a
tautology.
"""

from __future__ import annotations

from itertools import permutations

import pytest

from content.examples.counting_arrangements import (
    counting_all,
    counting_not_together,
    counting_together,
)
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

_PROBLEMS = {p.id: p for p in [counting_all, counting_together, counting_not_together]}
_ENGINE = Engine(registry=InMemoryRegistry(_PROBLEMS))


def _adjacent(perm, items) -> bool:
    """True if every label in `items` occupies a contiguous run of `perm`."""
    positions = sorted(perm.index(x) for x in items)
    return positions == list(range(positions[0], positions[0] + len(positions)))


def _brute_count(params) -> int:
    """Exhaustively count arrangements satisfying the params' restriction."""
    labels = params["labels"]
    restriction = params["restriction"]
    total = 0
    for perm in permutations(labels):
        if restriction == "all":
            total += 1
        elif restriction == "together":
            if _adjacent(perm, params["designated"]):
                total += 1
        elif restriction == "not_together":
            if not _adjacent(perm, params["designated"]):
                total += 1
        else:  # unreachable — a new restriction must extend this oracle
            raise AssertionError(f"unhandled restriction {restriction!r}")
    return total


@pytest.mark.parametrize("pid", list(_PROBLEMS))
def test_closed_form_matches_brute_force_enumeration(pid):
    for seed in range(60):
        inst = _ENGINE.instantiate(pid, seed=seed)
        assert int(inst.params["answer"]) == _brute_count(inst.params), (pid, seed)


@pytest.mark.parametrize("pid", list(_PROBLEMS))
def test_answer_is_a_positive_integer(pid):
    for seed in range(30):
        inst = _ENGINE.instantiate(pid, seed=seed)
        ans = int(inst.params["answer"])
        assert ans > 0


def test_designated_objects_are_distinct_and_present():
    for pid in ("counting_together", "counting_not_together"):
        for seed in range(20):
            inst = _ENGINE.instantiate(pid, seed=seed)
            labels, designated = inst.params["labels"], inst.params["designated"]
            assert len(set(designated)) == len(designated)
            assert set(designated) <= set(labels)
            assert len(set(labels)) == len(labels) == inst.params["n"]


def test_not_together_is_the_complement_of_together():
    """n! − (pair together) must equal (arrangements with the pair apart)."""
    from math import factorial

    for seed in range(30):
        inst = _ENGINE.instantiate("counting_not_together", seed=seed)
        n = inst.params["n"]
        apart = int(inst.params["answer"])
        together = 2 * factorial(n - 1)
        assert apart + together == factorial(n)


# --- verifier round-trips ----------------------------------------------------


@pytest.mark.parametrize("pid", list(_PROBLEMS))
def test_correct_answer_scores_full(pid):
    inst = _ENGINE.instantiate(pid, seed=5)
    attempt = SolutionAttempt(steps=[SubmittedStep(int(inst.params["answer"]))])
    r = inst.verifier.rate(attempt)
    assert r.marks_awarded == 1 and r.is_correct


def test_forgetting_the_block_permutation_is_wrong():
    """Dropping the internal k! for the together-block is the classic slip and
    must not score."""
    from math import factorial

    inst = _ENGINE.instantiate("counting_together", seed=5)
    n, k = inst.params["n"], inst.params["block_size"]
    slip = factorial(n - k + 1)  # block treated as one unit but never permuted
    attempt = SolutionAttempt(steps=[SubmittedStep(slip)])
    r = inst.verifier.rate(attempt)
    assert r.marks_awarded == 0 and not r.is_correct
    assert slip != int(inst.params["answer"])  # the slip is genuinely different


def test_answering_total_when_restricted_is_wrong():
    """Ignoring the restriction and answering n! must miss on both restriction
    variants."""
    from math import factorial

    for pid in ("counting_together", "counting_not_together"):
        inst = _ENGINE.instantiate(pid, seed=5)
        total = factorial(inst.params["n"])
        attempt = SolutionAttempt(steps=[SubmittedStep(total)])
        r = inst.verifier.rate(attempt)
        assert r.marks_awarded == 0, pid
