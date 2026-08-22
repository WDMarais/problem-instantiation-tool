"""
Independent oracle for ``exponential_from_graph``.

The generator builds ``y = a·b^x + q`` forward from a chosen asymptote and two
lattice points. These tests read the features back out of the baked expression
with SymPy — evaluate at the labelled points, take the limit toward the asymptote
— and assert they match the sketch's labels (the display-only contract). They
also pin the wire-only well-posedness invariant, that the verifier rejects a
wrong base, and that the template emits an inline graph plus a full memo.
"""

from __future__ import annotations

import sympy

from content.examples.exponential_from_graph import exponential_from_graph
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep
from worksheets.generate import template_exponential_from_graph

_x = sympy.Symbol("x")
_ENGINE = Engine(
    registry=InMemoryRegistry({exponential_from_graph.id: exponential_from_graph})
)


def _rate(inst, expr) -> tuple[int, int]:
    r = inst.verifier.rate(SolutionAttempt(steps=[SubmittedStep(expr)]))
    return r.marks_awarded, r.marks_possible


def test_answer_matches_the_labelled_features():
    for seed in range(80):
        inst = _ENGINE.instantiate("exponential_from_graph", seed=seed)
        p = inst.params
        expr, a, b, q = p["answer"], p["a"], p["b"], p["q"]
        # both labelled points lie on the curve
        assert expr.subs(_x, 0) == p["y_intercept"], (seed, p)
        assert expr.subs(_x, p["point_x"]) == p["point_y"], (seed, p)
        # horizontal asymptote: b > 1 ⇒ limit as x → -∞ is q
        assert sympy.limit(expr, _x, -sympy.oo) == q, (seed, p)
        # a and b read back off two evaluations
        assert expr.subs(_x, 0) - q == a, (seed, p)
        assert (expr.subs(_x, 1) - q) / a == b, (seed, p)


def test_is_always_well_posed():
    # wire-only claim: a ≠ 0 ⇒ base recoverable and y-intercept off the asymptote.
    for seed in range(80):
        p = _ENGINE.instantiate("exponential_from_graph", seed=seed).params
        assert p["a"] != 0 and p["q"] != 0
        assert p["b"] >= 2  # a genuine growth base, never the constant b = 1
        assert p["y_intercept"] != p["q"]


def test_verifier_rejects_wrong_base():
    for seed in range(40):
        inst = _ENGINE.instantiate("exponential_from_graph", seed=seed)
        p = inst.params
        assert _rate(inst, p["answer"]) == (3, 3)
        # assume b = 2: correct only when b really is 2
        assumed = p["a"] * sympy.Integer(2) ** _x + p["q"]
        awarded, _ = _rate(inst, assumed)
        assert (awarded == 3) == (p["b"] == 2)


def test_template_emits_graph_and_full_memo():
    params = _ENGINE.instantiate("exponential_from_graph", seed=5).params
    full = template_exponential_from_graph(params, detail="full")
    short = template_exponential_from_graph(params, detail="short")
    assert full.graph_svg and full.graph_svg.lstrip().startswith("<svg")
    assert len(full.worked_steps) == 4  # form, a, b, state
    assert len(short.worked_steps) == 1  # answer only
    assert any(r"\Rightarrow\; a =" in s for s in full.worked_steps)
    assert any(r"\Rightarrow\; b =" in s for s in full.worked_steps)
