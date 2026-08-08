"""
Core sequences/series expansion batch: two-terms→a,d / a,r; geometric symmetry
(find-missing / find-n / next-terms); Sₙ→n; sigma-evaluate.

Each generator is checked by *re-deriving* the answer independently of the
generator's own arithmetic, then round-tripping it through the verifier, and the
template is smoke-rendered.
"""

import pytest

from content.examples.arithmetic_sequence import from_two_terms as arith_from_two
from content.examples.geometric_sequence import (
    find_missing as geo_find_missing,
)
from content.examples.geometric_sequence import (
    find_n as geo_find_n,
)
from content.examples.geometric_sequence import (
    from_two_terms as geo_from_two,
)
from content.examples.geometric_sequence import (
    next_terms as geo_next_terms,
)
from content.examples.series import find_n_from_sum, sigma_evaluate
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep
from worksheets.generate import (
    BUNDLES,
    PROBLEMS,
    template_arith_from_two_terms,
    template_arith_series_find_n,
    template_arith_series_sigma,
    template_geo_find_missing,
    template_geo_find_n,
    template_geo_from_two_terms,
    template_geo_next_terms,
)

_ALL = [
    arith_from_two,
    geo_from_two,
    geo_find_missing,
    geo_find_n,
    geo_next_terms,
    find_n_from_sum,
    sigma_evaluate,
]


def _eng():
    return Engine(registry=InMemoryRegistry({p.id: p for p in _ALL}))


def _rate(inst, *answers):
    steps = [SubmittedStep(a) for a in answers]
    return inst.verifier.rate(SolutionAttempt(steps=steps))


# --- generator correctness (re-derived answers) -----------------------------


@pytest.mark.parametrize("seed", range(20))
def test_arith_from_two_terms_recovers_a_and_d(seed):
    p = _eng().instantiate(arith_from_two.id, seed=seed).params
    d = (p["tq"] - p["tp"]) // (p["q"] - p["p"])
    a = p["tp"] - (p["p"] - 1) * d
    assert (d, a) == (p["d"], p["a"])
    assert p["tp"] == a + (p["p"] - 1) * d
    assert p["tq"] == a + (p["q"] - 1) * d


@pytest.mark.parametrize("seed", range(20))
def test_geo_from_two_terms_gap_is_odd_when_r_negative(seed):
    """Sign of r must be recoverable: an even power of a negative r hides it."""
    p = _eng().instantiate(geo_from_two.id, seed=seed).params
    if p["r"] < 0:
        assert (p["q"] - p["p"]) % 2 == 1
    assert p["tp"] == p["a"] * p["r"] ** (p["p"] - 1)
    assert p["tq"] == p["a"] * p["r"] ** (p["q"] - 1)


@pytest.mark.parametrize("seed", range(20))
def test_geo_find_missing_is_positive_integer_mean(seed):
    p = _eng().instantiate(geo_find_missing.id, seed=seed).params
    assert p["answer"] ** 2 == p["t_before"] * p["t_after"]
    assert p["answer"] > 0
    assert p["t_before"] > 0 and p["t_after"] > 0


@pytest.mark.parametrize("seed", range(20))
def test_geo_find_n_target_is_the_nth_term(seed):
    p = _eng().instantiate(geo_find_n.id, seed=seed).params
    n = p["answer"]
    assert p["target"] == p["a"] * p["r"] ** (n - 1)


@pytest.mark.parametrize("seed", range(20))
def test_series_find_n_sum_matches_and_is_unique_positive(seed):
    p = _eng().instantiate(find_n_from_sum.id, seed=seed).params
    n = int(p["answer"])
    assert p["sn"] == sum(p["a"] + i * p["d"] for i in range(n))
    # strictly increasing positive partial sums ⇒ no other n gives the same sum
    assert p["a"] > 0 and p["d"] > 0


@pytest.mark.parametrize("seed", range(20))
def test_sigma_evaluate_matches_expansion(seed):
    p = _eng().instantiate(sigma_evaluate.id, seed=seed).params
    expected = sum(p["p"] * k + p["q"] for k in range(1, p["n"] + 1))
    assert int(p["answer"]) == expected


# --- verifier round-trips ---------------------------------------------------


def test_two_term_problems_score_full_on_correct():
    eng = _eng()
    a = eng.instantiate(arith_from_two.id, seed=1)
    r = _rate(a, a.params["d"], a.params["a"])
    assert r.is_correct and r.marks_awarded == 4
    g = eng.instantiate(geo_from_two.id, seed=1)
    rg = _rate(g, g.params["r"], g.params["a"])
    assert rg.is_correct and rg.marks_awarded == 4


def test_two_term_problems_partial_and_wrong():
    eng = _eng()
    a = eng.instantiate(arith_from_two.id, seed=2)
    # correct d, wrong a → partial (d marks only)
    partial = _rate(a, a.params["d"], a.params["a"] + 1)
    assert not partial.is_correct
    assert partial.marks_awarded == 2


def test_single_answer_problems_reject_wrong():
    eng = _eng()
    for prob, key in [
        (geo_find_missing, "answer"),
        (geo_find_n, "answer"),
        (find_n_from_sum, "answer"),
        (sigma_evaluate, "answer"),
    ]:
        inst = eng.instantiate(prob.id, seed=3)
        wrong = int(inst.params[key]) + 1
        assert not _rate(inst, wrong).is_correct


# --- templates + wiring -----------------------------------------------------


def test_templates_render_full_and_short():
    eng = _eng()
    cases = [
        (arith_from_two.id, template_arith_from_two_terms),
        (geo_from_two.id, template_geo_from_two_terms),
        (geo_find_missing.id, template_geo_find_missing),
        (geo_find_n.id, template_geo_find_n),
        (geo_next_terms.id, template_geo_next_terms),
        (find_n_from_sum.id, template_arith_series_find_n),
        (sigma_evaluate.id, template_arith_series_sigma),
    ]
    for pid, tmpl in cases:
        params = eng.instantiate(pid, seed=4).params
        for detail in ("full", "short"):
            card = tmpl(params, detail=detail)
            assert card.instruction
            assert card.display_math
            assert card.worked_steps


def test_all_new_types_registered_and_in_full_bundle():
    ids = {
        "arith_seq_from_two_terms",
        "geo_seq_from_two_terms",
        "geo_seq_find_missing",
        "geo_seq_find_n",
        "geo_seq_next_terms",
        "arith_series_find_n",
        "arith_series_sigma",
    }
    assert ids <= set(PROBLEMS)
    full = {pid for pid, _ in BUNDLES["sequences_full"]}
    assert ids <= full
