"""
Calculus, archetype 4 — ``cubic_stationary_points``.

The oracle is independent of the backward construction: the stationary points are
re-found with ``sympy.solve(f'(x), x)``, coordinates by evaluating f, and the
max/min labels by the sign of f″ at each. Distribution tests guard that a cubic
always yields exactly one local max and one local min, that both leading-
coefficient signs occur, and that b stays integer (the construction's parity
constraint holds).
"""

import sympy

from content.examples.cubic_stationary_points import cubic_stationary_points
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

_x = sympy.Symbol("x")


def _eng():
    return Engine(
        registry=InMemoryRegistry({cubic_stationary_points.id: cubic_stationary_points})
    )


def _rate(inst, *answers):
    steps = [SubmittedStep(a) for a in answers]
    return inst.verifier.rate(SolutionAttempt(steps=steps))


def _f(p):
    return p["a"] * _x**3 + p["b"] * _x**2 + p["c"] * _x + p["d"]


# --- generator correctness (independent oracle) -----------------------------


def test_stationary_x_solve_the_derivative():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(cubic_stationary_points.id, seed=seed).params
        roots = {int(r) for r in sympy.solve(sympy.diff(_f(p), _x), _x)}
        assert roots == set(p["stationary_x"]), (seed, p["function_latex"])


def test_coordinates_are_f_at_the_stationary_x():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(cubic_stationary_points.id, seed=seed).params
        oracle = {(xv, int(_f(p).subs(_x, xv))) for xv in p["stationary_x"]}
        assert oracle == set(p["tp_coords"]), seed


def test_classification_matches_second_derivative_sign():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(cubic_stationary_points.id, seed=seed).params
        f2 = sympy.diff(_f(p), _x, 2)
        oracle = {
            (xv, "local_max" if f2.subs(_x, xv) < 0 else "local_min")
            for xv in p["stationary_x"]
        }
        assert oracle == set(p["classification"]), (seed, p["function_latex"])


def test_exactly_one_max_and_one_min():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(cubic_stationary_points.id, seed=seed).params
        labels = sorted(label for _, label in p["classification"])
        assert labels == ["local_max", "local_min"], seed


def test_distribution_and_integer_coefficients():
    eng = _eng()
    saw_pos_a = saw_neg_a = False
    for seed in range(120):
        p = eng.instantiate(cubic_stationary_points.id, seed=seed).params
        assert p["a"] != 0, seed
        for key in ("a", "b", "c", "d"):
            assert isinstance(p[key], int), (seed, key)
        assert len(p["stationary_x"]) == 2, seed
        saw_pos_a |= p["a"] > 0
        saw_neg_a |= p["a"] < 0
    assert saw_pos_a and saw_neg_a


# --- verifier round-trips ---------------------------------------------------


def test_full_marks_on_all_three_steps():
    inst = _eng().instantiate(cubic_stationary_points.id, seed=1)
    p = inst.params
    r = _rate(inst, p["stationary_x"], p["tp_coords"], p["classification"])
    assert r.is_correct and r.marks_awarded == 6


def test_swapped_labels_lose_only_the_classification_marks():
    """Right x's and coords, but max/min swapped → the two classification marks
    are lost, the four coordinate marks stand."""
    inst = _eng().instantiate(cubic_stationary_points.id, seed=1)
    p = inst.params
    swapped = frozenset(
        {
            (xv, "local_min" if lab == "local_max" else "local_max")
            for xv, lab in p["classification"]
        }
    )
    r = _rate(inst, p["stationary_x"], p["tp_coords"], swapped)
    assert r.marks_awarded == 4 and not r.is_correct


def test_one_correct_turning_point_earns_partial_everywhere():
    inst = _eng().instantiate(cubic_stationary_points.id, seed=1)
    p = inst.params
    one_x = min(p["stationary_x"])
    one_coord = next(c for c in p["tp_coords"] if c[0] == one_x)
    one_label = next(c for c in p["classification"] if c[0] == one_x)
    r = _rate(
        inst,
        frozenset({one_x}),
        frozenset({one_coord}),
        frozenset({one_label}),
    )
    # 1 of 2 on each of the three steps
    assert r.marks_awarded == 3 and not r.is_correct


def test_all_wrong_scores_zero():
    inst = _eng().instantiate(cubic_stationary_points.id, seed=1)
    r = _rate(
        inst,
        frozenset({97, 98}),
        frozenset({(97, 1), (98, 2)}),
        frozenset({(97, "local_max"), (98, "local_min")}),
    )
    assert r.marks_awarded == 0
