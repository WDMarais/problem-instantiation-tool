"""
Functions & Graphs — ``exponential_inverse`` (the shared-stem compound, NSC Q6).

Two functions share one stem: an exponential ``f(x) = p^x + q`` and a line
``g(x) = mx + c`` that meet at ``A(ax, ay)``; ``B(0, by)`` is the y-intercept of f
and ``E`` the x-intercept of g. The whole of a real NSC Q6 works off that stem —
four coupled sub-parts:

    6.1  Calculate p and q          : q = by - 1 (from B), p^ax = ay - q      (4)
    6.2  Range of f                 : y > q  (a set, p > 1 increasing)        (1)
    6.3  g through the inverse hook : g⁻¹ passes through B ⇒ g through (by, 0);
                                       with A that pins g = mx + c            (4)
    6.4  Equation of g⁻¹            : swap ⇒ y = (x - c)/m                     (2)

The 6.3 hook is the coupling that makes this a *compound*, not four separate
problems: "g⁻¹ passes through B" is only meaningful because B is the same B that
6.1 read off f. Every sub-part has an engine-gradable answer (no sketch): p, q,
the range set, g's slope + equation, and g⁻¹'s equation — canonical total 6 of the
11 headline marks; the paper layer splits the rest into hand-marked method lines.

**F1-gated** (``exponential_inverse_in_scope``): re-deriving from the *presented*
A and B, ``q = by - 1`` and ``p^ax = ay - q`` must give an integer base ``p ≥ 2``
that is a genuine ``ax``-th power (a valid, increasing exponential — so the range
is the clean ``y > q``); ``ay ≠ 0`` so g is not horizontal (g⁻¹ exists); and
``ax ≠ by`` so g's two points (A and the swapped B) have distinct x (slope
defined). See ``content/scope_predicates.py``.
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

_x = sympy.Symbol("x")

# (base, intersection-x): the exponential base p and where f meets g. Kept small so
# p^ax (and the plotted tail) stay legible.
_PA_CHOICES = ((2, 2), (2, 3), (3, 2))
_BY_CHOICES = (-6, -5, -4, -3, -2, 2, 3, 4, 5, 6)  # y-intercept of f (integer)


def _gen(rng: random.Random) -> dict:
    p, ax = rng.choice(_PA_CHOICES)
    pax = p**ax
    # by: exclude the two degeneracies — ay = 0 (g horizontal) and ax = by (g's two
    # points share an x, slope undefined).
    by = rng.choice([b for b in _BY_CHOICES if b != ax and (pax + b - 1) != 0])
    q = by - 1  # f(0) = 1 + q = by
    ay = pax + q  # A(ax, ay) on f

    # g through A(ax, ay) and the swapped B (by, 0) — the "g⁻¹ through B" hook.
    m = sympy.Rational(ay, ax - by)
    c = -m * by
    g_expr = sympy.expand(m * _x + c)
    ginv_expr = sympy.expand((_x - c) / m)  # swap x,y in y = mx + c

    return {
        "p": p,
        "q": q,
        "ax": ax,
        "ay": ay,
        "by": by,
        # 6.1 — graded: the base and the asymptote
        "p_val": p,
        # (q already above — 6.1's second graded value)
        # 6.2 — graded: the range (all-or-nothing set), y > q
        "range_set": sympy.Interval.open(q, sympy.S.Infinity),
        # 6.3 — graded: g's slope and its full equation
        "g_slope": m,
        "g_intercept": c,
        "g_expr": g_expr,
        # 6.4 — graded: g⁻¹'s equation
        "ginv_expr": ginv_expr,
        "ginv_slope": sympy.Rational(1, 1) / m,
        "ginv_intercept": -c / m,
    }


exponential_inverse = Problem(
    id="exponential_inverse",
    type_id="exponential_inverse",
    name="Exponential + line + inverse off one shared stem (NSC Q6)",
    artifact_type="practice",
    problem_spec=_gen,
    # Six answer-value steps (canonical scheme = 6): p and q (6.1), the range set
    # (6.2), g's slope + equation (6.3), g⁻¹'s equation (6.4). The paper layer
    # splits each sub-part's headline marks into these auto steps + method lines.
    verifier_spec=[
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "p_val"},
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "q"},
        {"kind": "set_solution", "marks_possible": 1, "param_key": "range_set"},
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "g_slope"},
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "g_expr"},
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "ginv_expr"},
    ],
    corpus_anchor=CorpusAnchor(
        paper="2025 May/June P1",
        question="6",  # the whole exponential+inverse question (shared stem, 6.1–6.4)
        marks=11,
    ),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(
        registry=InMemoryRegistry({exponential_inverse.id: exponential_inverse})
    )
    for seed in (1, 7, 13):
        p = engine.instantiate(exponential_inverse.id, seed=seed).params
        print(
            f"=== seed {seed}: p={p['p']} q={p['q']} A={p['ax'], p['ay']} "
            f"B=(0,{p['by']})"
        )
        print(f"  range {p['range_set']}  g = {p['g_expr']}  g^-1 = {p['ginv_expr']}")
        inst = engine.instantiate(exponential_inverse.id, seed=seed)
        keys = ["p_val", "q", "range_set", "g_slope", "g_expr", "ginv_expr"]
        attempt = SolutionAttempt(steps=[SubmittedStep(p[k]) for k in keys])
        r = inst.verifier.rate(attempt)
        print(f"  all-correct → {r.marks_awarded}/{r.marks_possible} ok={r.is_correct}")
