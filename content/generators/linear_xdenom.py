"""
Generator for a/x = b problems (x in the denominator).

Produces FourStep instances for SheetData.
Steps: equation → ×x on both sides → intermediate a=bx → result.
"""

from __future__ import annotations

from fractions import Fraction
from random import Random

from content.generators import Kind
from content.sheet import CollapsedEx, FourStep, PracticeEx, SheetData

_SMALL_DENOMS = (2, 3, 4, 6)
_VAR_POOL = tuple("abcdfghkmnpqrstu")

_TITLE = "a / x = b  —  Multiply Both Sides by x"
_CAPTION = (
    "In the previous sheet you multiplied both sides by p, r, m — x follows the same rule. "
    "Multiplying by x clears it from the denominator, leaving a = bx. "
    "You then solve that as before: divide both sides by b."
)

_DETAILED_SHARE = {
    Kind.INTEGER: 4,
    Kind.FRACTION: 2,
    Kind.SYMBOL: 2,
}  # total 8; but max 6 for FourStep
_KIND_ORDER = (Kind.INTEGER, Kind.FRACTION, Kind.SYMBOL)


def _fmt(f: Fraction) -> str:
    if f.denominator == 1:
        return str(f.numerator)
    sign = "-" if f < 0 else ""
    return rf"{sign}\tfrac{{{abs(f.numerator)}}}{{{f.denominator}}}"


def _fmt_bx_int(b: int) -> str:
    """Format b*x for the intermediate step (integer b)."""
    return "x" if b == 1 else rf"{b}x"


def _fmt_bx_frac(b: Fraction) -> str:
    """Format b*x for the intermediate step (fraction b)."""
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
    # Pick b = Fraction(p, d) reduced; set a = b.numerator * k so x = a/b = k*b.denominator (integer).
    d = rng.choice(_SMALL_DENOMS)
    p = rng.randint(1, d - 1)
    b = Fraction(p, d)
    k = rng.randint(1, 4)
    a = b.numerator * k
    x = Fraction(a) / b  # = k * b.denominator (integer)
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


def gen_fourstep(kind: Kind, rng: Random) -> FourStep:
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

    # FourStep layout fits at most 6 detailed entries.
    n_detailed = 6
    if set(active) == set(Kind):
        shares = {Kind.INTEGER: 2, Kind.FRACTION: 2, Kind.SYMBOL: 2}
    else:
        base, extra = divmod(n_detailed, len(active))
        shares = {k: base + (1 if i < extra else 0) for i, k in enumerate(active)}
    detailed: list[FourStep] = [
        gen_fourstep(kind, rng) for kind in active for _ in range(shares[kind])
    ]

    collapsed: list[CollapsedEx] = []
    for i in range(12):
        step = gen_fourstep(active[i % len(active)], rng)
        collapsed.append(CollapsedEx(step.equation, step.result))

    practice: list[PracticeEx] = []
    for i in range(16):
        step = gen_fourstep(active[i % len(active)], rng)
        practice.append(PracticeEx(step.equation, step.result if i % 2 == 0 else None))

    return SheetData(
        title=_TITLE,
        caption=_CAPTION,
        output_name="linear_xdenom.html",
        detailed=detailed,
        collapsed=collapsed,
        practice=practice,
    )
