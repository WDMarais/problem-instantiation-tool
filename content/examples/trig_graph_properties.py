"""
Reference example: trig graph properties — four question variants (P2 Q6, 9 marks).

All four problems share the same underlying setup: f(x) = a·sin x and g(x) = b·cos x
for a ∈ {1,2,3}, b ∈ {1,2}.  Each instance includes a `graph` key in params that
encodes the visual description (curves, domain, any reference lines).  This key is
structurally complete — a renderer can consume it as-is — but no image is generated
here.  The two halves that remain:
  1. A renderer that turns `graph` into an SVG/PNG/PDF.
  2. A snapshot test that asserts "these params → this image" (separate from this file).
Neither is a blocker for the content layer, which is fully testable without them.

Design decisions demonstrated:

- trig_graph_amplitude: the only graph-dependent sub-question.  The params ARE the
  answer (a and b are chosen, not inferred from a visual).  The problem is only
  meaningful once the renderer hides those values behind an image; until then it is
  included so the Problem ID exists and the graph encoding is exercised.
  Two symbolic_equality param_key steps for answer_a and answer_b.

- trig_graph_range: purely analytical — range of g = b·cos x is [−b, b] regardless
  of the domain shown.  Two param_key steps (answer_min, answer_max) with integer
  values as SymPy Integers.

- trig_graph_decreasing: also analytical.  g(x) = b·cos x with b > 0 is strictly
  decreasing on (0°, 180°) within the shown domain [−180°, 180°].  Two param_key
  steps for the endpoints (always 0 and 180 for b > 0), testing the conceptual fact.

- trig_graph_solve: solve a·sin x − b·cos x = k for x ∈ [0°, 360°].  The equation
  is rewritten as R·sin(x − φ) = k with R = √(a²+b²) and φ = atan2(b, a).  Two
  distinct solutions exist iff |k| < R; k is chosen from {1, …, ⌊R⌋} to guarantee
  this.  Answers are floats; numeric_equality with tolerance=0.5° accommodates
  calculator rounding.
"""

from __future__ import annotations

import math
import random

import sympy

from problem_instantiation_tool.schemas import Problem

_A_CHOICES = [1, 2, 3]
_B_CHOICES = [1, 2]


def _graph_encoding(a: int, b: int, x_domain: tuple[int, int]) -> dict:
    return {
        "curves": [
            {"id": "f", "func": "sin", "amplitude": a, "period_deg": 360},
            {"id": "g", "func": "cos", "amplitude": b, "period_deg": 360},
        ],
        "x_domain_deg": list(x_domain),
    }


def _solve_x(a: int, b: int, k: int) -> tuple[float, float]:
    """Return (x1, x2) in degrees in [0°, 360°), sorted ascending."""
    R = math.sqrt(a**2 + b**2)
    phi = math.atan2(b, a)
    alpha = math.asin(k / R)
    x1 = math.degrees(phi + alpha) % 360
    x2 = math.degrees(phi + math.pi - alpha) % 360
    return tuple(sorted([x1, x2]))


# ---------------------------------------------------------------------------
# 1. trig_graph_amplitude
#    Read a and b from the graph of f(x)=a·sin x, g(x)=b·cos x.
#    Graph-dependent: meaningful only when the renderer hides a and b visually.
# ---------------------------------------------------------------------------


def _gen_amplitude(rng: random.Random) -> dict:
    a = rng.choice(_A_CHOICES)
    b = rng.choice(_B_CHOICES)
    return {
        "a": a,
        "b": b,
        "graph": _graph_encoding(a, b, (-360, 360)),
        "answer_a": sympy.Integer(a),
        "answer_b": sympy.Integer(b),
    }


trig_graph_amplitude = Problem(
    id="trig_graph_amplitude",
    type_id="trig_graph",
    name="Read the amplitudes a and b from the graph of f=a·sin x and g=b·cos x",
    artifact_type="practice",
    problem_spec=_gen_amplitude,
    verifier_spec=[
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "answer_a"},
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "answer_b"},
    ],
)


# ---------------------------------------------------------------------------
# 2. trig_graph_range
#    State the range of g(x) = b·cos x.
# ---------------------------------------------------------------------------


def _gen_range(rng: random.Random) -> dict:
    a = rng.choice(_A_CHOICES)
    b = rng.choice(_B_CHOICES)
    return {
        "a": a,
        "b": b,
        "graph": _graph_encoding(a, b, (-360, 360)),
        "answer_min": sympy.Integer(-b),
        "answer_max": sympy.Integer(b),
    }


trig_graph_range = Problem(
    id="trig_graph_range",
    type_id="trig_graph",
    name="State the range of g(x) = b·cos x",
    artifact_type="practice",
    problem_spec=_gen_range,
    verifier_spec=[
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "answer_min"},
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "answer_max"},
    ],
)


# ---------------------------------------------------------------------------
# 3. trig_graph_decreasing
#    State the interval in [−180°, 180°] on which g(x) = b·cos x is decreasing.
#    For b > 0 this is always (0°, 180°).
# ---------------------------------------------------------------------------


def _gen_decreasing(rng: random.Random) -> dict:
    a = rng.choice(_A_CHOICES)
    b = rng.choice(_B_CHOICES)
    return {
        "a": a,
        "b": b,
        "graph": _graph_encoding(a, b, (-180, 180)),
        "answer_lower": sympy.Integer(0),
        "answer_upper": sympy.Integer(180),
    }


trig_graph_decreasing = Problem(
    id="trig_graph_decreasing",
    type_id="trig_graph",
    name="State the interval in [−180°, 180°] on which g(x) = b·cos x is decreasing",
    artifact_type="practice",
    problem_spec=_gen_decreasing,
    verifier_spec=[
        {
            "kind": "symbolic_equality",
            "marks_possible": 1,
            "param_key": "answer_lower",
        },
        {
            "kind": "symbolic_equality",
            "marks_possible": 1,
            "param_key": "answer_upper",
        },
    ],
)


# ---------------------------------------------------------------------------
# 4. trig_graph_solve
#    Solve a·sin x − b·cos x = k for x ∈ [0°, 360°].
#    Two solutions, verified with numeric_equality (tolerance 0.5°).
# ---------------------------------------------------------------------------


def _gen_solve(rng: random.Random) -> dict:
    while True:
        a = rng.choice(_A_CHOICES)
        b = rng.choice(_B_CHOICES)
        R = math.sqrt(a**2 + b**2)
        k_max = math.floor(R - 1e-9)  # largest integer strictly less than R
        if k_max < 1:
            continue
        k = rng.randint(1, k_max)
        x1, x2 = _solve_x(a, b, k)
        graph = _graph_encoding(a, b, (0, 360))
        graph["k_line"] = k  # renderer draws f(x)−g(x) = k or equivalent
        return {
            "a": a,
            "b": b,
            "k": k,
            "graph": graph,
            "answer_x1": x1,
            "answer_x2": x2,
        }


trig_graph_solve = Problem(
    id="trig_graph_solve",
    type_id="trig_graph",
    name="Solve a·sin x − b·cos x = k for x ∈ [0°, 360°]",
    artifact_type="practice",
    problem_spec=_gen_solve,
    verifier_spec=[
        {
            "kind": "numeric_equality",
            "marks_possible": 1,
            "param_key": "answer_x1",
            "tolerance": 0.5,
        },
        {
            "kind": "numeric_equality",
            "marks_possible": 1,
            "param_key": "answer_x2",
            "tolerance": 0.5,
        },
    ],
)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    all_problems = {
        p.id: p
        for p in [
            trig_graph_amplitude,
            trig_graph_range,
            trig_graph_decreasing,
            trig_graph_solve,
        ]
    }
    engine = Engine(registry=InMemoryRegistry(all_problems))

    def show(label, instance, *answers):
        attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
        r = instance.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  is_correct={r.is_correct}"
        )

    print("=== trig_graph_amplitude (graph-dependent sub-question) ===")
    inst = engine.instantiate(trig_graph_amplitude.id, seed=42)
    p = inst.params
    print(f"  Graph: f(x)={p['a']}·sin x,  g(x)={p['b']}·cos x")
    print(f"  Graph encoding: {p['graph']}")
    a_c, b_c = inst.verifier.canonicals
    show("Correct (a,b)    ", inst, a_c, b_c)
    show("b wrong          ", inst, a_c, int(b_c) + 1)

    print()

    print("=== trig_graph_range ===")
    inst = engine.instantiate(trig_graph_range.id, seed=42)
    p = inst.params
    print(f"  g(x) = {p['b']}·cos x")
    mn, mx = inst.verifier.canonicals
    print(f"  Range: [{mn}, {mx}]")
    show("Correct           ", inst, mn, mx)
    show("Swapped min/max   ", inst, mx, mn)

    print()

    print("=== trig_graph_decreasing ===")
    inst = engine.instantiate(trig_graph_decreasing.id, seed=42)
    p = inst.params
    print(f"  g(x) = {p['b']}·cos x,  domain [−180°, 180°]")
    lo, hi = inst.verifier.canonicals
    print(f"  Decreasing on ({lo}°, {hi}°)")
    show("Correct (0, 180)  ", inst, lo, hi)
    show("Wrong (−180, 0)   ", inst, -180, 0)

    print()

    print("=== trig_graph_solve ===")
    inst = engine.instantiate(trig_graph_solve.id, seed=42)
    p = inst.params
    print(f"  {p['a']}·sin x − {p['b']}·cos x = {p['k']},  x ∈ [0°, 360°]")
    x1, x2 = inst.verifier.canonicals
    print(f"  Solutions: x ≈ {x1:.2f}°,  x ≈ {x2:.2f}°")
    show("Both correct (exact)      ", inst, x1, x2)
    show("Both correct (rounded)    ", inst, round(x1, 1), round(x2, 1))
    show("x1 off by 1°              ", inst, x1 + 1.0, x2)
    show("Both wrong                ", inst, x1 + 2.0, x2 + 2.0)
