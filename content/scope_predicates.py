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

import sympy

# Generators under trust gate. Imported here so the sweep test has a registry to drive.
from content.examples.arithmetic_sequence import (
    find_missing as arith_seq_find_missing,
)
from content.examples.arithmetic_sequence import (
    find_n as arith_seq_find_n,
)
from content.examples.arithmetic_sequence import (
    from_two_terms as arith_seq_from_two_terms,
)
from content.examples.arithmetic_sequence import (
    nth_term_formula,
)
from content.examples.circle_equation import circle_equation
from content.examples.circle_tangent import circle_tangent
from content.examples.cubic_stationary_points import cubic_stationary_points
from content.examples.discriminant_nature import discriminant_nature
from content.examples.exponential_equation import exponential_equation
from content.examples.geometric_sequence import (
    find_missing as geo_seq_find_missing,
)
from content.examples.geometric_sequence import (
    find_n as geo_seq_find_n,
)
from content.examples.geometric_sequence import (
    from_two_terms as geo_seq_from_two_terms,
)
from content.examples.grouped_mean_solve import grouped_mean_solve
from content.examples.line_equation import line_equation
from content.examples.linear_equation import problem as linear_add_pos
from content.examples.linear_equations import (
    linear_double_inequality,
    linear_expand,
    linear_literal,
    linear_rational,
    simultaneous_2x2,
)
from content.examples.monic_factorise import problem as monic_factorise
from content.examples.motion_calculus import motion_calculus
from content.examples.nonlinear_simultaneous import nonlinear_simultaneous
from content.examples.optimisation_solve import optimisation_solve
from content.examples.probability_venn import (
    prob_count_intersection,
    prob_venn_intersection,
)
from content.examples.quadratic_inequality import quadratic_inequality
from content.examples.quadratic_roots import problem as quadratic_factor
from content.examples.quadratic_sequence import find_n as quad_seq_find_n
from content.examples.rform_skills import rform_solve
from content.examples.series import find_n_from_sum as arith_series_find_n
from content.examples.surd_equation import surd_equation
from content.examples.trig import trig_special_angles
from content.examples.trig_graph_properties import trig_graph_solve
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


# ── sequence solve-mode family (ladder 3) ───────────────────────────────────────
#
# Each of these is a *solve-for-the-unknown* draw: the answer (a term index n, a
# missing middle term, a first term / ratio) is derived, and its cleanliness rests on
# a generator invariant (monotonicity, a positive geometric mean, an odd gap for a
# negative ratio). The predicate re-derives that answer from the *presented* terms and
# demands it is unique, integer, and in band — so a construction regression that widens
# a range and leaks a non-integer / ambiguous / sign-hidden solve is caught here.
_ARITH_FIND_N_RANGE = (5, 50)  # arith_seq_find_n: answer index n in [5, 50]
_ARITH_MISS_D_BOUND = 10  # find_missing / from_two_terms share the arith |d| ≤ 10 band
_ARITH_FROM2T_A_BOUND = 15  # arith_seq_from_two_terms: first term a in [−15, 15]
_GEO_FIND_N_RANGE = (5, 8)  # geo_seq_find_n: answer index n in [5, 8]
_GEO_R_ABS = (2, 3)  # geometric ratio magnitude |r| in {2, 3}
_ASERIES_A_RANGE = (1, 10)  # arith_series_find_n: first term a in [1, 10]
_ASERIES_D_RANGE = (1, 6)  # ... difference d in [1, 6]  (a>0, d>0 ⇒ unique positive n)
_ASERIES_N_RANGE = (5, 12)  # ... answer number-of-terms n in [5, 12]


def arith_find_n_in_scope(instance: ProblemInstance) -> list[str]:
    """Presented: an arithmetic sequence (first term a, difference d) and a target;
    the tutee solves a + (n−1)d = target for the term index n. Read a, d, target — the
    answer must be a positive integer in band (non-integer ⇒ no term equals it)."""
    p = instance.params
    a, d, target = p["a"], p["d"], p["target"]
    reasons: list[str] = []
    if d == 0:
        reasons.append("common difference 0: 'which term' is undefined")
        return reasons
    if abs(d) > _ARITH_MISS_D_BOUND:
        reasons.append(f"|d|={abs(d)} exceeds bound {_ARITH_MISS_D_BOUND}")
    if abs(a) > _ARITH_A_BOUND:
        reasons.append(f"|a|={abs(a)} exceeds bound {_ARITH_A_BOUND}")
    num = target - a
    if num % d != 0:
        reasons.append(
            f"(target − a)/d = ({num})/({d}) is not an integer: no term equals {target}"
        )
        return reasons
    n = num // d + 1
    n_lo, n_hi = _ARITH_FIND_N_RANGE
    if n < 1:
        reasons.append(f"solved index n={n} is not a positive term")
    elif not (n_lo <= n <= n_hi):
        reasons.append(f"answer index n={n} outside [{n_lo}, {n_hi}]")
    return reasons


def arith_find_missing_in_scope(instance: ProblemInstance) -> list[str]:
    """Presented: three consecutive arithmetic terms with the middle blank — t_before,
    ?, t_after. The missing term is the average (t_before + t_after)/2; it must be an
    integer (the gap t_after − t_before is even = 2d), with a nonzero d in band."""
    p = instance.params
    tb, ta = p["t_before"], p["t_after"]
    reasons: list[str] = []
    gap = ta - tb
    if gap % 2 != 0:
        reasons.append(
            f"gap t_after − t_before = {gap} is odd: middle term (t_b+t_a)/2 is not "
            f"an integer"
        )
        return reasons
    d = gap // 2
    if d == 0:
        reasons.append("common difference 0: constant run, excluded")
    if abs(d) > _ARITH_MISS_D_BOUND:
        reasons.append(f"|d|={abs(d)} exceeds bound {_ARITH_MISS_D_BOUND}")
    return reasons


def arith_from_two_terms_in_scope(instance: ProblemInstance) -> list[str]:
    """Presented: two terms T_p and T_q of an arithmetic sequence (p < q). The tutee
    solves d = (T_q − T_p)/(q − p) then a = T_p − (p−1)d. In scope when d is a nonzero
    integer in band and a is in band — a naive draw leaks a non-integer d."""
    p = instance.params
    pp, qq, tp, tq = p["p"], p["q"], p["tp"], p["tq"]
    reasons: list[str] = []
    if qq <= pp:
        reasons.append(f"term positions not increasing: p={pp}, q={qq}")
        return reasons
    span = qq - pp
    if (tq - tp) % span != 0:
        reasons.append(
            f"d = (T_q − T_p)/(q − p) = ({tq - tp})/({span}) is not an integer"
        )
        return reasons
    d = (tq - tp) // span
    if d == 0:
        reasons.append("common difference 0: constant sequence, excluded")
    if abs(d) > _ARITH_MISS_D_BOUND:
        reasons.append(f"|d|={abs(d)} exceeds bound {_ARITH_MISS_D_BOUND}")
    a = tp - (pp - 1) * d
    if abs(a) > _ARITH_FROM2T_A_BOUND:
        reasons.append(f"first term a={a} exceeds bound {_ARITH_FROM2T_A_BOUND}")
    return reasons


def geo_find_n_in_scope(instance: ProblemInstance) -> list[str]:
    """Presented: a geometric sequence t1, t2, t3 and a target; the tutee solves
    a·r^(n−1) = target for the term index n. Recover r from the terms and divide the
    target down by r: it must bottom out at the first term for a unique integer n in
    band (a target that is not a·r^(n−1) means no term equals it)."""
    p = instance.params
    t1, t2, t3, target = p["t1"], p["t2"], p["t3"], p["target"]
    reasons: list[str] = []
    if t1 == 0:
        reasons.append("first term 0: not a geometric sequence")
        return reasons
    if t2 % t1 != 0 or (t2 and t3 % t2 != 0):
        reasons.append(f"terms {t1}, {t2}, {t3} have a non-integer ratio")
        return reasons
    r = t2 // t1
    if t2 == 0 or t3 // t2 != r:
        reasons.append(f"terms {t1}, {t2}, {t3} are not geometric")
        return reasons
    r_lo, r_hi = _GEO_R_ABS
    if not (r_lo <= abs(r) <= r_hi):
        reasons.append(f"ratio r={r} outside |r| in [{r_lo}, {r_hi}]")
        return reasons
    if target % t1 != 0:
        reasons.append(f"target {target} is not t1·rᵏ: no term equals it")
        return reasons
    quotient = target // t1
    n_minus_1 = 0
    while quotient % r == 0 and abs(quotient) > 1:
        quotient //= r
        n_minus_1 += 1
    if quotient != 1:
        reasons.append(
            f"target {target} is not a term a·r^(n−1): no integer n solves it"
        )
        return reasons
    n = n_minus_1 + 1
    n_lo, n_hi = _GEO_FIND_N_RANGE
    if not (n_lo <= n <= n_hi):
        reasons.append(f"answer index n={n} outside [{n_lo}, {n_hi}]")
    return reasons


def geo_find_missing_in_scope(instance: ProblemInstance) -> list[str]:
    """Presented: three consecutive geometric terms with the middle blank — t_before,
    ?, t_after (positive by construction). The missing term is the geometric mean
    √(t_before·t_after); in scope when that product is a perfect square (integer mean,
    no surd) and the induced ratio √(t_after/t_before) is a valid integer in band."""
    p = instance.params
    tb, ta = p["t_before"], p["t_after"]
    reasons: list[str] = []
    if tb <= 0 or ta <= 0:
        reasons.append(
            f"non-positive terms t_before={tb}, t_after={ta}: ± mean ambiguity"
        )
        return reasons
    prod = tb * ta
    root = math.isqrt(prod)
    if root * root != prod:
        reasons.append(
            f"t_before·t_after = {prod} is not a perfect square: geometric mean is "
            f"irrational"
        )
        return reasons
    if ta % tb != 0:
        reasons.append(f"t_after/t_before = {ta}/{tb} is not r²: non-integer ratio")
        return reasons
    r_sq = ta // tb
    r = math.isqrt(r_sq)
    if r * r != r_sq:
        reasons.append(
            f"t_after/t_before = {r_sq} is not a perfect square: r irrational"
        )
        return reasons
    r_lo, r_hi = _GEO_R_ABS
    if not (r_lo <= r <= r_hi):
        reasons.append(f"ratio r={r} outside [{r_lo}, {r_hi}]")
    return reasons


def geo_from_two_terms_in_scope(instance: ProblemInstance) -> list[str]:
    """Presented: two terms T_p and T_q of a geometric sequence (p < q). The tutee
    solves r^(q−p) = T_q/T_p for r, then a. In scope when r is a unique integer in
    band: the ratio must be an exact (q−p)-th power, and — crucially — an EVEN gap must
    not hide the sign of r (T_q/T_p > 0 leaves r = ±root indistinguishable). The stored
    answer r is cross-checked, so a draw whose r is not recoverable from the terms is
    caught."""
    p = instance.params
    pp, qq, tp, tq, stored_r = p["p"], p["q"], p["tp"], p["tq"], p["r"]
    reasons: list[str] = []
    if qq <= pp:
        reasons.append(f"term positions not increasing: p={pp}, q={qq}")
        return reasons
    if tp == 0:
        reasons.append("T_p = 0: not a geometric sequence")
        return reasons
    gap = qq - pp
    if tq % tp != 0:
        reasons.append(f"T_q/T_p = {tq}/{tp} is not integer: ratio is not r^(q−p)")
        return reasons
    ratio = tq // tp
    approx = round(abs(ratio) ** (1.0 / gap))
    r_abs = next(
        (c for c in (approx - 1, approx, approx + 1) if c > 0 and c**gap == abs(ratio)),
        None,
    )
    if r_abs is None:
        reasons.append(
            f"T_q/T_p = {ratio} is not a perfect (q−p)-th power: r irrational"
        )
        return reasons
    r_lo, r_hi = _GEO_R_ABS
    if not (r_lo <= r_abs <= r_hi):
        reasons.append(f"ratio |r|={r_abs} outside [{r_lo}, {r_hi}]")
    if gap % 2 == 0 and stored_r < 0:
        reasons.append(
            f"even gap {gap} hides the sign of r: stored r={stored_r} not recoverable "
            f"from T_p, T_q"
        )
    if abs(stored_r) != r_abs:
        reasons.append(f"stored r={stored_r} disagrees with recovered |r|={r_abs}")
    return reasons


def arith_series_find_n_in_scope(instance: ProblemInstance) -> list[str]:
    """Presented: an arithmetic series (first term a, difference d) and the sum S_n of
    its first n terms; the tutee solves the quadratic d·n² + (2a − d)·n − 2·S_n = 0 for
    n. In scope when there is exactly ONE positive-integer n in band — a naive draw
    (e.g. a non-increasing partial-sum) leaks a second positive root or irrational n."""
    p = instance.params
    a, d, sn = p["a"], p["d"], p["sn"]
    reasons: list[str] = []
    a_lo, a_hi = _ASERIES_A_RANGE
    d_lo, d_hi = _ASERIES_D_RANGE
    if not (a_lo <= a <= a_hi):
        reasons.append(f"a={a} outside [{a_lo}, {a_hi}]")
    if not (d_lo <= d <= d_hi):
        reasons.append(f"d={d} outside [{d_lo}, {d_hi}]")
    A, B, C = d, 2 * a - d, -2 * sn
    if A == 0:
        reasons.append("d = 0: partial sum is linear, not a solvable quadratic in n")
        return reasons
    disc = B * B - 4 * A * C
    if disc < 0:
        reasons.append(f"discriminant {disc} < 0: no real n solves S_n = {sn}")
        return reasons
    root = math.isqrt(disc)
    if root * root != disc:
        reasons.append(f"discriminant {disc} is not a perfect square: n is irrational")
        return reasons
    positive_int_roots = []
    for sign in (root, -root):
        num = -B + sign
        if num % (2 * A) == 0:
            n = num // (2 * A)
            if n >= 1:
                positive_int_roots.append(n)
    positive_int_roots = sorted(set(positive_int_roots))
    if len(positive_int_roots) != 1:
        reasons.append(
            f"S_n = {sn} has {len(positive_int_roots)} positive-integer solutions "
            f"{positive_int_roots}: number of terms is ambiguous"
        )
        return reasons
    n = positive_int_roots[0]
    n_lo, n_hi = _ASERIES_N_RANGE
    if not (n_lo <= n <= n_hi):
        reasons.append(f"answer n={n} outside [{n_lo}, {n_hi}]")
    return reasons


# ── probability Venn "find the intersection" family (ladder 5) ───────────────────
#
# Both are solve-for-unknown: the tutee recovers the intersection from the other three
# quantities via inclusion–exclusion. The F1 surface is *Venn consistency* — the
# recovered intersection must be a legal region (0 < it ≤ min of the two sets, and the
# union ≤ the whole). A naive draw leaks an impossible Venn (a union too small, counts
# exceeding the total); the predicate re-derives the intersection and rejects it.


def prob_venn_intersection_in_scope(instance: ProblemInstance) -> list[str]:
    """Presented: P(A), P(B), P(A∪B). The tutee solves P(A∩B) = P(A)+P(B)−P(A∪B).
    In scope when that intersection is a legal probability consistent with a Venn
    diagram: 0 < P(A∩B) ≤ min(P(A), P(B)), each value in [0, 1], and P(A∪B) ≤ 1."""
    p = instance.params
    pa, pb, paub = p["p_a"], p["p_b"], p["p_aub"]
    reasons: list[str] = []
    for name, v in (("P(A)", pa), ("P(B)", pb), ("P(A∪B)", paub)):
        if not (0 <= v <= 1):
            reasons.append(f"{name} = {v} is not a probability in [0, 1]")
    if paub > 1:
        reasons.append(f"P(A∪B) = {paub} exceeds 1")
    p_ab = pa + pb - paub
    if p_ab <= 0:
        reasons.append(f"P(A∩B) = {p_ab} ≤ 0: events disjoint or Venn inconsistent")
    if p_ab > min(pa, pb):
        reasons.append(
            f"P(A∩B) = {p_ab} exceeds min(P(A), P(B)) = {min(pa, pb)}: impossible Venn"
        )
    return reasons


def prob_count_intersection_in_scope(instance: ProblemInstance) -> list[str]:
    """Presented: n(A), n(B), n(neither), n(total). The tutee solves
    n(A∩B) = n(A) + n(B) + n(neither) − n(total). In scope when that count is a legal
    Venn region: 0 ≤ n(A∩B) ≤ min(n(A), n(B)), and no single count exceeds the total."""
    p = instance.params
    nt, na, nb, nn = p["n_total"], p["n_a"], p["n_b"], p["n_neither"]
    reasons: list[str] = []
    if nn < 0:
        reasons.append(f"n(neither) = {nn} is negative")
    n_ab = na + nb + nn - nt
    if n_ab < 0:
        reasons.append(f"n(A∩B) = {n_ab} < 0: counts exceed the total (inconsistent)")
    if n_ab > min(na, nb):
        reasons.append(
            f"n(A∩B) = {n_ab} exceeds min(n(A), n(B)) = {min(na, nb)}: impossible"
        )
    if na > nt or nb > nt:
        reasons.append(f"a single-set count exceeds the total {nt}")
    return reasons


# ── statistics solve-mode family (ladder 6) ─────────────────────────────────────
#
# Of the four stats archetypes only ``grouped_mean_solve`` is solve-for-unknown: the
# tutee recovers a single missing frequency k from the presented table and the stated
# estimated mean. The other three (mean/σ, one-var five-number, grouped read-offs) are
# forward read-offs — the dataset IS the draw, answers are whatever it produces, and any
# degeneracy is guarded in the generator — so they carry no F1 surface and no predicate.
#
# The load-bearing property here is that k is a *count*: the linear equation
# x̄ = (Σ_known f·m + k·m_j)/(Σ_known f + k) must yield a positive whole-number k. We
# recover k from the presented midpoints/frequencies/mean — NOT the generator's stored
# ``unknown_frequency`` — so a construction regression that leaks a fractional or
# out-of-band k (or an unknown class whose midpoint equals the mean, dividing by zero)
# is caught here.
_GROUPED_MEAN_K_RANGE = (1, 40)  # grouped_mean_solve draws k as a whole frequency 1..40


def grouped_mean_solve_in_scope(instance: ProblemInstance) -> list[str]:
    """Presented: a grouped table (midpoints + frequencies, one class blank) and the
    stated estimated mean x̄. The tutee solves the single linear equation in the unknown
    frequency k. Re-derive k = (x̄·Σ_known f − Σ_known f·m)/(m_j − x̄) from the shown
    table and demand it is a positive whole number in band."""
    p = instance.params
    mids = p["midpoints"]
    freqs = p["frequencies"]  # None marks the unknown class
    j = p["unknown_index"]
    xbar = p["mean_given"]
    reasons: list[str] = []

    m_j = mids[j]
    if m_j == xbar:
        reasons.append(
            f"unknown-class midpoint {m_j} equals the mean {xbar}: divides by zero"
        )
        return reasons

    sum_known_f = sum(f for i, f in enumerate(freqs) if i != j)
    sum_known_fm = sum(f * mids[i] for i, f in enumerate(freqs) if i != j)
    num = xbar * sum_known_f - sum_known_fm
    den = m_j - xbar
    if num % den != 0:
        reasons.append(
            f"solved frequency ({num})/({den}) is not an integer: k must be a count"
        )
        return reasons

    k = num // den
    k_lo, k_hi = _GROUPED_MEAN_K_RANGE
    if not (k_lo <= k <= k_hi):
        reasons.append(f"solved frequency k={k} outside band [{k_lo}, {k_hi}]")
    if "unknown_frequency" in p and k != p["unknown_frequency"]:
        reasons.append(
            f"stored k={p['unknown_frequency']} disagrees with recovered k={k}"
        )
    return reasons


# ── analytic-geometry family (ladder 7) ─────────────────────────────────────────
#
# Of the five analytic-geo archetypes only the three that construct *toward a target
# answer-form* carry F1 surface: a line equation y = m·x + c and a circle centre/radius
# both fall out of scope when a draw makes that form undefined. The two forward
# read-offs (triangle five-answers, angle-between-lines) draw raw integer points and
# report whatever midpoint/gradient/surd/angle results — the surds and decimals ARE the
# expected answer and every degeneracy is guarded — so they carry no F1 surface.
#
# Each predicate re-derives the answer-form from the *presented* points/coefficients and
# flags the draw that pushes it out of the y = m·x + c (or real-circle) scope.

_CIRCLE_RSQ_RANGE = (2, 40)  # circle_equation draws r^2 as a whole number 2..40


def line_equation_in_scope(instance: ProblemInstance) -> list[str]:
    """Presented: line L through two points, a point P, and 'parallel'/'perpendicular'.
    The required line is y = m·x + c. Re-derive m from the shown points and the
    relation; flag the draws where that gradient is undefined — a vertical L (no m),
    or a horizontal L asked for a perpendicular (the required line is vertical)."""
    p = instance.params
    gx1, gy1, gx2, gy2 = p["gx1"], p["gy1"], p["gx2"], p["gy2"]
    px, py = p["px"], p["py"]
    relation = p["relation"]
    reasons: list[str] = []

    if gx1 == gx2:
        reasons.append(
            f"line L is vertical (x={gx1} twice): gradient undefined, no y=mx+c"
        )
        return reasons
    if relation == "perpendicular" and gy1 == gy2:
        reasons.append(
            f"L is horizontal (y={gy1} twice) and the ask is perpendicular: "
            "the required line is vertical, no y=mx+c"
        )
        return reasons

    m_l = sympy.Rational(gy2 - gy1, gx2 - gx1)
    required = m_l if relation == "parallel" else -1 / m_l
    c = sympy.Rational(py) - required * px
    if required != p["required_gradient"]:
        reasons.append(
            f"recovered gradient {required} disagrees with stored "
            f"{p['required_gradient']}"
        )
    if c != p["c"]:
        reasons.append(f"recovered intercept {c} disagrees with stored {p['c']}")
    return reasons


def circle_equation_in_scope(instance: ProblemInstance) -> list[str]:
    """Presented: x^2 + y^2 + Dx + Ey + F = 0. Completing the square gives centre
    (-D/2, -E/2) and r^2 = (D/2)^2 + (E/2)^2 - F. Re-derive both from the shown D, E, F
    and demand an integer centre (D, E even) and a positive, in-band, whole r^2 — an odd
    D/E leaks a non-integer centre and F too large leaves an imaginary circle."""
    p = instance.params
    d, e, f = p["D"], p["E"], p["F"]
    reasons: list[str] = []

    if d % 2 != 0 or e % 2 != 0:
        reasons.append(
            f"D={d}, E={e}: completing the square gives a non-integer centre"
        )
    centre_x = sympy.Rational(-d, 2)
    centre_y = sympy.Rational(-e, 2)
    rsq = sympy.Rational(d, 2) ** 2 + sympy.Rational(e, 2) ** 2 - f
    if rsq <= 0:
        reasons.append(f"radius^2 = {rsq} ≤ 0: not a real circle")
        return reasons
    lo, hi = _CIRCLE_RSQ_RANGE
    if rsq != int(rsq) or not (lo <= rsq <= hi):
        reasons.append(f"radius^2 = {rsq} outside the integer band [{lo}, {hi}]")
    if centre_x != p["centre_x"] or centre_y != p["centre_y"]:
        reasons.append(
            f"recovered centre ({centre_x}, {centre_y}) disagrees with stored "
            f"({p['centre_x']}, {p['centre_y']})"
        )
    return reasons


def circle_tangent_in_scope(instance: ProblemInstance) -> list[str]:
    """Presented: centre C(h, k) and point P(px, py) on the circle. The tangent at P is
    y = m·x + c with m = -(px-h)/(py-k). Re-derive the radius offset from the shown
    points; flag py==k (tangent vertical, no y=mx+c) and px==h (radius gradient
    undefined — the taught method divides by px-h)."""
    p = instance.params
    h, k, px, py = p["h"], p["k"], p["px"], p["py"]
    reasons: list[str] = []

    dx, dy = px - h, py - k
    if dx == 0:
        reasons.append(
            f"P is directly above/below the centre (x={px}=h): radius gradient "
            "undefined"
        )
    if dy == 0:
        reasons.append(
            f"P is level with the centre (y={py}=k): tangent is vertical, no y=mx+c"
        )
    if reasons:
        return reasons

    tangent = -sympy.Rational(dx, dy)
    c = sympy.Rational(py) - tangent * px
    if tangent != p["tangent_gradient"]:
        reasons.append(
            f"recovered tangent gradient {tangent} disagrees with stored "
            f"{p['tangent_gradient']}"
        )
    if c != p["c"]:
        reasons.append(f"recovered intercept {c} disagrees with stored {p['c']}")
    return reasons


# ── calculus family (ladder 8) ──────────────────────────────────────────────────
#
# Of the seven calculus archetypes only the three that construct *backward toward a
# clean, well-posed answer* carry F1 surface: the cubic-turning-points ask presumes
# two distinct real stationary points, the motion ask presumes a genuine maximum
# velocity in the physical domain, and the optimisation ask presumes a genuine minimum
# for x > 0. A draw that breaks the presumption leaves a question whose own wording is
# wrong. The other four (both differentiations, the tangent line, the concavity
# read-off) are forward reports: a polynomial always has a finite derivative and a
# cubic always has exactly one real inflection, so no draw pushes them out of scope.
# (Integer turning-point/inflection coordinates are cosmetic, not scope —
# numeric_equality accepts the decimal.)
#
# Each predicate re-derives the presumption from the *presented* coefficients — f′ / f″
# solved fresh — independently of the backward construction.


def cubic_stationary_points_in_scope(instance: ProblemInstance) -> list[str]:
    """Presented: cubic f(x) = a·x³ + b·x² + c·x + d, asked for *the two* turning
    points and their max/min classification. f′(x) = 3a·x² + 2b·x + c must have two
    distinct real roots — re-derive its discriminant Δ = (2b)² − 12ac from the shown
    coefficients and flag Δ ≤ 0, where the cubic has a repeated stationary point (Δ = 0,
    an inflection with a horizontal tangent) or none at all (Δ < 0) and the 'two turning
    points' ask is wrong."""
    p = instance.params
    a, b, c = p["a"], p["b"], p["c"]
    reasons: list[str] = []

    disc = (2 * b) ** 2 - 4 * (3 * a) * c
    if disc < 0:
        reasons.append(
            f"f'(x)=3·{a}x²+2·{b}x+{c} has discriminant {disc} < 0: no real "
            "stationary points, the 'two turning points' ask is unsolvable"
        )
        return reasons
    if disc == 0:
        reasons.append(
            f"f'(x) discriminant {disc} = 0: a single repeated stationary point, "
            "not the two distinct turning points the ask presumes"
        )
        return reasons

    xsym = sympy.Symbol("x")
    roots = sympy.solve(3 * a * xsym**2 + 2 * b * xsym + c, xsym)
    if frozenset(roots) != p["stationary_x"]:
        reasons.append(
            f"recovered stationary x {frozenset(roots)} disagrees with stored "
            f"{p['stationary_x']}"
        )
    return reasons


def motion_calculus_in_scope(instance: ProblemInstance) -> list[str]:
    """Presented: displacement s(t) = α·t³ + β·t² + γ·t + δ, asked for the *maximum*
    velocity. v(t) = 3α·t² + 2β·t + γ; its stationary point (a(t) = 6α·t + 2β = 0) is a
    maximum only when the parabola opens downward, i.e. 3α < 0, and lands in the
    physical domain t > 0. Re-derive t* = −β/(3α) and flag α ≥ 0 (the stationary
    velocity is a minimum, so 'maximum velocity' is wrong) and t* ≤ 0 (outside
    t ≥ 0)."""
    p = instance.params
    alpha, beta = p["alpha"], p["beta"]
    reasons: list[str] = []

    if alpha >= 0:
        reasons.append(
            f"α={alpha} ≥ 0: velocity v=3α·t²+… opens upward, its turning point is a "
            "minimum — 'maximum velocity' is wrong"
        )
        return reasons

    t_star = sympy.Rational(-beta, 3 * alpha)
    if t_star <= 0:
        reasons.append(
            f"time of maximum velocity t*={t_star} ≤ 0: outside the physical domain t≥0"
        )
        return reasons
    if t_star != p["t_max"]:
        reasons.append(f"recovered time t*={t_star} disagrees with stored {p['t_max']}")
    return reasons


def optimisation_solve_in_scope(instance: ProblemInstance) -> list[str]:
    """Presented: quantity Q(x) = a·x + b/x on x > 0, asked to *minimise*. Q′(x) = a −
    b/x² vanishes at x = √(b/a), and Q″ = 2b/x³ > 0 there, giving a genuine minimum,
    only when a > 0 and b > 0. Re-derive from the shown coefficients and flag a ≤ 0 (Q
    decreasing, no minimum for x > 0) or b ≤ 0 (Q′ never zero on x > 0, no stationary
    point)."""
    p = instance.params
    a, b = p["a"], p["b"]
    reasons: list[str] = []

    if a <= 0:
        reasons.append(
            f"a={a} ≤ 0: Q(x)=a·x+b/x has no minimum for x>0 (unbounded below)"
        )
        return reasons
    if b <= 0:
        reasons.append(
            f"b={b} ≤ 0: Q′(x)=a−b/x² never zero for x>0, no minimum to find"
        )
        return reasons

    x_star = sympy.sqrt(sympy.Rational(b, a))
    if x_star != p["optimal_x"]:
        reasons.append(
            f"recovered optimal x={x_star} disagrees with stored {p['optimal_x']}"
        )
    return reasons


# ── trigonometry family (ladder 9) ──────────────────────────────────────────────
#
# Eleven trig archetypes; three carry F1 surface. The special-angle evaluation is
# rejection-sampled toward an answer in ℚ[√2, √3] — a draw pairing a √2-term with a
# √3-term yields √6, out of Gr10 scope — so it is gated on the *presented* expression.
# The two "solve" archetypes (R-form and its graph twin) construct backward toward a
# solvable equation |k| < R; a draw with k ≥ R leaves the 'two solutions' ask with none,
# so both are gated on R re-derived from the shown coefficients (these two were wired in
# an earlier pass and are gated here for the first time).
#
# The other eight are forward reads with no F1 surface: cast-ratios (a proper-quadrant
# point always gives defined ratios in lowest terms), trig_equation (domain β ∈ [0°,
# 90°/n] forces nβ ∈ [0°, 90°] where each ratio is monotonic, so the tabulated answer is
# unique), and the amplitude / range / decreasing / match / find_R / find_φ read-offs.

_TRIG_FN = {
    "sin": sympy.sin,
    "cos": sympy.cos,
    "tan": sympy.tan,
    "cosec": lambda a: 1 / sympy.sin(a),
    "cot": lambda a: sympy.cos(a) / sympy.sin(a),
}


def _nice_surd(expr: sympy.Basic) -> bool:
    """True iff expr is real, finite, and its only surds are √2 and/or √3."""
    if not expr.is_real or expr.is_infinite:
        return False
    for pw in expr.atoms(sympy.Pow):
        if pw.exp == sympy.Rational(1, 2) and pw.base not in (
            sympy.Integer(2),
            sympy.Integer(3),
        ):
            return False
    return True


def trig_special_angles_in_scope(instance: ProblemInstance) -> list[str]:
    """Presented: a two-term special-angle expression f₁(θ₁) OP f₂(θ₂), asked to
    evaluate in exact form. Gr10 scope keeps the answer in ℚ[√2, √3] — a √2-term times a
    √3-term produces √6, out of scope. Re-evaluate the *shown* functions and angles from
    scratch and flag any answer carrying a surd other than √2/√3, or a trivially-zero
    result."""
    p = instance.params
    reasons: list[str] = []
    v1 = _TRIG_FN[p["func1"]](sympy.pi * p["angle1"] / 180)
    v2 = _TRIG_FN[p["func2"]](sympy.pi * p["angle2"] / 180)
    op = p["op"]
    if op == "+":
        result = v1 + v2
    elif op == "-":
        result = v1 - v2
    elif op == "*":
        result = v1 * v2
    else:
        result = v1 / v2
    result = sympy.simplify(result)

    label = f"{p['func1']}{p['angle1']}° {op} {p['func2']}{p['angle2']}°"
    if result == 0:
        reasons.append(
            f"{label} = 0: a trivially-zero result, not a genuine exact-form evaluation"
        )
        return reasons
    if not _nice_surd(result):
        reasons.append(
            f"{label} = {result} carries a surd beyond √2/√3 (e.g. √6): out of Gr10 "
            "exact-form scope"
        )
    return reasons


def rform_solve_in_scope(instance: ProblemInstance) -> list[str]:
    """Presented: R·sin(x − φ) = k with R = √(a² + b²), asked for the two solutions in
    [0°, 360°]. Those exist only when |k| < R (arcsin(k/R) is defined and the line k
    cuts the wave twice). Re-derive R from the shown a, b and flag k ≥ R, where the
    equation has at most one solution — the 'two solutions' ask is wrong."""
    p = instance.params
    a, b, k = p["a"], p["b"], p["k"]
    reasons: list[str] = []
    r_squared = a**2 + b**2
    if k**2 >= r_squared:
        reasons.append(
            f"k={k} ≥ R=√{r_squared}: |k| ≥ amplitude, R·sin(x−φ)=k has no two "
            "solutions in [0°,360°]"
        )
    return reasons


def trig_graph_solve_in_scope(instance: ProblemInstance) -> list[str]:
    """Presented: a·sin(nx) − b·cos(nx) = k on [0°, 360°/n], asked for the two
    solutions. Written as R·sin(nx − φ) = k with R = √(a² + b²), solutions exist only
    when |k| < R. Re-derive R from the shown a, b and flag k ≥ R, where the line k does
    not cut the wave twice and the 'two solutions' ask is wrong."""
    p = instance.params
    a, b, k = p["a"], p["b"], p["k"]
    reasons: list[str] = []
    r_squared = a**2 + b**2
    if k**2 >= r_squared:
        reasons.append(
            f"k={k} ≥ R=√{r_squared}: |k| ≥ amplitude, a·sin(nx)−b·cos(nx)=k has no "
            "two solutions in the shown domain"
        )
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


# ── quadratics family (ladder 2) ─────────────────────────────────────────────────
#
# Each predicate re-solves the *presented* problem via the discriminant, independent of
# the generator's (usually backward) construction, and cross-checks the stored
# set/categorical answer against that independent re-derivation. The leak these guard is
# a draw whose roots are irrational / non-integer / out-of-band, or whose stored
# categorical answer (region, nature, valid-set) disagrees with the shown coefficients.

_QUAD_INEQ_ROOT_BOUND = 8  # quadratic_inequality draws distinct roots in [−8, 8]
_QUAD_AB_COEFF = 2  # quadratic_inequality / discriminant_nature draw a in {±1, ±2}
_SURD_ROOT_BOUND = 6  # surd_equation draws candidate roots p, q in [−6, 6]
_NLS_X_BOUND = 5  # nonlinear_simultaneous draws intersection x-values in [−5, 5]


def _integer_roots(a: int, b: int, c: int) -> tuple[list[int], str | None]:
    """Solve ax²+bx+c=0 over the integers. Return (roots, reason-if-not-clean).

    ``reason`` is None when the roots are two real integers; otherwise it names why
    they are out of the archetype's scope (complex, irrational, non-integer)."""
    disc = b * b - 4 * a * c
    if disc < 0:
        return [], f"discriminant {disc} < 0: non-real roots"
    root = math.isqrt(disc)
    if root * root != disc:
        return [], f"discriminant {disc} is not a perfect square: irrational roots"
    if (-b + root) % (2 * a) != 0 or (-b - root) % (2 * a) != 0:
        return [], f"(-b ± √Δ)/2a is non-integer for a={a}, b={b}, c={c}"
    return [(-b + root) // (2 * a), (-b - root) // (2 * a)], None


def quadratic_inequality_in_scope(instance: ProblemInstance) -> list[str]:
    """Presented: ax²+bx+c ⧠ 0. Re-derive the two critical values and the sign-analysis
    region from a, b, c and the direction, independent of construction."""
    p = instance.params
    a, b, c = p["a"], p["b"], p["c"]
    reasons: list[str] = []
    if abs(a) > _QUAD_AB_COEFF or a == 0:
        reasons.append(f"a={a} outside {{±1, ±2}}")
    roots, bad = _integer_roots(a, b, c)
    if bad:
        reasons.append(bad)
        return reasons
    r1, r2 = roots
    if r1 == r2:
        reasons.append("double root: this archetype teaches two distinct roots")
    for r in roots:
        if abs(r) > _QUAD_INEQ_ROOT_BOUND:
            reasons.append(f"critical value {r} exceeds band {_QUAD_INEQ_ROOT_BOUND}")
    # Independent sign analysis: positive OUTSIDE the roots iff the parabola opens up.
    wants_positive = p["direction"] in (">", ">=")
    expected = "outside" if (wants_positive == (a > 0)) else "between"
    if p["region"] != expected:
        reasons.append(
            f"stored region '{p['region']}' ≠ sign-analysis result '{expected}'"
        )
    return reasons


def discriminant_nature_in_scope(instance: ProblemInstance) -> list[str]:
    """Presented: ax²+bx+c=0. Recompute Δ and reclassify the nature from a, b, c, then
    confirm the stored discriminant value and nature label match."""
    p = instance.params
    a, b, c = p["a"], p["b"], p["c"]
    reasons: list[str] = []
    if abs(a) > _QUAD_AB_COEFF or a == 0:
        reasons.append(f"a={a} outside {{±1, ±2}}")
    disc = b * b - 4 * a * c
    if disc != p["discriminant"]:
        reasons.append(f"stored Δ={p['discriminant']} ≠ b²−4ac={disc}")
    if disc < 0:
        nature = "non_real"
    elif disc == 0:
        nature = "real_equal"
    else:
        root = math.isqrt(disc)
        nature = (
            "real_unequal_rational"
            if root * root == disc
            else "real_unequal_irrational"
        )
    if p["nature"] != nature:
        reasons.append(f"stored nature '{p['nature']}' ≠ Δ-classification '{nature}'")
    return reasons


def surd_equation_in_scope(instance: ProblemInstance) -> list[str]:
    """Presented: √(ax+b) = sx+c. Re-derive the squared quadratic x²+(2sc−a)x+(c²−b)=0,
    solve for the candidate roots, and independently reject where sx+c < 0. Cross-check
    the stored candidate and valid sets."""
    p = instance.params
    a, b, c, s = p["a"], p["b"], p["c"], p["s"]
    reasons: list[str] = []
    if a == 0:
        reasons.append("a = 0: √(constant) = line is degenerate, not a surd equation")
        return reasons
    roots, bad = _integer_roots(1, 2 * s * c - a, c * c - b)
    if bad:
        reasons.append(bad.replace("roots", "candidate roots"))
        return reasons
    cands = frozenset(roots)
    if len(cands) < 2:
        reasons.append("candidate roots are not distinct")
    for t in cands:
        if abs(t) > _SURD_ROOT_BOUND:
            reasons.append(f"candidate root {t} exceeds band {_SURD_ROOT_BOUND}")
    valid = frozenset({t for t in cands if s * t + c >= 0})
    if not valid:
        reasons.append("no candidate survives the sx+c ≥ 0 check: empty solution set")
    if cands != p["candidate_roots"]:
        reasons.append(f"stored candidates {set(p['candidate_roots'])} ≠ {set(cands)}")
    if valid != p["valid_roots"]:
        reasons.append(f"stored valid {set(p['valid_roots'])} ≠ {set(valid)}")
    return reasons


def nonlinear_simultaneous_in_scope(instance: ProblemInstance) -> list[str]:
    """Presented: y=mx+k and y=x²+px+q. Equate to x²+(p−m)x+(q−k)=0, re-solve for the
    intersection x-values, back-substitute into the line for y, and cross-check the
    stored x-values and (x, y) pairs."""
    p = instance.params
    m, k, pp, qq = p["m"], p["k"], p["p"], p["q"]
    reasons: list[str] = []
    if m == 0:
        reasons.append("m = 0: a horizontal line hides the pairing skill")
    roots, bad = _integer_roots(1, pp - m, qq - k)
    if bad:
        reasons.append(bad.replace("roots", "intersection x-values"))
        return reasons
    xs = frozenset(roots)
    if len(xs) < 2:
        reasons.append("line is tangent (one intersection): not the two-pair scope")
    for x in xs:
        if abs(x) > _NLS_X_BOUND:
            reasons.append(f"intersection x={x} exceeds band {_NLS_X_BOUND}")
    pairs = frozenset({(x, m * x + k) for x in xs})
    if xs != p["x_values"]:
        reasons.append(f"stored x-values {set(p['x_values'])} ≠ {set(xs)}")
    if pairs != p["solution_pairs"]:
        reasons.append(f"stored pairs {set(p['solution_pairs'])} ≠ {set(pairs)}")
    return reasons


# ── exponents & surds family (ladder 10) ─────────────────────────────────────────
#
# Of the three archetypes only exponential_equation carries F1 surface. The two
# "simplify" drills are forward reductions: the rejection loops size the answer into an
# exam band (cosmetic, per the no-cosmetic-range rule) and pick a clean coefficient — no
# draw makes "simplify this expression" ill-posed, and symbolic_equality grades whatever
# the reduction yields. exponential_equation is the value-plus-reason / subset-guard
# shape (the exponential twin of surd_equation): the assessed skill is the u > 0
# rejection and the log_k back-substitution, so a leak is a stored valid-set that keeps
# a non-positive u, or an x-root that isn't log_k of a kept power. Re-derive all three
# sets from the presented base and coefficients.


def exponential_equation_in_scope(instance: ProblemInstance) -> list[str]:
    """Presented: k^(2x) + b·k^x + c = 0. Substitute u = k^x → u² + b·u + c = 0.
    Re-solve for the candidate u-roots from the shown b, c; independently reject u ≤ 0
    (k^x > 0 for all real x); and back-substitute x = log_k(u), which must be a clean
    non-negative integer (u a power of k). Cross-check the stored candidate / valid /
    x-root sets."""
    p = instance.params
    k, b, c = p["base"], p["b_coef"], p["c_coef"]
    reasons: list[str] = []
    roots, bad = _integer_roots(1, b, c)
    if bad:
        reasons.append(bad.replace("roots", "candidate u-values"))
        return reasons
    cands = frozenset(roots)
    if len(cands) < 2:
        reasons.append("candidate u-values are not distinct")
    valid = frozenset({u for u in cands if u > 0})
    if not valid:
        reasons.append(
            "no candidate u is positive: k^x > 0 leaves an empty solution set"
        )
    x_roots: set[int] = set()
    for u in valid:
        m, v = 0, 1
        while v < u:
            v *= k
            m += 1
        if v != u:
            reasons.append(
                f"valid u={u} is not a power of {k}: x = log_{k}(u) non-integer"
            )
        else:
            x_roots.add(m)
    if cands != p["candidate_u"]:
        reasons.append(f"stored candidates {set(p['candidate_u'])} ≠ {set(cands)}")
    if valid != p["valid_u"]:
        reasons.append(f"stored valid {set(p['valid_u'])} ≠ {set(valid)}")
    if frozenset(x_roots) != p["x_roots"]:
        reasons.append(f"stored x-roots {set(p['x_roots'])} ≠ {x_roots}")
    return reasons


# problem_id → its Problem object (drives the sweep registry)
PROBLEMS = {
    monic_factorise.id: monic_factorise,
    quadratic_factor.id: quadratic_factor,
    nth_term_formula.id: nth_term_formula,
    quad_seq_find_n.id: quad_seq_find_n,
    arith_seq_find_n.id: arith_seq_find_n,
    arith_seq_find_missing.id: arith_seq_find_missing,
    arith_seq_from_two_terms.id: arith_seq_from_two_terms,
    geo_seq_find_n.id: geo_seq_find_n,
    geo_seq_find_missing.id: geo_seq_find_missing,
    geo_seq_from_two_terms.id: geo_seq_from_two_terms,
    arith_series_find_n.id: arith_series_find_n,
    prob_venn_intersection.id: prob_venn_intersection,
    prob_count_intersection.id: prob_count_intersection,
    grouped_mean_solve.id: grouped_mean_solve,
    line_equation.id: line_equation,
    circle_equation.id: circle_equation,
    circle_tangent.id: circle_tangent,
    cubic_stationary_points.id: cubic_stationary_points,
    motion_calculus.id: motion_calculus,
    optimisation_solve.id: optimisation_solve,
    trig_special_angles.id: trig_special_angles,
    rform_solve.id: rform_solve,
    trig_graph_solve.id: trig_graph_solve,
    linear_add_pos.id: linear_add_pos,
    linear_expand.id: linear_expand,
    linear_literal.id: linear_literal,
    linear_rational.id: linear_rational,
    linear_double_inequality.id: linear_double_inequality,
    simultaneous_2x2.id: simultaneous_2x2,
    quadratic_inequality.id: quadratic_inequality,
    discriminant_nature.id: discriminant_nature,
    surd_equation.id: surd_equation,
    nonlinear_simultaneous.id: nonlinear_simultaneous,
    exponential_equation.id: exponential_equation,
}

# problem_id → its in-scope predicate
PREDICATES = {
    monic_factorise.id: monic_factorise_in_scope,
    quadratic_factor.id: quadratic_factor_in_scope,
    nth_term_formula.id: arith_nth_term_in_scope,
    quad_seq_find_n.id: quad_seq_find_n_in_scope,
    arith_seq_find_n.id: arith_find_n_in_scope,
    arith_seq_find_missing.id: arith_find_missing_in_scope,
    arith_seq_from_two_terms.id: arith_from_two_terms_in_scope,
    geo_seq_find_n.id: geo_find_n_in_scope,
    geo_seq_find_missing.id: geo_find_missing_in_scope,
    geo_seq_from_two_terms.id: geo_from_two_terms_in_scope,
    arith_series_find_n.id: arith_series_find_n_in_scope,
    prob_venn_intersection.id: prob_venn_intersection_in_scope,
    prob_count_intersection.id: prob_count_intersection_in_scope,
    grouped_mean_solve.id: grouped_mean_solve_in_scope,
    line_equation.id: line_equation_in_scope,
    circle_equation.id: circle_equation_in_scope,
    circle_tangent.id: circle_tangent_in_scope,
    cubic_stationary_points.id: cubic_stationary_points_in_scope,
    motion_calculus.id: motion_calculus_in_scope,
    optimisation_solve.id: optimisation_solve_in_scope,
    trig_special_angles.id: trig_special_angles_in_scope,
    rform_solve.id: rform_solve_in_scope,
    trig_graph_solve.id: trig_graph_solve_in_scope,
    linear_add_pos.id: linear_add_pos_in_scope,
    linear_expand.id: linear_expand_in_scope,
    linear_literal.id: linear_literal_in_scope,
    linear_rational.id: linear_rational_in_scope,
    linear_double_inequality.id: linear_double_inequality_in_scope,
    simultaneous_2x2.id: simultaneous_2x2_in_scope,
    quadratic_inequality.id: quadratic_inequality_in_scope,
    discriminant_nature.id: discriminant_nature_in_scope,
    surd_equation.id: surd_equation_in_scope,
    nonlinear_simultaneous.id: nonlinear_simultaneous_in_scope,
    exponential_equation.id: exponential_equation_in_scope,
}
