"""
In-scope predicates (F1) for the currently trust-gated generators.

Each predicate reads the **presented** problem — the coefficients/terms the tutee
actually sees — and re-derives the in-scope conditions *independently of how the
generator constructed the instance*. That independence is the whole point: a predicate
that restates the construction (e.g. "roots are integers" for a generator that picked
integer roots) is vacuous. See `problem_instantiation_tool/scope.py`.

Predicates return a list of human-readable reasons the instance is OUT of scope; an
empty list means in scope. As generators are wired into worksheets, add a predicate
here (or co-locate it with the generator) and register it in ``PREDICATES``.
"""

from __future__ import annotations

import math

# Generators under trust gate. Imported here so the sweep test has a registry to drive.
from content.examples.arithmetic_sequence import nth_term_formula
from content.examples.monic_factorise import problem as monic_factorise
from content.examples.quadratic_roots import problem as quadratic_factor
from problem_instantiation_tool.schemas import ProblemInstance

# Bounds mirror each generator's declared draw ranges. Kept here (not imported from the
# generator) on purpose: the predicate is an *independent* statement of intent, so a
# generator regression that widens a range is caught rather than silently followed.
_MONIC_ROOT_BOUND = 8  # monic_factorise draws roots in [-8, 8]
_ARITH_A_BOUND = 20  # arithmetic_sequence draws a in [-20, 20]
_ARITH_D_BOUND = 10  # ... and d in [-10, 10] \ {0}
_QUAD_ROOT_BOUND = 10  # quadratic_factor draws roots in [-10, 10]
_QUAD_COEFF_RANGE = (1, 3)  # ... leading_coeff in [1, 3]


def monic_factorise_in_scope(instance: ProblemInstance) -> list[str]:
    """Presented problem: x² + bx + c. Read b, c only — NOT root1/root2.

    Re-derive the roots from the presented coefficients and demand they are real,
    rational, integer, distinct-or-repeated within band, with b, c non-degenerate.
    """
    p = instance.params
    b, c = p["b"], p["c"]
    reasons: list[str] = []

    if b == 0:
        reasons.append("b == 0: difference-of-squares case, excluded by this generator")
    if c == 0:
        reasons.append("c == 0: trivial zero root, excluded by this generator")

    disc = b * b - 4 * c
    if disc < 0:
        reasons.append(f"discriminant b²−4c = {disc} < 0: complex roots (out of scope)")
        return reasons  # can't reason about root band on complex roots

    root_disc = math.isqrt(disc)
    if root_disc * root_disc != disc:
        reasons.append(f"discriminant {disc} is not a perfect square: irrational roots")
        return reasons
    if (-b + root_disc) % 2 != 0:
        reasons.append(f"(-b ± √disc) is odd: roots are non-integer for b={b}, c={c}")
        return reasons

    r1 = (-b + root_disc) // 2
    r2 = (-b - root_disc) // 2
    for r in (r1, r2):
        if abs(r) > _MONIC_ROOT_BOUND:
            reasons.append(f"root {r} exceeds magnitude bound {_MONIC_ROOT_BOUND}")
    return reasons


def quadratic_factor_in_scope(instance: ProblemInstance) -> list[str]:
    """Presented problem: a(x − r₁)(x − r₂) = 0 — the roots ARE shown. Check band and
    integrality of the presented roots and the leading coefficient."""
    p = instance.params
    reasons: list[str] = []

    for key in ("root1", "root2"):
        r = p[key]
        if int(r) != r:
            reasons.append(f"{key}={r} is not an integer")
        elif abs(r) > _QUAD_ROOT_BOUND:
            reasons.append(f"{key}={r} exceeds magnitude bound {_QUAD_ROOT_BOUND}")

    a = p["leading_coeff"]
    lo, hi = _QUAD_COEFF_RANGE
    if not (lo <= a <= hi):
        reasons.append(f"leading_coeff={a} outside [{lo}, {hi}]")
    return reasons


def arith_nth_term_in_scope(instance: ProblemInstance) -> list[str]:
    """Presented problem: the first three terms t1, t2, t3. Recompute the common
    difference from the presented terms and demand a genuine arithmetic sequence with
    non-zero integer d, first term and d within band."""
    p = instance.params
    t1, t2, t3 = p["t1"], p["t2"], p["t3"]
    reasons: list[str] = []

    d = t2 - t1
    if t3 - t2 != d:
        reasons.append(
            f"terms {t1}, {t2}, {t3} are not arithmetic (gaps {d} vs {t3 - t2})"
        )
    if d == 0:
        reasons.append("common difference 0: constant sequence, excluded")
    if abs(d) > _ARITH_D_BOUND:
        reasons.append(f"|d|={abs(d)} exceeds bound {_ARITH_D_BOUND}")
    if abs(t1) > _ARITH_A_BOUND:
        reasons.append(f"|a|={abs(t1)} exceeds bound {_ARITH_A_BOUND}")
    return reasons


# problem_id → its Problem object (drives the sweep registry)
PROBLEMS = {
    monic_factorise.id: monic_factorise,
    quadratic_factor.id: quadratic_factor,
    nth_term_formula.id: nth_term_formula,
}

# problem_id → its in-scope predicate
PREDICATES = {
    monic_factorise.id: monic_factorise_in_scope,
    quadratic_factor.id: quadratic_factor_in_scope,
    nth_term_formula.id: arith_nth_term_in_scope,
}
