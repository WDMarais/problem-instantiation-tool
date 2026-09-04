"""
Functions & Calculus — the NSC Q9 shared-stem cubic ``cubic_shared_analysis``.

Every answer is re-derived independently from the presented p, k, q; the F1 scope
predicate is exercised both directions; the verifier round-trips (including the
irrational 9.5 answer graded as either exact surd or rounded decimal); and the
shipped source instance is reproduced.
"""

import types

import sympy

from content.examples.cubic_shared_analysis import cubic_shared_analysis
from content.scope_predicates import cubic_shared_analysis_in_scope
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

_x = sympy.Symbol("x")
_KEYS = ["k", "x2", "y2", "concavity_q", "d_max"]


def _eng():
    return Engine(
        registry=InMemoryRegistry({cubic_shared_analysis.id: cubic_shared_analysis})
    )


def _rate(inst, overrides=None):
    vals = dict(zip(_KEYS, (inst.params[key] for key in _KEYS)))
    if overrides:
        vals.update(overrides)
    steps = [SubmittedStep(vals[key]) for key in _KEYS]
    return inst.verifier.rate(SolutionAttempt(steps=steps))


# --- independent re-derivation ----------------------------------------------


def test_answers_match_independent_solve():
    eng = _eng()
    for seed in range(120):
        p = eng.instantiate(cubic_shared_analysis.id, seed=seed).params
        pp, kk, qq = p["p"], p["k"], p["q"]
        f = (_x - pp) * (_x - kk) ** 2
        x2 = (kk + 2 * pp) // 3
        assert p["x2"] == x2
        assert p["y2"] == int(sympy.expand(f).subs(_x, x2))
        # one turning point is always the repeated root, on the axis
        assert sympy.expand(f).subs(_x, kk) == 0
        fpp = sympy.diff(f, _x, 2)
        want = "concave_up" if fpp.subs(_x, qq) > 0 else "concave_down"
        assert p["concavity_q"] == want


def test_ninefive_interval_and_h_definition():
    # 9.5's interval is exactly the open interval between the two turning points,
    # and h = −2f′
    eng = _eng()
    for seed in range(120):
        p = eng.instantiate(cubic_shared_analysis.id, seed=seed).params
        assert (p["lo"], p["hi"]) == (min(p["k"], p["x2"]), max(p["k"], p["x2"]))
        f = (_x - p["p"]) * (_x - p["k"]) ** 2
        assert sympy.expand(p["h"] + 2 * sympy.diff(f, _x)) == 0


def test_variety():
    eng = _eng()
    seen = {
        (
            (pp := eng.instantiate(cubic_shared_analysis.id, seed=s).params)["p"],
            pp["k"],
            pp["q"],
        )
        for s in range(120)
    }
    assert len(seen) >= 20


# --- F1 predicate (both directions) -----------------------------------------


def test_every_draw_is_in_scope():
    eng = _eng()
    for seed in range(120):
        inst = eng.instantiate(cubic_shared_analysis.id, seed=seed)
        assert cubic_shared_analysis_in_scope(inst) == []


def _fake(p, k, q):
    # structural rejections return before the stored-value cross-checks, so x2 /
    # d_max are only placeholders here
    return types.SimpleNamespace(params={"p": p, "k": k, "q": q, "x2": 0, "d_max": 0})


def test_predicate_rejects_coincident_roots():
    assert cubic_shared_analysis_in_scope(_fake(2, 2, -1))  # p == k


def test_predicate_rejects_non_integer_second_stationary_point():
    assert cubic_shared_analysis_in_scope(_fake(4, 2, -1))  # k+2p = 8, not ÷3


def test_predicate_rejects_q_on_the_inflection():
    # p=4, k=1 ⇒ inflection at x=(p+2k)/3=2; f″(2)=0 → no definite concavity
    assert cubic_shared_analysis_in_scope(_fake(4, 1, 2))


# --- verifier round-trips ---------------------------------------------------


def test_all_correct_scores_full_six():
    r = _rate(_eng().instantiate(cubic_shared_analysis.id, seed=1))
    assert r.is_correct and r.marks_awarded == 6


def test_dmax_accepts_exact_surd_and_rounded_decimal():
    inst = _eng().instantiate(cubic_shared_analysis.id, seed=1)
    approx = sympy.Float(round(float(inst.params["d_max"]), 2))
    assert _rate(inst, {"d_max": approx}).marks_awarded == 6  # calculator decimal
    # a clearly-wrong distance forfeits exactly the two d_max marks
    wrong = sympy.Float(round(float(inst.params["d_max"]) + 1.0, 2))
    assert _rate(inst, {"d_max": wrong}).marks_awarded == 4


def test_partial_credit_per_subpart():
    inst = _eng().instantiate(cubic_shared_analysis.id, seed=1)
    # wrong concavity direction loses only its 1 mark
    other = (
        "concave_up" if inst.params["concavity_q"] == "concave_down" else "concave_down"
    )
    assert _rate(inst, {"concavity_q": other}).marks_awarded == 5


# --- source reproduction ----------------------------------------------------


def test_reproduces_source_instance():
    # NSC 2025 M/J P1 Q9: f(x) = x³ − 6x² + 9x − 4 = (x−4)(x−1)²; TPs (1;0),(3;−4);
    # concave down at x=−3; y-int −4; max gap 10√5 − 14
    eng = _eng()
    for seed in range(4000):
        p = eng.instantiate(cubic_shared_analysis.id, seed=seed).params
        if (p["p"], p["k"], p["q"]) == (4, 1, -3):
            assert sympy.expand(p["f_expanded"] - (_x**3 - 6 * _x**2 + 9 * _x - 4)) == 0
            assert (p["x2"], p["y2"]) == (3, -4)
            assert p["concavity_q"] == "concave_down" and p["f_double_q"] == -30
            assert p["y_intercept"] == -4
            assert sympy.simplify(p["d_max"] - (10 * sympy.sqrt(5) - 14)) == 0
            return
    raise AssertionError("source instance (p,k,q)=(4,1,−3) not reachable in 4000")


# --- template + registration ------------------------------------------------


def test_template_builds_five_subparts_and_is_registered():
    from worksheets.generate import PROBLEMS, template_cubic_shared_analysis

    p = _eng().instantiate(cubic_shared_analysis.id, seed=2).params
    for detail in ("full", "short"):
        card = template_cubic_shared_analysis(p, detail=detail)
        assert [sp.suffix for sp in card.subparts] == ["1", "2", "3", "4", "5"]
        assert card.graph_svg is None  # no diagram — 9.4 is a hand-drawn sketch
        assert all(sp.memo_steps for sp in card.subparts)
    # the sub-part auto split sums to the generator's canonical total (6)
    full = template_cubic_shared_analysis(p)
    assert sum(sp.auto_marks for sp in full.subparts) == 6
    assert sum(sp.marks for sp in full.subparts) == 18
    assert cubic_shared_analysis.id in PROBLEMS
