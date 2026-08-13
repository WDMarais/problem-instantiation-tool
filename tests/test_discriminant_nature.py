"""
Q1 Algebra Extensions, archetype 5 — ``discriminant_nature``.

The oracle is independent of the generator's own ``b²−4ac``: the discriminant is
re-derived with ``sympy.discriminant`` and the nature is read off the *roots*
themselves (``sympy.solve`` — real vs complex, distinct vs repeated, rational vs
irrational). Distribution tests guard that all four natures actually occur and
both leading-coefficient signs appear.
"""

import sympy

from content.examples.discriminant_nature import discriminant_nature
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

_x = sympy.Symbol("x")


def _eng():
    return Engine(
        registry=InMemoryRegistry({discriminant_nature.id: discriminant_nature})
    )


def _rate(inst, *answers):
    steps = [SubmittedStep(a) for a in answers]
    return inst.verifier.rate(SolutionAttempt(steps=steps))


def _nature_from_roots(a: int, b: int, c: int) -> str:
    """Independent classification: inspect the actual roots, not the discriminant."""
    sols = sympy.solve(a * _x**2 + b * _x + c, _x)
    if any(not s.is_real for s in sols):
        return "non_real"
    if len(sols) == 1:
        return "real_equal"
    return (
        "real_unequal_rational"
        if all(s.is_rational for s in sols)
        else "real_unequal_irrational"
    )


# --- generator correctness (independent oracle) -----------------------------


def test_discriminant_matches_sympy():
    eng = _eng()
    for seed in range(120):
        p = eng.instantiate(discriminant_nature.id, seed=seed).params
        poly = sympy.Poly(p["a"] * _x**2 + p["b"] * _x + p["c"], _x)
        assert sympy.discriminant(poly) == p["discriminant"], (
            seed,
            p["quadratic_latex"],
        )


def test_nature_matches_the_actual_roots():
    eng = _eng()
    for seed in range(120):
        p = eng.instantiate(discriminant_nature.id, seed=seed).params
        assert _nature_from_roots(p["a"], p["b"], p["c"]) == p["nature"], (
            seed,
            p["quadratic_latex"],
            p["discriminant"],
        )


def test_leading_coefficient_never_zero():
    eng = _eng()
    for seed in range(120):
        p = eng.instantiate(discriminant_nature.id, seed=seed).params
        assert p["a"] != 0, seed


def test_distribution_covers_all_four_natures():
    eng = _eng()
    seen_natures = set()
    saw_pos_a = saw_neg_a = False
    for seed in range(120):
        p = eng.instantiate(discriminant_nature.id, seed=seed).params
        seen_natures.add(p["nature"])
        saw_pos_a |= p["a"] > 0
        saw_neg_a |= p["a"] < 0
    assert seen_natures == {
        "non_real",
        "real_equal",
        "real_unequal_rational",
        "real_unequal_irrational",
    }
    assert saw_pos_a and saw_neg_a


# --- verifier round-trips ---------------------------------------------------


def _seed_with_nature(nature: str):
    eng = _eng()
    for seed in range(200):
        inst = eng.instantiate(discriminant_nature.id, seed=seed)
        if inst.params["nature"] == nature:
            return inst
    raise AssertionError(f"no instance with nature {nature}")


def test_full_marks_for_each_nature():
    for nature in (
        "non_real",
        "real_equal",
        "real_unequal_rational",
        "real_unequal_irrational",
    ):
        inst = _seed_with_nature(nature)
        p = inst.params
        r = _rate(inst, p["discriminant"], p["nature"])
        assert r.is_correct and r.marks_awarded == 2, nature


def test_right_discriminant_wrong_nature_scores_one():
    inst = _seed_with_nature("non_real")
    p = inst.params
    r = _rate(inst, p["discriminant"], "real_equal")
    assert r.marks_awarded == 1 and not r.is_correct


def test_wrong_discriminant_right_nature_scores_one():
    inst = _seed_with_nature("real_unequal_rational")
    p = inst.params
    r = _rate(inst, p["discriminant"] + 5, p["nature"])
    assert r.marks_awarded == 1 and not r.is_correct


def test_nature_label_is_case_insensitive():
    inst = _seed_with_nature("real_unequal_irrational")
    p = inst.params
    r = _rate(inst, p["discriminant"], p["nature"].upper())
    assert r.is_correct and r.marks_awarded == 2


def test_all_wrong_scores_zero():
    inst = _seed_with_nature("real_equal")
    p = inst.params
    r = _rate(inst, p["discriminant"] + 100, "non_real")
    assert r.marks_awarded == 0
