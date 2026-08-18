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
    arith_find_missing_in_scope,
    arith_find_n_in_scope,
    arith_from_two_terms_in_scope,
    arith_series_find_n_in_scope,
    discriminant_nature_in_scope,
    geo_find_missing_in_scope,
    geo_find_n_in_scope,
    geo_from_two_terms_in_scope,
    grouped_mean_solve_in_scope,
    linear_add_pos_in_scope,
    linear_double_inequality_in_scope,
    linear_expand_in_scope,
    linear_literal_in_scope,
    linear_rational_in_scope,
    monic_factorise_in_scope,
    nonlinear_simultaneous_in_scope,
    prob_count_intersection_in_scope,
    prob_venn_intersection_in_scope,
    quad_seq_find_n_in_scope,
    quadratic_inequality_in_scope,
    simultaneous_2x2_in_scope,
    surd_equation_in_scope,
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
@pytest.mark.scope
@pytest.mark.parametrize(
    "predicate, out_of_scope_params, needle",
    [
        # linear_add_pos: x = b − a = 19 blows the [−10, 10] band.
        (linear_add_pos_in_scope, {"a": 1, "b": 20, "answer": 19}, "magnitude bound"),
        # linear_expand: (e − bd − a)/(1 − bc) = (−2)/(−3) is not an integer.
        (
            linear_expand_in_scope,
            {"a": 1, "b": 2, "c": 2, "d": 1, "e": 1},
            "not an integer",
        ),
        # linear_literal: a − c = 1 < 2 makes the coefficient of q trivial.
        (linear_literal_in_scope, {"a": 5, "c": 4, "b": 3}, "a − c"),
        # linear_rational: presented x² coefficient 3 ≠ A + B = 2 → still quadratic.
        (
            linear_rational_in_scope,
            {"A": 1, "B": 1, "p": 2, "q": 3, "rhs_quad_coeff": 3, "rhs_const": -10},
            "does not reduce to linear",
        ),
        # linear_double_inequality: boundary (p − b)/a = 1/2 is not an integer.
        (
            linear_double_inequality_in_scope,
            {"a": 2, "b": 0, "p": 1, "q": 5},
            "not integers",
        ),
        # simultaneous_2x2: det = ae − bd = 0 → singular system.
        (
            simultaneous_2x2_in_scope,
            {"a": 2, "b": 2, "c": 4, "d": 1, "e": 1, "f": 2},
            "singular",
        ),
    ],
)
def test_linear_predicates_have_teeth(
    predicate, out_of_scope_params: dict, needle: str
) -> None:
    """Non-tautological control for the linear ladder: each predicate re-solves the
    *presented* equation and must flag the exact leak its type is vulnerable to (a
    non-integer / out-of-band / degenerate solution), naming why."""
    instance = types.SimpleNamespace(params=out_of_scope_params)
    reasons = predicate(instance)
    assert any(needle in r for r in reasons), (
        f"predicate missed the out-of-scope draw {out_of_scope_params}: {reasons}"
    )


@pytest.mark.scope
@pytest.mark.parametrize(
    "predicate, out_of_scope_params, needle",
    [
        # quadratic_inequality: a>0 and ">0" holds OUTSIDE the roots, but the stored
        # region claims "between" — a sign-analysis contradiction.
        (
            quadratic_inequality_in_scope,
            {"a": 1, "b": 2, "c": -8, "direction": ">", "region": "between"},
            "sign-analysis",
        ),
        # discriminant_nature: Δ = 4 (>0, perfect square) ⇒ rational, but nature says
        # non_real.
        (
            discriminant_nature_in_scope,
            {"a": 1, "b": 8, "c": 15, "discriminant": 4, "nature": "non_real"},
            "Δ-classification",
        ),
        # surd_equation: candidates {−4, −1}, but only −1 survives s·t+c ≥ 0 (s=1,c=2);
        # the stored valid set wrongly keeps the extraneous −4.
        (
            surd_equation_in_scope,
            {
                "a": -1,
                "b": 0,
                "c": 2,
                "s": 1,
                "candidate_roots": frozenset({-4, -1}),
                "valid_roots": frozenset({-4, -1}),
            },
            "stored valid",
        ),
        # nonlinear_simultaneous: intersections (1,3) and (3,7), but the stored pair
        # set carries a wrong y for x=3.
        (
            nonlinear_simultaneous_in_scope,
            {
                "m": 2,
                "k": 1,
                "p": -2,
                "q": 4,
                "x_values": frozenset({1, 3}),
                "solution_pairs": frozenset({(1, 3), (3, 99)}),
            },
            "stored pairs",
        ),
    ],
)
def test_quadratic_predicates_have_teeth(
    predicate, out_of_scope_params: dict, needle: str
) -> None:
    """Non-tautological control for the quadratics ladder: each predicate re-solves the
    presented problem via the discriminant and cross-checks the stored categorical/set
    answer, flagging a draw whose stored answer disagrees with the coefficients."""
    instance = types.SimpleNamespace(params=out_of_scope_params)
    reasons = predicate(instance)
    assert any(needle in r for r in reasons), (
        f"predicate missed the out-of-scope draw {out_of_scope_params}: {reasons}"
    )


@pytest.mark.scope
@pytest.mark.parametrize(
    "predicate, out_of_scope_params, needle",
    [
        # arith_find_n: (target − a)/d = 5/2 is not an integer ⇒ no term equals 5.
        (arith_find_n_in_scope, {"a": 0, "d": 2, "target": 5}, "not an integer"),
        # arith_find_missing: gap t_after − t_before = 3 is odd ⇒ mean not an integer.
        (arith_find_missing_in_scope, {"t_before": 1, "t_after": 4}, "odd"),
        # arith_from_two_terms: (T_q − T_p)/(q − p) = 10/3 is not an integer d.
        (
            arith_from_two_terms_in_scope,
            {"p": 2, "q": 5, "tp": 0, "tq": 10},
            "not an integer",
        ),
        # geo_find_n: 5 is not a power a·rᵏ of the sequence 1, 2, 4 ⇒ no term equals it.
        (
            geo_find_n_in_scope,
            {"t1": 1, "t2": 2, "t3": 4, "target": 5},
            "not a term",
        ),
        # geo_find_missing: t_before·t_after = 12 is not a perfect square ⇒ surd mean.
        (geo_find_missing_in_scope, {"t_before": 2, "t_after": 6}, "irrational"),
        # geo_from_two_terms: even gap (q − p = 2), stored r = −2 ⇒ sign hidden.
        (
            geo_from_two_terms_in_scope,
            {"p": 1, "q": 3, "tp": 1, "tq": 4, "r": -2},
            "hides the sign",
        ),
        # arith_series_find_n: a=10, d=−2 ⇒ S₄ = S₇ = 28, two positive n solutions.
        (arith_series_find_n_in_scope, {"a": 10, "d": -2, "sn": 28}, "ambiguous"),
    ],
)
def test_sequence_solve_mode_predicates_have_teeth(
    predicate, out_of_scope_params: dict, needle: str
) -> None:
    """Non-tautological control for the sequence solve-mode ladder: each predicate
    re-derives the answer (term index / missing term / ratio) from the presented terms
    and must flag the exact leak its type is vulnerable to — a non-integer, ambiguous,
    or sign-hidden solve — even though the current generator closes that surface."""
    instance = types.SimpleNamespace(params=out_of_scope_params)
    reasons = predicate(instance)
    assert any(needle in r for r in reasons), (
        f"predicate missed the out-of-scope draw {out_of_scope_params}: {reasons}"
    )


@pytest.mark.scope
@pytest.mark.parametrize(
    "predicate, out_of_scope_params, needle",
    [
        # prob_venn_intersection: P(A)+P(B)−P(A∪B) = 0.3 > min(0.2, 0.2) ⇒ impossible.
        (
            prob_venn_intersection_in_scope,
            {"p_a": 0.2, "p_b": 0.2, "p_aub": 0.1},
            "impossible Venn",
        ),
        # prob_count_intersection: 10 + 10 + 5 − 40 = −15 ⇒ counts exceed the total.
        (
            prob_count_intersection_in_scope,
            {"n_total": 40, "n_a": 10, "n_b": 10, "n_neither": 5},
            "inconsistent",
        ),
    ],
)
def test_probability_predicates_have_teeth(
    predicate, out_of_scope_params: dict, needle: str
) -> None:
    """Non-tautological control for the probability Venn ladder: each predicate
    re-derives the intersection via inclusion–exclusion and must flag a draw whose
    presented quantities describe an impossible Venn diagram."""
    instance = types.SimpleNamespace(params=out_of_scope_params)
    reasons = predicate(instance)
    assert any(needle in r for r in reasons), (
        f"predicate missed the out-of-scope draw {out_of_scope_params}: {reasons}"
    )


@pytest.mark.scope
@pytest.mark.parametrize(
    "out_of_scope_params, needle",
    [
        # k = (28·4 − 150)/(25 − 28) = −38/−3 is not a whole number ⇒ k isn't a count.
        (
            {
                "midpoints": [15, 25, 35, 45, 55],
                "frequencies": [1, None, 1, 1, 1],
                "unknown_index": 1,
                "mean_given": 28,
            },
            "not an integer",
        ),
        # unknown class midpoint (35) equals the stated mean (35) ⇒ divides by zero.
        (
            {
                "midpoints": [15, 25, 35, 45, 55],
                "frequencies": [4, 6, None, 6, 4],
                "unknown_index": 2,
                "mean_given": 35,
            },
            "divides by zero",
        ),
        # recovered k = (35·10 − 370)/(55 − 35) = −20/20 = −1 ⇒ negative, out of band.
        (
            {
                "midpoints": [15, 25, 35, 45, 55],
                "frequencies": [1, 1, 3, 5, None],
                "unknown_index": 4,
                "mean_given": 35,
            },
            "outside band",
        ),
    ],
)
def test_grouped_mean_solve_predicate_has_teeth(
    out_of_scope_params: dict, needle: str
) -> None:
    """Non-tautological control for the stats solve-mode: the predicate re-derives the
    unknown frequency k from the presented table + mean and must flag the leaks a naive
    draw would produce — a fractional k, a divide-by-zero unknown class, or an
    out-of-band (negative) count — even though the generator closes that surface."""
    instance = types.SimpleNamespace(params=out_of_scope_params)
    reasons = grouped_mean_solve_in_scope(instance)
    assert any(needle in r for r in reasons), (
        f"predicate missed the out-of-scope draw {out_of_scope_params}: {reasons}"
    )


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
