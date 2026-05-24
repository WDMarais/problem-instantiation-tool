"""Generator for ax = b problems (divide both sides)."""

from __future__ import annotations

from fractions import Fraction
from random import Random

from content.generators import Kind
from content.generators.base import LinearGenerator, _SMALL_DENOMS, _VAR_POOL, _fmt
from content.sheet import ThreeStep


def _gen_integer(rng: Random) -> ThreeStep:
    a = rng.randint(2, 10)
    b = rng.choice([*range(-10, 0), *range(1, 16)])
    x = Fraction(b, a)
    return ThreeStep(
        rf"{a}x = {b}",
        rf"{a}x \div {a} = {b} \div {a}",
        rf"x = {_fmt(x)}",
    )


def _gen_fraction(rng: Random) -> ThreeStep:
    a = rng.randint(2, 6)
    d = rng.choice(_SMALL_DENOMS)
    b = Fraction(rng.randint(1, d - 1), d)
    x = b / Fraction(a)
    fb = _fmt(b)
    return ThreeStep(
        rf"{a}x = {fb}",
        rf"{a}x \div {a} = {fb} \div {a}",
        rf"x = {_fmt(x)}",
    )


def _gen_symbol(rng: Random) -> ThreeStep:
    v1, v2 = rng.sample(_VAR_POOL, 2)
    return ThreeStep(
        rf"{v1}x = {v2}",
        rf"{v1}x \div {v1} = {v2} \div {v1}",
        rf"x = \tfrac{{{v2}}}{{{v1}}}",
    )


class DivideGenerator(LinearGenerator):
    title = "ax = b  —  Divide Both Sides"
    caption = (
        "Principle: divide both sides by the same value to keep the equation balanced. "
        "Here we divide by the coefficient in front of x to leave x on its own."
    )
    output_name = "linear_divide.html"
    detailed_share = {Kind.INTEGER: 4, Kind.FRACTION: 2, Kind.SYMBOL: 2}

    def gen(self, kind: Kind, rng: Random) -> ThreeStep:
        if kind is Kind.INTEGER:
            return _gen_integer(rng)
        if kind is Kind.FRACTION:
            return _gen_fraction(rng)
        return _gen_symbol(rng)


_GEN = DivideGenerator()
make_sheet = _GEN.make_sheet
gen_threestep = _GEN.gen
