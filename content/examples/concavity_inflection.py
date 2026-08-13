"""
Calculus, archetype 7 — ``concavity_inflection``.

Given a cubic  f(x) = a·x³ + b·x² + c·x + d, find its **point of inflection** and
describe its **concavity**. The second derivative f″(x) = 6a·x + 2b is linear and
changes sign at  x = −b/(3a), which is therefore always a point of inflection;
either side of it the curve has opposite concavity (f″ > 0 concave up, f″ < 0
concave down).

The concavity answer is naturally an *interval* ("f is concave up for x > …"),
and the engine has no interval/solution-set verifier (``symbolic_equality``
mishandles SymPy `Set`s — see the reason-verifier signal log,
``project-quadratic-inequality-region-signal``). So it is decomposed, exactly as
that log prescribes for interval answers, into a value plus a categorical tag:

  1. the **inflection x-coordinate**  x = −b/(3a)  (``numeric_equality``, 1 mark)
     — the boundary where concavity changes; and
  2. the **concavity to the right of it**, one of ``concave_up`` / ``concave_down``
     for x > x_infl (``exact_equality``, 1 mark) — determined by the sign of a.

Together these reconstruct the full concavity picture (concave one way left of
the inflection point, the other way right of it). Encoding the interval as
boundary + direction is the same interim as ``quadratic_inequality``'s
critical-values + region.

**Construction** is backward from an integer inflection x: choose a and x_infl,
set b = −3a·x_infl so f″ = 6a·(x − x_infl) vanishes exactly there; c and d are
free.
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

_x = sympy.Symbol("x")


def _gen(rng: random.Random) -> dict:
    a = rng.choice([-2, -1, 1, 2])
    x_infl = rng.randint(-3, 3)
    b = -3 * a * x_infl
    c = rng.randint(-6, 6)
    d = rng.randint(-6, 6)

    f = a * _x**3 + b * _x**2 + c * _x + d
    # for x > x_infl, f″ = 6a·(x − x_infl) has the sign of a
    concavity_right = "concave_up" if a > 0 else "concave_down"

    return {
        "a": a,
        "b": b,
        "c": c,
        "d": d,
        "inflection_x": x_infl,
        "inflection_y": int(f.subs(_x, x_infl)),
        "concavity_right": concavity_right,
        "function_latex": rf"f(x) = {sympy.latex(f)}",
        "second_derivative_latex": sympy.latex(sympy.diff(f, _x, 2)),
    }


concavity_inflection = Problem(
    id="concavity_inflection",
    type_id="concavity_inflection",
    name="Point of inflection and concavity of a cubic (f″=0, sign of f″)",
    artifact_type="practice",
    problem_spec=_gen,
    verifier_spec=[
        {"kind": "numeric_equality", "marks_possible": 1, "param_key": "inflection_x"},
        {
            "kind": "exact_equality",
            "marks_possible": 1,
            "param_key": "concavity_right",
            "normalize": ["whitespace"],
        },
    ],
    corpus_anchor=CorpusAnchor(
        paper="2025 May/June P1",
        question="9.2–9.5",  # concavity/inflection part of the cubic-analysis block
        # standalone sub-part mark not in our provenance notes → left unset
    ),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(
        registry=InMemoryRegistry({concavity_inflection.id: concavity_inflection})
    )

    def show(label, inst, *answers):
        attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
        r = inst.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  "
            f"is_correct={r.is_correct}"
        )

    for seed in range(4):
        inst = engine.instantiate(concavity_inflection.id, seed=seed)
        p = inst.params
        print(f"=== seed {seed} ===")
        print(f"  {p['function_latex']}")
        print(
            f"  inflection x = {p['inflection_x']}   "
            f"concave (x>x_infl): {p['concavity_right']}"
        )
        show("both correct    ", inst, p["inflection_x"], p["concavity_right"])
        show("x ok, wrong dir ", inst, p["inflection_x"], "concave_up")
