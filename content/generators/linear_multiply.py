"""
Generator for x/a = b problems (multiply both sides).

Produces ThreeStep instances for SheetData.
"""

from __future__ import annotations

from fractions import Fraction
from random import Random

from content.generators import Kind
from content.sheet import CollapsedEx, PracticeEx, SheetData, ThreeStep

_SMALL_DENOMS = (2, 3, 4, 6)
_VAR_POOL = tuple("abcdfghkmnpqrstu")

_TITLE = "x / a = b  —  Multiply Both Sides"
_CAPTION = (
    "Principle: multiply both sides by the same value to keep the equation balanced. "
    "Here we multiply by the denominator under x to leave x on its own."
)

_DETAILED_SHARE = {Kind.INTEGER: 4, Kind.FRACTION: 2, Kind.SYMBOL: 2}
_KIND_ORDER = (Kind.INTEGER, Kind.FRACTION, Kind.SYMBOL)


def _fmt(f: Fraction) -> str:
    if f.denominator == 1:
        return str(f.numerator)
    sign = "-" if f < 0 else ""
    return rf"{sign}\tfrac{{{abs(f.numerator)}}}{{{f.denominator}}}"


def _gen_integer(rng: Random) -> ThreeStep:
    a = rng.randint(2, 10)
    b = rng.choice([*range(-4, 0), *range(1, 13)])  # non-zero, mostly positive
    x = a * b
    return ThreeStep(
        rf"\tfrac{{x}}{{{a}}} = {b}",
        rf"\tfrac{{x}}{{{a}}} \times {a} = {b} \times {a}",
        rf"x = {x}",
    )


def _gen_fraction(rng: Random) -> ThreeStep:
    a = rng.randint(2, 6)
    d = rng.choice(_SMALL_DENOMS)
    b = Fraction(rng.randint(1, d - 1), d)  # positive fraction
    x = Fraction(a) * b
    fb = _fmt(b)
    return ThreeStep(
        rf"\tfrac{{x}}{{{a}}} = {fb}",
        rf"\tfrac{{x}}{{{a}}} \times {a} = {fb} \times {a}",
        rf"x = {_fmt(x)}",
    )


def _gen_symbol(rng: Random) -> ThreeStep:
    v1, v2 = rng.sample(_VAR_POOL, 2)
    return ThreeStep(
        rf"\tfrac{{x}}{{{v1}}} = {v2}",
        rf"\tfrac{{x}}{{{v1}}} \times {v1} = {v2} \times {v1}",
        rf"x = {v1}{v2}",
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

    if set(active) == set(Kind):
        shares = _DETAILED_SHARE
    else:
        base, extra = divmod(8, len(active))
        shares = {k: base + (1 if i < extra else 0) for i, k in enumerate(active)}
    detailed: list[ThreeStep] = [
        gen_threestep(kind, rng) for kind in active for _ in range(shares[kind])
    ]

    collapsed: list[CollapsedEx] = []
    for i in range(12):
        step = gen_threestep(active[i % len(active)], rng)
        collapsed.append(CollapsedEx(step.equation, step.result))

    practice: list[PracticeEx] = []
    for i in range(16):
        step = gen_threestep(active[i % len(active)], rng)
        practice.append(PracticeEx(step.equation, step.result if i % 2 == 0 else None))

    return SheetData(
        title=_TITLE,
        caption=_CAPTION,
        output_name="linear_multiply.html",
        detailed=detailed,
        collapsed=collapsed,
        practice=practice,
    )
