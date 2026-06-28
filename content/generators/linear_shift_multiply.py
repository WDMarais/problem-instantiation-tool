"""Generator for x/a ± b = 0 problems (shift b, then multiply by a)."""

from __future__ import annotations

from fractions import Fraction
from random import Random

from content.generators import Kind
from content.generators.base import _SMALL_DENOMS, _VAR_POOL, LinearGenerator, _fmt
from content.sheet import FiveStep


def _gen_integer(rng: Random) -> FiveStep:
    a = rng.randint(2, 10)
    b = rng.choice([*range(-8, 0), *range(1, 9)])
    x = -(a * b)  # x/a + b = 0  →  x = -ab
    if b > 0:
        return FiveStep(
            rf"\tfrac{{x}}{{{a}}} + {b} = 0",
            rf"\tfrac{{x}}{{{a}}} + {b} - {b} = 0 - {b}",
            rf"\tfrac{{x}}{{{a}}} = -{b}",
            rf"\tfrac{{x}}{{{a}}} \times {a} = -{b} \times {a}",
            rf"x = {x}",
        )
    else:
        ab = -b
        return FiveStep(
            rf"\tfrac{{x}}{{{a}}} - {ab} = 0",
            rf"\tfrac{{x}}{{{a}}} - {ab} + {ab} = 0 + {ab}",
            rf"\tfrac{{x}}{{{a}}} = {ab}",
            rf"\tfrac{{x}}{{{a}}} \times {a} = {ab} \times {a}",
            rf"x = {x}",
        )


def _gen_fraction(rng: Random) -> FiveStep:
    a = rng.randint(2, 6)
    d = rng.choice(_SMALL_DENOMS)
    b_num = rng.choice([*range(-(d - 1), 0), *range(1, d)])
    b = Fraction(b_num, d)
    x = -Fraction(a) * b
    if b > 0:
        fb = _fmt(b)
        return FiveStep(
            rf"\tfrac{{x}}{{{a}}} + {fb} = 0",
            rf"\tfrac{{x}}{{{a}}} + {fb} - {fb} = 0 - {fb}",
            rf"\tfrac{{x}}{{{a}}} = -{fb}",
            rf"\tfrac{{x}}{{{a}}} \times {a} = -{fb} \times {a}",
            rf"x = {_fmt(x)}",
        )
    else:
        fnegb = _fmt(-b)
        return FiveStep(
            rf"\tfrac{{x}}{{{a}}} - {fnegb} = 0",
            rf"\tfrac{{x}}{{{a}}} - {fnegb} + {fnegb} = 0 + {fnegb}",
            rf"\tfrac{{x}}{{{a}}} = {fnegb}",
            rf"\tfrac{{x}}{{{a}}} \times {a} = {fnegb} \times {a}",
            rf"x = {_fmt(x)}",
        )


def _gen_symbol(rng: Random) -> FiveStep:
    v1, v2 = rng.sample(_VAR_POOL, 2)
    return FiveStep(
        rf"\tfrac{{x}}{{{v1}}} + {v2} = 0",
        rf"\tfrac{{x}}{{{v1}}} + {v2} - {v2} = 0 - {v2}",
        rf"\tfrac{{x}}{{{v1}}} = -{v2}",
        rf"\tfrac{{x}}{{{v1}}} \times {v1} = -{v2} \times {v1}",
        rf"x = -{v1}{v2}",
    )


class ShiftMultiplyGenerator(LinearGenerator):
    title = "x/a ± b = 0  —  Shift, then Multiply"
    caption = (
        "Two moves you already know, applied in order: "
        "first undo the addition or subtraction (shift b to the right-hand side), "
        "then undo the division by multiplying both sides by a."
    )
    output_name = "linear_shift_multiply.html"
    n_detailed = 4
    detailed_share = {Kind.INTEGER: 2, Kind.FRACTION: 1, Kind.SYMBOL: 1}

    def gen(self, kind: Kind, rng: Random) -> FiveStep:
        if kind is Kind.INTEGER:
            return _gen_integer(rng)
        if kind is Kind.FRACTION:
            return _gen_fraction(rng)
        return _gen_symbol(rng)


_GEN = ShiftMultiplyGenerator()
make_sheet = _GEN.make_sheet
gen_fivestep = _GEN.gen
