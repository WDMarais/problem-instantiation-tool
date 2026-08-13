"""
Calculus, archetype 4 — ``cubic_stationary_points``.

Given a cubic  f(x) = a·x³ + b·x² + c·x + d, find the **stationary (turning)
points** — solve f′(x) = 0 for the x-coordinates, evaluate f there for the full
coordinates — and **classify each as a local maximum or minimum** via the second
derivative (f″ < 0 → max, f″ > 0 → min). A cubic with two distinct stationary
points always has exactly one of each.

The answer is decomposed into the three things a marker rewards:

  1. the **stationary x-values**  {x : f′(x) = 0}  (``set_equality``, 2 marks,
     partial credit per root) — solving f′(x) = 0;
  2. the **turning-point coordinates**  {(x, f(x))}  (``set_equality``, 2 marks,
     partial per point) — evaluating f; and
  3. the **classification**  {(x, "local_max" | "local_min")}
     (``set_equality``, 2 marks, partial per point) — the second-derivative test.

Encoding the classification as a set of ``(x, label)`` tuples is the same
compound-element trick as the coordinates, now carrying a *categorical* second
component — a per-point reason map (see the reason-verifier signal log,
``project-quadratic-inequality-region-signal``).

**Construction** is backward from the two stationary points: choose distinct
integers p, q and a leading a, set f′(x) = 3a·(x−p)(x−q) (so b = −3a(p+q)/2,
c = 3a·p·q — the draw is retried until 3a(p+q) is even so b stays integer), then
integrate with an arbitrary constant d. The y-coordinates of the turning points
are exactly what the (deferred, class-c) "value of k for three real roots"
graph-interpretation variant reads off.
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

_x = sympy.Symbol("x")


def _gen(rng: random.Random) -> dict:
    while True:
        p = rng.randint(-4, 4)
        q = rng.randint(-4, 4)
        a = rng.choice([-2, -1, 1, 2])
        # b = -3a(p+q)/2 must be an integer, and the points must be distinct
        if p != q and (a * (p + q)) % 2 == 0:
            break

    b = -3 * a * (p + q) // 2
    c = 3 * a * p * q
    d = rng.randint(-6, 6)

    f = a * _x**3 + b * _x**2 + c * _x + d
    f2 = sympy.diff(f, _x, 2)

    def label(xv: int) -> str:
        return "local_max" if f2.subs(_x, xv) < 0 else "local_min"

    coords = frozenset({(p, int(f.subs(_x, p))), (q, int(f.subs(_x, q)))})
    classification = frozenset({(p, label(p)), (q, label(q))})

    return {
        "a": a,
        "b": b,
        "c": c,
        "d": d,
        "stationary_x": frozenset({p, q}),
        "tp_coords": coords,
        "classification": classification,
        "function_latex": rf"f(x) = {sympy.latex(f)}",
        "derivative_latex": sympy.latex(sympy.diff(f, _x)),
    }


cubic_stationary_points = Problem(
    id="cubic_stationary_points",
    type_id="cubic_stationary_points",
    name="Find and classify the turning points of a cubic (f′=0, then the f″ test)",
    artifact_type="practice",
    problem_spec=_gen,
    verifier_spec=[
        {"kind": "set_equality", "marks_possible": 2, "param_key": "stationary_x"},
        {"kind": "set_equality", "marks_possible": 2, "param_key": "tp_coords"},
        {"kind": "set_equality", "marks_possible": 2, "param_key": "classification"},
    ],
    corpus_anchor=CorpusAnchor(
        paper="2023 Nov P1",
        question="8.1",
        # 8.1 is the 4-mark coordinate-finding item; this archetype is a superset
        # (it adds the f″ max/min classification), so a single part-mark does not
        # apply — left unset.
    ),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(
        registry=InMemoryRegistry({cubic_stationary_points.id: cubic_stationary_points})
    )

    def show(label, inst, *answers):
        attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
        r = inst.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  "
            f"is_correct={r.is_correct}"
        )

    for seed in range(3):
        inst = engine.instantiate(cubic_stationary_points.id, seed=seed)
        p = inst.params
        print(f"=== seed {seed} ===")
        print(f"  {p['function_latex']}")
        print(f"  TPs = {sorted(p['tp_coords'])}   {sorted(p['classification'])}")
        show(
            "all three correct  ",
            inst,
            p["stationary_x"],
            p["tp_coords"],
            p["classification"],
        )
        show(
            "coords ok, class off",
            inst,
            p["stationary_x"],
            p["tp_coords"],
            frozenset({(xv, "local_min") for xv, _ in p["classification"]}),
        )
