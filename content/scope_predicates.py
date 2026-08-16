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
from content.examples.linear_equation import problem as linear_add_pos
from content.examples.linear_equations import (
    linear_double_inequality,
    linear_expand,
    linear_literal,
    linear_rational,
    simultaneous_2x2,
)
from content.examples.monic_factorise import problem as monic_factorise
from content.examples.quadratic_roots import problem as quadratic_factor
from content.examples.quadratic_sequence import find_n as quad_seq_find_n
from problem_instantiation_tool.schemas import ProblemInstance

# Bounds mirror each generator's declared draw ranges. Kept here (not imported from the
# generator) on purpose: the predicate is an *independent* statement of intent, so a
# generator regression that widens a range is caught rather than silently followed.
_MONIC_ROOT_BOUND = 8  # monic_factorise draws roots in [-8, 8]
_ARITH_A_BOUND = 20  # arithmetic_sequence draws a in [-20, 20]
_ARITH_D_BOUND = 10  # ... and d in [-10, 10] \ {0}
_QUAD_ROOT_BOUND = 10  # quadratic_factor draws roots in [-10, 10]
_QUAD_COEFF_RANGE = (1, 3)  # ... leading_coeff in [1, 3]
_QUAD_SEQ_A_RANGE = (1, 2)  # quad_seq_find_n draws a in {1, 2} (a > 0: increasing)
_QUAD_SEQ_B_RANGE = (0, 6)  # ... b in [0, 6]  (b ≥ 0 keeps the vertex at n ≤ 0)
_QUAD_SEQ_C_RANGE = (-4, 6)  # ... c in [-4, 6]
_QUAD_SEQ_N_RANGE = (4, 9)  # ... the answer term index n in [4, 9]


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


def quad_seq_find_n_in_scope(instance: ProblemInstance) -> list[str]:
    """Presented problem: three terms t1, t2, t3 of a quadratic sequence and a target
    value; the tutee is asked *which term* equals the target.

    The load-bearing property is that "which term" has ONE unambiguous answer that the
    tutee can reach by rational methods: the induced quadratic ``a n² + b n + c =
    target`` must have a perfect-square discriminant (rational roots, no surds) and
    exactly one positive-integer root (no ± ambiguity, no second valid term index).
    We recover a, b, c from the presented terms — NOT from the generator's stored
    coefficients — so a construction regression that leaks an ambiguous or irrational
    solve is caught here.
    """
    p = instance.params
    t1, t2, t3, target = p["t1"], p["t2"], p["t3"], p["target"]
    reasons: list[str] = []

    d1 = t2 - t1  # first first-difference = 3a + b
    second_diff = (t3 - t2) - d1  # = 2a for a genuine quadratic sequence
    if second_diff == 0:
        reasons.append(f"second difference 0: terms {t1}, {t2}, {t3} are not quadratic")
        return reasons
    if second_diff % 2 != 0:
        reasons.append(f"second difference {second_diff} is odd: a is non-integer")
        return reasons

    a = second_diff // 2
    b = d1 - 3 * a
    c = t1 - a - b

    a_lo, a_hi = _QUAD_SEQ_A_RANGE
    if not (a_lo <= a <= a_hi):
        reasons.append(f"a={a} outside [{a_lo}, {a_hi}] (needs a>0 for a unique term)")
    b_lo, b_hi = _QUAD_SEQ_B_RANGE
    if not (b_lo <= b <= b_hi):
        reasons.append(f"b={b} outside [{b_lo}, {b_hi}]")
    c_lo, c_hi = _QUAD_SEQ_C_RANGE
    if not (c_lo <= c <= c_hi):
        reasons.append(f"c={c} outside [{c_lo}, {c_hi}]")

    # Induced equation: a n² + b n + (c − target) = 0.
    disc = b * b - 4 * a * (c - target)
    if disc < 0:
        reasons.append(f"discriminant {disc} < 0: no real term solves T_n = {target}")
        return reasons
    root_disc = math.isqrt(disc)
    if root_disc * root_disc != disc:
        reasons.append(f"discriminant {disc} is not a perfect square: irrational n")
        return reasons

    positive_int_roots = []
    for sign in (root_disc, -root_disc):
        num = -b + sign
        if num % (2 * a) == 0:
            n = num // (2 * a)
            if n >= 1:
                positive_int_roots.append(n)
    positive_int_roots = sorted(set(positive_int_roots))
    if len(positive_int_roots) != 1:
        reasons.append(
            f"T_n = {target} has {len(positive_int_roots)} positive-integer "
            f"solutions {positive_int_roots}: 'which term' is ambiguous"
        )
        return reasons

    n_lo, n_hi = _QUAD_SEQ_N_RANGE
    n = positive_int_roots[0]
    if not (n_lo <= n <= n_hi):
        reasons.append(f"answer term n={n} outside [{n_lo}, {n_hi}]")
    return reasons


# ── linear-equation family (ladder 1) ───────────────────────────────────────────
#
# Each predicate re-solves the *presented* equation independently of how the generator
# built it, then checks the answer is integer-or-clean-rational, non-degenerate, and in
# the intended teaching band. A naive generator's leak is exactly a non-integer /
# out-of-band / degenerate solution — read off the shown coefficients.

_LINEAR_ADD_A_RANGE = (1, 15)  # linear_add_pos: a is a positive constant in [1, 15]
_LINEAR_ADD_X_BOUND = 10  # ... solution x = b − a lands in [−10, 10]
_LINEAR_EXPAND_X_BOUND = 5  # linear_expand: integer solution in [−5, 5] \ {0}
_LINEAR_EXPAND_A_BOUND = 15  # ... |a| ≤ 15, a ≠ 0
_LINEAR_LITERAL_A_RANGE = (3, 8)  # linear_literal: a in [3, 8]
_LINEAR_LITERAL_B_RANGE = (2, 8)  # ... b in [2, 8]
_LINEAR_RATIONAL_X_BOUND = 8  # linear_rational: integer solution in [−8, 8] \ {0,p,q}
_LINEAR_INEQ_X_BOUND = 10  # linear_double_inequality: integer bounds within [−10, 10]
_SIMUL_XY_BOUND = 5  # simultaneous_2x2: integer x, y in [−5, 5]
_SIMUL_COEFF_BOUND = 4  # ... coefficients a,b,d,e in [−4, 4] \ {0}


def linear_add_pos_in_scope(instance: ProblemInstance) -> list[str]:
    """Presented: x + a = b. Read a, b only; the answer is x = b − a."""
    p = instance.params
    a, b = p["a"], p["b"]
    reasons: list[str] = []
    a_lo, a_hi = _LINEAR_ADD_A_RANGE
    if not (a_lo <= a <= a_hi):
        reasons.append(f"a={a} outside positive-constant band [{a_lo}, {a_hi}]")
    x = b - a
    if abs(x) > _LINEAR_ADD_X_BOUND:
        reasons.append(f"solution x={x} exceeds magnitude bound {_LINEAR_ADD_X_BOUND}")
    return reasons


def linear_expand_in_scope(instance: ProblemInstance) -> list[str]:
    """Presented: a − b(cx − d) = −(x − e). Solve independently:
    x·(1 − bc) = e − bd − a ⇒ x must be a nonzero integer in the band."""
    p = instance.params
    a, b, c, d, e = p["a"], p["b"], p["c"], p["d"], p["e"]
    reasons: list[str] = []
    if a == 0 or abs(a) > _LINEAR_EXPAND_A_BOUND:
        reasons.append(f"a={a} is zero or exceeds |a| ≤ {_LINEAR_EXPAND_A_BOUND}")
    denom = 1 - b * c
    if denom == 0:
        reasons.append(f"1 − bc = 0 for b={b}, c={c}: no unique solution")
        return reasons
    num = e - b * d - a
    if num % denom != 0:
        reasons.append(f"solution ({num})/({denom}) is not an integer")
        return reasons
    x = num // denom
    if x == 0:
        reasons.append("solution x = 0 (excluded — trivial)")
    if abs(x) > _LINEAR_EXPAND_X_BOUND:
        reasons.append(f"solution x={x} exceeds band {_LINEAR_EXPAND_X_BOUND}")
    return reasons


def linear_literal_in_scope(instance: ProblemInstance) -> list[str]:
    """Presented: ax − bq = cx. Solve independently: x = bq/(a − c). In scope when
    a − c ≥ 2 (unique, non-trivial coefficient) and a, b in band."""
    p = instance.params
    a, b, c = p["a"], p["b"], p["c"]
    reasons: list[str] = []
    a_lo, a_hi = _LINEAR_LITERAL_A_RANGE
    b_lo, b_hi = _LINEAR_LITERAL_B_RANGE
    if not (a_lo <= a <= a_hi):
        reasons.append(f"a={a} outside band [{a_lo}, {a_hi}]")
    if not (b_lo <= b <= b_hi):
        reasons.append(f"b={b} outside band [{b_lo}, {b_hi}]")
    if a - c < 2:
        reasons.append(
            f"a − c = {a - c} < 2: coefficient of q is trivial or undefined "
            f"(need a − c ≥ 2 for a unique, non-degenerate x)"
        )
    return reasons


def linear_rational_in_scope(instance: ProblemInstance) -> list[str]:
    """Presented: Ax/(x−p) + Bx/(x−q) = (kx² + m)/((x−p)(x−q)). For the equation to
    reduce to a *linear* one the presented x² coefficient k must equal A + B (else it
    stays quadratic). Then the remainder solves to x = −m/(Aq + Bp) — check integer,
    nonzero, in band, and off the excluded values."""
    p = instance.params
    A, B, pp, qq = p["A"], p["B"], p["p"], p["q"]
    k, m = p["rhs_quad_coeff"], p["rhs_const"]
    reasons: list[str] = []
    if pp == qq:
        reasons.append(f"excluded values coincide (p = q = {pp})")
    if k != A + B:
        reasons.append(
            f"x² coefficient {k} ≠ A+B ({A + B}): equation does not reduce to linear"
        )
        return reasons
    denom = A * qq + B * pp
    if denom == 0:
        reasons.append("Aq + Bp = 0: linear term vanishes, no unique solution")
        return reasons
    if (-m) % denom != 0:
        reasons.append(f"solution ({-m})/({denom}) is not an integer")
        return reasons
    x = (-m) // denom
    if x == 0 or x == pp or x == qq:
        reasons.append(f"solution x={x} is excluded (0 or an excluded value)")
    if abs(x) > _LINEAR_RATIONAL_X_BOUND:
        reasons.append(f"solution x={x} exceeds band {_LINEAR_RATIONAL_X_BOUND}")
    return reasons


def linear_double_inequality_in_scope(instance: ProblemInstance) -> list[str]:
    """Presented: p < ax + b < q. Solve independently: the two boundary x-values are
    (p−b)/a and (q−b)/a. In scope when both are integers, distinct, and in band. (a<0
    just swaps which is the lower bound — min/max normalise it.)"""
    p = instance.params
    a, b, lo_bound, hi_bound = p["a"], p["b"], p["p"], p["q"]
    reasons: list[str] = []
    if a == 0:
        reasons.append("a = 0: not linear in x")
        return reasons
    n1, n2 = lo_bound - b, hi_bound - b
    if n1 % a != 0 or n2 % a != 0:
        reasons.append(f"boundary x-values ({n1})/({a}), ({n2})/({a}) are not integers")
        return reasons
    xb1, xb2 = n1 // a, n2 // a
    lo, hi = min(xb1, xb2), max(xb1, xb2)
    if lo == hi:
        reasons.append(f"solution bounds coincide (x = {lo}): empty/degenerate range")
    if abs(lo) > _LINEAR_INEQ_X_BOUND or abs(hi) > _LINEAR_INEQ_X_BOUND:
        reasons.append(f"solution bounds {lo}, {hi} exceed band {_LINEAR_INEQ_X_BOUND}")
    return reasons


def simultaneous_2x2_in_scope(instance: ProblemInstance) -> list[str]:
    """Presented: ax+by=c, dx+ey=f. Solve independently by Cramer's rule:
    det = ae − bd must be nonzero (unique), and x = (ce−bf)/det, y = (af−cd)/det must
    be integers in band, not both zero."""
    p = instance.params
    a, b, c = p["a"], p["b"], p["c"]
    d, e, f = p["d"], p["e"], p["f"]
    reasons: list[str] = []
    for name, v in (("a", a), ("b", b), ("d", d), ("e", e)):
        if v == 0 or abs(v) > _SIMUL_COEFF_BOUND:
            reasons.append(f"{name}={v} is zero or exceeds |·| ≤ {_SIMUL_COEFF_BOUND}")
    det = a * e - b * d
    if det == 0:
        reasons.append(f"determinant ae − bd = {det}: system is singular")
        return reasons
    nx, ny = c * e - b * f, a * f - c * d
    if nx % det != 0 or ny % det != 0:
        reasons.append(f"solution ({nx}/{det}, {ny}/{det}) is not integer")
        return reasons
    x, y = nx // det, ny // det
    if x == 0 and y == 0:
        reasons.append("solution (0, 0): trivial")
    if abs(x) > _SIMUL_XY_BOUND or abs(y) > _SIMUL_XY_BOUND:
        reasons.append(f"solution ({x}, {y}) exceeds band {_SIMUL_XY_BOUND}")
    return reasons


# problem_id → its Problem object (drives the sweep registry)
PROBLEMS = {
    monic_factorise.id: monic_factorise,
    quadratic_factor.id: quadratic_factor,
    nth_term_formula.id: nth_term_formula,
    quad_seq_find_n.id: quad_seq_find_n,
    linear_add_pos.id: linear_add_pos,
    linear_expand.id: linear_expand,
    linear_literal.id: linear_literal,
    linear_rational.id: linear_rational,
    linear_double_inequality.id: linear_double_inequality,
    simultaneous_2x2.id: simultaneous_2x2,
}

# problem_id → its in-scope predicate
PREDICATES = {
    monic_factorise.id: monic_factorise_in_scope,
    quadratic_factor.id: quadratic_factor_in_scope,
    nth_term_formula.id: arith_nth_term_in_scope,
    quad_seq_find_n.id: quad_seq_find_n_in_scope,
    linear_add_pos.id: linear_add_pos_in_scope,
    linear_expand.id: linear_expand_in_scope,
    linear_literal.id: linear_literal_in_scope,
    linear_rational.id: linear_rational_in_scope,
    linear_double_inequality.id: linear_double_inequality_in_scope,
    simultaneous_2x2.id: simultaneous_2x2_in_scope,
}
