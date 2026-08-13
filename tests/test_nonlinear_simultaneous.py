"""
Q1 Algebra Extensions, archetype 4 — ``nonlinear_simultaneous``.

The oracle is an independent ``sympy.solve`` of the two equations as a system —
it never sees the backward construction. Every reported pair is additionally
confirmed to satisfy BOTH equations exactly. Distribution tests guard that the
pairs are genuinely distinct (two different x AND two different y, so the pairing
skill is actually exercised) and that both slope signs appear.
"""

import sympy

from content.examples.nonlinear_simultaneous import nonlinear_simultaneous
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

_x, _y = sympy.symbols("x y")


def _eng():
    return Engine(
        registry=InMemoryRegistry({nonlinear_simultaneous.id: nonlinear_simultaneous})
    )


def _rate(inst, *answers):
    steps = [SubmittedStep(a) for a in answers]
    return inst.verifier.rate(SolutionAttempt(steps=steps))


# --- generator correctness (independent oracle) -----------------------------


def test_pairs_match_an_independent_system_solve():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(nonlinear_simultaneous.id, seed=seed).params
        line = sympy.Eq(_y, p["m"] * _x + p["k"])
        parabola = sympy.Eq(_y, _x**2 + p["p"] * _x + p["q"])
        sols = sympy.solve([line, parabola], [_x, _y], dict=True)
        oracle = {(int(s[_x]), int(s[_y])) for s in sols}
        assert oracle == set(p["solution_pairs"]), (seed, p["line_latex"])


def test_every_pair_satisfies_both_equations():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(nonlinear_simultaneous.id, seed=seed).params
        for x, y in p["solution_pairs"]:
            assert y == p["m"] * x + p["k"], (seed, x, y)  # on the line
            assert y == x**2 + p["p"] * x + p["q"], (seed, x, y)  # on the parabola


def test_x_values_are_the_pair_abscissae():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(nonlinear_simultaneous.id, seed=seed).params
        assert {x for x, _ in p["solution_pairs"]} == set(p["x_values"]), seed


def test_two_distinct_pairs():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(nonlinear_simultaneous.id, seed=seed).params
        assert len(p["solution_pairs"]) == 2, seed
        assert len(p["x_values"]) == 2, seed


def test_distribution_exercises_the_pairing():
    """Distinct x AND distinct y must both occur, so the pairing is non-trivial;
    both slope signs must appear."""
    eng = _eng()
    saw_pos_slope = saw_neg_slope = False
    saw_distinct_y = False
    for seed in range(120):
        p = eng.instantiate(nonlinear_simultaneous.id, seed=seed).params
        saw_pos_slope |= p["m"] > 0
        saw_neg_slope |= p["m"] < 0
        ys = {y for _, y in p["solution_pairs"]}
        saw_distinct_y |= len(ys) == 2
    assert saw_pos_slope and saw_neg_slope
    assert saw_distinct_y


# --- verifier round-trips ---------------------------------------------------


def test_full_marks_on_both_complete_pairs():
    inst = _eng().instantiate(nonlinear_simultaneous.id, seed=1)
    p = inst.params
    r = _rate(inst, p["x_values"], p["solution_pairs"])
    assert r.is_correct and r.marks_awarded == 4


def test_x_values_without_pairing_loses_the_pair_marks():
    inst = _eng().instantiate(nonlinear_simultaneous.id, seed=1)
    p = inst.params
    # solved for x (2) but presented no (x, y) pairs → pair step scores 0.
    r = _rate(inst, p["x_values"], p["x_values"])
    assert r.marks_awarded == 2 and not r.is_correct


def test_one_complete_pair_earns_partial_on_both_steps():
    inst = _eng().instantiate(nonlinear_simultaneous.id, seed=1)
    p = inst.params
    one_pair = min(p["solution_pairs"])
    r = _rate(inst, frozenset({one_pair[0]}), frozenset({one_pair}))
    # one x (1 of 2) + one complete pair (1 of 2) = 2
    assert r.marks_awarded == 2 and not r.is_correct


def test_right_x_wrong_pairing_scores_only_the_x_marks():
    inst = _eng().instantiate(nonlinear_simultaneous.id, seed=1)
    p = inst.params
    # swap the y-values between the two x's — correct x's, wrong pairing.
    (xa, ya), (xb, yb) = sorted(p["solution_pairs"])
    swapped = frozenset({(xa, yb), (xb, ya)})
    r = _rate(inst, p["x_values"], swapped)
    assert r.marks_awarded == 2 and not r.is_correct


def test_all_wrong_scores_zero():
    inst = _eng().instantiate(nonlinear_simultaneous.id, seed=1)
    r = _rate(inst, frozenset({98, 99}), frozenset({(98, 1), (99, 2)}))
    assert r.marks_awarded == 0
