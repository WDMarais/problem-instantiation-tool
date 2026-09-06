"""
Analytical geometry — ``circle_tangent_chain`` (P2 Q4).

Answers are checked against independent reconstructions from the raw inputs: the
tangent/radius perpendicularity, the x-intercept D and DM, the point C on the
tangent, the parallelogram S = E − M + C, the inside/outside comparison, and the
angle ÊTM — the last computed at the T-vertex of ΔEMT (via T's actual
coordinates), not the generator's isosceles shortcut.
"""

from __future__ import annotations

import math
import random

import sympy

from content.examples.circle_tangent_chain import _generate, problem
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

_R = 5


def _params(seed):
    return _generate(random.Random(seed))


def test_E_on_circle_and_tangent_perpendicular_through_E():
    for seed in range(150):
        p = _params(seed)
        a, ex, ey = p["a"], p["ex"], p["ey"]
        assert (ex - a) ** 2 + ey**2 == _R**2
        m_me = sympy.Rational(ey, ex - a)
        assert p["tangent_gradient"] * m_me == -1  # tangent ⊥ radius
        assert p["tangent_gradient"] * ex + p["tangent_c"] == ey  # through E


def test_D_and_DM():
    for seed in range(150):
        p = _params(seed)
        assert p["tangent_gradient"] * p["d_x"] + p["tangent_c"] == 0  # D on tangent
        assert p["answer_DM"] == abs(sympy.Integer(p["a"]) - p["d_x"])


def test_p_and_parallelogram_S():
    for seed in range(150):
        p = _params(seed)
        cx, pp = p["cx"], int(p["answer_p"])
        assert p["tangent_gradient"] * cx + p["tangent_c"] == pp  # C on tangent
        # S = E - M + C
        assert int(p["answer_Sx"]) == p["ex"] - p["a"] + cx
        assert int(p["answer_Sy"]) == p["ey"] + pp
        assert int(p["answer_Sx"]) < 0  # the x_S < 0 branch


def test_region_matches_distance_comparison():
    for seed in range(200):
        p = _params(seed)
        ms2 = (p["a"] - int(p["answer_Sx"])) ** 2 + int(p["answer_Sy"]) ** 2
        assert p["answer_MS"] ** 2 == ms2
        outside = ms2 > p["r_new"] ** 2
        assert p["answer_region"] == ("outside" if outside else "inside")
        assert abs(ms2 - p["r_new"] ** 2) >= 3  # comparison stays off the boundary


def test_angle_etm_via_triangle_vertex():
    for seed in range(200):
        p = _params(seed)
        a, ex, ey, cx, pp = p["a"], p["ex"], p["ey"], p["cx"], int(p["answer_p"])
        # T = M + R·(C − M)/|C − M|  (MT is a radius produced toward C)
        wx, wy = cx - a, pp
        wlen = math.hypot(wx, wy)
        tx, ty = a + _R * wx / wlen, _R * wy / wlen
        # angle at T in triangle E-T-M, from the two edge vectors
        e_t = (ex - tx, ey - ty)
        m_t = (a - tx, 0 - ty)
        cos_t = (e_t[0] * m_t[0] + e_t[1] * m_t[1]) / (
            math.hypot(*e_t) * math.hypot(*m_t)
        )
        angle = math.degrees(math.acos(max(-1.0, min(1.0, cos_t))))
        assert abs(angle - p["answer_angle_etm"]) < 0.05, seed


def test_variety():
    seen = set()
    for s in range(300):
        p = _params(s)
        seen.add((p["a"], p["dx"], p["dy"], p["cx"], p["delta"]))
    assert len(seen) >= 40


def test_both_regions_occur():
    regions = {_params(s)["answer_region"] for s in range(200)}
    assert regions == {"inside", "outside"}


_KEYS = [
    "answer_angle_cem",
    "tangent_gradient",
    "tangent_c",
    "answer_DM",
    "answer_Sx",
    "answer_Sy",
    "answer_MS",
    "answer_region",
    "answer_angle_etm",
]


def _rate(inst, *answers):
    return inst.verifier.rate(
        SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
    )


def test_verifier_grades_all_eleven():
    eng = Engine(registry=InMemoryRegistry({problem.id: problem}))
    for seed in range(40):
        inst = eng.instantiate(problem.id, seed=seed)
        p = inst.params
        r = _rate(inst, *(p[k] for k in _KEYS))
        assert r.marks_awarded == 11 and r.is_correct, seed


def test_wrong_region_and_angle_lose_only_their_marks():
    eng = Engine(registry=InMemoryRegistry({problem.id: problem}))
    inst = eng.instantiate(problem.id, seed=2)
    p = inst.params
    answers = [p[k] for k in _KEYS]
    flip = "inside" if p["answer_region"] == "outside" else "outside"
    answers[7] = flip  # wrong region (worth 1)
    answers[8] = p["answer_angle_etm"] + 10  # wrong angle (worth 2)
    r = _rate(inst, *answers)
    assert r.marks_awarded == 11 - 3 and not r.is_correct


def test_source_instance_reachable():
    # NSC 2025 M/J P2 Q4: (x−3)²+y²=25, E(−1;3), tangent 4x/3+13/3, p=−5,
    # S(−11;−2), MS=10√2, ÊTM≈58.28°
    for seed in range(1200):
        p = _params(seed)
        if (p["a"], p["dx"], p["dy"], p["cx"]) == (3, -4, 3, -7):
            assert p["tangent_gradient"] == sympy.Rational(4, 3)
            assert p["tangent_c"] == sympy.Rational(13, 3)
            assert p["answer_DM"] == sympy.Rational(25, 4)
            assert int(p["answer_p"]) == -5
            assert (int(p["answer_Sx"]), int(p["answer_Sy"])) == (-11, -2)
            assert p["answer_MS"] == 10 * sympy.sqrt(2)
            assert abs(p["answer_angle_etm"] - 58.28) < 0.05
            return
    raise AssertionError("source instance (x−3)²+y²=25, E(−1;3), C(−7;p) not reached")


def test_template_is_shared_stem_compound():
    from worksheets.generate import PROBLEMS, template_circle_tangent_chain

    p = _params(1)
    for detail in ("full", "short"):
        card = template_circle_tangent_chain(p, detail=detail)
        assert len(card.subparts) == 7
        assert sum(sp.marks for sp in card.subparts) == 20
        assert sum(sp.auto_marks for sp in card.subparts) == 11  # 4.4 is hand-marked
        assert not card.worked_steps
        assert all(sp.memo_steps for sp in card.subparts)
    assert problem.id in PROBLEMS
    # the stem shows C(cx; p) with the literal p, and does not draw/reveal S
    assert f";{int(p['answer_p'])})" not in card.instruction
    assert "S" not in card.instruction.replace("EC", "").replace("SEMC", "")
