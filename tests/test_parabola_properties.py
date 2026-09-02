"""
Functions & Graphs — ``parabola_properties`` (the shared-stem compound, NSC Q5).

The generator's arithmetic is never trusted: each instance is re-derived from the
*presented* turning point ``C(h, q)`` and point ``B(bx, by)`` with independent
SymPy — the stretch ``a`` by substitution, the expanded form by ``expand``, the
no-real-roots region by requiring the (downward) maximum below the axis, and the
reflected ``g'`` over ``y = q`` — then the three answer values are round-tripped
through the verifier. The F1 predicate is exercised both ways: every draw is in
scope, and each out-of-scope construction is individually rejected.
"""

import types

import sympy

from content.examples.parabola_properties import parabola_properties
from content.scope_predicates import parabola_properties_in_scope
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

_x = sympy.Symbol("x")
_KEYS = ["a_coeff", "f_expanded", "k_set"]


def _eng():
    return Engine(
        registry=InMemoryRegistry({parabola_properties.id: parabola_properties})
    )


def _rate(inst, *answers):
    return inst.verifier.rate(
        SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
    )


def _independent(p) -> dict:
    """Re-solve all three answers from the presented C(h, q) and B(bx, by)."""
    h, q, bx, by = p["h"], p["q"], p["bx"], p["by"]
    a = sympy.Rational(by - q, (bx - h) ** 2)  # substitute B into vertex form
    f = a * (_x - h) ** 2 + q
    # h(x) = f + k downward ⇒ no real roots iff the maximum q + k is below 0
    k = sympy.Symbol("k")
    k_set = sympy.solveset(q + k < 0, k, sympy.S.Reals)
    return {
        "a_coeff": a,
        "f_expanded": sympy.expand(f),
        "k_set": k_set,
        "g_prime": sympy.expand(2 * q - f),  # reflection in y = q
    }


# --- generator correctness (independently re-derived) -----------------------


def test_every_answer_matches_an_independent_solve():
    eng = _eng()
    for seed in range(120):
        p = eng.instantiate(parabola_properties.id, seed=seed).params
        indep = _independent(p)
        for key in ("a_coeff", "f_expanded", "g_prime"):
            assert sympy.sympify(p[key]) == sympy.sympify(indep[key]), (seed, key)
        # the k region: same set, re-derived (solveset gives (-oo, -q))
        assert p["k_set"] == indep["k_set"], seed


def test_B_lies_on_f_and_is_not_the_vertex():
    eng = _eng()
    for seed in range(120):
        p = eng.instantiate(parabola_properties.id, seed=seed).params
        f = p["a"] * (_x - p["h"]) ** 2 + p["q"]
        assert f.subs(_x, p["bx"]) == p["by"]  # B on f
        assert p["bx"] != p["h"]  # B distinct from the turning point


def test_parabola_is_downward_with_integer_expansion():
    eng = _eng()
    for seed in range(120):
        p = eng.instantiate(parabola_properties.id, seed=seed).params
        assert p["a"] < 0  # downward: turning point is a maximum
        poly = sympy.Poly(p["f_expanded"], _x)
        assert all(int(c) == c for c in poly.all_coeffs())  # integer coefficients


def test_k_region_is_a_negative_unbounded_interval():
    eng = _eng()
    for seed in range(120):
        p = eng.instantiate(parabola_properties.id, seed=seed).params
        sol = p["k_set"]
        assert isinstance(sol, sympy.Interval)
        assert sol.right == -p["q"] and sol.right_open  # k < -q, open at the bound
        assert sol.left == sympy.S.NegativeInfinity


def test_draws_exercise_variety():
    eng = _eng()
    seen_a, seen_h_sign = set(), set()
    for seed in range(120):
        p = eng.instantiate(parabola_properties.id, seed=seed).params
        seen_a.add(p["a"])
        seen_h_sign.add(p["h"] > 0)
    assert seen_a == {-1, -2, -3}
    assert seen_h_sign == {True, False}


# --- F1 predicate (independent, both directions) ----------------------------


def test_every_draw_is_in_scope():
    eng = _eng()
    for seed in range(120):
        inst = eng.instantiate(parabola_properties.id, seed=seed)
        assert parabola_properties_in_scope(inst) == []


def _fake(h, q, bx, by):
    return types.SimpleNamespace(params={"h": h, "q": q, "bx": bx, "by": by})


def test_predicate_rejects_B_at_the_vertex():
    assert parabola_properties_in_scope(_fake(-1, 4, -1, 4))  # bx = h


def test_predicate_rejects_nonpositive_q():
    assert parabola_properties_in_scope(_fake(-1, -2, 1, -10))  # q < 0


def test_predicate_rejects_upward_parabola():
    # a = (by - q)/(bx - h)^2 = (8 - 4)/(1)^2 = +4 ≥ 0 → not downward
    assert parabola_properties_in_scope(_fake(0, 4, 1, 8))


def test_predicate_rejects_non_integer_stretch():
    # a = (by - q)/(bx - h)^2 = (0 - 1)/(2)^2 = -1/4 → non-integer expansion
    assert parabola_properties_in_scope(_fake(0, 1, 2, 0))


# --- verifier round-trips ---------------------------------------------------


def test_all_three_correct_scores_full():
    inst = _eng().instantiate(parabola_properties.id, seed=1)
    p = inst.params
    r = _rate(inst, *[p[k] for k in _KEYS])
    assert r.is_correct and r.marks_awarded == 3


def test_wrong_stretch_drops_one_mark():
    inst = _eng().instantiate(parabola_properties.id, seed=1)
    p = inst.params
    ans = [p[k] for k in _KEYS]
    ans[_KEYS.index("a_coeff")] = p["a_coeff"] + 1  # wrong a, rest right
    r = _rate(inst, *ans)
    assert r.marks_awarded == 2 and not r.is_correct


def test_wrong_k_region_openness_loses_the_set_mark():
    inst = _eng().instantiate(parabola_properties.id, seed=1)
    p = inst.params
    ans = [p[k] for k in _KEYS]
    # k ≤ -q (closed at the bound) is wrong: at k = -q the max touches the axis
    ans[_KEYS.index("k_set")] = sympy.Interval(
        sympy.S.NegativeInfinity, -p["q"], right_open=False
    )
    r = _rate(inst, *ans)
    assert r.marks_awarded == 2 and not r.is_correct


def test_all_wrong_scores_zero():
    inst = _eng().instantiate(parabola_properties.id, seed=1)
    bogus = [999, _x**2 + 1, sympy.Interval(100, 200)]
    assert _rate(inst, *bogus).marks_awarded == 0


# --- compound template + registration ---------------------------------------


def test_template_builds_three_subparts_with_a_shared_diagram():
    from worksheets.generate import PROBLEMS, template_parabola_properties

    p = _eng().instantiate(parabola_properties.id, seed=7).params
    for detail in ("full", "short"):
        card = template_parabola_properties(p, detail=detail)
        assert card.graph_svg and card.subparts is not None
        assert [sp.suffix for sp in card.subparts] == ["1", "2", "3"]
        for sp in card.subparts:
            assert sp.memo_steps and 0 <= sp.auto_marks <= sp.marks
        assert sum(sp.marks for sp in card.subparts) == 9
        assert sum(sp.auto_marks for sp in card.subparts) == 3  # canonical total
    # registered as a worksheet entry so the paper layer can resolve it
    assert parabola_properties.id in PROBLEMS
