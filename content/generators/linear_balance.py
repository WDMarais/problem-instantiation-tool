"""Generator for x ± a = 0 problems (zero RHS, balance method)."""

from __future__ import annotations

from fractions import Fraction
from random import Random

from content.generators import Kind
from content.generators.base import LinearGenerator, _SMALL_DENOMS, _VAR_POOL, _fmt
from content.sheet import ThreeStep


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


class BalanceGenerator(LinearGenerator):
    title = "x ± a = 0  —  Balance Method"
    caption = (
        "Principle: we add or subtract the same value on both sides to keep the "
        "equation balanced."
    )
    output_name = "linear_balance.html"
    detailed_share = {Kind.INTEGER: 4, Kind.FRACTION: 2, Kind.SYMBOL: 2}

    def gen(self, kind: Kind, rng: Random) -> ThreeStep:
        if kind is Kind.INTEGER:
            return _gen_integer(rng)
        if kind is Kind.FRACTION:
            return _gen_fraction(rng)
        return _gen_symbol(rng)


_GEN = BalanceGenerator()
make_sheet = _GEN.make_sheet
gen_threestep = _GEN.gen
