"""
Trigonometry — ``trig_given_ratio`` (the shared-stem P2 Q5.1).

Given one ratio (cos θ) and the quadrant, derive three things without a calculator:

    5.1.1  sin²θ                                    (Pythagoras + the quadrant sign)
    5.1.2  a reduction-formula ratio, e.g. tan(360° − θ) = −tan θ
    5.1.3  a compound-angle value, e.g. cos(θ − 135°) = cos θ cos135° + sin θ sin135°

A Pythagorean triple (adj, opp, hyp) and a quadrant fix θ exactly: cos θ = ±adj/hyp
and sin θ = ±opp/hyp with the CAST signs. The reduction ratio is one of the standard
co-terminal/co-function reductions (its answer is a signed rational); the compound-angle
value is a genuine surd (a special angle A with exact sin/cos). Every answer is an exact
SymPy value, graded with ``symbolic_equality`` (which accepts an equivalent surd form or
the calculator decimal).

Well-posed for every draw — the quadrant range pins all signs and the triple legs are a
real right triangle — so no F1 scope predicate. Engine-graded canonical total = 3 of
the 9 headline marks (the final value of each part); the Pythagoras/quadrant/expansion
method lines are hand-marked.

(Q5.2 "simplify an identity to a single ratio" and Q5.3 the special tan-product are a
fixed-answer / symbolic-in-x shape with little seed-to-seed variation, so they are left
for a later slot rather than forced into this generator.)
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

# (adjacent, opposite, hypotenuse) — real primitive right triangles
_TRIPLES = ((3, 4, 5), (5, 12, 13), (8, 15, 17), (7, 24, 25), (20, 21, 29))

# quadrant → (cos sign, sin sign) and its exact degree range
_QUAD = {
    2: (-1, 1, r"90^\circ < \theta < 180^\circ"),
    3: (-1, -1, r"180^\circ < \theta < 270^\circ"),
    4: (1, -1, r"270^\circ < \theta < 360^\circ"),
}


def _exact(deg: int):
    """Exact sin/cos of a special angle in degrees (SymPy surds)."""
    rad = sympy.pi * sympy.Rational(deg, 180)
    return sympy.cos(rad), sympy.sin(rad)


def _gen(rng: random.Random) -> dict:
    adj0, opp0, hyp = rng.choice(_TRIPLES)
    adj, opp = (adj0, opp0) if rng.random() < 0.5 else (opp0, adj0)  # swap → variety
    q = rng.choice((2, 3, 4))
    sx, sy, rng_latex = _QUAD[q]

    cos_t = sympy.Rational(sx * adj, hyp)
    sin_t = sympy.Rational(sy * opp, hyp)
    tan_t = sin_t / cos_t

    # 5.1.2 — one standard reduction. Each row carries a display, the reduced middle
    # step, its exact value, and an (outer func, base angle, θ-sign) descriptor so a
    # test can recompute the LHS  func(base° + sign·θ)  independently.
    reductions = [
        (r"\tan(360^\circ - \theta)", r"-\tan\theta", -tan_t, ("tan", 360, -1)),
        (r"\sin(180^\circ + \theta)", r"-\sin\theta", -sin_t, ("sin", 180, 1)),
        (r"\cos(180^\circ - \theta)", r"-\cos\theta", -cos_t, ("cos", 180, -1)),
        (r"\sin(360^\circ - \theta)", r"-\sin\theta", -sin_t, ("sin", 360, -1)),
        (r"\tan(180^\circ - \theta)", r"-\tan\theta", -tan_t, ("tan", 180, -1)),
        (r"\cos(-\theta)", r"\cos\theta", cos_t, ("cos", 0, -1)),
    ]
    red_latex, red_mid_latex, red_val, red_lhs = rng.choice(reductions)

    # 5.1.3 — a compound-angle value; special angle A ⇒ a genuine surd
    a_deg = rng.choice((30, 45, 60, 120, 135, 150))
    outer = rng.choice(("cos", "sin"))
    sign = rng.choice((-1, 1))  # θ − A  or  θ + A
    cos_a, sin_a = _exact(a_deg)
    ct, st = sympy.latex(cos_t), sympy.latex(sin_t)
    ca, sa = sympy.latex(cos_a), sympy.latex(sin_a)
    if outer == "cos":
        # cos(θ ∓ A) = cosθ cosA ± sinθ sinA
        compound = cos_t * cos_a - sign * sin_t * sin_a
        mid_op = "+" if sign == -1 else "-"
        expand = rf"({ct})({ca}) {mid_op} ({st})({sa})"
    else:
        # sin(θ ∓ A) = sinθ cosA ∓ cosθ sinA
        compound = sin_t * cos_a + sign * cos_t * sin_a
        mid_op = "-" if sign == -1 else "+"
        expand = rf"({st})({ca}) {mid_op} ({ct})({sa})"
    compound = sympy.nsimplify(sympy.simplify(compound))
    op_latex = "-" if sign == -1 else "+"
    comp_latex = rf"\{outer}(\theta {op_latex} {a_deg}^\circ)"

    return {
        "adj": adj,
        "opp": opp,
        "hyp": hyp,
        "quadrant": q,
        "range_latex": rng_latex,
        "cos_t": cos_t,
        "sin_t": sin_t,
        "tan_t": tan_t,
        "reduction_latex": red_latex,
        "reduction_mid_latex": red_mid_latex,
        "reduction_lhs": red_lhs,  # (func, base°, θ-sign) — for an independent oracle
        "compound_latex": comp_latex,
        "compound_expand_latex": expand,
        "compound_outer": outer,  # "cos" | "sin"
        "compound_a_deg": a_deg,
        "compound_sign": sign,  # −1 ⇒ θ − A, +1 ⇒ θ + A
        "answer_sin2": sin_t**2,  # 5.1.1
        "answer_reduction": red_val,  # 5.1.2
        "answer_compound": compound,  # 5.1.3
    }


trig_given_ratio = Problem(
    id="trig_given_ratio",
    type_id="trig_given_ratio",
    name="Given cos θ and the quadrant — sin²θ, a reduction ratio, a compound angle",
    artifact_type="practice",
    problem_spec=_gen,
    verifier_spec=[
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "answer_sin2"},
        {
            "kind": "symbolic_equality",
            "marks_possible": 1,
            "param_key": "answer_reduction",
        },
        {
            "kind": "symbolic_equality",
            "marks_possible": 1,
            "param_key": "answer_compound",
        },
    ],
    corpus_anchor=CorpusAnchor(
        paper="2025 May/June P2",
        question="5.1",
        marks=9,
    ),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(registry=InMemoryRegistry({trig_given_ratio.id: trig_given_ratio}))
    for seed in range(5):
        inst = engine.instantiate(trig_given_ratio.id, seed=seed)
        p = inst.params
        print(
            f"seed {seed}: q{p['quadrant']} cosθ={p['cos_t']} "
            f"| 5.1.3 {p['compound_latex']} = {p['answer_compound']}"
        )
        keys = ["answer_sin2", "answer_reduction", "answer_compound"]
        attempt = SolutionAttempt(steps=[SubmittedStep(p[k]) for k in keys])
        r = inst.verifier.rate(attempt)
        print(f"  all-correct → {r.marks_awarded}/{r.marks_possible} ok={r.is_correct}")
