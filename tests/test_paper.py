"""
Paper-assembly layer — ``worksheets.paper``.

Covers the per-paper marking-scheme model added alongside the M/J P1 spine:
``PaperSlot`` construction invariants, the ``auto_marks`` reconciliation in
``build_paper`` (a false coverage claim raises; an unacknowledged divergence
warns; a correct claim resolves the auto/manual split), and a regression guard
that the shipped 2025 M/J P1 manifest builds with **zero** calibration warnings.

The generator canonical totals these tests pin (quadratic_formula = 2, etc.) are
the ``verifier_spec`` sums — the answer-value marks a verifier step covers — not
the paper's headline part-marks.
"""

import pytest

from worksheets.paper import (
    _MJ2025_P1,
    PaperSlot,
    PaperSpec,
    StaticContent,
    build_paper,
)

_STATIC = StaticContent(
    instruction="Prove that $x = x$.",
    memo_steps=("x = x",),
)


def _spec(*slots: PaperSlot) -> PaperSpec:
    return PaperSpec(title="T", source="src", slots=slots)


# --- PaperSlot construction invariants --------------------------------------


def test_slot_requires_exactly_one_source():
    with pytest.raises(ValueError, match="exactly one"):
        PaperSlot("1", 3, "t")  # neither problem_id nor static
    with pytest.raises(ValueError, match="exactly one"):
        PaperSlot("1", 3, "t", problem_id="quadratic_formula", static=_STATIC)


def test_auto_marks_meaningless_on_static_slot():
    with pytest.raises(ValueError, match="static"):
        PaperSlot("1", 3, "t", static=_STATIC, auto_marks=1)


def test_auto_marks_cannot_exceed_slot_marks():
    with pytest.raises(ValueError, match="can't auto-grade more"):
        PaperSlot("1", 3, "t", problem_id="quadratic_formula", auto_marks=4)


def test_auto_marks_cannot_be_negative():
    with pytest.raises(ValueError, match="must be in"):
        PaperSlot("1", 3, "t", problem_id="quadratic_formula", auto_marks=-1)


def test_total_marks_sums_slots():
    spec = _spec(
        PaperSlot("1", 3, "t", problem_id="quadratic_formula", auto_marks=2),
        PaperSlot("2", 4, "t", static=_STATIC),
    )
    assert spec.total_marks == 7


# --- build_paper: auto_marks reconciliation ---------------------------------


def test_false_auto_marks_claim_raises():
    # quadratic_formula's canonical total is 2; claiming 3 is a wrong coverage
    # claim and must raise (loud, never silently reconciled).
    spec = _spec(PaperSlot("1", 3, "t", problem_id="quadratic_formula", auto_marks=3))
    with pytest.raises(ValueError, match="canonical total"):
        build_paper(spec, seed=0)


def test_correct_auto_marks_resolves_manual_split():
    spec = _spec(PaperSlot("1", 3, "t", problem_id="quadratic_formula", auto_marks=2))
    rs = build_paper(spec, seed=0)[0]
    assert rs.auto_marks == 2
    assert rs.manual_marks == 1
    assert rs.mark_warning is None
    assert rs.warnings == []


def test_unacknowledged_divergence_warns_not_raises():
    # marks (3) diverge from the generator total (2) with no auto_marks declared:
    # a calibration gap surfaced loudly, but not fatal.
    spec = _spec(PaperSlot("1", 3, "t", problem_id="quadratic_formula"))
    rs = build_paper(spec, seed=0)[0]
    assert rs.mark_warning is not None
    assert "declare auto_marks" in rs.mark_warning
    assert rs.warnings == [rs.mark_warning]
    # resolved auto falls back to the generator total; the gap is the manual mark
    assert rs.auto_marks == 2
    assert rs.manual_marks == 1


def test_fully_covered_slot_has_no_warning_and_no_manual():
    # marks == generator total, auto_marks unset: the common, fully-covered case.
    spec = _spec(PaperSlot("1", 2, "t", problem_id="quadratic_formula"))
    rs = build_paper(spec, seed=0)[0]
    assert rs.mark_warning is None
    assert rs.auto_marks == 2
    assert rs.manual_marks == 0


# --- build_paper: static passthrough ----------------------------------------


def test_static_slot_passes_through_unmarked():
    spec = _spec(PaperSlot("1", 3, "t", static=_STATIC))
    rs = build_paper(spec, seed=0)[0]
    assert not rs.generated
    assert rs.auto_marks is None
    assert rs.manual_marks == 0  # no verifier, no split — hand-marked in full
    assert rs.instruction == _STATIC.instruction
    assert rs.memo_steps == list(_STATIC.memo_steps)


def test_generated_slot_carries_a_memo():
    spec = _spec(PaperSlot("1", 2, "t", problem_id="quadratic_formula"))
    rs = build_paper(spec, seed=0)[0]
    assert rs.generated
    assert rs.instruction  # engine-authored stem
    assert rs.memo_steps  # engine-derived worked memo


# --- regression guard: the shipped paper is clean ---------------------------


def test_shipped_mj_p1_builds_without_calibration_warnings():
    rendered = build_paper(_MJ2025_P1, seed=0)
    warnings = [w for rs in rendered for w in rs.warnings]
    assert warnings == [], warnings


def test_shipped_mj_p1_marks_reconcile_per_slot():
    for rs in build_paper(_MJ2025_P1, seed=0):
        if rs.generated:
            # every generated slot's marks fully split into auto + manual
            assert rs.auto_marks is not None
            assert rs.auto_marks + rs.manual_marks == rs.slot.marks
        else:
            assert rs.auto_marks is None


def test_shipped_mj_p1_is_deterministic_per_seed():
    a = build_paper(_MJ2025_P1, seed=11)
    b = build_paper(_MJ2025_P1, seed=11)
    assert [rs.instruction for rs in a] == [rs.instruction for rs in b]
