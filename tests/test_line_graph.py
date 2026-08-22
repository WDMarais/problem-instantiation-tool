"""
Independent oracle for ``line_from_graph``.

The generator builds ``y = mx + c`` forward from a chosen gradient/intercept and
two lattice points. These tests read the features back out of the baked expression
with SymPy — evaluate at the two labelled points, recover the gradient from a
difference quotient, read c off x = 0 — and assert they match the sketch's labels
(the display-only contract). They also pin the wire-only well-posedness invariant,
that the verifier rejects a sign-flipped gradient, and that the template emits an
inline graph plus a full memo.
"""

from __future__ import annotations

import sympy

from content.examples.line_from_graph import line_from_graph
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep
from worksheets.generate import template_line_from_graph

_x = sympy.Symbol("x")
_ENGINE = Engine(registry=InMemoryRegistry({line_from_graph.id: line_from_graph}))


def _rate(inst, expr) -> tuple[int, int]:
    r = inst.verifier.rate(SolutionAttempt(steps=[SubmittedStep(expr)]))
    return r.marks_awarded, r.marks_possible


def test_answer_matches_the_labelled_features():
    for seed in range(80):
        inst = _ENGINE.instantiate("line_from_graph", seed=seed)
        p = inst.params
        expr, m, c = p["answer"], p["m"], p["c"]
        x1, y1 = p["point1_x"], p["point1_y"]
        x2, y2 = p["point2_x"], p["point2_y"]
        # both labelled points lie on the line
        assert expr.subs(_x, x1) == y1, (seed, p)
        assert expr.subs(_x, x2) == y2, (seed, p)
        # gradient recovered from the difference quotient; c is the y-intercept
        assert (expr.subs(_x, x2) - expr.subs(_x, x1)) / (x2 - x1) == m, (seed, p)
        assert expr.subs(_x, 0) == c, (seed, p)


def test_is_always_well_posed():
    # wire-only claim: a genuinely sloped line through two distinct off-axis points.
    for seed in range(80):
        p = _ENGINE.instantiate("line_from_graph", seed=seed).params
        assert p["m"] != 0 and p["c"] != 0
        assert p["point1_x"] != p["point2_x"]  # distinct x ⇒ finite gradient
        assert p["point1_x"] != 0 and p["point2_x"] != 0  # both off the y-axis


def test_verifier_rejects_wrong_gradient():
    for seed in range(40):
        inst = _ENGINE.instantiate("line_from_graph", seed=seed)
        p = inst.params
        assert _rate(inst, p["answer"]) == (3, 3)
        # sign-flipped gradient through point 1: never the baked line (m != 0)
        wrong = -p["m"] * _x + (p["point1_y"] + p["m"] * p["point1_x"])
        awarded, _ = _rate(inst, wrong)
        assert awarded != 3
        # forgot to solve for c (used c = 0): correct only if c really is 0 (never)
        forgot_c = p["m"] * _x
        awarded_c, _ = _rate(inst, forgot_c)
        assert (awarded_c == 3) == (p["c"] == 0)


def test_template_emits_graph_and_full_memo():
    params = _ENGINE.instantiate("line_from_graph", seed=5).params
    full = template_line_from_graph(params, detail="full")
    short = template_line_from_graph(params, detail="short")
    assert full.graph_svg and full.graph_svg.lstrip().startswith("<svg")
    assert len(full.worked_steps) == 3  # gradient, sub for c, state
    assert len(short.worked_steps) == 1  # answer only
    assert any(r"\dfrac" in s for s in full.worked_steps)  # gradient quotient shown
    assert any(r"\Rightarrow\; c =" in s for s in full.worked_steps)
