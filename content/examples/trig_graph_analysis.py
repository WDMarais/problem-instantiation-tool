"""
Trigonometry — ``trig_graph_analysis`` (the shared-stem P2 Q7).

Two curves on x ∈ [−180°, 180°]:  f(x) = a·cos x + q  and  g(x) = sin(bx).  Six
properties are read straight off the equations (no drawing, so the whole question is
engine-graded):

    7.1  range of f                                     [q − a ; q + a]
    7.2  period of g                                    360°/b
    7.3  where f is increasing                          (−180° ; 0°)   (f′ = −a sin x)
    7.4.1  where g·f′ < 0                                sin(bx)·sin x > 0
    7.4.2  where f ≤ 0                                   cos x ≤ −q/a
    7.5  g shifted s° right → h, in simplest form       sin(b(x − s°))

f is pinned so the 7.4.2 boundary −q/a is a nice cosine value (−½, 0, ½ ⇒ 120°, 90°,
60°); b ∈ {1, 2} and the right-shift s is chosen so h collapses to a single ±sin/±cos.
Every part is well-posed for every draw (a > 0, a real cosine level, a clean shift), so
no F1 scope predicate. The four interval answers are graded with ``set_solution``
(mutual subset), the period with ``numeric_equality`` and the shifted equation with
``symbolic_equality``; all 10 marks are engine-graded.
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

_X = sympy.Symbol("x", real=True)

# (a, q) with −q/a ∈ {−½, 0, ½} so f ≤ 0 has a nice boundary angle
_FQ = ((2, 1), (4, 2), (2, -1), (4, -2), (2, 0), (3, 0), (4, 0))
_B = (1, 2)
# right-shift options per b so sin(b(x − s°)) simplifies to a single ±sin/±cos
_SHIFT = {1: (90, 180, 270), 2: (45, 90, 135)}
# cos x ≤ c  ⇒  boundary angle B with cos B = c; f ≤ 0 on [−180;−B] ∪ [B;180]
_BOUNDARY = {sympy.Rational(-1, 2): 120, sympy.Integer(0): 90, sympy.Rational(1, 2): 60}


def _f_latex(a: int, q: int) -> str:
    coeff = "" if a == 1 else str(a)
    body = rf"{coeff}\cos x"
    if q > 0:
        body += rf" + {q}"
    elif q < 0:
        body += rf" - {abs(q)}"
    return body


def _iv_latex(lo, hi, lo_open: bool, hi_open: bool) -> str:
    lb, rb = ("(" if lo_open else "["), (")" if hi_open else "]")
    return rf"{lb}{lo}^\circ;\ {hi}^\circ{rb}"


def _gen(rng: random.Random) -> dict:
    a, q = rng.choice(_FQ)
    b = rng.choice(_B)
    s = rng.choice(_SHIFT[b])
    c = sympy.Rational(-q, a)  # the cos level for f ≤ 0
    boundary = _BOUNDARY[c]

    # 7.1 range of f
    range_set = sympy.Interval(q - a, q + a)
    range_latex = _iv_latex(q - a, q + a, False, False)

    # 7.3 f increasing: f′ = −a sin x > 0 ⇔ sin x < 0 ⇔ x ∈ (−180°, 0°)
    incr_set = sympy.Interval(-180, 0, left_open=True, right_open=True)
    incr_latex = _iv_latex(-180, 0, True, True)

    # 7.4.1 g·f′ < 0 ⇔ sin(bx)·sin x > 0  (f′ = −a sin x, a > 0)
    if b == 2:
        # 2 sin²x cos x > 0 ⇔ cos x > 0, sin x ≠ 0
        prod_set = sympy.Union(
            sympy.Interval(-90, 0, left_open=True, right_open=True),
            sympy.Interval(0, 90, left_open=True, right_open=True),
        )
        prod_latex = (
            _iv_latex(-90, 0, True, True) + r"\ \cup\ " + _iv_latex(0, 90, True, True)
        )
    else:
        # sin²x > 0 ⇔ sin x ≠ 0
        prod_set = sympy.Union(
            sympy.Interval(-180, 0, left_open=True, right_open=True),
            sympy.Interval(0, 180, left_open=True, right_open=True),
        )
        prod_latex = (
            _iv_latex(-180, 0, True, True) + r"\ \cup\ " + _iv_latex(0, 180, True, True)
        )

    # 7.4.2 f ≤ 0 ⇔ cos x ≤ c ⇔ x ∈ [−180°;−B] ∪ [B;180°]
    fneg_set = sympy.Union(
        sympy.Interval(-180, -boundary),
        sympy.Interval(boundary, 180),
    )
    fneg_latex = (
        _iv_latex(-180, -boundary, False, False)
        + r"\ \cup\ "
        + _iv_latex(boundary, 180, False, False)
    )

    # 7.5 shift g right by s°: h = sin(b(x − s°)) → a single ±sin/±cos
    shift_rad = sympy.pi * sympy.Rational(s, 180)
    shift_expr = sympy.simplify(sympy.sin(b * _X - b * shift_rad))

    return {
        "a": a,
        "q": q,
        "b": b,
        "shift_deg": s,
        "boundary": boundary,
        "f_latex": _f_latex(a, q),
        "g_latex": rf"\sin {b}x" if b != 1 else r"\sin x",
        "range_latex": range_latex,
        "incr_latex": incr_latex,
        "prod_latex": prod_latex,
        "fneg_latex": fneg_latex,
        "shift_latex": sympy.latex(shift_expr),
        "answer_range": range_set,  # 7.1
        "answer_period": sympy.Integer(360 // b),  # 7.2
        "answer_increasing": incr_set,  # 7.3
        "answer_prod_negative": prod_set,  # 7.4.1
        "answer_f_nonpositive": fneg_set,  # 7.4.2
        "answer_shift": shift_expr,  # 7.5
    }


trig_graph_analysis = Problem(
    id="trig_graph_analysis",
    type_id="trig_graph_analysis",
    name="Trig graphs — range, period, increasing, sign intervals, a right shift (Q7)",
    artifact_type="practice",
    problem_spec=_gen,
    verifier_spec=[
        {"kind": "set_solution", "marks_possible": 1, "param_key": "answer_range"},
        {"kind": "numeric_equality", "marks_possible": 1, "param_key": "answer_period"},
        {
            "kind": "set_solution",
            "marks_possible": 1,
            "param_key": "answer_increasing",
        },
        {
            "kind": "set_solution",
            "marks_possible": 2,
            "param_key": "answer_prod_negative",
        },
        {
            "kind": "set_solution",
            "marks_possible": 3,
            "param_key": "answer_f_nonpositive",
        },
        {
            "kind": "symbolic_equality",
            "marks_possible": 2,
            "param_key": "answer_shift",
        },
    ],
    corpus_anchor=CorpusAnchor(
        paper="2025 May/June P2",
        question="7",
        marks=10,
    ),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(
        registry=InMemoryRegistry({trig_graph_analysis.id: trig_graph_analysis})
    )
    keys = [
        "answer_range",
        "answer_period",
        "answer_increasing",
        "answer_prod_negative",
        "answer_f_nonpositive",
        "answer_shift",
    ]
    for seed in range(6):
        inst = engine.instantiate(trig_graph_analysis.id, seed=seed)
        p = inst.params
        print(
            f"seed {seed}: f={p['f_latex']}, g={p['g_latex']}, shift {p['shift_deg']}° "
            f"→ h={p['shift_latex']}"
        )
        attempt = SolutionAttempt(steps=[SubmittedStep(p[k]) for k in keys])
        r = inst.verifier.rate(attempt)
        print(f"  all-correct → {r.marks_awarded}/{r.marks_possible} ok={r.is_correct}")
