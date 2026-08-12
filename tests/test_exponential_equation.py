"""
Q1 Algebra Extensions, archetype 3 — ``exponential_equation``.

The oracle is independent of the backward construction: candidate u-values are
re-solved from the quadratic  u² + b·u + c = 0  with ``sympy.solve``; validity is
the sign test  u > 0; and every reported x-root is confirmed by back-substitution
``base**x == u`` against the *original* exponential equation. Distribution tests
guard the archetype's honesty — the rejection case must occur, a non-positive
(not merely negative) root must be rejected, and the both-valid case must retain
the smaller root so "reject the smaller root" is never a passing shortcut.
"""

import sympy

from content.examples.exponential_equation import exponential_equation
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

_u = sympy.Symbol("u")


def _eng():
    return Engine(
        registry=InMemoryRegistry({exponential_equation.id: exponential_equation})
    )


def _rate(inst, *answers):
    steps = [SubmittedStep(a) for a in answers]
    return inst.verifier.rate(SolutionAttempt(steps=steps))


# --- generator correctness (independent oracle) -----------------------------


def test_candidates_solve_the_substituted_quadratic():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(exponential_equation.id, seed=seed).params
        quadratic = _u**2 + p["b_coef"] * _u + p["c_coef"]
        roots = {int(r) for r in sympy.solve(quadratic, _u)}
        assert roots == set(p["candidate_u"]), (seed, p["equation_latex"])


def test_valid_u_are_exactly_the_positive_candidates():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(exponential_equation.id, seed=seed).params
        positive = {u for u in p["candidate_u"] if u > 0}
        assert positive == set(p["valid_u"]), (seed, p["equation_latex"])
        assert set(p["rejected_u"]) == set(p["candidate_u"]) - positive


def test_x_roots_back_substitute_to_the_valid_u():
    """Every x-root must satisfy the ORIGINAL equation: base**x is a valid u, and
    the x-set is exactly the back-substitution of the valid u-set."""
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(exponential_equation.id, seed=seed).params
        k = p["base"]
        reconstructed = set()
        for x in p["x_roots"]:
            u = k**x
            assert u in p["valid_u"], (seed, x, u)
            reconstructed.add(u)
        assert reconstructed == set(p["valid_u"]), (seed, p["equation_latex"])


def test_two_distinct_candidates():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(exponential_equation.id, seed=seed).params
        assert len(p["candidate_u"]) == 2, seed


def test_distribution_is_honest():
    eng = _eng()
    saw_rejection = saw_both_valid = False
    saw_zero_rejected = False
    both_valid_kept_smaller = False
    for seed in range(200):
        p = eng.instantiate(exponential_equation.id, seed=seed).params
        if p["rejected_u"]:
            saw_rejection = True
            saw_zero_rejected |= 0 in p["rejected_u"]
        else:
            saw_both_valid = True
            # the smaller root is positive here and MUST be retained — this is
            # what defeats a "reject the smaller root" heuristic.
            both_valid_kept_smaller |= min(p["candidate_u"]) in p["valid_u"]
    assert saw_rejection and saw_both_valid
    assert saw_zero_rejected  # a u = 0 root is rejected, not just negative ones
    assert both_valid_kept_smaller


# --- verifier round-trips ---------------------------------------------------


def _first_seed_with_rejection():
    eng = _eng()
    for seed in range(200):
        inst = eng.instantiate(exponential_equation.id, seed=seed)
        if inst.params["rejected_u"]:
            return inst
    raise AssertionError("no rejection instance found")


def test_full_marks_on_solve_reject_backsub():
    inst = _first_seed_with_rejection()
    p = inst.params
    r = _rate(inst, p["candidate_u"], p["valid_u"], p["x_roots"])
    assert r.is_correct and r.marks_awarded == 4


def test_forgetting_to_reject_loses_only_the_reject_mark():
    inst = _first_seed_with_rejection()
    p = inst.params
    # candidates right (2), valid step keeps the bad root (0), x still right (1).
    r = _rate(inst, p["candidate_u"], p["candidate_u"], p["x_roots"])
    assert r.marks_awarded == 3 and not r.is_correct


def test_partial_credit_on_one_candidate_u():
    inst = _first_seed_with_rejection()
    p = inst.params
    one = frozenset({min(p["candidate_u"])})
    r = _rate(inst, one, p["valid_u"], p["x_roots"])
    # one of two candidates (1) + valid (1) + x (1) = 3
    assert r.marks_awarded == 3 and not r.is_correct


def test_all_wrong_scores_zero():
    inst = _first_seed_with_rejection()
    r = _rate(inst, frozenset({98, 99}), frozenset({98}), frozenset({97}))
    assert r.marks_awarded == 0
