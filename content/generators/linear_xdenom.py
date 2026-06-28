"""Generator for a/x = b problems (x in the denominator)."""

from __future__ import annotations

from fractions import Fraction
from random import Random

from content.generators import Kind
from content.generators.base import _SMALL_DENOMS, _VAR_POOL, LinearGenerator, _fmt
from content.sheet import FourStep


def _fmt_bx_int(b: int) -> str:
    return "x" if b == 1 else rf"{b}x"


def _fmt_bx_frac(b: Fraction) -> str:
    n, d = b.numerator, b.denominator
    if n == 1:
        return rf"\tfrac{{x}}{{{d}}}"
    return rf"\tfrac{{{n}x}}{{{d}}}"


def _gen_integer(rng: Random) -> FourStep:
    a = rng.randint(2, 12)
    b = rng.randint(1, 8)
    x = Fraction(a, b)
    return FourStep(
        rf"\tfrac{{{a}}}{{x}} = {b}",
        rf"\tfrac{{{a}}}{{x}} \times x = {b} \times x",
        rf"{a} = {_fmt_bx_int(b)}",
        rf"x = {_fmt(x)}",
    )


def _gen_fraction(rng: Random) -> FourStep:
    # a = b.numerator * k ensures x = a/b = k * b.denominator
    # (integer, no LCD surprises).
    d = rng.choice(_SMALL_DENOMS)
    p = rng.randint(1, d - 1)
    b = Fraction(p, d)
    k = rng.randint(1, 4)
    a = b.numerator * k
    x = Fraction(a) / b
    fb = _fmt(b)
    return FourStep(
        rf"\tfrac{{{a}}}{{x}} = {fb}",
        rf"\tfrac{{{a}}}{{x}} \times x = {fb} \times x",
        rf"{a} = {_fmt_bx_frac(b)}",
        rf"x = {_fmt(x)}",
    )


def _gen_symbol(rng: Random) -> FourStep:
    v1, v2 = rng.sample(_VAR_POOL, 2)
    return FourStep(
        rf"\tfrac{{{v1}}}{{x}} = {v2}",
        rf"\tfrac{{{v1}}}{{x}} \times x = {v2} \times x",
        rf"{v1} = {v2}x",
        rf"x = \tfrac{{{v1}}}{{{v2}}}",
    )


class XDenomGenerator(LinearGenerator):
    title = "a / x = b  —  Multiply Both Sides by x"
    caption = (
        "In the previous sheet you multiplied both sides by p, r, m — "
        "x follows the same rule. "
        "Multiplying by x clears it from the denominator, leaving a = bx. "
        "You then solve that as before: divide both sides by b."
    )
    output_name = "linear_xdenom.html"
    n_detailed = 6
    detailed_share = {Kind.INTEGER: 2, Kind.FRACTION: 2, Kind.SYMBOL: 2}

    def gen(self, kind: Kind, rng: Random) -> FourStep:
        if kind is Kind.INTEGER:
            return _gen_integer(rng)
        if kind is Kind.FRACTION:
            return _gen_fraction(rng)
        return _gen_symbol(rng)


_GEN = XDenomGenerator()
make_sheet = _GEN.make_sheet
gen_fourstep = _GEN.gen
