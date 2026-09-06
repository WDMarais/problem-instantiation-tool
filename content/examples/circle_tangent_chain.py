"""
Analytical geometry — the circle/tangent chain (P2 Q4).

One instance drives seven sub-parts that fan out from a circle centred on the
x-axis at M(a; 0) with radius 5, a lattice point E on it, the tangent at E, and
a point C on that tangent:

  4.1 the tangent-radius angle CÊM (always 90°),
  4.2 the tangent EC: y = mx + c,
  4.3 the length DM, where D is the tangent's x-intercept,
  4.4 the value p, with C(cx; p) on the tangent,
  4.5 S so that SEMC is a parallelogram (S = E − M + C), x_S < 0,
  4.6 whether S is inside/outside the circle after the radius grows by Δ,
  4.7 the angle ÊTM, where MT (a radius toward C) is produced to C.

Keeping M on the x-axis (as the source does) makes D and DM rational. The
instance is searched so p is an integer, C sits outside the circle, x_S < 0, and
the inside/outside comparison in 4.6 is unambiguous. Everything but 4.7 is exact
rational/surd; 4.7 is an angle graded numerically (tolerance). A diagram orients
the figure — points are labelled by letter only, so no answer is given away.
"""

from __future__ import annotations

import math
import random

import sympy

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

_x = sympy.Symbol("x")
_R = 5  # radius (integer lattice points E available in all 8 diagonal directions)
_OFFSETS = (
    (3, 4),
    (4, 3),
    (3, -4),
    (4, -3),
    (-3, 4),
    (-4, 3),
    (-3, -4),
    (-4, -3),
)
_DELTAS = (5, 6, 7, 8)  # radius increase for 4.6


def _generate(rng: random.Random) -> dict:
    for _ in range(4000):
        a = rng.randint(-3, 7)
        dx, dy = rng.choice(_OFFSETS)
        ex, ey = a + dx, dy  # E on the circle (M = (a, 0))

        m = sympy.Rational(-dx, dy)  # tangent ⊥ radius
        c = sympy.Integer(ey) - m * ex
        d_x = -c / m  # tangent's x-intercept D = (d_x, 0)
        dm = abs(sympy.Integer(a) - d_x)  # M and D both on the x-axis

        cx = rng.randint(a - 14, a + 14)
        p = m * cx + c
        if p != int(p):
            continue
        p = int(p)
        if abs(p) > 12:  # keep C (and the diagram viewport) exam-sized
            continue
        if cx == ex:  # C must differ from E
            continue
        if (cx - a) ** 2 + p**2 <= _R**2:  # C must lie outside the circle
            continue
        s_x, s_y = ex - a + cx, ey + p  # S = E - M + C
        if s_x >= 0:  # the x_S < 0 branch of the parallelogram
            continue

        delta = rng.choice(_DELTAS)
        r_new2 = (_R + delta) ** 2
        ms2 = (a - s_x) ** 2 + s_y**2
        if abs(ms2 - r_new2) < 3:  # keep the comparison off the boundary
            continue
        region = "outside" if ms2 > r_new2 else "inside"

        # 4.7: angle ÊTM. MT is a radius toward C, so ∠EMT = ∠(E−M, C−M);
        # ME = MT = R, so the isosceles base angle ∠ETM = (180 − ∠EMT)/2.
        ux, uy = dx, dy  # E − M
        wx, wy = cx - a, p  # C − M
        cos_emt = (ux * wx + uy * wy) / (_R * math.hypot(wx, wy))
        angle_emt = math.degrees(math.acos(max(-1.0, min(1.0, cos_emt))))
        angle_etm = (180.0 - angle_emt) / 2.0

        return {
            "a": a,
            "dx": dx,
            "dy": dy,
            "ex": ex,
            "ey": ey,
            "cx": cx,
            "delta": delta,
            "radius_sq": _R**2,
            "answer_angle_cem": sympy.Integer(90),
            "tangent_gradient": m,
            "tangent_c": c,
            "tangent_rhs": m * _x + c,
            "d_x": d_x,
            "answer_DM": dm,
            "answer_p": sympy.Integer(p),
            "answer_Sx": sympy.Integer(s_x),
            "answer_Sy": sympy.Integer(s_y),
            "answer_MS": sympy.sqrt(ms2),
            "answer_region": region,
            "r_new": _R + delta,
            "ms2": ms2,
            "answer_angle_etm": round(angle_etm, 2),
        }
    raise RuntimeError("circle_tangent_chain: no clean instance found")


problem = Problem(
    id="circle_tangent_chain",
    type_id="circle_tangent",
    name="Circle/tangent chain: angle, tangent, DM, p, parallelogram, region, ÊTM",
    artifact_type="practice",
    problem_spec=_generate,
    verifier_spec=[
        {
            "kind": "numeric_equality",
            "marks_possible": 1,
            "param_key": "answer_angle_cem",
        },
        {
            "kind": "symbolic_equality",
            "marks_possible": 1,
            "param_key": "tangent_gradient",
        },
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "tangent_c"},
        {"kind": "symbolic_equality", "marks_possible": 2, "param_key": "answer_DM"},
        # 4.4 "show that p = …" gives the value in the question, so there is nothing
        # for the engine to grade — it is a hand-marked step (auto 0), not scored here.
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "answer_Sx"},
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "answer_Sy"},
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "answer_MS"},
        {"kind": "exact_equality", "marks_possible": 1, "param_key": "answer_region"},
        {
            "kind": "numeric_equality",
            "marks_possible": 2,
            "param_key": "answer_angle_etm",
            "tolerance": 0.5,
        },
    ],
    corpus_anchor=CorpusAnchor(
        paper="2025 May/June P2",
        question="4",
        marks=20,
    ),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(registry=InMemoryRegistry({problem.id: problem}))
    inst = engine.instantiate(problem.id, seed=42)
    p = inst.params
    print(f"circle (x-{p['a']})^2+y^2=25  E=({p['ex']};{p['ey']})")
    print(f"C=({p['cx']};{p['answer_p']})  tangent y={sympy.latex(p['tangent_rhs'])}")
    print(f"DM={p['answer_DM']}  S=({p['answer_Sx']};{p['answer_Sy']})")
    print(f"MS={p['answer_MS']}  r_new={p['r_new']} -> {p['answer_region']}")
    print(f"angle ETM={p['answer_angle_etm']}")

    keys = [
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
    attempt = SolutionAttempt(steps=[SubmittedStep(p[k]) for k in keys])
    res = inst.verifier.rate(attempt)
    print(f"all correct: {res.marks_awarded}/{res.marks_possible} ok={res.is_correct}")
