"""
Functions & Graphs — ``hyperbola_properties`` (the shared-stem compound).

Given the *equation* of a rectangular hyperbola ``f(x) = a/(x - m) + q`` (with the
vertical asymptote at ``x = m = -p`` in the internal ``y = a/(x+p)+q`` convention),
read/compute six coupled properties off it — the whole of a real NSC Q4:

    4.1  M  = asymptote intersection  = (-p, q)
    4.2  D  = y-intercept             = (0, a/p + q)
    4.3  t  : line of symmetry y = x + t through M → t = p + q
    4.4  f(x) ≤ 0  : the half-open interval [C, -p)  (C = x-intercept)
    4.5  A  = point on f closest to M = (-p + √a, q + √a)   (upper-right branch)
    4.6  AA′ under a reflection in the y-axis (h(x) = f(-x)) = 2·|Aₓ|

This is the tool's first *compound* problem: ONE instantiation feeds all six
sub-parts, so 4.6 genuinely reads 4.5's A and 4.3 reads 4.1's M — a coupling the
independent-slot paper layer could not express. The verifier grades the eight
answer *values* (M and A coordinate-wise, like ``circumcentre``; the interval via
``set_solution``); the method/setup lines each sub-part also carries are marked by
hand (declared per sub-part in the template, reconciled by the paper layer).

**F1-gated** (``hyperbola_properties_in_scope``): the closest-point A must be a
lattice point (``a`` a perfect square) and must not collapse onto the y-axis
(``-p + √a ≠ 0``, else A = D and AA′ = 0), and the ``f ≤ 0`` region must be the
clean non-empty half-open interval the archetype assumes (``a > 0``, ``q > 0``,
``q | a`` for an integer x-intercept). The predicate re-derives all of this from
the presented ``a, p, q`` — see ``content/scope_predicates.py``.
"""

from __future__ import annotations

import math
import random

import sympy

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

_x = sympy.Symbol("x")

_A_SQUARES = (1, 4, 9)  # a a perfect square ⇒ A = (-p+√a, q+√a) is a lattice point
_P_CHOICES = (-3, -2, -1, 1, 2, 3)  # asymptote off the y-axis (p ≠ 0)


def _gen(rng: random.Random) -> dict:
    a = rng.choice(_A_SQUARES)
    r = int(math.isqrt(a))
    # q > 0 and q | a → integer x-intercept C, non-empty half-open f≤0 interval.
    q = rng.choice([d for d in range(1, a + 1) if a % d == 0])
    # p ≠ 0 (M off y-axis); p ≠ r (A off y-axis ⇒ AA′ ≠ 0, A ≠ D);
    # p ≠ -a/q (x-intercept C off the y-axis, distinct from D).
    forbidden = {0, r, sympy.Rational(-a, q)}
    p = rng.choice([v for v in _P_CHOICES if v not in forbidden])

    mx, my = -p, q  # 4.1 M
    cx = sympy.Rational(-a, q) - p  # x-intercept C (f = 0)
    dy = sympy.Rational(a, p) + q  # 4.2 D (y-intercept, may be a fraction)
    t = p + q  # 4.3 line-of-symmetry offset
    # 4.4 f(x) ≤ 0 on [C, M_x): closed at the intercept, open at the asymptote.
    solution_set = sympy.Interval(cx, mx, left_open=False, right_open=True)
    ax, ay = mx + r, my + r  # 4.5 A on the upper-right branch
    aa_prime = 2 * abs(ax)  # 4.6 reflection in y-axis: A′ = (-Aₓ, A_y)

    denom = f"x - {mx}" if mx >= 0 else f"x + {-mx}"
    return {
        "a": a,
        "p": p,
        "q": q,
        "sqrt_a": r,
        "f_latex": rf"f(x) = \frac{{{a}}}{{{denom}}} + {q}",
        # 4.1 M — graded coordinate-wise
        "m_x": mx,
        "m_y": my,
        # 4.2 D
        "d_y": dy,
        # 4.3 t
        "t": t,
        # 4.4 f ≤ 0
        "c_x": cx,
        "solution_set": solution_set,
        # 4.5 A — graded coordinate-wise
        "a_x": ax,
        "a_y": ay,
        # 4.6 AA′
        "aa_prime": aa_prime,
    }


hyperbola_properties = Problem(
    id="hyperbola_properties",
    type_id="hyperbola_properties",
    name="Read six coupled properties off a hyperbola's equation (NSC Q4)",
    artifact_type="practice",
    problem_spec=_gen,
    # Eight answer-value steps (canonical scheme = 9). M and A coordinate-wise;
    # the f≤0 interval via set_solution. The paper layer splits each sub-part's
    # headline marks into these auto steps + hand-marked method lines.
    verifier_spec=[
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "m_x"},
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "m_y"},
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "d_y"},
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "t"},
        {"kind": "set_solution", "marks_possible": 2, "param_key": "solution_set"},
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "a_x"},
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "a_y"},
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "aa_prime"},
    ],
    corpus_anchor=CorpusAnchor(
        paper="2025 May/June P1",
        question="4",  # the whole hyperbola question (shared stem, 4.1–4.6)
        marks=15,
    ),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(
        registry=InMemoryRegistry({hyperbola_properties.id: hyperbola_properties})
    )
    for seed in (1, 7, 13):
        p = engine.instantiate(hyperbola_properties.id, seed=seed).params
        print(f"=== seed {seed}: a={p['a']} p={p['p']} q={p['q']} ===")
        print(
            f"  M={p['m_x'], p['m_y']}  D=(0,{p['d_y']})  t={p['t']}  "
            f"f<=0 on {p['solution_set']}  A={p['a_x'], p['a_y']}  AA'={p['aa_prime']}"
        )
        inst = engine.instantiate(hyperbola_properties.id, seed=seed)
        keys = ["m_x", "m_y", "d_y", "t", "solution_set", "a_x", "a_y", "aa_prime"]
        attempt = SolutionAttempt(steps=[SubmittedStep(p[k]) for k in keys])
        r = inst.verifier.rate(attempt)
        print(f"  all-correct → {r.marks_awarded}/{r.marks_possible} ok={r.is_correct}")
