"""
Trigonometry — ``trig_graph_analysis`` (P2 Q7).

The interval answers are checked against an independent oracle: the domain is
sampled at half-integer degrees (so no sample ever lands on a boundary), and at each
x the raw inequality is compared with membership of the stored SymPy set. The range
is checked against the numeric min/max of f, and the shifted equation against a direct
evaluation of sin(b(x − s°)). None of this reuses the generator's interval logic.
"""

from __future__ import annotations

import math
import random

import sympy

from content.examples.trig_graph_analysis import _gen, trig_graph_analysis
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

_X = sympy.Symbol("x", real=True)
# half-integer degrees so no sample lands on a boundary; coarse enough to stay fast
_SAMPLES = [k + 0.5 for k in range(-180, 180, 3)]


def _params(seed):
    return _gen(random.Random(seed))


def _in(s, xdeg) -> bool:
    return bool(s.contains(sympy.Float(xdeg)))


def test_interval_sets_match_raw_inequalities():
    for seed in range(40):
        p = _params(seed)
        a, q, b = p["a"], p["q"], p["b"]
        for x in _SAMPLES:
            rx = math.radians(x)
            f = a * math.cos(rx) + q
            fprime = -a * math.sin(rx)
            g = math.sin(b * rx)

            # 7.3 increasing: f' > 0
            assert (fprime > 0) == _in(p["answer_increasing"], x), (seed, x)
            # 7.4.1 g·f' < 0
            assert (g * fprime < 0) == _in(p["answer_prod_negative"], x), (seed, x)
            # 7.4.2 f ≤ 0
            assert (f <= 0) == _in(p["answer_f_nonpositive"], x), (seed, x)


def test_range_is_numeric_min_max_of_f():
    for seed in range(120):
        p = _params(seed)
        a, q = p["a"], p["q"]
        vals = [a * math.cos(math.radians(x)) + q for x in range(-180, 181)]
        lo, hi = p["answer_range"].inf, p["answer_range"].sup
        assert abs(float(lo) - min(vals)) < 1e-6
        assert abs(float(hi) - max(vals)) < 1e-6


def test_period_is_360_over_b():
    for seed in range(60):
        p = _params(seed)
        assert int(p["answer_period"]) == 360 // p["b"]
        # g really repeats over that period
        T = math.radians(int(p["answer_period"]))
        for x in (0.3, 1.1, 2.0):
            assert abs(math.sin(p["b"] * x) - math.sin(p["b"] * (x + T))) < 1e-9


def test_shift_equation_matches_direct_evaluation():
    for seed in range(120):
        p = _params(seed)
        b, s = p["b"], p["shift_deg"]
        for xdeg in (10.0, 47.0, 123.0, -95.0):
            rx = math.radians(xdeg)
            direct = math.sin(b * (rx - math.radians(s)))
            stored = float(p["answer_shift"].subs(_X, rx))
            assert abs(direct - stored) < 1e-9, (seed, xdeg)


def test_f_le_0_boundary_is_a_nice_angle():
    for seed in range(60):
        p = _params(seed)
        assert p["boundary"] in (60, 90, 120)


def test_variety():
    seen = set()
    for s in range(120):
        p = _params(s)
        seen.add((p["a"], p["q"], p["b"], p["shift_deg"]))
    assert len(seen) >= 12


def _rate(inst, *answers):
    return inst.verifier.rate(
        SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
    )


_KEYS = [
    "answer_range",
    "answer_period",
    "answer_increasing",
    "answer_prod_negative",
    "answer_f_nonpositive",
    "answer_shift",
]


def test_verifier_grades_all_ten():
    eng = Engine(
        registry=InMemoryRegistry({trig_graph_analysis.id: trig_graph_analysis})
    )
    for seed in range(40):
        inst = eng.instantiate(trig_graph_analysis.id, seed=seed)
        p = inst.params
        r = _rate(inst, *(p[k] for k in _KEYS))
        assert r.marks_awarded == 10 and r.is_correct, seed


def test_wrong_set_loses_only_its_marks():
    eng = Engine(
        registry=InMemoryRegistry({trig_graph_analysis.id: trig_graph_analysis})
    )
    inst = eng.instantiate(trig_graph_analysis.id, seed=1)
    p = inst.params
    answers = [p[k] for k in _KEYS]
    answers[4] = sympy.Interval(0, 10)  # wrong f≤0 set (worth 3)
    r = _rate(inst, *answers)
    assert r.marks_awarded == 7 and not r.is_correct


def test_source_instance_reachable():
    # NSC 2025 M/J P2 Q7: f = 2cos x + 1, g = sin 2x, shift 45° → h = −cos 2x
    for seed in range(400):
        p = _params(seed)
        if (p["a"], p["q"], p["b"], p["shift_deg"]) == (2, 1, 2, 45):
            assert p["answer_shift"] == -sympy.cos(2 * _X)
            assert p["boundary"] == 120
            return
    raise AssertionError("source instance f=2cos x+1, g=sin2x, shift 45° not reached")


def test_template_is_shared_stem_compound():
    from worksheets.generate import PROBLEMS, template_trig_graph_analysis

    p = _params(1)
    for detail in ("full", "short"):
        card = template_trig_graph_analysis(p, detail=detail)
        assert len(card.subparts) == 6
        assert sum(sp.marks for sp in card.subparts) == 10
        assert sum(sp.auto_marks for sp in card.subparts) == 10  # fully engine-graded
        assert not card.worked_steps
        assert all(sp.memo_steps for sp in card.subparts)
    assert trig_graph_analysis.id in PROBLEMS
