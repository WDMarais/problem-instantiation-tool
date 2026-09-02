"""
Functions & Graphs — ``exponential_inverse`` (the shared-stem compound, NSC Q6).

The generator's arithmetic is never trusted: each instance is re-derived from the
*presented* intersection ``A(ax, ay)`` and y-intercept ``B(0, by)`` with
independent SymPy — ``q`` and the base ``p`` from f's two points, the range from
the (increasing) asymptote, and g from A plus the *swapped* B(by, 0) that the g⁻¹
hook produces — then the six answer values are round-tripped through the verifier.
The F1 predicate is exercised both ways: every draw is in scope, and each
out-of-scope construction is individually rejected.
"""

import types

import sympy

from content.examples.exponential_inverse import exponential_inverse
from content.scope_predicates import exponential_inverse_in_scope
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

_x = sympy.Symbol("x")
_KEYS = ["p_val", "q", "range_set", "g_slope", "g_expr", "ginv_expr"]


def _eng():
    return Engine(
        registry=InMemoryRegistry({exponential_inverse.id: exponential_inverse})
    )


def _rate(inst, *answers):
    return inst.verifier.rate(
        SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
    )


def _independent(p) -> dict:
    """Re-solve all six answers from the presented A(ax, ay) and B(0, by)."""
    ax, ay, by = p["ax"], p["ay"], p["by"]
    q = by - 1  # f(0) = 1 + q = by
    base = sympy.Integer(ay - q) ** sympy.Rational(1, ax)  # p^ax = ay - q
    # g through A(ax, ay) and the swapped B(by, 0)
    m = sympy.Rational(ay - 0, ax - by)
    c = -m * by
    y = sympy.Symbol("y")
    ginv = sympy.solve(sympy.Eq(_x, m * y + c), y)[0]  # swap x,y, solve for y
    return {
        "p_val": base,
        "q": q,
        "range_set": sympy.Interval.open(q, sympy.S.Infinity),
        "g_slope": m,
        "g_expr": sympy.expand(m * _x + c),
        "ginv_expr": sympy.expand(ginv),
    }


# --- generator correctness (independently re-derived) -----------------------


def test_every_answer_matches_an_independent_solve():
    eng = _eng()
    for seed in range(120):
        p = eng.instantiate(exponential_inverse.id, seed=seed).params
        indep = _independent(p)
        for key in _KEYS:
            assert sympy.sympify(p[key]) == sympy.sympify(indep[key]), (seed, key)


def test_A_and_B_lie_on_f():
    eng = _eng()
    for seed in range(120):
        p = eng.instantiate(exponential_inverse.id, seed=seed).params
        f = p["p"] ** _x + p["q"]
        assert f.subs(_x, 0) == p["by"]  # B is f's y-intercept
        assert f.subs(_x, p["ax"]) == p["ay"]  # A is on f


def test_base_is_an_integer_at_least_two():
    eng = _eng()
    for seed in range(120):
        p = eng.instantiate(exponential_inverse.id, seed=seed).params
        assert int(p["p"]) == p["p"] and p["p"] >= 2  # valid increasing exponential


def test_g_and_its_inverse_are_mutual():
    eng = _eng()
    for seed in range(120):
        p = eng.instantiate(exponential_inverse.id, seed=seed).params
        # g(g⁻¹(x)) = x — a genuine functional inverse
        composed = sympy.simplify(p["g_expr"].subs(_x, p["ginv_expr"]))
        assert composed == _x
        # and g⁻¹ passes through the swapped B: g⁻¹(by) has… g through (by,0) ⇒
        # g⁻¹(0) = by
        assert p["ginv_expr"].subs(_x, 0) == p["by"]


def test_range_is_the_open_ray_above_the_asymptote():
    eng = _eng()
    for seed in range(120):
        p = eng.instantiate(exponential_inverse.id, seed=seed).params
        sol = p["range_set"]
        assert isinstance(sol, sympy.Interval)
        assert sol.left == p["q"] and sol.left_open  # y > q, open at the asymptote
        assert sol.right == sympy.S.Infinity


def test_draws_exercise_variety():
    eng = _eng()
    seen_p, seen_ax = set(), set()
    for seed in range(120):
        p = eng.instantiate(exponential_inverse.id, seed=seed).params
        seen_p.add(p["p"])
        seen_ax.add(p["ax"])
    assert seen_p == {2, 3}
    assert seen_ax == {2, 3}


# --- F1 predicate (independent, both directions) ----------------------------


def test_every_draw_is_in_scope():
    eng = _eng()
    for seed in range(120):
        inst = eng.instantiate(exponential_inverse.id, seed=seed)
        assert exponential_inverse_in_scope(inst) == []


def _fake(ax, ay, by):
    return types.SimpleNamespace(params={"ax": ax, "ay": ay, "by": by})


def test_predicate_rejects_horizontal_g():
    assert exponential_inverse_in_scope(_fake(3, 0, -3))  # ay = 0 → g horizontal


def test_predicate_rejects_undefined_slope():
    # ax = by = 2: g's two points A(2, ay) and (2, 0) share an x
    assert exponential_inverse_in_scope(_fake(2, 5, 2))


def test_predicate_rejects_non_integer_base():
    # q = by - 1 = -3; p^ax = ay - q = 5 - (-3) = 8, but ax = 2 → p = √8 non-integer
    assert exponential_inverse_in_scope(_fake(2, 5, -2))


def test_predicate_rejects_degenerate_base():
    # p^ax = ay - q = 3 - 0 = 3 with ax = 3 → not a perfect cube (base non-integer)
    assert exponential_inverse_in_scope(_fake(3, 3, 1))


# --- verifier round-trips ---------------------------------------------------


def test_all_six_correct_scores_full():
    inst = _eng().instantiate(exponential_inverse.id, seed=1)
    p = inst.params
    r = _rate(inst, *[p[k] for k in _KEYS])
    assert r.is_correct and r.marks_awarded == 6


def test_wrong_base_drops_one_mark():
    inst = _eng().instantiate(exponential_inverse.id, seed=1)
    p = inst.params
    ans = [p[k] for k in _KEYS]
    ans[_KEYS.index("p_val")] = p["p_val"] + 1  # wrong p, rest right
    r = _rate(inst, *ans)
    assert r.marks_awarded == 5 and not r.is_correct


def test_wrong_range_openness_loses_the_set_mark():
    inst = _eng().instantiate(exponential_inverse.id, seed=1)
    p = inst.params
    ans = [p[k] for k in _KEYS]
    ans[_KEYS.index("range_set")] = sympy.Interval(
        p["q"], sympy.S.Infinity, left_open=False
    )  # y ≥ q wrongly includes the asymptote
    r = _rate(inst, *ans)
    assert r.marks_awarded == 5 and not r.is_correct


def test_all_wrong_scores_zero():
    inst = _eng().instantiate(exponential_inverse.id, seed=1)
    bogus = [99, 99, sympy.Interval(100, 200), 99, _x + 1, _x - 1]
    assert _rate(inst, *bogus).marks_awarded == 0


# --- compound template + registration ---------------------------------------


def test_template_builds_four_subparts_with_a_shared_diagram():
    from worksheets.generate import PROBLEMS, template_exponential_inverse

    p = _eng().instantiate(exponential_inverse.id, seed=7).params
    for detail in ("full", "short"):
        card = template_exponential_inverse(p, detail=detail)
        assert card.graph_svg and card.subparts is not None
        assert [sp.suffix for sp in card.subparts] == ["1", "2", "3", "4"]
        for sp in card.subparts:
            assert sp.memo_steps and 0 <= sp.auto_marks <= sp.marks
        assert sum(sp.marks for sp in card.subparts) == 11
        assert sum(sp.auto_marks for sp in card.subparts) == 6  # canonical total
    assert exponential_inverse.id in PROBLEMS
