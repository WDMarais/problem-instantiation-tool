"""
Trig-simplify archetypes (P2 Q5.2 reduce + Q5.3 product).

Both are single fixed-answer ``symbolic_equality`` problems. The properties that
make them honest: the *printed* expression genuinely equals the graded answer
(reconstruct it from the params and simplify — the reductions are checked, not
asserted); the answers vary and stay inside the intended clean set; and grading
has teeth (a wrong ratio / wrong constant scores nothing, an equivalent form still
scores full).
"""

from __future__ import annotations

import random

import sympy

from content.examples.trig_simplify import (
    _FUNCS,
    _TRANSFORMS,
    _gen_product,
    _gen_reduce,
    trig_simplify_product,
    trig_simplify_reduce,
)
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

_X = sympy.Symbol("x")
_SINGLE_RATIOS = {
    sympy.sin(_X),
    -sympy.sin(_X),
    sympy.cos(_X),
    -sympy.cos(_X),
    sympy.tan(_X),
    -sympy.tan(_X),
    sympy.Integer(1),
    sympy.Integer(-1),
}


def _engine() -> Engine:
    return Engine(
        registry=InMemoryRegistry(
            {
                trig_simplify_reduce.id: trig_simplify_reduce,
                trig_simplify_product.id: trig_simplify_product,
            }
        )
    )


def _reduce_expr(params: dict) -> sympy.Basic:
    """Rebuild the printed expression from the drawn factors."""
    num = sympy.Integer(1)
    for f, t in params["num"]:
        num *= _FUNCS[f](_TRANSFORMS[t][0])
    den = sympy.Integer(1)
    for f, t in params["den"]:
        den *= _FUNCS[f](_TRANSFORMS[t][0])
    return num / den


def _product_expr(params: dict) -> sympy.Basic:
    expr = sympy.Integer(1)
    for f, d in params["factors"]:
        expr *= _FUNCS[f](sympy.pi * sympy.Rational(d, 180))
    return expr


# ── 5.2 reduce: single-ratio answers, faithful expression, variety ───────────────


def test_reduce_answer_is_always_a_single_ratio():
    for seed in range(60):
        ans = _gen_reduce(random.Random(seed))["answer"]
        assert ans in _SINGLE_RATIOS, (seed, ans)


def test_reduce_printed_expression_equals_the_answer():
    # the archetype's claim: not schematic — every printed factor reduces so that
    # the whole expression genuinely equals the baked answer.
    for seed in range(60):
        p = _gen_reduce(random.Random(seed))
        assert sympy.simplify(_reduce_expr(p) - p["answer"]) == 0, seed


def test_reduce_answers_vary_across_seeds():
    seen = {str(_gen_reduce(random.Random(seed))["answer"]) for seed in range(60)}
    assert len(seen) >= 5  # not a constant answer


def test_reduce_all_factors_are_genuine_reductions():
    # no factor is the identity angle "x"; every one needs a rule applied.
    for seed in range(30):
        p = _gen_reduce(random.Random(seed))
        assert p["num"] and p["den"]
        assert all(t in _TRANSFORMS for _f, t in p["num"] + p["den"])


# ── 5.2 grading teeth ─────────────────────────────────────────────────────────


def test_reduce_correct_answer_scores_full():
    inst = _engine().instantiate(trig_simplify_reduce.id, seed=3)
    ans = inst.verifier.canonicals[0]
    r = inst.verifier.rate(SolutionAttempt(steps=[SubmittedStep(ans)]))
    assert r.marks_awarded == 3 and r.marks_possible == 3 and r.is_correct


def test_reduce_equivalent_form_scores_full():
    # find a tan-x answer and submit sin x / cos x — algebraically equal.
    for seed in range(60):
        inst = _engine().instantiate(trig_simplify_reduce.id, seed=seed)
        if inst.verifier.canonicals[0] == sympy.tan(_X):
            r = inst.verifier.rate(
                SolutionAttempt(steps=[SubmittedStep(sympy.sin(_X) / sympy.cos(_X))])
            )
            assert r.is_correct and r.marks_awarded == 3
            return
    raise AssertionError("no tan x draw found in 60 seeds")


def test_reduce_wrong_ratio_scores_zero():
    inst = _engine().instantiate(trig_simplify_reduce.id, seed=3)
    wrong = -inst.verifier.canonicals[0]  # flip the sign → a different ratio
    r = inst.verifier.rate(SolutionAttempt(steps=[SubmittedStep(wrong)]))
    assert r.marks_awarded == 0 and not r.is_correct


# ── 5.3 product: nice-constant answers, faithful, varied ─────────────────────────


def test_product_answer_is_a_nonzero_nice_constant():
    for seed in range(40):
        ans = _gen_product(random.Random(seed))["answer"]
        assert ans.is_constant() and ans.is_real and ans != 0
        assert ans not in (1, -1)  # a trivial ±1 product isn't the "trick"
        # only √2/√3 surds (Gr10 scope)
        for p in ans.atoms(sympy.Pow):
            if p.exp == sympy.Rational(1, 2):
                assert p.base in (sympy.Integer(2), sympy.Integer(3))


def test_product_printed_expression_equals_the_answer():
    for seed in range(40):
        p = _gen_product(random.Random(seed))
        assert sympy.simplify(_product_expr(p) - p["answer"]) == 0, seed


def test_product_answers_vary_across_seeds():
    seen = {str(_gen_product(random.Random(seed))["answer"]) for seed in range(40)}
    assert len(seen) >= 6


# ── 5.3 grading teeth ─────────────────────────────────────────────────────────


def test_product_correct_answer_scores_full():
    inst = _engine().instantiate(trig_simplify_product.id, seed=7)
    ans = inst.verifier.canonicals[0]
    r = inst.verifier.rate(SolutionAttempt(steps=[SubmittedStep(ans)]))
    assert r.marks_awarded == 2 and r.marks_possible == 2 and r.is_correct


def test_product_wrong_constant_scores_zero():
    inst = _engine().instantiate(trig_simplify_product.id, seed=7)
    ans = inst.verifier.canonicals[0]
    r = inst.verifier.rate(SolutionAttempt(steps=[SubmittedStep(ans + 1)]))
    assert r.marks_awarded == 0 and not r.is_correct


# ── the templates render an expression + a memo ─────────────────────────────────


def test_templates_emit_expression_and_memo():
    from worksheets.generate import (
        template_trig_simplify_product,
        template_trig_simplify_reduce,
    )

    rc = template_trig_simplify_reduce(_gen_reduce(random.Random(2)))
    assert r"\dfrac" in rc.display_math and len(rc.worked_steps) == 2

    pc = template_trig_simplify_product(_gen_product(random.Random(2)))
    assert r"\cdot" in pc.display_math and len(pc.worked_steps) == 2
