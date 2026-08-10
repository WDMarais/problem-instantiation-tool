"""
F1 scope sweep — every trust-gated generator must produce only in-scope draws.

This is the test-time consumer of the in-scope predicate (the per-draw guard,
`assert_in_scope`, is the runtime consumer). A green here is the CI half of the
"no generator ships without a green sweep" acceptance bar (`mvp-scope.md` §4c).

Spec section: F1 trust harness (`problem_instantiation_tool/scope.py`).
"""

from __future__ import annotations

import types

import pytest

from content.scope_predicates import (
    PREDICATES,
    PROBLEMS,
    monic_factorise_in_scope,
    quad_seq_find_n_in_scope,
)
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.exceptions import ScopeViolationError
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.scope import assert_in_scope, assert_scope_holds, sweep


@pytest.fixture(scope="module")
def engine() -> Engine:
    return Engine(registry=InMemoryRegistry(PROBLEMS))


@pytest.mark.scope
@pytest.mark.parametrize("problem_id", sorted(PREDICATES))
def test_generator_draws_are_all_in_scope(engine: Engine, problem_id: str) -> None:
    # min_distinct guards against a vacuous green: the sweep must actually explore
    # the draw space, not draw one instance 2000 times.
    report = assert_scope_holds(
        engine, problem_id, PREDICATES[problem_id], seeds=range(2000), min_distinct=20
    )
    assert report.instances_drawn == 2000


@pytest.mark.scope
def test_predicate_has_teeth_catches_out_of_scope() -> None:
    """Negative control: a hand-built out-of-scope instance MUST be flagged, and the
    guard MUST raise. Without this, a predicate that always returns [] would pass the
    sweep vacuously and prove nothing."""
    # x² + x + 0: c == 0 (trivial zero root) — out of scope by construction.
    bad = types.SimpleNamespace(
        params={"b": 1, "c": 0},
        spec=types.SimpleNamespace(id="monic_factorise"),
        seed=None,
    )
    reasons = monic_factorise_in_scope(bad)
    assert reasons, "predicate failed to flag a c==0 instance"

    with pytest.raises(ScopeViolationError) as exc:
        assert_in_scope(bad, monic_factorise_in_scope)
    assert exc.value.problem_id == "monic_factorise"
    assert exc.value.reasons


@pytest.mark.scope
def test_predicate_flags_irrational_and_complex_roots() -> None:
    """The non-tautological core: irrational (non-perfect-square disc) and complex
    (negative disc) presented coefficients are the exact draws a naive generator would
    leak, and the predicate reads them off b, c alone."""
    # x² + x + 1: disc = 1 - 4 = -3 < 0 → complex roots.
    complex_roots = types.SimpleNamespace(params={"b": 1, "c": 1})
    assert any("complex" in r for r in monic_factorise_in_scope(complex_roots))

    # x² + x - 1: disc = 1 + 4 = 5, not a perfect square → irrational roots.
    irrational = types.SimpleNamespace(params={"b": 1, "c": -1})
    assert any("irrational" in r for r in monic_factorise_in_scope(irrational))


@pytest.mark.scope
def test_quad_seq_find_n_predicate_flags_ambiguous_and_non_quadratic() -> None:
    """The non-tautological core for the sequence solve: 'which term equals V' must
    have exactly one positive-integer answer reachable by rational methods. The two
    draws a naive generator would leak are (a) a downward parabola where a second
    positive term also equals the target, and (b) terms that aren't quadratic at all.
    The predicate reads them off the presented terms + target alone."""
    # terms 5, 8, 9 ⇒ a=-1, b=6, c=0 (downward): T_2 = T_4 = 8, so "which term = 8?"
    # has two positive-integer answers — ambiguous.
    ambiguous = types.SimpleNamespace(params={"t1": 5, "t2": 8, "t3": 9, "target": 8})
    reasons = quad_seq_find_n_in_scope(ambiguous)
    assert any("ambiguous" in r for r in reasons), reasons

    # arithmetic run (constant first difference ⇒ second difference 0): not quadratic.
    not_quadratic = types.SimpleNamespace(
        params={"t1": 2, "t2": 4, "t3": 6, "target": 10}
    )
    assert any("not quadratic" in r for r in quad_seq_find_n_in_scope(not_quadratic))


@pytest.mark.scope
def test_sweep_report_is_informative_on_failure() -> None:
    """A failing sweep must name the offending seed + params so the author can replay.
    Drive it with a deliberately-broken predicate that rejects everything."""
    engine = Engine(registry=InMemoryRegistry(PROBLEMS))
    report = sweep(
        engine,
        "monic_factorise",
        lambda inst: ["deliberately rejected"],
        seeds=range(10),
    )
    assert not report.ok
    assert len(report.violations) == 10
    summary = report.summary()
    assert "monic_factorise" in summary
    assert "seed=" in summary
