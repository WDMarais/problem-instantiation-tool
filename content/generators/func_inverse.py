"""Generator for inverse function question: given f(var) = c, find var."""

from __future__ import annotations

from fractions import Fraction
from random import Random

from content.generators import Kind
from content.generators.base import _SMALL_DENOMS, _VAR_POOL, _fmt
from content.generators.func_eval import _FUNC_POOL, _fdef, _fn
from content.sheet import CollapsedEx, FourStep, PracticeEx, SheetData

_KIND_ORDER = (Kind.INTEGER, Kind.FRACTION, Kind.SYMBOL, Kind.VARARG)

_PRACTICE_INTRO = (
    "Find the unknown variable for each problem. Show your working on a separate sheet "
    "and write only your answer in the box. "
    'Problems marked <span class="star">*</span> '
    "have answers at the bottom."
)


def _lhs(a: int, b: int, var: str = "x") -> str:
    """Format a·var + b as a KaTeX string."""
    av = var if a == 1 else (f"-{var}" if a == -1 else rf"{a}{var}")
    if b > 0:
        return rf"{av} + {b}"
    if b < 0:
        return rf"{av} - {-b}"
    return av


def _av(a: int, var: str = "x") -> str:
    return var if a == 1 else (f"-{var}" if a == -1 else rf"{a}{var}")


def _given_line(given: str, solve_for: str) -> str:
    """Second equation line: 'given <given>, find <var>'."""
    return rf"\text{{given }} {given}\text{{, find }} {solve_for}"


def _gen_integer(rng: Random) -> tuple[FourStep, str, str, str, str]:
    name = rng.choice(_FUNC_POOL)
    fname = _fn(name)
    a = rng.choice([-5, -4, -3, -2, 2, 3, 4, 5])
    b = rng.choice([*range(-5, 0), *range(1, 6)])
    x_ans = rng.choice([*range(-5, 0), *range(1, 6)])
    c = a * x_ans + b

    defn = _fdef(fname, a, b)
    given = rf"{fname}(x) = {c}"
    equation = defn + "\n" + _given_line(given, "x")
    result = rf"x = {x_ans}"

    return (
        FourStep(
            equation=equation,
            operation=rf"{_lhs(a, b)} = {c}",
            intermediate=rf"{_av(a)} = {c - b}",
            result=result,
            model_ref="",
        ),
        defn,
        given,
        result,
        "x",
    )


def _gen_fraction(rng: Random) -> tuple[FourStep, str, str, str, str]:
    name = rng.choice(_FUNC_POOL)
    fname = _fn(name)
    den = rng.choice(_SMALL_DENOMS)
    p = rng.randint(1, den - 1)
    x_ans = Fraction(p, den)
    a = den  # ensures a * x_ans = p (integer)
    b = rng.choice([*range(-5, 0), *range(1, 6)])
    c = p + b  # = a * x_ans + b

    defn = _fdef(fname, a, b)
    given = rf"{fname}(x) = {c}"
    equation = defn + "\n" + _given_line(given, "x")
    result = rf"x = {_fmt(x_ans)}"

    return (
        FourStep(
            equation=equation,
            operation=rf"{_lhs(a, b)} = {c}",
            intermediate=rf"{a}x = {p}",
            result=result,
            model_ref="",
        ),
        defn,
        given,
        result,
        "x",
    )


def _gen_symbol(rng: Random) -> tuple[FourStep, str, str, str, str]:
    name = rng.choice(_FUNC_POOL)
    fname = _fn(name)
    a = rng.choice([2, 3, 4, 5])
    b = rng.choice([*range(-5, 0), *range(1, 6)])
    param = rng.choice(_VAR_POOL)
    d = rng.choice([*range(-4, 0), *range(1, 5)])

    # x_ans = param + d  =>  c = a*(param+d) + b = a*param + (a*d + b)
    combined = a * d + b
    ad = a * d

    c_sym = rf"{a}{param}"
    if combined > 0:
        c_sym += rf" + {combined}"
    elif combined < 0:
        c_sym += rf" - {-combined}"

    rhs_mid = rf"{a}{param}"
    if ad > 0:
        rhs_mid += rf" + {ad}"
    elif ad < 0:
        rhs_mid += rf" - {-ad}"

    x_ans_str = rf"{param} + {d}" if d > 0 else rf"{param} - {-d}"

    defn = _fdef(fname, a, b)
    given = rf"{fname}(x) = {c_sym}"
    equation = defn + "\n" + _given_line(given, "x")
    result = rf"x = {x_ans_str}"

    return (
        FourStep(
            equation=equation,
            operation=rf"{_lhs(a, b)} = {c_sym}",
            intermediate=rf"{a}x = {rhs_mid}",
            result=result,
            model_ref="",
        ),
        defn,
        given,
        result,
        "x",
    )


def _gen_vararg(rng: Random) -> tuple[FourStep, str, str, str, str]:
    """Like INTEGER but with an arbitrary input variable (not x)."""
    name = rng.choice(_FUNC_POOL)
    fname = _fn(name)
    var = rng.choice(_VAR_POOL)
    a = rng.choice([-5, -4, -3, -2, 2, 3, 4, 5])
    b = rng.choice([*range(-5, 0), *range(1, 6)])
    ans_val = rng.choice([*range(-5, 0), *range(1, 6)])
    c = a * ans_val + b

    defn = _fdef(fname, a, b, var=var)
    given = rf"{fname}({var}) = {c}"
    equation = defn + "\n" + _given_line(given, var)
    result = rf"{var} = {ans_val}"

    return (
        FourStep(
            equation=equation,
            operation=rf"{_lhs(a, b, var)} = {c}",
            intermediate=rf"{_av(a, var)} = {c - b}",
            result=result,
            model_ref="",
        ),
        defn,
        given,
        result,
        var,
    )


class FuncInverseGenerator:
    title = "f(x) = ax + b: Find x given f(x)"
    caption = (
        r"Stage 1 asked: <em>given $x$</em>, find $f(x)$. "
        r"This sheet asks the inverse: <em>given $f(x)$</em>, find $x$. "
        r"Method: the rule gives $f(x) = ax+b$, so write $ax+b = c$ and solve. "
        r"(Same framing governs every inverse question: $\arcsin$, $\log$, etc.)"
    )
    output_name = "func_inverse.html"
    n_detailed = 6
    detailed_share = {Kind.INTEGER: 2, Kind.FRACTION: 1, Kind.SYMBOL: 1, Kind.VARARG: 2}

    def _gen_with_parts(
        self, kind: Kind, rng: Random
    ) -> tuple[FourStep, str, str, str, str]:
        if kind is Kind.INTEGER:
            return _gen_integer(rng)
        if kind is Kind.FRACTION:
            return _gen_fraction(rng)
        if kind is Kind.SYMBOL:
            return _gen_symbol(rng)
        return _gen_vararg(rng)

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

        # Collapsed: numeric kinds only — symbolic expressions overflow 3-col cells
        numeric = [k for k in active if k is not Kind.SYMBOL] or active
        collapsed = []
        for i in range(12):
            s = self.gen(numeric[i % len(numeric)], rng)
            collapsed.append(CollapsedEx(s.operation, s.result))

        practice = []
        for i in range(18):
            s, defn, given, result, ans_var = self._gen_with_parts(
                active[i % len(active)], rng
            )
            practice.append(
                PracticeEx(
                    equation=defn,
                    equation2=given,
                    answer=result if i % 2 == 0 else None,
                    answer_var=ans_var,
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
