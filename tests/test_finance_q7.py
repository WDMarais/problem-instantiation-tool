"""
Financial mathematics — the two new NSC Q7 generators: ``effective_rate`` (7.1)
and ``lump_plus_annuity`` (7.3). (Q7.2 reuses the existing ``finance_pv_annuity_n``,
covered by its own module.)

Each generator's arithmetic is re-derived independently from the presented inputs,
the canonical answer is round-tripped through the verifier, and the shipped source
instance is reproduced to the cent / basis point.
"""

import math

from content.examples.finance import effective_rate, lump_plus_annuity
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep


def _eng():
    return Engine(
        registry=InMemoryRegistry(
            {p.id: p for p in (effective_rate, lump_plus_annuity)}
        )
    )


def _rate(inst, answer):
    return inst.verifier.rate(SolutionAttempt(steps=[SubmittedStep(answer)]))


# --- effective_rate (7.1) ---------------------------------------------------


def test_effective_rate_matches_independent_solve():
    eng = _eng()
    for seed in range(120):
        p = eng.instantiate(effective_rate.id, seed=seed).params
        r, m = p["nominal_rate"], p["compounding"]
        expected = ((1 + r / (100 * m)) ** m - 1) * 100
        assert math.isclose(p["answer"], expected, rel_tol=1e-12)


def test_effective_rate_exceeds_nominal():
    # m > 1 ⇒ compounding within the year makes the effective rate strictly larger
    eng = _eng()
    for seed in range(120):
        p = eng.instantiate(effective_rate.id, seed=seed).params
        assert p["answer"] > p["nominal_rate"]


def test_effective_rate_reproduces_source_instance():
    # John's 15% p.a. compounded monthly → 16,08% effective (NSC 2025 M/J P1 7.1)
    eff = ((1 + 0.15 / 12) ** 12 - 1) * 100
    assert round(eff, 2) == 16.08


def test_effective_rate_verifier_round_trips():
    inst = _eng().instantiate(effective_rate.id, seed=3)
    ans = inst.params["answer"]
    assert _rate(inst, round(ans, 2)).is_correct  # a 2-dp calculator answer passes
    assert not _rate(inst, round(ans, 2) + 0.05).is_correct  # 0,05% off fails


# --- lump_plus_annuity (7.3) ------------------------------------------------


def test_lump_plus_annuity_matches_independent_solve():
    eng = _eng()
    for seed in range(120):
        p = eng.instantiate(lump_plus_annuity.id, seed=seed).params
        i = p["rate"] / (100 * 12)
        n_lump, n_ann = 12 * p["lump_years"], 12 * p["deposit_years"]
        lump = p["principal"] * (1 + i) ** n_lump
        annuity = p["deposit"] * ((1 + i) ** n_ann - 1) / i
        assert math.isclose(p["answer"], lump + annuity, rel_tol=1e-12)


def test_lump_plus_annuity_stream_is_deferred():
    # the deposit phase is strictly shorter than the lump phase — a genuinely
    # deferred stream (else it is a plain annuity, a different archetype)
    eng = _eng()
    for seed in range(120):
        p = eng.instantiate(lump_plus_annuity.id, seed=seed).params
        assert 0 < p["deposit_years"] < p["lump_years"]
        assert p["defer_years"] == p["lump_years"] - p["deposit_years"]
        # the two components sum to the answer (no double count / omission)
        assert math.isclose(p["lump_fv"] + p["annuity_fv"], p["answer"], rel_tol=1e-12)


def test_lump_plus_annuity_reproduces_source_instance():
    # R12 000 lump for 4 yr + R500/mo for the last 2 yr at 9,5% monthly → R30 679,83
    i = 0.095 / 12
    total = 12000 * (1 + i) ** 48 + 500 * ((1 + i) ** 24 - 1) / i
    assert round(total, 2) == 30679.83


def test_lump_plus_annuity_verifier_round_trips():
    inst = _eng().instantiate(lump_plus_annuity.id, seed=5)
    ans = inst.params["answer"]
    assert _rate(inst, round(ans, 2)).is_correct
    # rel_tol 1e-4 on a large total is a few rand; miss by well beyond it
    assert not _rate(inst, round(ans, 2) + 100.0).is_correct


def test_verifier_awards_full_part_marks():
    # finance-family convention: the single numeric answer carries the whole part
    for pid, marks in ((effective_rate.id, 2), (lump_plus_annuity.id, 6)):
        inst = _eng().instantiate(pid, seed=1)
        r = _rate(inst, inst.params["answer"])
        assert r.is_correct and r.marks_awarded == marks


# --- templates + registration -----------------------------------------------


def test_templates_build_and_are_registered():
    from worksheets.generate import (
        PROBLEMS,
        template_effective_rate,
        template_lump_plus_annuity,
    )

    eng = _eng()
    for pid, template in (
        (effective_rate.id, template_effective_rate),
        (lump_plus_annuity.id, template_lump_plus_annuity),
    ):
        p = eng.instantiate(pid, seed=7).params
        for detail in ("full", "short"):
            card = template(p, detail=detail)
            assert card.instruction and card.worked_steps
        assert pid in PROBLEMS
