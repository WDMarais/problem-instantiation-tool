"""
Independent oracle for ``circle_from_graph``.

The generator builds ``(x - a)^2 + (y - b)^2 = r^2`` forward from a chosen centre
and a lattice point on the circle. These tests reconstruct the expected equation
with SymPy, confirm the labelled point lies on the baked circle, and recompute r²
from the distance formula — the display-only contract. They also pin the wire-only
well-posedness invariant, that the verifier rejects an equation missing the radius,
and that the template emits an inline circle (a native ``<ellipse>``) plus a full
memo.
"""

from __future__ import annotations

import sympy

from content.examples.circle_from_graph import circle_from_graph
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep
from worksheets.generate import template_circle_from_graph

_x, _y = sympy.symbols("x y")
_ENGINE = Engine(registry=InMemoryRegistry({circle_from_graph.id: circle_from_graph}))


def _rate(inst, expr) -> tuple[int, int]:
    r = inst.verifier.rate(SolutionAttempt(steps=[SubmittedStep(expr)]))
    return r.marks_awarded, r.marks_possible


def test_answer_matches_the_labelled_features():
    for seed in range(80):
        inst = _ENGINE.instantiate("circle_from_graph", seed=seed)
        p = inst.params
        expr, a, b, r2 = p["answer"], p["a"], p["b"], p["radius_sq"]
        x0, y0 = p["point_x"], p["point_y"]
        # the baked equation is exactly the centred form, "= 0" side
        expected = (_x - a) ** 2 + (_y - b) ** 2 - r2
        assert sympy.simplify(expr - expected) == 0, (seed, p)
        # the labelled point lies on the circle
        assert sympy.simplify(expr.subs({_x: x0, _y: y0})) == 0, (seed, p)
        # r² is the squared distance centre → point
        assert r2 == (x0 - a) ** 2 + (y0 - b) ** 2, (seed, p)


def test_is_always_well_posed():
    # wire-only claim: centre off both axes, a genuine positive radius.
    for seed in range(80):
        p = _ENGINE.instantiate("circle_from_graph", seed=seed).params
        assert p["a"] != 0 and p["b"] != 0
        assert p["radius_sq"] > 0
        assert (p["point_x"], p["point_y"]) != (p["a"], p["b"])  # point off centre


def test_verifier_rejects_missing_radius():
    for seed in range(40):
        inst = _ENGINE.instantiate("circle_from_graph", seed=seed)
        p = inst.params
        assert _rate(inst, p["answer"]) == (3, 3)
        assert _rate(inst, sympy.expand(p["answer"])) == (3, 3)  # equivalent form
        # forgot to subtract r² (left the raw squares): r² > 0 ⇒ always wrong
        forgot = (_x - p["a"]) ** 2 + (_y - p["b"]) ** 2
        awarded, _ = _rate(inst, forgot)
        assert awarded != 3


def test_template_emits_circle_and_full_memo():
    params = _ENGINE.instantiate("circle_from_graph", seed=5).params
    full = template_circle_from_graph(params, detail="full")
    short = template_circle_from_graph(params, detail="short")
    assert full.graph_svg and full.graph_svg.lstrip().startswith("<svg")
    assert "<ellipse" in full.graph_svg  # the circle primitive
    assert len(full.worked_steps) == 3  # centre, r², state
    assert len(short.worked_steps) == 1  # equation only
    assert any(r"r^2 =" in s for s in full.worked_steps)  # distance-formula step
    assert any(r"\text{centre }" in s for s in full.worked_steps)
