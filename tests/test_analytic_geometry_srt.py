"""
Analytical geometry — ``analytic_geometry_srt`` (P2 Q3).

Every stored answer is checked against an independent numeric oracle rebuilt
straight from the five integer inputs (k, r, t, s, m): the intercept condition,
the distance, the given ratio, the perpendicular foot of R on ST (computed by a
vector projection that never touches the generator's own foot routine), and the
shoelace area of RVTR′. None of this reuses the generator's derived keys.
"""

from __future__ import annotations

import math
import random

import sympy

from content.examples.analytic_geometry_srt import _generate, problem
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep


def _params(seed):
    return _generate(random.Random(seed))


def _foot_numeric(r, m, s_y, t):
    """Foot of perpendicular from R(r,0) onto line S(m,s)->T(0,t), plus λ."""
    ax, ay, bx, by = m, s_y, 0, t
    dx, dy = bx - ax, by - ay
    lam = ((r - ax) * dx + (0 - ay) * dy) / (dx * dx + dy * dy)
    return ax + lam * dx, ay + lam * dy, lam


def test_R_is_on_the_line_and_x_axis():
    for seed in range(120):
        p = _params(seed)
        k, r, t = p["k"], p["r"], p["t"]
        assert int(p["answer_R_x"]) == r
        assert k * r - 0 + t == 0  # R(r,0) satisfies kx - y + t = 0
        assert r < 0  # R on the negative x-axis


def test_RT_is_distance_R_to_T():
    for seed in range(120):
        p = _params(seed)
        r, t = p["r"], p["t"]
        assert abs(float(p["answer_RT"]) - math.hypot(r, t)) < 1e-9


def test_ratio_and_m_are_consistent():
    for seed in range(160):
        p = _params(seed)
        r, t, s_y, m = p["r"], p["t"], p["s_y"], p["m"]
        rt2, sr2 = r * r + t * t, (m - r) ** 2 + s_y**2
        # the presented ratio q·RT² = p·SR² really holds
        assert p["q_coef"] * rt2 == p["p_coef"] * sr2
        assert p["p_coef"] != p["q_coef"]
        assert int(p["answer_m"]) == m
        assert m < r  # S is left of R (the disambiguating root)
        # the other root sits to the right of R, so the diagram fact is needed
        assert 2 * r - m > r


def test_V_is_the_perpendicular_foot_inside_the_segment():
    for seed in range(160):
        p = _params(seed)
        vx, vy, lam = _foot_numeric(p["r"], p["m"], p["s_y"], p["t"])
        assert abs(float(p["answer_Vx"]) - vx) < 1e-9
        assert abs(float(p["answer_Vy"]) - vy) < 1e-9
        assert 0 < lam < 1  # foot lies strictly between S and T


def test_VR_line_is_perpendicular_and_through_R_and_V():
    for seed in range(160):
        p = _params(seed)
        g, c = float(p["answer_VR_gradient"]), float(p["answer_VR_intercept"])
        # perpendicular to ST
        assert abs(g * float(p["grad_st"]) + 1) < 1e-9
        # passes through R(r,0) and V
        assert abs(g * p["r"] + c) < 1e-9
        assert abs(g * float(p["answer_Vx"]) + c - float(p["answer_Vy"])) < 1e-9


def test_area_is_shoelace_of_RVTRprime():
    for seed in range(160):
        p = _params(seed)
        pts = [
            (p["r"], 0.0),
            (float(p["answer_Vx"]), float(p["answer_Vy"])),
            (0.0, p["t"]),
            (p["r_refl"], 0.0),
        ]
        acc = 0.0
        for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
            acc += x0 * y1 - x1 * y0
        assert abs(float(p["answer_area"]) - abs(acc) / 2) < 1e-9
        assert p["r_refl"] == -p["r"]


def test_variety():
    seen = set()
    for s in range(300):
        p = _params(s)
        seen.add((p["k"], p["r"], p["t"], p["s_y"], p["m"]))
    assert len(seen) >= 30


_KEYS = [
    "answer_R_x",
    "answer_RT",
    "answer_m",
    "answer_VR_gradient",
    "answer_VR_intercept",
    "answer_Vx",
    "answer_Vy",
    "answer_area",
]


def _rate(inst, *answers):
    return inst.verifier.rate(
        SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
    )


def test_verifier_grades_all_twelve():
    eng = Engine(registry=InMemoryRegistry({problem.id: problem}))
    for seed in range(40):
        inst = eng.instantiate(problem.id, seed=seed)
        p = inst.params
        r = _rate(inst, *(p[k] for k in _KEYS))
        assert r.marks_awarded == 12 and r.is_correct, seed


def test_wrong_area_loses_only_its_marks():
    eng = Engine(registry=InMemoryRegistry({problem.id: problem}))
    inst = eng.instantiate(problem.id, seed=1)
    p = inst.params
    answers = [p[k] for k in _KEYS]
    answers[-1] = p["answer_area"] + 1  # wrong area (worth 2)
    r = _rate(inst, *answers)
    assert r.marks_awarded == 10 and not r.is_correct


def test_source_instance_reachable():
    # NSC 2025 M/J P2 Q3: RT 2x-y+10=0, S(m;1), 2RT²=5SR² → m=-12, V=(-8;4), area 75
    for seed in range(900):
        p = _params(seed)
        if (p["r"], p["t"], p["s_y"], p["m"]) == (-5, 10, 1, -12):
            assert (p["q_coef"], p["p_coef"]) == (2, 5)
            assert p["answer_RT"] == 5 * sympy.sqrt(5)
            assert (int(p["answer_Vx"]), int(p["answer_Vy"])) == (-8, 4)
            assert int(p["answer_area"]) == 75
            return
    raise AssertionError("source instance RT 2x-y+10=0, S(m;1), m=-12 not reached")


def test_template_is_shared_stem_compound():
    from worksheets.generate import PROBLEMS, template_analytic_geometry_srt

    p = _params(1)
    for detail in ("full", "short"):
        card = template_analytic_geometry_srt(p, detail=detail)
        assert len(card.subparts) == 6
        assert sum(sp.marks for sp in card.subparts) == 21
        assert sum(sp.auto_marks for sp in card.subparts) == 12
        assert not card.worked_steps
        assert all(sp.memo_steps for sp in card.subparts)
    assert problem.id in PROBLEMS
    # the unknown m must not be pre-revealed in the shared stem
    assert f"({p['m']};{p['s_y']})" not in card.instruction
