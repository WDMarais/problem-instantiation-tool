"""Generator for function evaluation: f(x) = ax + b, evaluate at a given input."""

from __future__ import annotations

from fractions import Fraction
from random import Random

from content.generators import Kind
from content.generators.base import _SMALL_DENOMS, _VAR_POOL, _fmt
from content.sheet import CollapsedEx, FourStep, PracticeEx, SheetData

_FUNC_POOL: tuple[str, ...] = (
    "blorp",
    "zig",
    "gloop",
    "sprock",
    "wibble",
    "plonk",
    "snorf",
    "flarn",
    "quomp",
    "zing",
    "flib",
    "quirk",
)
_KIND_ORDER = (Kind.INTEGER, Kind.FRACTION, Kind.SYMBOL)

_PRACTICE_INTRO = (
    "Evaluate each function. Show your working on a separate sheet and write only your "
    'final answer in the box. Problems marked <span class="star">*</span> have answers '
    "at the bottom."
)


def _fn(name: str) -> str:
    return rf"\text{{{name}}}"


def _fdef(fname: str, a: int, b: int) -> str:
    """Format fname(x) = ax + b."""
    ax = "x" if a == 1 else ("-x" if a == -1 else rf"{a}x")
    if b > 0:
        return rf"{fname}(x) = {ax} + {b}"
    if b < 0:
        return rf"{fname}(x) = {ax} - {-b}"
    return rf"{fname}(x) = {ax}"


def _gen_integer(rng: Random) -> FourStep:
    name = rng.choice(_FUNC_POOL)
    fname = _fn(name)
    a = rng.choice([-5, -4, -3, -2, 2, 3, 4, 5])
    b = rng.choice([*range(-5, 0), *range(1, 6)])
    xval = rng.choice([*range(-5, 0), *range(1, 6)])
    ax_val = a * xval
    result_val = ax_val + b
    # Always wrap input in parens for unambiguous juxtaposition: 3(2), -3(-2)
    x_str = f"({xval})"
    a_part = rf"{a}{x_str}"
    if b > 0:
        op = rf"{fname}({xval}) = {a_part} + {b}"
        mid = rf"= {ax_val} + {b}"
    else:
        ab = -b
        op = rf"{fname}({xval}) = {a_part} - {ab}"
        mid = rf"= {ax_val} - {ab}"
    return FourStep(
        equation=rf"{_fdef(fname, a, b)},\quad {fname}({xval})",
        operation=op,
        intermediate=mid,
        result=rf"{fname}({xval}) = {result_val}",
        model_ref="",
    )


def _gen_fraction(rng: Random) -> FourStep:
    name = rng.choice(_FUNC_POOL)
    fname = _fn(name)
    a = rng.choice([2, 3, 4, 5])
    b = rng.choice([*range(-4, 0), *range(1, 5)])
    den = rng.choice(_SMALL_DENOMS)
    p = rng.randint(1, den - 1)
    xval = Fraction(p, den)
    fxval = _fmt(xval)
    ax_val = a * xval
    result_val = ax_val + b
    if b > 0:
        op = rf"{fname}({fxval}) = {a} \cdot {fxval} + {b}"
        mid = rf"= {_fmt(ax_val)} + {b}"
    else:
        ab = -b
        op = rf"{fname}({fxval}) = {a} \cdot {fxval} - {ab}"
        mid = rf"= {_fmt(ax_val)} - {ab}"
    return FourStep(
        equation=rf"{_fdef(fname, a, b)},\quad {fname}({fxval})",
        operation=op,
        intermediate=mid,
        result=rf"{fname}({fxval}) = {_fmt(result_val)}",
        model_ref="",
    )


def _gen_symbol(rng: Random) -> FourStep:
    name = rng.choice(_FUNC_POOL)
    fname = _fn(name)
    a = rng.choice([2, 3, 4, 5])
    b = rng.choice([*range(-5, 0), *range(1, 6)])
    var = rng.choice(_VAR_POOL)
    c = rng.choice([*range(-4, 0), *range(1, 5)])
    ac = a * c
    combined = ac + b
    c_str = f"{var} + {c}" if c > 0 else rf"{var} - {-c}"
    call = rf"{fname}({c_str})"
    op_b = f"+ {b}" if b > 0 else f"- {-b}"
    op = rf"{call} = {a}({c_str}) {op_b}"
    ac_part = f"+ {ac}" if ac > 0 else f"- {-ac}"
    b_part = f"+ {b}" if b > 0 else f"- {-b}"
    mid = rf"= {a}{var} {ac_part} {b_part}"
    if combined > 0:
        res_rhs = rf"{a}{var} + {combined}"
    elif combined < 0:
        res_rhs = rf"{a}{var} - {-combined}"
    else:
        res_rhs = rf"{a}{var}"
    return FourStep(
        equation=rf"{_fdef(fname, a, b)},\quad {call}",
        operation=op,
        intermediate=mid,
        result=rf"{call} = {res_rhs}",
        model_ref="",
    )


class FuncEvalGenerator:
    title = "f(x) = ax + b  —  Evaluate a Function"
    caption = (
        r"A function is a rule: the same input always gives the same output. "
        r"The name ($\text{blorp}$, $f$, $g$) is arbitrary — it just labels which rule. "
        r"To evaluate: replace every $x$ in the rule with the given input, then simplify."
    )
    output_name = "func_eval.html"
    n_detailed = 6
    detailed_share = {Kind.INTEGER: 3, Kind.FRACTION: 2, Kind.SYMBOL: 1}

    def gen(self, kind: Kind, rng: Random) -> FourStep:
        if kind is Kind.INTEGER:
            return _gen_integer(rng)
        if kind is Kind.FRACTION:
            return _gen_fraction(rng)
        return _gen_symbol(rng)

    def make_sheet(
        self,
        kinds: frozenset[Kind] = frozenset(Kind),
        *,
        seed: int | None = None,
    ) -> SheetData:
        rng = Random(seed)
        active = [k for k in _KIND_ORDER if k in kinds]

        if self.detailed_share is not None and set(active) == set(Kind):
            shares = self.detailed_share
        else:
            base, extra = divmod(self.n_detailed, len(active))
            shares = {k: base + (1 if i < extra else 0) for i, k in enumerate(active)}

        detailed = [self.gen(k, rng) for k in active for _ in range(shares[k])]

        # Collapsed shows the direct substitution: "blorp(2) = 3(2)+1 ⟹ blorp(2) = 7"
        collapsed = []
        for i in range(12):
            s = self.gen(active[i % len(active)], rng)
            collapsed.append(CollapsedEx(s.operation, s.result))

        practice = []
        for i in range(18):
            s = self.gen(active[i % len(active)], rng)
            practice.append(PracticeEx(s.equation, s.result if i % 2 == 0 else None))

        return SheetData(
            title=self.title,
            caption=self.caption,
            output_name=self.output_name,
            detailed=detailed,
            collapsed=collapsed,
            practice=practice,
            practice_intro=_PRACTICE_INTRO,
            practice_cols=3,
        )


_GEN = FuncEvalGenerator()
make_sheet = _GEN.make_sheet
