"""
Functions & Graphs — ``hyperbola_properties`` (the shared-stem compound, NSC Q4).

The generator's arithmetic is never trusted: each instance is re-derived from the
*presented* equation ``f(x) = a/(x - m) + q`` with independent SymPy — asymptotes by
limit/denominator, the intercepts by substitution, the ``f ≤ 0`` region by
``solveset``, and the closest point A by minimising the real distance to M — then the
eight answer values are round-tripped through the verifier. The F1 predicate is
exercised both ways: every draw is in scope, and each out-of-scope construction is
individually rejected.
"""

import types

import sympy

from content.examples.hyperbola_properties import hyperbola_properties
from content.scope_predicates import hyperbola_properties_in_scope
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

_x = sympy.Symbol("x")
_KEYS = ["m_x", "m_y", "d_y", "t", "solution_set", "a_x", "a_y", "aa_prime"]


def _eng():
    return Engine(
        registry=InMemoryRegistry({hyperbola_properties.id: hyperbola_properties})
    )


def _rate(inst, *answers):
    return inst.verifier.rate(
        SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
    )


def _f_of(p):
    """The presented function f(x) = a/(x - m) + q, m = -p — built from a, p, q only."""
    return sympy.Rational(p["a"]) / (_x - (-p["p"])) + p["q"]


def _independent(p) -> dict:
    """Re-solve all eight answers from the presented equation, from scratch."""
    m = -p["p"]
    f = _f_of(p)
    d_y = f.subs(_x, 0)
    sol = sympy.solveset(f <= 0, _x, sympy.S.Reals)
    # closest point to M(m, q): minimise the real distance², take the upper branch
    dist2 = (_x - m) ** 2 + (f - p["q"]) ** 2
    crit = sympy.solveset(sympy.diff(dist2, _x), _x, sympy.S.Reals)
    upper = sorted(float(c) for c in crit if float(c) > m)
    ax = int(round(upper[0]))
    ay = int(f.subs(_x, ax))
    return {
        "m_x": m,
        "m_y": p["q"],
        "d_y": d_y,
        "t": p["q"] + p["p"],
        "solution_set": sol,
        "a_x": ax,
        "a_y": ay,
        "aa_prime": 2 * abs(ax),
    }


# --- generator correctness (independently re-derived) -----------------------


def test_every_answer_matches_an_independent_solve():
    eng = _eng()
    for seed in range(120):
        p = eng.instantiate(hyperbola_properties.id, seed=seed).params
        indep = _independent(p)
        for key in _KEYS:
            assert sympy.sympify(p[key]) == sympy.sympify(indep[key]), (seed, key)


def test_solution_set_is_a_nonempty_half_open_interval():
    eng = _eng()
    for seed in range(120):
        p = eng.instantiate(hyperbola_properties.id, seed=seed).params
        sol = p["solution_set"]
        assert isinstance(sol, sympy.Interval)
        assert not sol.is_empty
        assert not sol.left_open and sol.right_open  # [C, m)
        assert sol.right == p["m_x"]  # open end at the vertical asymptote


def test_A_is_a_lattice_point_off_the_y_axis():
    eng = _eng()
    for seed in range(120):
        p = eng.instantiate(hyperbola_properties.id, seed=seed).params
        assert int(p["a_x"]) == p["a_x"] and int(p["a_y"]) == p["a_y"]
        assert p["a_x"] != 0  # else AA' = 0 and A collides with D
        assert p["aa_prime"] == 2 * abs(p["a_x"]) > 0


def test_draws_exercise_variety():
    eng = _eng()
    seen_a, seen_p_sign = set(), set()
    for seed in range(120):
        p = eng.instantiate(hyperbola_properties.id, seed=seed).params
        seen_a.add(p["a"])
        seen_p_sign.add(p["p"] > 0)
    assert seen_a == {1, 4, 9}
    assert seen_p_sign == {True, False}


# --- F1 predicate (independent, both directions) ----------------------------


def test_every_draw_is_in_scope():
    eng = _eng()
    for seed in range(120):
        inst = eng.instantiate(hyperbola_properties.id, seed=seed)
        assert hyperbola_properties_in_scope(inst) == []


def _fake(a, p, q):
    return types.SimpleNamespace(params={"a": a, "p": p, "q": q})


def test_predicate_rejects_non_square_a():
    assert hyperbola_properties_in_scope(_fake(3, -3, 1))  # 3 not a square


def test_predicate_rejects_nonpositive_q():
    assert hyperbola_properties_in_scope(_fake(4, -3, -1))  # q < 0


def test_predicate_rejects_q_not_dividing_a():
    assert hyperbola_properties_in_scope(_fake(4, -3, 3))  # 3 ∤ 4 → non-integer C


def test_predicate_rejects_M_on_y_axis():
    assert hyperbola_properties_in_scope(_fake(4, 0, 2))  # p = 0


def test_predicate_rejects_A_on_y_axis():
    # A_x = -p + √a = -2 + 2 = 0 → AA' = 0, A = D
    assert hyperbola_properties_in_scope(_fake(4, 2, 1))


# --- verifier round-trips ---------------------------------------------------


def test_all_eight_correct_scores_full():
    inst = _eng().instantiate(hyperbola_properties.id, seed=1)
    p = inst.params
    r = _rate(inst, *[p[k] for k in _KEYS])
    assert r.is_correct and r.marks_awarded == 9


def test_wrong_one_coordinate_of_A_drops_one_mark():
    inst = _eng().instantiate(hyperbola_properties.id, seed=1)
    p = inst.params
    ans = [p[k] for k in _KEYS]
    ans[_KEYS.index("a_y")] = p["a_y"] + 1  # A_y wrong, everything else right
    r = _rate(inst, *ans)
    assert r.marks_awarded == 8 and not r.is_correct


def test_wrong_interval_openness_loses_the_set_marks():
    inst = _eng().instantiate(hyperbola_properties.id, seed=1)
    p = inst.params
    ans = [p[k] for k in _KEYS]
    closed = sympy.Interval(p["solution_set"].left, p["solution_set"].right)  # [C, m]
    ans[_KEYS.index("solution_set")] = closed
    r = _rate(inst, *ans)
    assert r.marks_awarded == 7 and not r.is_correct  # lost the 2 set marks


def test_all_wrong_scores_zero():
    inst = _eng().instantiate(hyperbola_properties.id, seed=1)
    bogus = [999, 999, 999, 999, sympy.Interval(-100, -99), 999, 999, 999]
    assert _rate(inst, *bogus).marks_awarded == 0


# --- compound template + registration ---------------------------------------


def test_template_builds_six_subparts_with_a_shared_diagram():
    from worksheets.generate import PROBLEMS, template_hyperbola_properties

    p = _eng().instantiate(hyperbola_properties.id, seed=7).params
    for detail in ("full", "short"):
        card = template_hyperbola_properties(p, detail=detail)
        assert card.graph_svg and card.subparts is not None
        assert [sp.suffix for sp in card.subparts] == ["1", "2", "3", "4", "5", "6"]
        # every sub-part has a memo (full = fuller than short) and a legal auto split
        for sp in card.subparts:
            assert sp.memo_steps and 0 <= sp.auto_marks <= sp.marks
        assert sum(sp.marks for sp in card.subparts) == 15
        assert sum(sp.auto_marks for sp in card.subparts) == 9  # canonical total
    # registered as a worksheet entry so the paper layer can resolve it
    assert hyperbola_properties.id in PROBLEMS
