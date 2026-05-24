"""Generator for x ± a = b problems (non-zero RHS)."""

from __future__ import annotations

from fractions import Fraction
from random import Random

from content.generators import Kind
from content.generators.base import LinearGenerator, _SMALL_DENOMS, _VAR_POOL, _fmt
from content.sheet import ThreeStep


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
    # Both a and x share denominator d so b = x ± a has denominator dividing d.
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


class ShiftGenerator(LinearGenerator):
    title = "x ± a = b  —  Non-Zero Right-Hand Side"
    caption = (
        "The 3 does not simply disappear from the left and reappear as $-3$ on the right. "
        "You subtract 3 from both sides: on the left it cancels to zero; "
        "on the right, 7 becomes $7 - 3 = 4$. "
        "The right-hand side is always affected too."
    )
    output_name = "linear_shift.html"
    detailed_share = {Kind.INTEGER: 4, Kind.FRACTION: 2, Kind.SYMBOL: 2}

    def gen(self, kind: Kind, rng: Random) -> ThreeStep:
        if kind is Kind.INTEGER:
            return _gen_integer(rng)
        if kind is Kind.FRACTION:
            return _gen_fraction(rng)
        return _gen_symbol(rng)


_GEN = ShiftGenerator()
make_sheet = _GEN.make_sheet
gen_threestep = _GEN.gen
