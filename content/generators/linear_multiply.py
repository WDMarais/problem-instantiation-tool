"""Generator for x/a = b problems (multiply both sides)."""

from __future__ import annotations

from fractions import Fraction
from random import Random

from content.generators import Kind
from content.generators.base import _SMALL_DENOMS, _VAR_POOL, LinearGenerator, _fmt
from content.sheet import ThreeStep


def _gen_integer(rng: Random) -> ThreeStep:
    a = rng.randint(2, 10)
    b = rng.choice([*range(-4, 0), *range(1, 13)])
    x = a * b
    return ThreeStep(
        rf"\tfrac{{x}}{{{a}}} = {b}",
        rf"\tfrac{{x}}{{{a}}} \times {a} = {b} \times {a}",
        rf"x = {x}",
    )


def _gen_fraction(rng: Random) -> ThreeStep:
    a = rng.randint(2, 6)
    d = rng.choice(_SMALL_DENOMS)
    b = Fraction(rng.randint(1, d - 1), d)
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


class MultiplyGenerator(LinearGenerator):
    title = "x / a = b  —  Multiply Both Sides"
    caption = (
        "Principle: multiply both sides by the same value "
        "to keep the equation balanced. "
        "Here we multiply by the denominator under x to leave x on its own."
    )
    output_name = "linear_multiply.html"
    detailed_share = {Kind.INTEGER: 4, Kind.FRACTION: 2, Kind.SYMBOL: 2}

    def gen(self, kind: Kind, rng: Random) -> ThreeStep:
        if kind is Kind.INTEGER:
            return _gen_integer(rng)
        if kind is Kind.FRACTION:
            return _gen_fraction(rng)
        return _gen_symbol(rng)


_GEN = MultiplyGenerator()
make_sheet = _GEN.make_sheet
gen_threestep = _GEN.gen
