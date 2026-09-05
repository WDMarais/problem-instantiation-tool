"""
Trigonometry — ``trig_given_ratio`` (P2 Q5.1).

The three stored answers are validated against a completely independent numeric
oracle: θ is rebuilt with ``atan2`` from the exact sin/cos, then

  * sin²θ is recomputed with ``math.sin``,
  * the reduction identity is checked by evaluating its LHS  func(base° + sign·θ)
    directly (so "tan(360° − θ) = −tanθ" is verified, not assumed), and
  * the compound-angle value is checked by evaluating outer(θ ± A) directly.

The verifier round-trips all three (exact and calculator-decimal forms), the
quadrant signs are correct, and the source instance cos θ = −5/13 is reachable.
"""

from __future__ import annotations

import math
import random

import sympy

from content.examples.trig_given_ratio import _gen, trig_given_ratio
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

_FUNC = {"sin": math.sin, "cos": math.cos, "tan": math.tan}


def _theta_deg(p) -> float:
    """Rebuild θ in [0, 360) from the exact sin/cos — the true quadrant angle."""
    t = math.degrees(math.atan2(float(p["sin_t"]), float(p["cos_t"])))
    return t % 360.0


def _params(seed):
    return _gen(random.Random(seed))


def test_answers_match_numeric_oracle():
    for seed in range(200):
        p = _params(seed)
        th = _theta_deg(p)

        # 5.1.1
        assert abs(float(p["answer_sin2"]) - math.sin(math.radians(th)) ** 2) < 1e-9

        # 5.1.2 — evaluate the reduction's LHS directly and confirm the identity
        func, base, tsign = p["reduction_lhs"]
        lhs = _FUNC[func](math.radians(base + tsign * th))
        assert abs(float(p["answer_reduction"]) - lhs) < 1e-9, seed

        # 5.1.3 — evaluate the compound angle directly
        ang = th + p["compound_sign"] * p["compound_a_deg"]
        comp = _FUNC[p["compound_outer"]](math.radians(ang))
        assert abs(float(p["answer_compound"]) - comp) < 1e-9, seed


def test_quadrant_signs_are_consistent():
    for seed in range(200):
        p = _params(seed)
        q = p["quadrant"]
        cos_pos = p["cos_t"] > 0
        sin_pos = p["sin_t"] > 0
        assert cos_pos == (q == 4)  # cos > 0 only in Q4 (of {2,3,4})
        assert sin_pos == (q == 2)  # sin > 0 only in Q2


def test_compound_value_is_a_surd():
    # the special angle A always injects a √2 or √3, so the answer is irrational
    surd = 0
    for seed in range(60):
        p = _params(seed)
        if not p["answer_compound"].is_rational:
            surd += 1
    assert surd == 60


def test_variety():
    seen = set()
    for s in range(200):
        p = _params(s)
        seen.add((p["cos_t"], p["reduction_latex"], p["compound_latex"]))
    assert len(seen) >= 60


def _rate(inst, *answers):
    attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
    return inst.verifier.rate(attempt)


def test_verifier_grades_exact_and_decimal():
    eng = Engine(registry=InMemoryRegistry({trig_given_ratio.id: trig_given_ratio}))
    for seed in range(40):
        inst = eng.instantiate(trig_given_ratio.id, seed=seed)
        p = inst.params
        keys = ["answer_sin2", "answer_reduction", "answer_compound"]
        exact = _rate(inst, *(p[k] for k in keys))
        assert exact.marks_awarded == 3 and exact.is_correct, seed
        # calculator decimals also land
        dec = [sympy.Float(round(float(p[k]), 4)) for k in keys]
        assert _rate(inst, *dec).marks_awarded == 3, seed


def test_partial_credit():
    eng = Engine(registry=InMemoryRegistry({trig_given_ratio.id: trig_given_ratio}))
    inst = eng.instantiate(trig_given_ratio.id, seed=1)
    p = inst.params
    res = _rate(
        inst,
        p["answer_sin2"],
        p["answer_reduction"] + 1,  # wrong
        p["answer_compound"],
    )
    assert res.marks_awarded == 2 and not res.is_correct


def test_source_instance_reachable():
    # NSC 2025 M/J P2 Q5: cos θ = −5/13 with 180° < θ < 360° (⇒ Q3 here)
    for seed in range(400):
        p = _params(seed)
        if p["cos_t"] == sympy.Rational(-5, 13) and p["quadrant"] == 3:
            assert p["answer_sin2"] == sympy.Rational(144, 169)
            return
    raise AssertionError("source instance cos θ = −5/13, Q3 not reached in 400 seeds")


def test_template_is_shared_stem_compound():
    from worksheets.generate import PROBLEMS, template_trig_given_ratio

    p = _params(1)
    for detail in ("full", "short"):
        card = template_trig_given_ratio(p, detail=detail)
        assert len(card.subparts) == 3
        assert sum(sp.marks for sp in card.subparts) == 9
        assert sum(sp.auto_marks for sp in card.subparts) == 3
        assert not card.worked_steps
        assert all(sp.memo_steps for sp in card.subparts)
    assert trig_given_ratio.id in PROBLEMS
