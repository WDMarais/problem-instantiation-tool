"""
Generator for x ± a = 0 problems (zero RHS, balance method).

Produces ThreeStep instances for SheetData.
"""

from __future__ import annotations

from fractions import Fraction
from random import Random

from content.generators import Kind
from content.sheet import CollapsedEx, PracticeEx, SheetData, ThreeStep

_SMALL_DENOMS = (2, 3, 4, 6)
_VAR_POOL = tuple("abcdfghkmnpqrstu")

_TITLE = "x ± a = 0  —  Balance Method"
_CAPTION = (
    "Principle: we add or subtract the same value on both sides to keep the "
    "equation balanced."
)

_DETAILED_SHARE = {Kind.INTEGER: 4, Kind.FRACTION: 2, Kind.SYMBOL: 2}
_KIND_ORDER = (Kind.INTEGER, Kind.FRACTION, Kind.SYMBOL)


def _fmt(f: Fraction) -> str:
    if f.denominator == 1:
        return str(f.numerator)
    sign = "-" if f < 0 else ""
    return rf"{sign}\tfrac{{{abs(f.numerator)}}}{{{f.denominator}}}"


def _gen_integer(rng: Random) -> ThreeStep:
    plus = rng.choice([True, False])
    a = rng.randint(1, 12)
    x = -a if plus else a
    if plus:
        return ThreeStep(
            rf"x + {a} = 0",
            rf"x + {a} - {a} = 0 - {a}",
            rf"x = {x}",
        )
    return ThreeStep(
        rf"x - {a} = 0",
        rf"x - {a} + {a} = 0 + {a}",
        rf"x = {x}",
    )


def _gen_fraction(rng: Random) -> ThreeStep:
    plus = rng.choice([True, False])
    d = rng.choice(_SMALL_DENOMS)
    a = Fraction(rng.randint(1, d - 1), d)
    x = -a if plus else a
    fa = _fmt(a)
    if plus:
        return ThreeStep(
            rf"x + {fa} = 0",
            rf"x + {fa} - {fa} = 0 - {fa}",
            rf"x = {_fmt(x)}",
        )
    return ThreeStep(
        rf"x - {fa} = 0",
        rf"x - {fa} + {fa} = 0 + {fa}",
        rf"x = {_fmt(x)}",
    )


def _gen_symbol(rng: Random) -> ThreeStep:
    plus = rng.choice([True, False])
    (v,) = rng.sample(_VAR_POOL, 1)
    if plus:
        return ThreeStep(
            rf"x + {v} = 0",
            rf"x + {v} - {v} = 0 - {v}",
            rf"x = -{v}",
        )
    return ThreeStep(
        rf"x - {v} = 0",
        rf"x - {v} + {v} = 0 + {v}",
        rf"x = {v}",
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
        output_name="linear_balance.html",
        detailed=detailed,
        collapsed=collapsed,
        practice=practice,
    )
