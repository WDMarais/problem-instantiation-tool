"""
Analytical geometry — the ΔSRT chain (P2 Q3).

One instance drives six sub-parts that fan out from three shared points:
R on the x-axis, T on the y-axis, S(m; s) to the left of R, and the line
RT: kx − y + t = 0. Everything downstream — the length RT, the value of m
(from a given RT²:SR² ratio), the perpendicular foot V of R onto ST, and the
area of the quadrilateral RVTR′ (R′ the reflection of R in the y-axis) — is
forced by those points. A dict spec cannot express this fan-out; a code
generator can, and stores each answer under its own key so the verifier can
route a canonical to every sub-part.

The instance is searched (not clamped) so that V is rational and lies strictly
between S and T on the segment — i.e. the foot really sits inside the drawn
triangle, as the exam's diagram shows — while keeping the given ratio small and
integer. No diagram is emitted: every part is answerable from the line equation
and the given facts, so the question is fully engine-graded.
"""

from __future__ import annotations

import random
from math import gcd

import sympy

from problem_instantiation_tool.schemas import Problem

_K = (1, 2, 3)  # gradient of RT (keeps R an integer x-intercept)
_ABS_R = (2, 3, 4, 5, 6, 7, 8, 9, 10)  # |R_x|
_S_Y = (1, 2, 3)  # height of S


def _foot(r, s_x, s_y, t):
    """Foot of the perpendicular from R(r,0) to the line ST through
    S(s_x, s_y) and T(0, t), as an exact SymPy point, plus the parameter λ
    with V = S + λ(T − S)."""
    sx, sy, tt, rr = (sympy.Integer(v) for v in (s_x, s_y, t, r))
    dx, dy = -sx, tt - sy  # direction S → T
    denom = dx * dx + dy * dy
    lam = ((rr - sx) * dx + (0 - sy) * dy) / denom
    vx = sx + lam * dx
    vy = sy + lam * dy
    return vx, vy, lam


def _generate(rng: random.Random) -> dict:
    combos = [(k, ar, sy) for k in _K for ar in _ABS_R for sy in _S_Y]
    rng.shuffle(combos)
    for k, abs_r, s_y in combos:
        r = -abs_r
        t = k * abs_r  # T = (0, t); RT: y = kx + t through R(r, 0)
        m_choices = list(range(r - 16, r))  # strictly left of R
        rng.shuffle(m_choices)
        for m in m_choices:
            if m == 0:
                continue
            rt2 = r * r + t * t
            sr2 = (m - r) ** 2 + s_y**2
            g = gcd(rt2, sr2)
            p_coef, q_coef = rt2 // g, sr2 // g  # q·RT² = p·SR²
            if p_coef == q_coef or max(p_coef, q_coef) > 20:
                continue
            if t == s_y:  # ST would be horizontal → VR vertical, no y = mx + c
                continue
            vx, vy, lam = _foot(r, m, s_y, t)
            if not (0 < lam < 1):  # V must sit inside segment ST
                continue
            if vx.q > 6 or vy.q > 6:  # keep V readable
                continue

            grad_st = sympy.Rational(t - s_y, -m)  # (t − s)/(0 − m)
            vr_grad = -1 / grad_st
            vr_c = -vr_grad * r  # through R(r, 0)
            r_refl = -r
            # shoelace of R, V, T, R′ (in order)
            pts = [(r, 0), (vx, vy), (0, t), (r_refl, 0)]
            acc = sympy.Integer(0)
            for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
                acc += x0 * y1 - x1 * y0
            area = sympy.Rational(abs(acc), 2)

            return {
                "k": k,
                "r": r,
                "t": t,
                "s_y": s_y,
                "m": m,
                "p_coef": p_coef,
                "q_coef": q_coef,
                "rt2": rt2,
                "sr2": sr2,
                "grad_st": grad_st,
                "answer_R_x": sympy.Integer(r),
                "answer_RT": sympy.sqrt(rt2),
                "answer_m": sympy.Integer(m),
                "answer_VR_gradient": vr_grad,
                "answer_VR_intercept": vr_c,
                "answer_Vx": vx,
                "answer_Vy": vy,
                "answer_area": area,
                "r_refl": r_refl,
            }
    raise RuntimeError("analytic_geometry_srt: no clean instance found")


problem = Problem(
    id="analytic_geometry_srt",
    type_id="analytic_geometry",
    name="Triangle SRT chain: intercepts, length, ratio, foot, reflected area",
    artifact_type="practice",
    problem_spec=_generate,
    verifier_spec=[
        {"kind": "symbolic_equality", "marks_possible": 2, "param_key": "answer_R_x"},
        {"kind": "symbolic_equality", "marks_possible": 2, "param_key": "answer_RT"},
        {"kind": "symbolic_equality", "marks_possible": 2, "param_key": "answer_m"},
        {
            "kind": "symbolic_equality",
            "marks_possible": 1,
            "param_key": "answer_VR_gradient",
        },
        {
            "kind": "symbolic_equality",
            "marks_possible": 1,
            "param_key": "answer_VR_intercept",
        },
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "answer_Vx"},
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "answer_Vy"},
        {"kind": "symbolic_equality", "marks_possible": 2, "param_key": "answer_area"},
    ],
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(registry=InMemoryRegistry({problem.id: problem}))
    inst = engine.instantiate(problem.id, seed=42)
    p = inst.params
    print(f"RT: {p['k']}x - y + {p['t']} = 0   R=({p['r']};0)  T=(0;{p['t']})")
    print(f"S=({p['m']};{p['s_y']})   ratio {p['q_coef']}RT²={p['p_coef']}SR²")
    print(
        f"RT={p['answer_RT']}  m={p['answer_m']}  V=({p['answer_Vx']};{p['answer_Vy']})"
    )
    print(f"VR grad={p['answer_VR_gradient']} c={p['answer_VR_intercept']}")
    print(f"area={p['answer_area']}")

    keys = [
        "answer_R_x",
        "answer_RT",
        "answer_m",
        "answer_VR_gradient",
        "answer_VR_intercept",
        "answer_Vx",
        "answer_Vy",
        "answer_area",
    ]
    attempt = SolutionAttempt(steps=[SubmittedStep(p[k]) for k in keys])
    res = inst.verifier.rate(attempt)
    print(f"all correct: {res.marks_awarded}/{res.marks_possible} ok={res.is_correct}")
