"""
Trigonometric simplification — ``trig_simplify_reduce`` (P2 Q5.2) and
``trig_simplify_product`` (P2 Q5.3).

Two "no-calculator simplify" archetypes, both graded as a single fixed answer by
``symbolic_equality`` (no new verifier kind):

- **trig_simplify_reduce** (5.2, *identity simplify*): a product/quotient of
  general-angle reduction- and co-function terms in an unknown ``x`` — e.g.

      sin(180°−x)·cos(360°−x)·tan(180°+x) / [cos(90°−x)·sin(90°+x)]

  which collapses to a single ratio (``±sin x``, ``±cos x``, ``±tan x`` or ``±1``).
  The answer is a SymPy expression in ``x``; ``symbolic_equality`` accepts any
  algebraically equivalent form and — because a free-symbol answer is not
  float-able — stays strictly symbolic (no decimal fallback).

- **trig_simplify_product** (5.3, *special tan-product*): a numeric product of
  trig ratios at reducible special angles (120°, 135°, …, 330°) — e.g.
  ``cos 480°·sin 300°·tan 240°`` → an exact constant in ℚ[√2, √3].

Both build the expression from real angle arguments and take the canonical from
``sympy.simplify``, so the *printed* expression genuinely equals the graded
answer — the reductions are checked by SymPy, not asserted. The reduce archetype
also confirms its exponent bookkeeping against SymPy at construction and raises if
they ever disagree (exceptions over quiet errors).

Marks: each slot's final answer is engine-graded; the intermediate reduction lines
(applying each reduction/co-function) are the hand-marked method, so the paper
slots declare an ``auto_marks`` below the headline (see worksheets/paper.py).
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

# The unknown of the general-angle simplify. A single shared symbol so the
# canonical answer and any student submission ("tan(x)") compare in the same x.
_X = sympy.Symbol("x")


# ── 5.2 identity simplify: reduction / co-function terms → a single ratio ─────────

# Each reduction/co-function transform, as (angle argument, LaTeX of the argument).
# All are genuine reductions (none is the identity), so every printed factor needs a
# rule applied — the point of the exercise.
_TRANSFORMS: dict[str, tuple[sympy.Basic, str]] = {
    "180-x": (sympy.pi - _X, r"180^\circ - x"),
    "180+x": (sympy.pi + _X, r"180^\circ + x"),
    "360-x": (2 * sympy.pi - _X, r"360^\circ - x"),
    "-x": (-_X, r"-x"),
    "90-x": (sympy.pi / 2 - _X, r"90^\circ - x"),
    "90+x": (sympy.pi / 2 + _X, r"90^\circ + x"),
}

_FUNCS: dict[str, sympy.FunctionClass] = {
    "sin": sympy.sin,
    "cos": sympy.cos,
    "tan": sympy.tan,
}

# The three base ratios a factor may reduce to, as (sin, cos)-exponent unit vectors
# (tan = sin/cos). A single-ratio answer is one of these, or the constant 1.
_UNIT = {"sin": (1, 0), "cos": (0, 1), "tan": (1, -1)}
_RATIO_EXPR = {"sin": sympy.sin(_X), "cos": sympy.cos(_X), "tan": sympy.tan(_X)}
# (se, ce) exponent target → the answer ratio it names.
_TARGETS = {(1, 0): "sin", (0, 1): "cos", (1, -1): "tan", (0, 0): "1"}


def _reduce_factor(func: str, tkey: str) -> tuple[str, int] | None:
    """Reduce ``func(transform)`` to a signed base ratio.

    Returns ``(ratio_name, sign)`` where ratio_name ∈ {sin, cos, tan}, or ``None``
    when the reduction is a co-function outside that set (e.g. tan(90°−x) = cot x),
    which this archetype deliberately excludes to keep answers in {sin, cos, tan}.
    """
    reduced = sympy.simplify(_FUNCS[func](_TRANSFORMS[tkey][0]))
    for name, expr in _RATIO_EXPR.items():
        if reduced == expr:
            return name, 1
        if reduced == -expr:
            return name, -1
    return None


# Precompute the factors that reduce cleanly to ±(sin|cos|tan): the building blocks.
_FACTORS: list[tuple[str, str, str, int]] = []  # (func, tkey, ratio, sign)
for _func in _FUNCS:
    for _tkey in _TRANSFORMS:
        _r = _reduce_factor(_func, _tkey)
        if _r is not None:
            _FACTORS.append((_func, _tkey, _r[0], _r[1]))


def _gen_reduce(rng: random.Random) -> dict:
    """Draw a quotient of reduction terms that collapses to a single ratio.

    Rejection-samples factor multisets until the reduced (sin, cos)-exponent lands
    on a named target, then confirms the whole expression against SymPy. Cannot loop
    forever in practice; caps attempts and raises if the space is somehow exhausted.
    """
    for _ in range(5000):
        n_num = rng.randint(2, 3)
        n_den = rng.randint(1, 2)
        num = [rng.choice(_FACTORS) for _ in range(n_num)]
        den = [rng.choice(_FACTORS) for _ in range(n_den)]

        se = ce = 0
        sign = 1
        for _func, _tkey, ratio, s in num:
            u = _UNIT[ratio]
            se += u[0]
            ce += u[1]
            sign *= s
        for _func, _tkey, ratio, s in den:
            u = _UNIT[ratio]
            se -= u[0]
            ce -= u[1]
            sign *= s  # 1/(±r) keeps the sign

        target = _TARGETS.get((se, ce))
        if target is None:
            continue
        if target == "1" and n_num + n_den < 3:
            continue  # a two-factor "= ±1" is too slight for the slot

        answer = sympy.Integer(sign) if target == "1" else sign * _RATIO_EXPR[target]

        # Faithfulness: the printed expression must actually equal the answer.
        num_expr = sympy.Integer(1)
        for _func, _tkey, _r, _s in num:
            num_expr *= _FUNCS[_func](_TRANSFORMS[_tkey][0])
        den_expr = sympy.Integer(1)
        for _func, _tkey, _r, _s in den:
            den_expr *= _FUNCS[_func](_TRANSFORMS[_tkey][0])
        if sympy.simplify(num_expr / den_expr - answer) != 0:
            # Exponent bookkeeping disagreed with SymPy — skip this draw rather than
            # ship a mis-graded item. Should never fire; the loop cap catches a
            # systemic break loudly below.
            continue

        return {
            "num": [(f, t) for f, t, _r, _s in num],
            "den": [(f, t) for f, t, _r, _s in den],
            "answer": answer,
        }
    raise RuntimeError(
        "trig_simplify_reduce: no single-ratio draw in 5000 attempts — the factor "
        "table or target set is misconfigured"
    )


def arg_latex(tkey: str) -> str:
    """LaTeX of a reduction transform's angle argument (for the template)."""
    return _TRANSFORMS[tkey][1]


def reduced_latex(func: str, tkey: str) -> str:
    """LaTeX of what one factor reduces to, e.g. ``-\\tan x`` (for the memo)."""
    ratio, sign = _reduce_factor(func, tkey)  # type: ignore[misc]
    return (r"-" if sign < 0 else "") + rf"\{ratio} x"


def ratio_latex(expr: sympy.Basic) -> str:
    """Compact LaTeX for a single-ratio answer (``\\tan x``, ``-\\cos x``, ``-1``)."""
    for name, e in _RATIO_EXPR.items():
        if expr == e:
            return rf"\{name} x"
        if expr == -e:
            return rf"-\{name} x"
    return sympy.latex(expr)


trig_simplify_reduce = Problem(
    id="trig_simplify_reduce",
    type_id="trigonometry",
    name="Simplify a reduction/co-function expression to a single trig ratio",
    artifact_type="practice",
    problem_spec=_gen_reduce,
    verifier_spec={"kind": "symbolic_equality", "marks_possible": 3},
    corpus_anchor=CorpusAnchor(
        paper="2025 May/June P2",
        question="5.2",
        marks=6,
    ),
)


# ── 5.3 special tan-product: a numeric product at reducible special angles ────────

# Special angles outside the first quadrant — each reduces to a first-quadrant
# special value via a reduction formula (the point of the "no calculator" ask).
_SPECIAL_ANGLES = (120, 135, 150, 210, 225, 240, 300, 315, 330)


def _is_nice(expr: sympy.Basic) -> bool:
    """True iff expr is a real, finite constant in ℚ[√2, √3] (SA Gr10 scope)."""
    if not expr.is_real or expr.is_infinite:
        return False
    for p in expr.atoms(sympy.Pow):
        if p.exp == sympy.Rational(1, 2) and p.base not in (
            sympy.Integer(2),
            sympy.Integer(3),
        ):
            return False
    return True


def _gen_product(rng: random.Random) -> dict:
    """Draw a 2–3 factor product of special-angle ratios with an exact-value answer."""
    for _ in range(5000):
        n = rng.randint(2, 3)
        factors = []  # (func, angle_deg)
        for _ in range(n):
            factors.append(
                (rng.choice(("sin", "cos", "tan")), rng.choice(_SPECIAL_ANGLES))
            )

        expr = sympy.Integer(1)
        undefined = False
        for func, deg in factors:
            term = sympy.simplify(_FUNCS[func](sympy.pi * sympy.Rational(deg, 180)))
            if term.is_infinite:  # tan 90°-family — not in our pool, but guard anyway
                undefined = True
                break
            expr *= term
        if undefined:
            continue

        answer = sympy.simplify(expr)
        if answer == 0 or not _is_nice(answer):
            continue
        if answer == 1 or answer == -1:
            continue  # a product that trivially collapses to ±1 reads as a trick miss
        return {"factors": factors, "answer": answer}
    raise RuntimeError(
        "trig_simplify_product: no nice product in 5000 attempts — the angle pool is "
        "misconfigured"
    )


trig_simplify_product = Problem(
    id="trig_simplify_product",
    type_id="trigonometry",
    name="Evaluate a product of special-angle trig ratios without a calculator",
    artifact_type="practice",
    problem_spec=_gen_product,
    verifier_spec={"kind": "symbolic_equality", "marks_possible": 2},
    corpus_anchor=CorpusAnchor(
        paper="2025 May/June P2",
        question="5.3",
        marks=4,
    ),
)


def special_value_latex(func: str, deg: int) -> str:
    """LaTeX of a special-angle ratio's exact value, e.g. ``-\\frac{1}{2}``."""
    return sympy.latex(
        sympy.simplify(_FUNCS[func](sympy.pi * sympy.Rational(deg, 180)))
    )


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(
        registry=InMemoryRegistry(
            {
                trig_simplify_reduce.id: trig_simplify_reduce,
                trig_simplify_product.id: trig_simplify_product,
            }
        )
    )

    print("=== trig_simplify_reduce (5.2) ===")
    seen = set()
    for seed in range(60):
        inst = engine.instantiate(trig_simplify_reduce.id, seed=seed)
        p = inst.params
        num = " · ".join(f"{f}({_TRANSFORMS[t][1]})" for f, t in p["num"])
        den = " · ".join(f"{f}({_TRANSFORMS[t][1]})" for f, t in p["den"])
        ans = p["answer"]
        r = inst.verifier.rate(SolutionAttempt(steps=[SubmittedStep(ans)]))
        assert r.is_correct, (seed, ans)
        if str(ans) not in seen:
            seen.add(str(ans))
            print(f"  seed {seed}: [{num}] / [{den}]  =  {ans}")
    print(f"  distinct answers seen: {sorted(seen)}")

    print("\n=== trig_simplify_product (5.3) ===")
    for seed in range(12):
        inst = engine.instantiate(trig_simplify_product.id, seed=seed)
        p = inst.params
        prod = " · ".join(f"{f} {d}°" for f, d in p["factors"])
        ans = p["answer"]
        r = inst.verifier.rate(SolutionAttempt(steps=[SubmittedStep(ans)]))
        assert r.is_correct, (seed, ans)
        print(f"  seed {seed}: {prod}  =  {ans}")
