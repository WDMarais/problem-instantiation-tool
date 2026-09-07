"""
3-D trigonometry — ``trig_3d_tower`` (P2 Q8).

Answers are re-derived from the raw givens: the sine rule in the horizontal
triangle AFB for AF, then tan θ in the vertical right-triangle AFT for the tower
height TF. 8.2 ("show that TF = AF·tan θ") is a hand-marked derivation, so only
AF and TF reach the verifier.
"""

from __future__ import annotations

import math
import random

from content.examples.trig_3d_tower import _generate, problem
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep


def _params(seed):
    return _generate(random.Random(seed))


def test_ground_triangle_and_height_reconstructed():
    for seed in range(200):
        p = _params(seed)
        a, b, th, d = p["alpha"], p["beta"], p["theta"], p["d"]
        third = 180 - a - b
        assert p["angle_F"] == third
        assert 35 <= third  # non-degenerate
        af = d * math.sin(math.radians(b)) / math.sin(math.radians(third))
        bf = d * math.sin(math.radians(a)) / math.sin(math.radians(third))
        tf = af * math.tan(math.radians(th))
        assert abs(p["answer_AF"] - round(af, 2)) < 1e-9
        assert abs(p["answer_BF"] - round(bf, 2)) < 1e-9
        assert abs(p["answer_TF"] - round(tf, 2)) < 1e-9
        # the 8.2 relation the candidate must show
        assert abs(p["answer_TF"] - p["answer_AF"] * math.tan(math.radians(th))) < 0.02


def test_af_differs_from_bf():
    for seed in range(100):
        p = _params(seed)
        assert p["alpha"] != p["beta"]
        assert p["answer_AF"] != p["answer_BF"]


def test_variety():
    seen = {
        (p["alpha"], p["beta"], p["theta"], p["d"])
        for p in (_params(s) for s in range(300))
    }
    assert len(seen) >= 40


def _rate(inst, *answers):
    return inst.verifier.rate(
        SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
    )


def test_verifier_grades_all_six():
    eng = Engine(registry=InMemoryRegistry({problem.id: problem}))
    for seed in range(40):
        inst = eng.instantiate(problem.id, seed=seed)
        p = inst.params
        r = _rate(inst, p["answer_AF"], p["answer_TF"])
        assert r.marks_awarded == 6 and r.is_correct, seed


def test_wrong_af_loses_its_three_marks():
    eng = Engine(registry=InMemoryRegistry({problem.id: problem}))
    inst = eng.instantiate(problem.id, seed=3)
    p = inst.params
    r = _rate(inst, p["answer_AF"] + 5, p["answer_TF"])  # AF wrong, TF right
    assert r.marks_awarded == 3 and not r.is_correct


def test_template_is_shared_stem_compound():
    from worksheets.generate import PROBLEMS, template_trig_3d_tower

    p = _params(1)
    for detail in ("full", "short"):
        card = template_trig_3d_tower(p, detail=detail)
        assert len(card.subparts) == 3
        assert sum(sp.marks for sp in card.subparts) == 8
        assert sum(sp.auto_marks for sp in card.subparts) == 6  # 8.2 is hand-marked
        assert not card.worked_steps
        assert all(sp.memo_steps for sp in card.subparts)
        assert card.graph_svg and "<svg" in card.graph_svg
    assert problem.id in PROBLEMS
    # 8.2 asks to *show* TF = AF·tan θ; the height value must not be handed over there
    assert str(p["answer_TF"]) not in card.subparts[1].instruction
