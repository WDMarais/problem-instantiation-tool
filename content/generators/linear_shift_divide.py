"""Generator for ax ± b = 0 problems (shift b, then divide by a)."""

from __future__ import annotations

from fractions import Fraction
from random import Random

from content.generators import Kind
from content.generators.base import _SMALL_DENOMS, _VAR_POOL, LinearGenerator, _fmt
from content.sheet import FiveStep


def _gen_integer(rng: Random) -> FiveStep:
    a = rng.randint(2, 10)
    x = rng.choice([*range(-8, 0), *range(1, 9)])
    b = -(a * x)  # ax + b = 0
    if b > 0:
        return FiveStep(
            rf"{a}x + {b} = 0",
            rf"{a}x + {b} - {b} = 0 - {b}",
            rf"{a}x = -{b}",
            rf"{a}x \div {a} = -{b} \div {a}",
            rf"x = {_fmt(Fraction(-b, a))}",
        )
    else:
        ab = -b
        return FiveStep(
            rf"{a}x - {ab} = 0",
            rf"{a}x - {ab} + {ab} = 0 + {ab}",
            rf"{a}x = {ab}",
            rf"{a}x \div {a} = {ab} \div {a}",
            rf"x = {_fmt(Fraction(ab, a))}",
        )


def _gen_fraction(rng: Random) -> FiveStep:
    a = rng.randint(2, 6)
    d = rng.choice(_SMALL_DENOMS)
    x_num = rng.choice([*range(-(d - 1), 0), *range(1, d)])
    x = Fraction(x_num, d)
    b = -Fraction(a) * x
    if b > 0:
        fb = _fmt(b)
        return FiveStep(
            rf"{a}x + {fb} = 0",
            rf"{a}x + {fb} - {fb} = 0 - {fb}",
            rf"{a}x = -{fb}",
            rf"{a}x \div {a} = -{fb} \div {a}",
            rf"x = {_fmt(x)}",
        )
    else:
        fnegb = _fmt(-b)
        return FiveStep(
            rf"{a}x - {fnegb} = 0",
            rf"{a}x - {fnegb} + {fnegb} = 0 + {fnegb}",
            rf"{a}x = {fnegb}",
            rf"{a}x \div {a} = {fnegb} \div {a}",
            rf"x = {_fmt(x)}",
        )


def _gen_symbol(rng: Random) -> FiveStep:
    v1, v2 = rng.sample(_VAR_POOL, 2)
    return FiveStep(
        rf"{v1}x + {v2} = 0",
        rf"{v1}x + {v2} - {v2} = 0 - {v2}",
        rf"{v1}x = -{v2}",
        rf"{v1}x \div {v1} = -{v2} \div {v1}",
        rf"x = -\tfrac{{{v2}}}{{{v1}}}",
    )


class ShiftDivideGenerator(LinearGenerator):
    title = "ax ± b = 0  —  Shift, then Divide"
    caption = (
        "Two operations in sequence: first undo the addition or subtraction "
        "(same move as before — add or subtract on both sides), "
        "then undo the multiplication by dividing both sides by a."
    )
    output_name = "linear_shift_divide.html"
    n_detailed = 4
    detailed_share = {Kind.INTEGER: 2, Kind.FRACTION: 1, Kind.SYMBOL: 1}

    def gen(self, kind: Kind, rng: Random) -> FiveStep:
        if kind is Kind.INTEGER:
            return _gen_integer(rng)
        if kind is Kind.FRACTION:
            return _gen_fraction(rng)
        return _gen_symbol(rng)


_GEN = ShiftDivideGenerator()
make_sheet = _GEN.make_sheet
gen_fivestep = _GEN.gen
