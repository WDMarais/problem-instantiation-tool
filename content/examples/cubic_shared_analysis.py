"""
Functions & Calculus — ``cubic_shared_analysis`` (the shared-stem compound, NSC Q9).

One cubic  f(x) = (x − p)(x − k)²  — a single root at ``p`` and a *repeated* root at
``k`` (so f touches the x-axis at ``k``) — carries the whole of a real NSC Q9, five
coupled sub-parts off that single stem:

    9.1  Show that k = <value>        : compare the x² coefficient       (auto: k)
    9.2  Coordinates of the turning points                              (auto: x₂, y₂)
    9.3  Describe the concavity of f at x = q : sign of f″(q)            (auto: tag)
    9.4  Draw the graph, label TPs + intercepts                         (hand-drawn)
    9.5  Max vertical distance between f and h = −2f′ on (k ; x₂)        (auto: d_max)

The stem is presented as  f(x) = <expanded> = (x − p)(x − k)²  with ``k`` an unknown
the student recovers in 9.1. The two turning points are always ``(k ; 0)`` (the
repeated root, on the axis) and ``(x₂ ; y₂)`` where ``x₂ = (k + 2p)/3`` is the other
root of f′(x) = 3(x − k)(x − x₂). The 9.5 interval is intrinsic — it is exactly the
open interval between the two turning-point x-values — and the maximum of the
vertical gap |h − f| there falls at the single interior stationary point of
d = h − f, an irrational x in general (source: x = √5, d_max = 10√5 − 14 ≈ 8,36).

Engine-graded canonical total = 6 of the 18 headline marks: k (9.1), x₂ and y₂
(9.2), the concavity tag (9.3) and d_max (9.5). 9.4's sketch and every method line
(expanding, differentiating, forming and solving d′ = 0) are hand-marked; the paper
layer splits each sub-part's headline marks into these auto steps + manual lines.
d_max is graded with ``symbolic_equality``, which accepts either the exact surd
``10√5 − 14`` or the rounded ``8,36`` (numeric answers carry a decimal tolerance).

**F1-gated** (``cubic_shared_analysis_in_scope``): from the presented ``p, k`` the
second turning point ``x₂ = (k + 2p)/3`` must be a genuine second integer stationary
point (``3 | k + 2p`` and ``x₂ ≠ k``) so 9.2 has two distinct turning points and 9.5
has a clean interval; the concavity point ``q`` must miss the inflection
(``f″(q) ≠ 0``) so 9.3 has a definite answer; and d = h − f must have exactly one
interior stationary point on (k ; x₂) that attains the maximum gap. The predicate
re-derives all of this from p, k, q — see ``content/scope_predicates.py``.
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

_x = sympy.Symbol("x")

_P_CHOICES = (-4, -3, -2, -1, 1, 2, 3, 4, 5)  # single root
_K_CHOICES = (-4, -3, -2, -1, 0, 1, 2, 3, 4)  # repeated root (≠ p)


def _analyse(p: int, k: int, q: int):
    """Re-derive the whole cubic from (p, k, q); return the answer bundle, or None
    if this (p, k, q) is out of the archetype's scope. Pure — used by both the
    generator and the F1 predicate so they agree by construction."""
    if p == k or (k + 2 * p) % 3 != 0:
        return None
    x2 = (k + 2 * p) // 3
    if x2 == k:
        return None

    f = (_x - p) * (_x - k) ** 2
    f_expanded = sympy.expand(f)
    f_prime = sympy.expand(sympy.diff(f, _x))
    f_double = sympy.diff(f, _x, 2)
    if f_double.subs(_x, q) == 0:  # q on the inflection → no definite concavity
        return None

    lo, hi = sorted((k, x2))
    h = sympy.expand(-2 * f_prime)
    d = sympy.expand(h - f)  # vertical gap h − f
    d_prime = sympy.diff(d, _x)
    crit = [r for r in sympy.solve(d_prime, _x) if r.is_real and lo < r < hi]
    if len(crit) != 1:
        return None
    x_star = crit[0]
    d_star = d.subs(_x, x_star)
    # the interior stationary point must be the global max gap on [lo, hi]
    if not (abs(d_star) >= abs(d.subs(_x, lo)) and abs(d_star) >= abs(d.subs(_x, hi))):
        return None

    return {
        "x2": x2,
        "y2": int(f_expanded.subs(_x, x2)),
        "lo": lo,
        "hi": hi,
        "f_expanded": f_expanded,
        "f_prime": f_prime,
        "f_double": f_double,
        "concavity_q": "concave_up" if f_double.subs(_x, q) > 0 else "concave_down",
        "f_double_q": int(f_double.subs(_x, q)),
        "y_intercept": int(f_expanded.subs(_x, 0)),
        "h": h,
        "d": d,
        "x_star": sympy.simplify(x_star),
        "d_max": sympy.simplify(d_star),
    }


def _gen(rng: random.Random) -> dict:
    while True:
        p = rng.choice(_P_CHOICES)
        k = rng.choice(_K_CHOICES)
        if p == k or (k + 2 * p) % 3 != 0:
            continue
        x2 = (k + 2 * p) // 3
        if x2 == k:
            continue
        # concavity point, a clear integer left of the interval (off the inflection)
        q = min(k, x2) - rng.choice([1, 2, 3, 4])
        res = _analyse(p, k, q)
        if res is not None:
            break

    return {
        "p": p,
        "k": k,  # 9.1 answer (the repeated root)
        "q": q,  # 9.3 concavity point
        **res,
    }


cubic_shared_analysis = Problem(
    id="cubic_shared_analysis",
    type_id="cubic_shared_analysis",
    name="Analyse a cubic with a repeated root — k, turning points, concavity, "
    "max gap (NSC Q9)",
    artifact_type="practice",
    problem_spec=_gen,
    # Five answer-value steps (canonical scheme = 6): k (9.1); x₂, y₂ (9.2); the
    # concavity tag (9.3); d_max worth 2 (9.5). 9.4 is a hand-drawn sketch — no step.
    verifier_spec=[
        {"kind": "numeric_equality", "marks_possible": 1, "param_key": "k"},
        {"kind": "numeric_equality", "marks_possible": 1, "param_key": "x2"},
        {"kind": "numeric_equality", "marks_possible": 1, "param_key": "y2"},
        {
            "kind": "exact_equality",
            "marks_possible": 1,
            "param_key": "concavity_q",
            "normalize": ["whitespace"],
        },
        {"kind": "symbolic_equality", "marks_possible": 2, "param_key": "d_max"},
    ],
    corpus_anchor=CorpusAnchor(
        paper="2025 May/June P1",
        question="9",  # the whole cubic question (shared stem, 9.1–9.5)
        marks=18,
    ),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(
        registry=InMemoryRegistry({cubic_shared_analysis.id: cubic_shared_analysis})
    )
    for seed in (1, 7, 13):
        inst = engine.instantiate(cubic_shared_analysis.id, seed=seed)
        p = inst.params
        print(f"=== seed {seed}: p={p['p']} k={p['k']} q={p['q']} ===")
        print(f"  f = {p['f_expanded']}")
        print(
            f"  TPs: ({p['k']};0), ({p['x2']};{p['y2']})   concavity@{p['q']}: "
            f"{p['concavity_q']}"
        )
        print(
            f"  9.5 on ({p['lo']};{p['hi']}): x*={p['x_star']} d_max={p['d_max']} "
            f"(~{float(p['d_max']):.3f})"
        )
        keys = ["k", "x2", "y2", "concavity_q", "d_max"]
        attempt = SolutionAttempt(steps=[SubmittedStep(p[key]) for key in keys])
        r = inst.verifier.rate(attempt)
        print(f"  all-correct → {r.marks_awarded}/{r.marks_possible} ok={r.is_correct}")
