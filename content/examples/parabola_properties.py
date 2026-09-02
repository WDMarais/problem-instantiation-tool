"""
Functions & Graphs — ``parabola_properties`` (the shared-stem compound, NSC Q5).

Given the *turning point* ``C(h, q)`` and one further point ``B(bx, by)`` on a
downward parabola ``f(x) = a(x + p)^2 + q`` (with ``p = -h``), work the whole of a
real NSC Q5 off that single stem — three coupled sub-parts:

    5.1  Show that f(x) = <expanded>  : find a from B, expand      (a<0, integer)
    5.2  k for which f(x) + k has no real roots : k < -q  (a set)
    5.3  reflect f over y = q → g' = 2q - f; sketch the cubic g    (hand-drawn)

Only 5.1 and 5.2 have engine-gradable answers (the stretch factor + the expanded
form; the ``k`` region via ``set_solution``). 5.3's deliverable is a *sketch* — it
is hand-marked in full, presented with a worked memo (the reflection, that g' > 0
so g is strictly increasing with an inflection at x = h). So the canonical
engine-graded total is 3 of the 9 headline marks; the paper layer splits the rest.

**F1-gated** (``parabola_properties_in_scope``): the archetype needs a *downward*
parabola with an integer stretch (``a < 0``, ``a`` integer) so 5.1 expands to
integer coefficients and 5.3's "g' > 0 everywhere ⇒ g strictly increasing"
conclusion holds; ``q > 0`` so the no-real-roots bound ``k < -q`` is a genuine
negative and g' has a positive minimum; and B must be a real second point
(``bx ≠ h``). The predicate re-derives ``a = (by - q)/(bx - h)^2`` from the
*presented* C and B — see ``content/scope_predicates.py``.
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

_x = sympy.Symbol("x")

_A_CHOICES = (-1, -2, -3)  # downward, integer stretch → integer expansion
_H_CHOICES = (-2, -1, 1, 2)  # turning point off the y-axis, both signs
_Q_CHOICES = (2, 3, 4, 6)  # q > 0: negative k-bound, g' minimum positive
_DX_CHOICES = (-2, -1, 1, 2)  # B a clear second point, distinct from the vertex


def _gen(rng: random.Random) -> dict:
    a = rng.choice(_A_CHOICES)
    h = rng.choice(_H_CHOICES)
    q = rng.choice(_Q_CHOICES)
    bx = h + rng.choice(_DX_CHOICES)
    by = a * (bx - h) ** 2 + q  # B on f — integer, since a, bx, h, q are integers

    f_expanded = sympy.expand(a * (_x - h) ** 2 + q)  # 5.1 target
    k_set = sympy.Interval.open(sympy.S.NegativeInfinity, -q)  # 5.2 k < -q
    g_prime = sympy.expand(2 * q - (a * (_x - h) ** 2 + q))  # 5.3 reflection over y=q

    return {
        "a": a,
        "h": h,
        "q": q,
        "p": -h,  # the (x + p) form coefficient shown to the student
        "bx": bx,
        "by": by,
        # 5.1 — graded: the stretch found from B, and the expanded form
        "a_coeff": a,
        "f_expanded": f_expanded,
        # 5.2 — graded: the k region (all-or-nothing set)
        "k_set": k_set,
        # 5.3 — memo only (the sketch is hand-marked)
        "g_prime": g_prime,
        "inflection_x": h,
    }


parabola_properties = Problem(
    id="parabola_properties",
    type_id="parabola_properties",
    name="Determine a parabola from its turning point + a point, then reflect (NSC Q5)",
    artifact_type="practice",
    problem_spec=_gen,
    # Three answer-value steps (canonical scheme = 3): the stretch a and the
    # expanded form (5.1), and the no-real-roots k region (5.2, via set_solution).
    # 5.3 is a hand-drawn sketch — no engine step. The paper layer splits each
    # sub-part's headline marks into these auto steps + hand-marked method lines.
    verifier_spec=[
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "a_coeff"},
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "f_expanded"},
        {"kind": "set_solution", "marks_possible": 1, "param_key": "k_set"},
    ],
    corpus_anchor=CorpusAnchor(
        paper="2025 May/June P1",
        question="5",  # the whole parabola question (shared stem, 5.1–5.3)
        marks=9,
    ),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(
        registry=InMemoryRegistry({parabola_properties.id: parabola_properties})
    )
    for seed in (1, 7, 13):
        p = engine.instantiate(parabola_properties.id, seed=seed).params
        print(f"=== seed {seed}: a={p['a']} h={p['h']} q={p['q']} B={p['bx'], p['by']}")
        print(f"  f = {p['f_expanded']}   k in {p['k_set']}   g' = {p['g_prime']}")
        inst = engine.instantiate(parabola_properties.id, seed=seed)
        keys = ["a_coeff", "f_expanded", "k_set"]
        attempt = SolutionAttempt(steps=[SubmittedStep(p[k]) for k in keys])
        r = inst.verifier.rate(attempt)
        print(f"  all-correct → {r.marks_awarded}/{r.marks_possible} ok={r.is_correct}")
