"""Generator for a/x ± b = 0 problems (shift b, multiply by x, divide by b)."""

from __future__ import annotations

from fractions import Fraction
from random import Random

from content.generators import Kind
from content.generators.base import _SMALL_DENOMS, _VAR_POOL, LinearGenerator, _fmt
from content.sheet import SixStep


def _gen_integer(rng: Random) -> SixStep:
    # Pick b and k so that x = -a/b = ±k (integer), a > 0.
    k = rng.randint(1, 4)
    b = rng.choice([*range(-6, 0), *range(1, 7)])
    a = abs(b) * k
    x = Fraction(-a, b)  # = -k if b>0, +k if b<0
    if b > 0:
        return SixStep(
            rf"\tfrac{{{a}}}{{x}} + {b} = 0",
            rf"\tfrac{{{a}}}{{x}} + {b} - {b} = 0 - {b}",
            rf"\tfrac{{{a}}}{{x}} = -{b}",
            rf"\tfrac{{{a}}}{{x}} \times x = -{b} \times x",
            rf"{a} = -{b}x",
            rf"x = {_fmt(x)}",
        )
    else:
        ab = -b
        return SixStep(
            rf"\tfrac{{{a}}}{{x}} - {ab} = 0",
            rf"\tfrac{{{a}}}{{x}} - {ab} + {ab} = 0 + {ab}",
            rf"\tfrac{{{a}}}{{x}} = {ab}",
            rf"\tfrac{{{a}}}{{x}} \times x = {ab} \times x",
            rf"{a} = {ab}x",
            rf"x = {_fmt(x)}",
        )


def _gen_fraction(rng: Random) -> SixStep:
    # b is a positive fraction; a = b.numerator * k ensures
    # x = -k*b.denominator (integer).
    k = rng.randint(1, 4)
    d = rng.choice(_SMALL_DENOMS)
    p = rng.randint(1, d - 1)
    b = Fraction(p, d)
    a = b.numerator * k
    x = Fraction(-a) / b  # = -k * b.denominator (negative integer)
    fb = _fmt(b)
    return SixStep(
        rf"\tfrac{{{a}}}{{x}} + {fb} = 0",
        rf"\tfrac{{{a}}}{{x}} + {fb} - {fb} = 0 - {fb}",
        rf"\tfrac{{{a}}}{{x}} = -{fb}",
        rf"\tfrac{{{a}}}{{x}} \times x = -{fb} \times x",
        rf"{a} = -{fb}x",
        rf"x = {_fmt(x)}",
    )


def _gen_symbol(rng: Random) -> SixStep:
    v1, v2 = rng.sample(_VAR_POOL, 2)
    return SixStep(
        rf"\tfrac{{{v1}}}{{x}} + {v2} = 0",
        rf"\tfrac{{{v1}}}{{x}} + {v2} - {v2} = 0 - {v2}",
        rf"\tfrac{{{v1}}}{{x}} = -{v2}",
        rf"\tfrac{{{v1}}}{{x}} \times x = -{v2} \times x",
        rf"{v1} = -{v2}x",
        rf"x = -\tfrac{{{v1}}}{{{v2}}}",
    )


class ShiftXDenomGenerator(LinearGenerator):
    title = "a/x ± b = 0  —  Shift, Multiply by x, Divide"
    caption = (
        "Three moves in sequence: shift b to the right, "
        "then multiply both sides by x to clear the denominator, "
        "then divide both sides by the remaining coefficient."
    )
    output_name = "linear_shift_xdenom.html"
    n_detailed = 4
    detailed_share = {Kind.INTEGER: 2, Kind.FRACTION: 1, Kind.SYMBOL: 1}

    def gen(self, kind: Kind, rng: Random) -> SixStep:
        if kind is Kind.INTEGER:
            return _gen_integer(rng)
        if kind is Kind.FRACTION:
            return _gen_fraction(rng)
        return _gen_symbol(rng)


_GEN = ShiftXDenomGenerator()
make_sheet = _GEN.make_sheet
gen_sixstep = _GEN.gen
