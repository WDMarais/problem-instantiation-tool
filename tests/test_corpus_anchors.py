"""
Corpus-anchor sweep — the machine-checked half of "calibrated against real DBE
papers".

Every ``Problem`` that carries a ``corpus_anchor`` is checked here for:
  - citation hygiene (paper + question present),
  - mark consistency — the anchor's part-mark must equal the verifier's own
    marks, so our mark allocation can't silently drift from the paper's, and
  - memo reproduction — where the anchor records the exam's given ``inputs`` and
    published ``memo_value``, our formula, re-derived independently below, must
    still land on that number.

Anchors store only facts and a citation (never the question's wording); the
past-paper item is a sanity check on our independent engine, not a source
(project corpus-provenance rule).
"""

import pytest

from content.examples.compound_periodic import (
    appreciation,
    compound_amount,
    compound_rate,
)
from content.examples.future_value_annuity import (
    fv_annuity_amount,
    fv_annuity_deposit,
)
from content.examples.nominal_effective import nominal_to_effective
from content.examples.present_value_annuity import (
    pv_annuity_n,
    pv_annuity_total_interest,
)

# Every anchored problem type in the family. New anchored types get appended
# here; the sweep then covers them automatically.
ANCHORED = [
    compound_amount,
    compound_rate,
    appreciation,
    nominal_to_effective,
    fv_annuity_amount,
    fv_annuity_deposit,
    pv_annuity_n,
    pv_annuity_total_interest,
]


def _verifier_marks(problem) -> int:
    spec = problem.verifier_spec
    specs = spec if isinstance(spec, list) else [spec]
    return sum(s.get("marks_possible", 1) for s in specs)


# Independent re-derivations of each anchor's memo figure, keyed by problem id.
# Duplicating the formula here is deliberate: it is the golden check — if the
# generator's arithmetic and this re-derivation ever disagree with the real
# memo, the anchor fails.
_RECOMPUTE = {
    "finance_nominal_to_effective": lambda i: (
        ((1 + (i["nominal_rate"] / 100) / i["compounding"]) ** i["compounding"] - 1)
        * 100
    ),
}


def test_every_anchored_problem_actually_has_an_anchor():
    for prob in ANCHORED:
        assert prob.corpus_anchor is not None, prob.id


@pytest.mark.parametrize("prob", ANCHORED, ids=lambda p: p.id)
def test_citation_is_present(prob):
    anchor = prob.corpus_anchor
    assert anchor.paper.strip(), prob.id
    assert anchor.question.strip(), prob.id


@pytest.mark.parametrize("prob", ANCHORED, ids=lambda p: p.id)
def test_anchor_marks_match_the_verifier(prob):
    anchor = prob.corpus_anchor
    if anchor.marks is None:
        pytest.skip(f"{prob.id} anchor records no part-mark")
    assert anchor.marks == _verifier_marks(prob), (
        f"{prob.id}: anchor marks {anchor.marks} != verifier "
        f"{_verifier_marks(prob)} — mark allocation drifted from the paper"
    )


@pytest.mark.parametrize("prob", ANCHORED, ids=lambda p: p.id)
def test_memo_value_is_reproduced_from_inputs(prob):
    anchor = prob.corpus_anchor
    if anchor.memo_value is None:
        pytest.skip(f"{prob.id} anchor records no verified memo value yet")
    assert anchor.inputs is not None, (
        f"{prob.id}: memo_value set but no inputs to reproduce it from"
    )
    recompute = _RECOMPUTE.get(prob.id)
    assert recompute is not None, (
        f"{prob.id}: memo_value set but no independent re-derivation registered"
    )
    assert round(recompute(anchor.inputs), 2) == anchor.memo_value, prob.id
