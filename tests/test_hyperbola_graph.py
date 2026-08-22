"""
Independent oracle for ``hyperbola_from_graph``.

The generator builds ``y = a/(x + p) + q`` forward from chosen asymptotes and a
lattice point. These tests read those features back out of the baked expression
with SymPy — evaluate at the labelled point, take limits at the asymptotes — and
assert they match the sketch's labels (the display-only contract). They also pin
the wire-only well-posedness invariant (the point never lies on an asymptote, so
``a`` is always recoverable), that equivalent algebraic forms grade full marks,
and that the template emits an inline two-branch graph plus a full memo.
"""

from __future__ import annotations

import sympy

from content.examples.hyperbola_from_graph import hyperbola_from_graph
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep
from worksheets.generate import template_hyperbola_from_graph

_x = sympy.Symbol("x")
_ENGINE = Engine(
    registry=InMemoryRegistry({hyperbola_from_graph.id: hyperbola_from_graph})
)


def _rate(inst, expr) -> tuple[int, int]:
    r = inst.verifier.rate(SolutionAttempt(steps=[SubmittedStep(expr)]))
    return r.marks_awarded, r.marks_possible


def test_answer_matches_the_labelled_features():
    for seed in range(80):
        inst = _ENGINE.instantiate("hyperbola_from_graph", seed=seed)
        p = inst.params
        expr, a, pp, qq = p["answer"], p["a"], p["p"], p["q"]
        # the labelled point lies on the curve
        assert sympy.simplify(expr.subs(_x, p["point_x"]) - p["point_y"]) == 0, (
            seed,
            p,
        )
        # horizontal asymptote: limit as x → ±∞ is q
        assert sympy.limit(expr, _x, sympy.oo) == qq, (seed, p)
        # vertical asymptote at x = -p: the curve blows up there
        assert sympy.limit(expr, _x, -pp, "+") in (sympy.oo, -sympy.oo), (seed, p)
        # a read back off the leading (1/x) behaviour
        assert sympy.limit((expr - qq) * (_x + pp), _x, sympy.oo) == a, (seed, p)


def test_is_always_well_posed():
    # wire-only claim: point never on an asymptote ⇒ a is recoverable.
    for seed in range(80):
        p = _ENGINE.instantiate("hyperbola_from_graph", seed=seed).params
        assert p["p"] != 0 and p["q"] != 0  # asymptotes off the axes
        assert p["point_x"] != -p["p"]  # not on the vertical asymptote
        assert p["point_y"] != p["q"]  # not on the horizontal asymptote
        assert p["a"] != 0


def test_verifier_accepts_baked_and_equivalent_forms():
    for seed in range(30):
        inst = _ENGINE.instantiate("hyperbola_from_graph", seed=seed)
        p = inst.params
        assert _rate(inst, p["answer"]) == (3, 3)
        # single combined fraction — algebraically identical, must grade full
        assert _rate(inst, sympy.together(p["answer"])) == (3, 3)
        # forgot to solve a (left a = 1): correct only if a really is 1
        assumed = 1 / (_x + p["p"]) + p["q"]
        awarded, _ = _rate(inst, assumed)
        assert (awarded == 3) == (p["a"] == 1)


def test_template_emits_two_branch_graph_and_full_memo():
    params = _ENGINE.instantiate("hyperbola_from_graph", seed=5).params
    full = template_hyperbola_from_graph(params, detail="full")
    short = template_hyperbola_from_graph(params, detail="short")
    assert full.graph_svg and full.graph_svg.lstrip().startswith("<svg")
    # two branches ⇒ at least two <polyline> runs from the None break
    assert full.graph_svg.count("<polyline") >= 2
    assert len(full.worked_steps) == 3  # form, pin a, state
    assert len(short.worked_steps) == 1  # answer only
    assert any("a = " in s for s in full.worked_steps)
