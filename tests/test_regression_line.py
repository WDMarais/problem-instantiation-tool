"""
Independent-oracle tests for ``regression_line``.

The generator fits the line with the deviation formulas (Sxy/Sxx, ȳ − Bx̄) in
exact SymPy rationals. The oracle here recomputes the same three quantities with
Python's stdlib ``statistics`` module — a completely separate implementation — so
agreement is a real cross-check, not the same arithmetic run twice.
"""

from __future__ import annotations

import random
import statistics

import sympy

from content.examples.regression_line import _fit, _gen, regression_line
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep


def _params(seed):
    return _gen(random.Random(seed))


# --- the oracle: stdlib statistics reproduces the stored coefficients --------


def test_stdlib_regression_matches_stored_coefficients():
    for seed in range(200):
        p = _params(seed)
        slope, intercept = statistics.linear_regression(p["xs"], p["ys"])
        r = statistics.correlation(p["xs"], p["ys"])
        assert abs(float(p["gradient"]) - slope) < 1e-9, seed
        assert abs(float(p["intercept"]) - intercept) < 1e-9, seed
        assert abs(p["correlation"] - r) < 1e-4, seed  # stored rounded to 4 dp


def test_prediction_is_the_line_evaluated_at_x_pred():
    for seed in range(200):
        p = _params(seed)
        slope, intercept = statistics.linear_regression(p["xs"], p["ys"])
        assert abs(float(p["prediction"]) - (intercept + slope * p["x_pred"])) < 1e-9


# --- the two least-squares formulas agree (deviation vs raw-sum) -------------


def test_deviation_and_raw_sum_formulas_agree():
    # A second internal check: the raw-sum (calculator) formula equals the
    # deviation formula the generator uses — same B, symbolically.
    for seed in range(100):
        p = _params(seed)
        xs, ys, n = p["xs"], p["ys"], p["n"]
        sx, sy = sum(xs), sum(ys)
        sxy = sum(x * y for x, y in zip(xs, ys))
        sxx = sum(x * x for x in xs)
        b_raw = sympy.Rational(n * sxy - sx * sy, n * sxx - sx * sx)
        assert b_raw == p["gradient"], seed


# --- construction is well-formed --------------------------------------------


def test_data_is_non_degenerate():
    for seed in range(300):
        p = _params(seed)
        assert len(set(p["xs"])) == p["n"], seed  # distinct x
        assert len(set(p["ys"])) > 1, seed  # y varies
        assert -1 < p["correlation"] < 1, seed  # not a perfect line
        assert p["x_pred"] not in p["xs"], seed  # genuine off-grid prediction


def test_positive_association_by_construction():
    # The scenario is a positive association, so r and the gradient are positive.
    for seed in range(200):
        p = _params(seed)
        assert p["correlation"] > 0, seed
        assert float(p["gradient"]) > 0, seed


# --- distribution honesty ----------------------------------------------------


def test_coefficients_are_not_stuck():
    grads, rs, ns = set(), set(), set()
    for seed in range(300):
        p = _params(seed)
        grads.add(round(float(p["gradient"]), 1))
        rs.add(p["correlation"])
        ns.add(p["n"])
    assert len(grads) > 10  # a real spread of fitted gradients
    assert len(rs) > 50  # correlation genuinely varies
    assert ns == {7, 8, 9, 10}  # all dataset sizes appear


# --- verifier round-trips ----------------------------------------------------


def _rate(inst, *answers):
    attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
    return inst.verifier.rate(attempt)


def _calc_2dp(p):
    return (
        round(float(p["gradient"]), 2),
        round(float(p["intercept"]), 2),
        p["correlation"],
        round(float(p["prediction"]), 2),
    )


def test_two_dp_calculator_answers_score_full():
    engine = Engine(registry=InMemoryRegistry({regression_line.id: regression_line}))
    for seed in range(40):
        inst = engine.instantiate(regression_line.id, seed=seed)
        b, a, r, pred = _calc_2dp(inst.params)
        res = _rate(inst, b, a, r, pred)
        assert res.marks_awarded == 4 and res.is_correct, seed


def test_wrong_correlation_loses_only_its_mark():
    engine = Engine(registry=InMemoryRegistry({regression_line.id: regression_line}))
    for seed in range(30):
        inst = engine.instantiate(regression_line.id, seed=seed)
        b, a, r, pred = _calc_2dp(inst.params)
        res = _rate(inst, b, a, r - 0.4, pred)  # r off by 0.4
        assert res.marks_awarded == 3 and not res.is_correct, seed


def test_x_on_y_gradient_confusion_misses_the_gradient_mark():
    # Regressing x on y gives Sxy/Syy, not Sxy/Sxx — a different, wrong slope.
    engine = Engine(registry=InMemoryRegistry({regression_line.id: regression_line}))
    caught = 0
    for seed in range(60):
        inst = engine.instantiate(regression_line.id, seed=seed)
        p = inst.params
        fit = _fit(p["xs"], p["ys"])
        wrong_b = fit["sxy"] / fit["syy"]
        b, a, r, pred = _calc_2dp(p)
        res = _rate(inst, float(wrong_b), a, r, pred)
        # the swapped gradient is far outside the 0.05 band ⇒ at most 3/4
        if res.marks_awarded < 4:
            caught += 1
    assert caught == 60
