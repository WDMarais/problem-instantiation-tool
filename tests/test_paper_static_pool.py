"""
StaticPool — a resistant slot filled by a small pool of hand-authored variants,
one drawn per seed (P2 Q6, the trig-identity proofs).

The pool is not a generator: nothing is numerically instantiated or engine-graded,
so the slot renders as static (hand-marked). What it must do is rotate which fixed
variant a given seed sees — enough to keep the same proof from recurring across the
papers we ship — while keeping the paper contiguous and warning-free.
"""

from __future__ import annotations

import random

import pytest

from worksheets.paper import (
    PAPERS,
    RenderedSlot,
    StaticContent,
    StaticPool,
    build_paper,
)


def _q6(seed: int) -> RenderedSlot:
    slots = build_paper(PAPERS["2025_mj_p2"], seed=seed)
    return next(s for s in slots if s.slot.number == "6.1")


def test_empty_pool_is_rejected():
    with pytest.raises(ValueError):
        StaticPool(())


def test_choose_returns_a_variant():
    pool = StaticPool(
        (
            StaticContent(instruction="a", memo_steps=("1",)),
            StaticContent(instruction="b", memo_steps=("2",)),
        )
    )
    assert pool.choose(random.Random(0)) in pool.variants


def test_q6_is_a_static_hand_marked_slot():
    rs = _q6(4)
    assert not rs.generated  # renders with the "static" badge
    assert rs.auto_marks is None  # nothing engine-graded
    assert rs.slot.marks == 6
    assert rs.memo_steps  # carries a worked proof
    assert "RHS" in rs.memo_steps[-1]  # a completed identity proof


def test_q6_rotates_through_the_whole_pool_across_seeds():
    shown = {_q6(seed).display_math for seed in range(40)}
    assert len(shown) == 5  # all five identities are reachable


def test_q6_is_deterministic_per_seed():
    assert _q6(4).display_math == _q6(4).display_math


def test_p2_is_contiguous_and_warning_free_with_q6():
    slots = build_paper(PAPERS["2025_mj_p2"], seed=3)
    assert not [w for s in slots for w in s.warnings]
    nums = [s.slot.number for s in slots]
    i = nums.index("5.3")
    # the 5.1.3 -> 7 hole is closed: 5.3, then Q6 (static proof + live solve), then 7
    assert nums[i : i + 4] == ["5.3", "6.1", "6.2", "7"]


def test_p2_reconciles_to_the_nsc_150():
    # the paper's headline total matches a real NSC P2 (the live archetypes plus the
    # hand-marked static proof blocks that carry the resistant proof marks).
    assert PAPERS["2025_mj_p2"].total_marks == 150


def test_geometry_questions_carry_a_static_proof_part():
    slots = build_paper(PAPERS["2025_mj_p2"], seed=5)
    for proof_num in ("9.3", "10.3", "11.3"):
        rs = next(s for s in slots if s.slot.number == proof_num)
        assert not rs.generated  # hand-marked static proof
        assert "RHS" not in "".join(rs.memo_steps)  # a geometry proof, not an identity
        assert rs.memo_steps  # carries the worked proof
