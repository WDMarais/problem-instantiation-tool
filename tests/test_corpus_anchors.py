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

import math

import pytest

from content.examples.compound_periodic import (
    appreciation,
    compound_amount,
    compound_rate,
)
from content.examples.concavity_inflection import concavity_inflection
from content.examples.cubic_stationary_points import cubic_stationary_points
from content.examples.depreciation import (
    depreciation_rate,
    depreciation_to_zero,
)
from content.examples.derivative_first_principles import derivative_first_principles
from content.examples.derivative_rules import derivative_rules
from content.examples.discriminant_nature import discriminant_nature
from content.examples.exponential_equation import exponential_equation
from content.examples.future_value_annuity import (
    fv_annuity_amount,
    fv_annuity_deposit,
)
from content.examples.inclination_angle import inclination_angle
from content.examples.motion_calculus import motion_calculus
from content.examples.nominal_effective import nominal_to_effective
from content.examples.nonlinear_simultaneous import nonlinear_simultaneous
from content.examples.optimisation_solve import optimisation_solve
from content.examples.present_value_annuity import (
    pv_annuity_n,
    pv_annuity_total_interest,
)
from content.examples.quadratic_inequality import quadratic_inequality
from content.examples.surd_equation import surd_equation
from content.examples.tangent_line import tangent_line

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
    depreciation_rate,
    depreciation_to_zero,
    quadratic_inequality,
    surd_equation,
    exponential_equation,
    nonlinear_simultaneous,
    discriminant_nature,
    inclination_angle,
    derivative_first_principles,
    derivative_rules,
    tangent_line,
    cubic_stationary_points,
    optimisation_solve,
    motion_calculus,
    concavity_inflection,
]


def _verifier_marks(problem) -> int:
    spec = problem.verifier_spec
    specs = spec if isinstance(spec, list) else [spec]
    return sum(s.get("marks_possible", 1) for s in specs)


# Independent re-derivations of each anchor's memo figure, keyed by problem id.
# Duplicating the formula here is deliberate: it is the golden check — if the
# generator's arithmetic and this re-derivation ever disagree with the real
# memo, the anchor fails. Each reads only the anchor's ``inputs`` (the exam's
# given numbers); the rounding/floor/ceil convention the memo applies lives here
# in the re-derivation, since ``inputs`` can hold numbers only.


def _rc_compound_amount(d):
    i = d["rate"] / (100 * d["compounding"])
    return d["principal"] * (1 + i) ** (d["compounding"] * d["years"])


def _rc_compound_rate(d):
    growth = d["amount"] / d["principal"]
    return 100 * d["compounding"] * (growth ** (1 / d["periods"]) - 1)


def _rc_appreciation(d):
    return d["price"] * (1 + d["rate"] / 100) ** d["years"]


def _rc_fv_amount_due(d):
    i = d["rate"] / (100 * d["compounding"])
    ordinary = d["deposit"] * ((1 + i) ** (d["compounding"] * d["years"]) - 1) / i
    return ordinary * (1 + i)  # due: deposits at the start of each period


def _rc_fv_deposit(d):
    i = d["rate"] / (100 * d["compounding"])
    return d["target_amount"] / (((1 + i) ** d["periods"] - 1) / i)


def _rc_pv_n_withdrawals(d):
    i = d["rate"] / (100 * d["compounding"])
    solved = -math.log(1 - d["present_value"] * i / d["payment"]) / math.log(1 + i)
    return math.floor(solved)  # withdrawal fund: whole withdrawals only


def _rc_pv_total_interest(d):
    return d["instalment"] * d["periods"] - d["loan_amount"]


def _rc_depreciation_rate(d):
    return 100 * (1 - d["book_value"] / d["book_price"]) / d["years"]


def _rc_depreciation_to_zero(d):
    return math.ceil(1 / (d["rate"] / 100))


_RECOMPUTE = {
    "finance_nominal_to_effective": lambda i: (
        ((1 + (i["nominal_rate"] / 100) / i["compounding"]) ** i["compounding"] - 1)
        * 100
    ),
    "finance_compound_periodic_amount": _rc_compound_amount,
    "finance_compound_periodic_rate": _rc_compound_rate,
    "finance_appreciation": _rc_appreciation,
    "finance_fv_annuity_amount": _rc_fv_amount_due,
    "finance_fv_annuity_deposit": _rc_fv_deposit,
    "finance_pv_annuity_n": _rc_pv_n_withdrawals,
    "finance_pv_annuity_total_interest": _rc_pv_total_interest,
    "finance_depreciation_rate": _rc_depreciation_rate,
    "finance_depreciation_to_zero": _rc_depreciation_to_zero,
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
