"""
Generator for x ± a = b problems (non-zero RHS).

Produces ThreeStep / CollapsedEx / PracticeEx instances for SheetData.
Three problem kinds: INTEGER, FRACTION, SYMBOL (any subset via make_sheet).
"""

from __future__ import annotations

from fractions import Fraction
from random import Random

from content.generators import Kind
from content.sheet import CollapsedEx, PracticeEx, SheetData, ThreeStep

_SMALL_DENOMS = (2, 3, 4, 6)

# Excludes x (the unknown), and e i l o (look like numbers/operators).
_VAR_POOL = tuple("abcdfghkmnpqrstu")

_TITLE = "x ± a = b  —  Non-Zero Right-Hand Side"
_CAPTION = (
    "The 3 does not simply disappear from the left and reappear as $-3$ on the right. "
    "You subtract 3 from both sides: on the left it cancels to zero; "
    "on the right, 7 becomes $7 - 3 = 4$. "
    "The right-hand side is always affected too."
)

# Proportion of the 8 detailed slots per kind when all three are active.
_DETAILED_SHARE = {Kind.INTEGER: 4, Kind.FRACTION: 2, Kind.SYMBOL: 2}
_KIND_ORDER = (Kind.INTEGER, Kind.FRACTION, Kind.SYMBOL)


def _fmt(f: Fraction) -> str:
    """Format a Fraction as a KaTeX string."""
    if f.denominator == 1:
        return str(f.numerator)
    sign = "-" if f < 0 else ""
    return rf"{sign}\tfrac{{{abs(f.numerator)}}}{{{f.denominator}}}"


def _gen_integer(rng: Random) -> ThreeStep:
    plus = rng.choice([True, False])
    a = rng.randint(1, 12)
    b = rng.randint(-10, 15)
    x = b - a if plus else b + a
    if plus:
        return ThreeStep(
            rf"x + {a} = {b}",
            rf"x + {a} - {a} = {b} - {a}",
            rf"x = {x}",
        )
    return ThreeStep(
        rf"x - {a} = {b}",
        rf"x - {a} + {a} = {b} + {a}",
        rf"x = {x}",
    )


def _gen_fraction(rng: Random) -> ThreeStep:
    plus = rng.choice([True, False])
    d = rng.choice(_SMALL_DENOMS)
    # a is a positive fraction with denominator d; x avoids zero.
    # Both share denominator d so b = x ± a has denominator dividing d — no LCD surprises.
    a = Fraction(rng.randint(1, d - 1), d)
    x_num = rng.randint(-(d - 1), d - 1)
    while x_num == 0:
        x_num = rng.randint(-(d - 1), d - 1)
    x = Fraction(x_num, d)
    b = x + a if plus else x - a
    fa, fb, fx = _fmt(a), _fmt(b), _fmt(x)
    if plus:
        return ThreeStep(
            rf"x + {fa} = {fb}",
            rf"x + {fa} - {fa} = {fb} - {fa}",
            rf"x = {fx}",
        )
    return ThreeStep(
        rf"x - {fa} = {fb}",
        rf"x - {fa} + {fa} = {fb} + {fa}",
        rf"x = {fx}",
    )


def _gen_symbol(rng: Random) -> ThreeStep:
    plus = rng.choice([True, False])
    v1, v2 = rng.sample(_VAR_POOL, 2)
    if plus:
        return ThreeStep(
            rf"x + {v1} = {v2}",
            rf"x + {v1} - {v1} = {v2} - {v1}",
            rf"x = {v2} - {v1}",
        )
    return ThreeStep(
        rf"x - {v1} = {v2}",
        rf"x - {v1} + {v1} = {v2} + {v1}",
        rf"x = {v2} + {v1}",
    )


def gen_threestep(kind: Kind, rng: Random) -> ThreeStep:
    if kind is Kind.INTEGER:
        return _gen_integer(rng)
    if kind is Kind.FRACTION:
        return _gen_fraction(rng)
    return _gen_symbol(rng)


def make_sheet(
    kinds: frozenset[Kind] = frozenset(Kind),
    *,
    seed: int | None = None,
) -> SheetData:
    rng = Random(seed)
    active = [k for k in _KIND_ORDER if k in kinds]

    # Section A: pedagogical order (integers → fractions → symbols).
    # Uses fixed share when all three are active; equal split otherwise.
    if set(active) == set(Kind):
        shares = _DETAILED_SHARE
    else:
        base, extra = divmod(8, len(active))
        shares = {k: base + (1 if i < extra else 0) for i, k in enumerate(active)}
    detailed: list[ThreeStep] = [
        gen_threestep(kind, rng) for kind in active for _ in range(shares[kind])
    ]

    # Section B: interleaved across active kinds (cycles kind order).
    collapsed: list[CollapsedEx] = []
    for i in range(12):
        step = gen_threestep(active[i % len(active)], rng)
        collapsed.append(CollapsedEx(step.equation, step.result))

    # Section C: interleaved; odd-indexed problems are unstarred (no answer printed).
    practice: list[PracticeEx] = []
    for i in range(16):
        step = gen_threestep(active[i % len(active)], rng)
        practice.append(PracticeEx(step.equation, step.result if i % 2 == 0 else None))

    return SheetData(
        title=_TITLE,
        caption=_CAPTION,
        output_name="linear_shift.html",
        detailed=detailed,
        collapsed=collapsed,
        practice=practice,
    )
