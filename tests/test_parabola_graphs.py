"""
Independent oracle for the two determine-the-equation parabola problems
(``parabola_from_graph``, ``parabola_from_turning_point``).

The generators build the answer *forward* from chosen features (intercepts+a, or
vertex+a). These tests re-read the features *back* out of the baked, expanded
polynomial with SymPy — a different computation — and assert they match what the
sketch would label. Agreement corroborates that the graph a student sees and the
answer the verifier grades describe the same parabola (the display-only contract).

They also pin the wire-only well-posedness invariant (``a`` is always recoverable)
and that each template emits an inline graph plus a full show-the-method memo.
"""

from __future__ import annotations

import sympy

from content.examples.parabola_from_graph import parabola_from_graph
from content.examples.parabola_from_turning_point import parabola_from_turning_point
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep
from worksheets.generate import (
    template_parabola_from_graph,
    template_parabola_from_turning_point,
)

_x = sympy.Symbol("x")
_ENGINE = Engine(
    registry=InMemoryRegistry(
        {p.id: p for p in (parabola_from_graph, parabola_from_turning_point)}
    )
)


def _rate(inst, expr) -> tuple[int, int]:
    attempt = SolutionAttempt(steps=[SubmittedStep(expr)])
    r = inst.verifier.rate(attempt)
    return r.marks_awarded, r.marks_possible


# ── parabola_from_graph (intercepts sketch) ─────────────────────────────────────


def test_from_graph_answer_matches_the_labelled_features():
    for seed in range(80):
        inst = _ENGINE.instantiate("parabola_from_graph", seed=seed)
        p = inst.params
        poly = sympy.Poly(p["answer"], _x)
        r1, r2, a = p["root1"], p["root2"], p["a"]
        # the expanded polynomial vanishes at both labelled x-intercepts …
        assert poly.eval(r1) == 0, (seed, p)
        assert poly.eval(r2) == 0, (seed, p)
        # … its y-intercept is the labelled one, and its lead coeff is a
        assert poly.eval(0) == p["y_intercept"], (seed, p)
        assert poly.all_coeffs()[0] == a, (seed, p)


def test_from_graph_is_always_well_posed():
    # wire-only claim: distinct nonzero roots ⇒ y-intercept a·r1·r2 ≠ 0, so a is
    # always recoverable from f(0); no draw is degenerate.
    for seed in range(80):
        p = _ENGINE.instantiate("parabola_from_graph", seed=seed).params
        assert p["root1"] != p["root2"]
        assert p["root1"] != 0 and p["root2"] != 0
        assert p["y_intercept"] != 0


def test_from_graph_verifier_accepts_baked_rejects_wrong():
    for seed in range(30):
        inst = _ENGINE.instantiate("parabola_from_graph", seed=seed)
        p = inst.params
        assert _rate(inst, p["answer"]) == (3, 3)
        # drop the leading coefficient: correct iff a really is 1
        forgot_a = sympy.expand((_x - p["root1"]) * (_x - p["root2"]))
        awarded, _ = _rate(inst, forgot_a)
        assert (awarded == 3) == (p["a"] == 1)


# ── parabola_from_turning_point (vertex sketch) ─────────────────────────────────


def test_from_turning_point_answer_matches_the_labelled_features():
    for seed in range(80):
        inst = _ENGINE.instantiate("parabola_from_turning_point", seed=seed)
        p = inst.params
        expr, vx, vy, a = p["answer"], p["vertex_x"], p["vertex_y"], p["a"]
        # vertex: f(p) = q and the derivative vanishes there
        assert sympy.expand(expr.subs(_x, vx)) == vy, (seed, p)
        assert sympy.diff(expr, _x).subs(_x, vx) == 0, (seed, p)
        # y-intercept and lead coeff match the labels
        assert expr.subs(_x, 0) == p["y_intercept"], (seed, p)
        assert sympy.Poly(expr, _x).all_coeffs()[0] == a, (seed, p)


def test_from_turning_point_is_always_well_posed():
    # wire-only claim: vertex off the y-axis (p ≠ 0) ⇒ f(0) = a·p² + q ≠ q, so a
    # is always recoverable.
    for seed in range(80):
        p = _ENGINE.instantiate("parabola_from_turning_point", seed=seed).params
        assert p["vertex_x"] != 0
        assert p["y_intercept"] != p["vertex_y"]


def test_from_turning_point_verifier_accepts_baked_rejects_wrong():
    for seed in range(30):
        inst = _ENGINE.instantiate("parabola_from_turning_point", seed=seed)
        p = inst.params
        assert _rate(inst, p["answer"]) == (3, 3)
        forgot_a = sympy.expand((_x - p["vertex_x"]) ** 2 + p["vertex_y"])
        awarded, _ = _rate(inst, forgot_a)
        assert (awarded == 3) == (p["a"] == 1)


# ── templates emit a graph + a full memo ────────────────────────────────────────


def test_templates_emit_inline_graph_and_full_memo():
    specs = [
        ("parabola_from_graph", template_parabola_from_graph),
        ("parabola_from_turning_point", template_parabola_from_turning_point),
    ]
    for pid, template in specs:
        params = _ENGINE.instantiate(pid, seed=3).params
        full = template(params, detail="full")
        short = template(params, detail="short")
        assert full.graph_svg and full.graph_svg.lstrip().startswith("<svg")
        assert len(full.worked_steps) == 3, pid  # method, pin a, expand
        assert len(short.worked_steps) == 1, pid  # answer only
        # the coefficient-pinning step is always present (the a = 1 lesson)
        assert any(r"\Rightarrow\; a =" in s for s in full.worked_steps), pid
