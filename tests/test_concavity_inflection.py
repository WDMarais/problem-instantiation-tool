"""
Calculus, archetype 7 — ``concavity_inflection``.

The oracle re-derives everything from f″ independently: the inflection x by
solving f″(x)=0, and the concavity to the right by the *sign* of f″ sampled just
past the inflection point (not from the sign of a). It also confirms the defining
property — that the concavity genuinely flips across the inflection point.
Distribution tests guard that both concavity directions and both signs of a
occur.
"""

import sympy

from content.examples.concavity_inflection import concavity_inflection
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

_x = sympy.Symbol("x")


def _eng():
    return Engine(
        registry=InMemoryRegistry({concavity_inflection.id: concavity_inflection})
    )


def _rate(inst, *answers):
    steps = [SubmittedStep(a) for a in answers]
    return inst.verifier.rate(SolutionAttempt(steps=steps))


def _f(p):
    return p["a"] * _x**3 + p["b"] * _x**2 + p["c"] * _x + p["d"]


# --- generator correctness (independent oracle) -----------------------------


def test_inflection_x_solves_second_derivative_zero():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(concavity_inflection.id, seed=seed).params
        roots = sympy.solve(sympy.diff(_f(p), _x, 2), _x)
        assert roots == [p["inflection_x"]], (seed, p["function_latex"])


def test_concavity_right_matches_sign_of_second_derivative():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(concavity_inflection.id, seed=seed).params
        f2 = sympy.diff(_f(p), _x, 2)
        just_right = f2.subs(_x, p["inflection_x"] + 1)
        expected = "concave_up" if just_right > 0 else "concave_down"
        assert expected == p["concavity_right"], (seed, p["function_latex"])


def test_concavity_flips_across_the_inflection_point():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(concavity_inflection.id, seed=seed).params
        f2 = sympy.diff(_f(p), _x, 2)
        left = f2.subs(_x, p["inflection_x"] - 1)
        right = f2.subs(_x, p["inflection_x"] + 1)
        assert left * right < 0, seed  # opposite signs ⇒ concavity changes


def test_inflection_y_is_f_at_inflection_x():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(concavity_inflection.id, seed=seed).params
        assert _f(p).subs(_x, p["inflection_x"]) == p["inflection_y"], seed


def test_distribution_covers_both_directions():
    eng = _eng()
    seen_dir = set()
    saw_pos_a = saw_neg_a = False
    for seed in range(120):
        p = eng.instantiate(concavity_inflection.id, seed=seed).params
        seen_dir.add(p["concavity_right"])
        saw_pos_a |= p["a"] > 0
        saw_neg_a |= p["a"] < 0
    assert seen_dir == {"concave_up", "concave_down"}
    assert saw_pos_a and saw_neg_a


# --- verifier round-trips ---------------------------------------------------


def test_full_marks_on_inflection_and_concavity():
    inst = _eng().instantiate(concavity_inflection.id, seed=1)
    p = inst.params
    r = _rate(inst, p["inflection_x"], p["concavity_right"])
    assert r.is_correct and r.marks_awarded == 2


def test_inflection_right_concavity_wrong_scores_one():
    inst = _eng().instantiate(concavity_inflection.id, seed=1)
    p = inst.params
    wrong = "concave_up" if p["concavity_right"] == "concave_down" else "concave_down"
    r = _rate(inst, p["inflection_x"], wrong)
    assert r.marks_awarded == 1 and not r.is_correct


def test_concavity_right_inflection_wrong_scores_one():
    inst = _eng().instantiate(concavity_inflection.id, seed=1)
    p = inst.params
    r = _rate(inst, p["inflection_x"] + 4, p["concavity_right"])
    assert r.marks_awarded == 1 and not r.is_correct


def test_concavity_label_is_case_insensitive():
    inst = _eng().instantiate(concavity_inflection.id, seed=1)
    p = inst.params
    r = _rate(inst, p["inflection_x"], p["concavity_right"].upper())
    assert r.is_correct and r.marks_awarded == 2


def test_all_wrong_scores_zero():
    inst = _eng().instantiate(concavity_inflection.id, seed=1)
    r = _rate(inst, 99, "not_a_label")
    assert r.marks_awarded == 0
