"""Generator for ax + b = cx + d problems (collect x terms, shift, divide)."""

from __future__ import annotations

from fractions import Fraction
from random import Random

from content.generators import Kind
from content.generators.base import LinearGenerator, _SMALL_DENOMS, _VAR_POOL, _fmt
from content.sheet import SixStep


def _coefx(coef: int) -> str:
    return "x" if coef == 1 else rf"{coef}x"


def _eqside(coef: int, const: int) -> str:
    """Format coef*x + const with correct sign, handling coef=1."""
    cx = _coefx(coef)
    if const > 0:
        return rf"{cx} + {const}"
    if const < 0:
        return rf"{cx} - {-const}"
    return cx


def _gen_integer(rng: Random) -> SixStep:
    c = rng.randint(1, 5)
    a = c + rng.randint(1, 4)  # a > c, so collected coef = a-c is positive
    x = rng.choice([*range(-4, 0), *range(1, 5)])
    b = rng.choice([*range(-4, 0), *range(1, 5)])  # non-zero
    coef = a - c
    d = coef * x + b  # derived so ax + b = cx + d holds
    cx = _coefx(coef)

    cc = _coefx(c)
    eq = f"{_eqside(a, b)} = {_eqside(c, d)}"
    op1 = rf"{_eqside(a, b)} - {cc} = {_eqside(c, d)} - {cc}"
    mid1 = f"{_eqside(coef, b)} = {d}"
    if b > 0:
        op2 = rf"{cx} + {b} - {b} = {d} - {b}"
    else:
        ab = -b
        op2 = rf"{cx} - {ab} + {ab} = {d} + {ab}"
    mid2 = f"{cx} = {d - b}"
    result = rf"x = {_fmt(Fraction(d - b, coef))}"

    return SixStep(eq, op1, mid1, op2, mid2, result)


def _gen_fraction(rng: Random) -> SixStep:
    # x positive so d = coef*x + b > 0 — keeps all constant terms positive.
    c = rng.randint(1, 4)
    a = c + rng.randint(1, 4)
    x = rng.randint(1, 4)
    den = rng.choice(_SMALL_DENOMS)
    b = Fraction(rng.randint(1, den - 1), den)
    coef = a - c
    d = Fraction(coef * x) + b  # positive fraction
    fb = _fmt(b)
    fd = _fmt(d)
    cx = _coefx(coef)

    cc = _coefx(c)
    eq = rf"{a}x + {fb} = {cc} + {fd}"
    op1 = rf"{a}x + {fb} - {cc} = {cc} + {fd} - {cc}"
    mid1 = rf"{_coefx(coef)} + {fb} = {fd}"
    op2 = rf"{cx} + {fb} - {fb} = {fd} - {fb}"
    mid2 = rf"{cx} = {_fmt(d - b)}"  # d - b = coef*x (integer)
    result = rf"x = {_fmt(Fraction(d - b, coef))}"

    return SixStep(eq, op1, mid1, op2, mid2, result)


def _gen_symbol(rng: Random) -> SixStep:
    v1, v2, v3, v4 = rng.sample(_VAR_POOL, 4)
    return SixStep(
        rf"{v1}x + {v3} = {v2}x + {v4}",
        rf"{v1}x + {v3} - {v2}x = {v2}x + {v4} - {v2}x",
        rf"({v1} - {v2})x + {v3} = {v4}",
        rf"({v1} - {v2})x + {v3} - {v3} = {v4} - {v3}",
        rf"({v1} - {v2})x = {v4} - {v3}",
        rf"x = \tfrac{{{v4} - {v3}}}{{{v1} - {v2}}}",
    )


class CollectGenerator(LinearGenerator):
    title = "ax + b = cx + d  —  Collect x Terms"
    caption = (
        "When x appears on both sides, subtract the smaller x term from both sides first. "
        "This gives a form you already know: shift the constant, then divide."
    )
    output_name = "linear_collect.html"
    n_detailed = 4
    detailed_share = {Kind.INTEGER: 2, Kind.FRACTION: 1, Kind.SYMBOL: 1}

    def gen(self, kind: Kind, rng: Random) -> SixStep:
        if kind is Kind.INTEGER:
            return _gen_integer(rng)
        if kind is Kind.FRACTION:
            return _gen_fraction(rng)
        return _gen_symbol(rng)


_GEN = CollectGenerator()
make_sheet = _GEN.make_sheet
gen_sixstep = _GEN.gen
