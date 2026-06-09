"""Generator for inverse function question: given f(x) = c, find x."""

from __future__ import annotations

from fractions import Fraction
from random import Random

from content.generators import Kind
from content.generators.base import _SMALL_DENOMS, _VAR_POOL, _fmt
from content.generators.func_eval import _FUNC_POOL, _fn, _fdef
from content.sheet import CollapsedEx, FourStep, PracticeEx, SheetData

_KIND_ORDER = (Kind.INTEGER, Kind.FRACTION, Kind.SYMBOL)

_PRACTICE_INTRO = (
    "Find $x$ for each problem. Show your working on a separate sheet and write only your "
    'answer in the box. Problems marked <span class="star">*</span> have answers at the bottom.'
)


def _lhs(a: int, b: int) -> str:
    """Format ax + b as a KaTeX string (LHS of the linear equation)."""
    ax = "x" if a == 1 else ("-x" if a == -1 else rf"{a}x")
    if b > 0:
        return rf"{ax} + {b}"
    if b < 0:
        return rf"{ax} - {-b}"
    return ax


def _ax(a: int) -> str:
    return "x" if a == 1 else ("-x" if a == -1 else rf"{a}x")


def _gen_integer(rng: Random) -> tuple[FourStep, str, str, str]:
    name = rng.choice(_FUNC_POOL)
    fname = _fn(name)
    a = rng.choice([-5, -4, -3, -2, 2, 3, 4, 5])
    b = rng.choice([*range(-5, 0), *range(1, 6)])
    x_ans = rng.choice([*range(-5, 0), *range(1, 6)])
    c = a * x_ans + b

    defn = _fdef(fname, a, b)
    equation = rf"{defn},\quad {fname}(x) = {c}"
    operation = rf"{_lhs(a, b)} = {c}"
    intermediate = rf"{_ax(a)} = {c - b}"
    result = rf"x = {x_ans}"
    call_expr = rf"{fname}(x) = {c},\quad x"

    return (
        FourStep(
            equation=equation,
            operation=operation,
            intermediate=intermediate,
            result=result,
            model_ref="",
        ),
        defn,
        call_expr,
        result,
    )


def _gen_fraction(rng: Random) -> tuple[FourStep, str, str, str]:
    name = rng.choice(_FUNC_POOL)
    fname = _fn(name)
    den = rng.choice(_SMALL_DENOMS)
    p = rng.randint(1, den - 1)
    x_ans = Fraction(p, den)
    a = den  # ensures a * x_ans = p (integer)
    b = rng.choice([*range(-5, 0), *range(1, 6)])
    c = p + b  # = a * x_ans + b

    defn = _fdef(fname, a, b)
    equation = rf"{defn},\quad {fname}(x) = {c}"
    operation = rf"{_lhs(a, b)} = {c}"
    intermediate = rf"{a}x = {p}"
    result = rf"x = {_fmt(x_ans)}"
    call_expr = rf"{fname}(x) = {c},\quad x"

    return (
        FourStep(
            equation=equation,
            operation=operation,
            intermediate=intermediate,
            result=result,
            model_ref="",
        ),
        defn,
        call_expr,
        result,
    )


def _gen_symbol(rng: Random) -> tuple[FourStep, str, str, str]:
    name = rng.choice(_FUNC_POOL)
    fname = _fn(name)
    a = rng.choice([2, 3, 4, 5])
    b = rng.choice([*range(-5, 0), *range(1, 6)])
    var = rng.choice(_VAR_POOL)
    d = rng.choice([*range(-4, 0), *range(1, 5)])

    # x_ans = var + d  =>  c = a*(var+d) + b = a*var + (a*d + b)
    combined = a * d + b
    ad = a * d

    c_sym = rf"{a}{var}"
    if combined > 0:
        c_sym += rf" + {combined}"
    elif combined < 0:
        c_sym += rf" - {-combined}"

    rhs_mid = rf"{a}{var}"
    if ad > 0:
        rhs_mid += rf" + {ad}"
    elif ad < 0:
        rhs_mid += rf" - {-ad}"

    x_ans_str = rf"{var} + {d}" if d > 0 else rf"{var} - {-d}"

    defn = _fdef(fname, a, b)
    equation = rf"{defn},\quad {fname}(x) = {c_sym}"
    operation = rf"{_lhs(a, b)} = {c_sym}"
    intermediate = rf"{a}x = {rhs_mid}"
    result = rf"x = {x_ans_str}"
    call_expr = rf"{fname}(x) = {c_sym},\quad x"

    return (
        FourStep(
            equation=equation,
            operation=operation,
            intermediate=intermediate,
            result=result,
            model_ref="",
        ),
        defn,
        call_expr,
        result,
    )


class FuncInverseGenerator:
    title = "f(x) = ax + b  —  Find x given f(x)"
    caption = (
        r"Stage 1 asked: <em>given $x$</em>, find $f(x)$. "
        r"This sheet asks the inverse: <em>given $f(x)$</em>, find $x$. "
        r"Method: the rule gives $f(x) = ax+b$, so write $ax+b = c$ and solve. "
        r"(Same framing governs every inverse question: $\arcsin$, $\log$, etc.)"
    )
    output_name = "func_inverse.html"
    n_detailed = 6
    detailed_share = {Kind.INTEGER: 3, Kind.FRACTION: 2, Kind.SYMBOL: 1}

    def _gen_with_parts(
        self, kind: Kind, rng: Random
    ) -> tuple[FourStep, str, str, str]:
        if kind is Kind.INTEGER:
            return _gen_integer(rng)
        if kind is Kind.FRACTION:
            return _gen_fraction(rng)
        return _gen_symbol(rng)

    def gen(self, kind: Kind, rng: Random) -> FourStep:
        return self._gen_with_parts(kind, rng)[0]

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

        collapsed = []
        for i in range(12):
            s = self.gen(active[i % len(active)], rng)
            collapsed.append(CollapsedEx(s.equation, s.result))

        practice = []
        for i in range(18):
            s, defn, call_expr, result = self._gen_with_parts(
                active[i % len(active)], rng
            )
            practice.append(
                PracticeEx(
                    equation=s.equation,
                    answer=result if i % 2 == 0 else None,
                    definition=defn,
                    call_expr=call_expr,
                )
            )

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


_GEN = FuncInverseGenerator()
make_sheet = _GEN.make_sheet
