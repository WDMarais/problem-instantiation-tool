"""
Statistics, archetype 1 — ``regression_line``.

Given a bivariate dataset (a table of x, y pairs), find the **least-squares
regression line** ŷ = A + Bx, the **correlation coefficient** r, and use the
line to **predict** ŷ at a stated x. This is the recurring Q1 of every DBE P2 —
the mark is really "drive the calculator's stat mode correctly", so every answer
is a calculator decimal and is graded numerically with tolerance (a student's
2-dp value lands inside the band; the classic error of regressing x-on-y instead
of y-on-x lands far outside it).

The four sub-answers are graded independently: gradient B, intercept A,
correlation r, and the prediction. B and A are exact rationals internally
(Sxy/Sxx and ȳ − Bx̄); r carries a square root, so it is stored as a rounded
float. The intercept and prediction get a wider band because a student who feeds
a 2-dp-rounded gradient back into A = ȳ − Bx̄ accumulates a little drift — DBE
marks that as correct.

**Construction** draws a genuine positive-association scatter: distinct integer x
values and y = intercept + slope·x + integer noise. Only the *scenario sign* is
fixed (a positive association, the common exam setup); the coefficients A, B, r
are whatever the least-squares fit produces — never clamped toward round numbers.
A perfectly collinear draw (|r| = 1, a degenerate "regression") is rejected, the
way the straight-line archetypes reject a vertical line.
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import CorpusAnchor, Problem


def _fit(xs: list[int], ys: list[int]) -> dict:
    """Least-squares fit via the deviation formulas (exact where rational)."""
    n = len(xs)
    xbar = sympy.Rational(sum(xs), n)
    ybar = sympy.Rational(sum(ys), n)
    sxx = sum((x - xbar) ** 2 for x in xs)
    syy = sum((y - ybar) ** 2 for y in ys)
    sxy = sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys))
    b = sxy / sxx
    a = ybar - b * xbar
    r = sxy / sympy.sqrt(sxx * syy)
    return {"a": a, "b": b, "r": r, "sxx": sxx, "syy": syy, "sxy": sxy}


def _gen(rng: random.Random) -> dict:
    while True:
        n = rng.choice([7, 8, 9, 10])
        xs = sorted(rng.sample(range(1, 21), n))  # distinct ⇒ Sxx > 0
        slope = rng.randint(2, 5)  # positive association (the common P2 setup)
        intercept = rng.randint(10, 40)
        ys = [intercept + slope * x + rng.randint(-6, 6) for x in xs]

        fit = _fit(xs, ys)
        if fit["syy"] == 0:  # all y equal — no correlation defined
            continue
        if fit["sxy"] ** 2 == fit["sxx"] * fit["syy"]:  # perfect line — degenerate
            continue
        break

    # predict at an x inside the range but off the data grid
    while True:
        x_pred = rng.randint(min(xs), max(xs))
        if x_pred not in xs:
            break

    a, b = fit["a"], fit["b"]
    prediction = a + b * x_pred

    header = " & ".join(str(x) for x in xs)
    yrow = " & ".join(str(y) for y in ys)
    table_latex = (
        r"\begin{array}{c|" + "c" * n + "}"
        rf"x & {header} \\ \hline y & {yrow}"
        r"\end{array}"
    )

    return {
        "xs": xs,
        "ys": ys,
        "n": n,
        "x_pred": x_pred,
        "gradient": b,  # exact rational
        "intercept": a,  # exact rational
        "correlation": round(float(fit["r"]), 4),
        "prediction": prediction,  # exact rational
        "table_latex": table_latex,
    }


regression_line = Problem(
    id="regression_line",
    type_id="regression_line",
    name="Least-squares regression line, correlation and prediction",
    artifact_type="practice",
    problem_spec=_gen,
    verifier_spec=[
        {
            "kind": "numeric_equality",
            "marks_possible": 1,
            "param_key": "gradient",
            "tolerance": 0.05,
        },
        {
            "kind": "numeric_equality",
            "marks_possible": 1,
            "param_key": "intercept",
            "tolerance": 0.5,
        },
        {
            "kind": "numeric_equality",
            "marks_possible": 1,
            "param_key": "correlation",
            "tolerance": 0.05,
        },
        {
            "kind": "numeric_equality",
            "marks_possible": 1,
            "param_key": "prediction",
            "tolerance": 1.0,
        },
    ],
    corpus_anchor=CorpusAnchor(
        paper="2024 Nov P2",
        question="1.1–1.3",  # regression / correlation / predict — recurs every P2
        # the sub-parts share a 6-mark block in our provenance notes; the
        # standalone answer-mark split is left unset rather than forced to match.
    ),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(registry=InMemoryRegistry({regression_line.id: regression_line}))

    def show(label, inst, *answers):
        attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
        r = inst.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  "
            f"is_correct={r.is_correct}"
        )

    for seed in range(4):
        inst = engine.instantiate(regression_line.id, seed=seed)
        p = inst.params
        b2, a2 = round(float(p["gradient"]), 2), round(float(p["intercept"]), 2)
        pred2 = round(float(p["prediction"]), 2)
        print(f"=== seed {seed} ===")
        print(f"  x: {p['xs']}")
        print(f"  y: {p['ys']}")
        print(
            f"  ŷ = {a2} + {b2}x   r = {p['correlation']}   ŷ({p['x_pred']}) = {pred2}"
        )
        # calculator answers, rounded to 2 dp, all score
        show("2-dp calc values", inst, b2, a2, p["correlation"], pred2)
        # regressing x-on-y (Sxy/Syy) instead of y-on-x is the classic error → misses
        xbar = sum(p["xs"]) / p["n"]
        ybar = sum(p["ys"]) / p["n"]
        syy = sum((y - ybar) ** 2 for y in p["ys"])
        sxy = sum((x - xbar) * (y - ybar) for x, y in zip(p["xs"], p["ys"]))
        show("x-on-y gradient ", inst, sxy / syy, a2, p["correlation"], pred2)
