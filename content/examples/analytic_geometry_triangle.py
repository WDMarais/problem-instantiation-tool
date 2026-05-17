"""
Reference example: analytic geometry — triangle on the Cartesian plane.

Design decisions demonstrated:
- Code generator is required here: midpoint, gradient, distance, and area are
  all derived from the same three points A, B, C. A dict spec can only draw
  independent ranges; it cannot express this fan-out from shared inputs.
- The generator stores each answer under a named key (midpoint_x, midpoint_y,
  gradient_ac, distance_bc, area) rather than a single "answer" key. Each step
  in the verifier spec uses param_key to route to the right canonical. Without
  param_key, every step would fall through to params.get("answer") and share
  the same canonical.
- sympy.Rational is used for fraction-valued answers (midpoint coordinates,
  gradient, area). symbolic_equality uses sympy.simplify which handles
  equivalent fractions correctly; Python float comparison does not.
- Distance is left as sympy.sqrt(...) — not evaluated to float. A student who
  writes sqrt(200) and one who writes 10*sqrt(2) are both correct;
  sympy.simplify(sqrt(200) - 10*sqrt(2)) == 0 catches both.
- The collinearity guard (area == 0) and vertical-AC guard (x3 == x1) both
  retry rather than accepting a degenerate case that would make the gradient
  undefined or the triangle flat.
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import Problem


def _generate(rng: random.Random) -> dict:
    while True:
        x1, y1 = rng.randint(-8, 8), rng.randint(-8, 8)
        x2, y2 = rng.randint(-8, 8), rng.randint(-8, 8)
        x3, y3 = rng.randint(-8, 8), rng.randint(-8, 8)

        area2 = x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2)
        if area2 == 0:
            continue
        if x3 == x1:
            continue

        break

    return {
        "x1": x1,
        "y1": y1,
        "x2": x2,
        "y2": y2,
        "x3": x3,
        "y3": y3,
        "midpoint_x": sympy.Rational(x2 + x3, 2),
        "midpoint_y": sympy.Rational(y2 + y3, 2),
        "gradient_ac": sympy.Rational(y3 - y1, x3 - x1),
        "distance_bc": sympy.sqrt((x3 - x2) ** 2 + (y3 - y2) ** 2),
        "area": sympy.Rational(abs(area2), 2),
    }


problem = Problem(
    id="analytic_geometry_triangle",
    type_id="analytic_geometry",
    name="Four sub-problems on a triangle in the Cartesian plane",
    artifact_type="practice",
    problem_spec=_generate,
    verifier_spec=[
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "midpoint_x"},
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "midpoint_y"},
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "gradient_ac"},
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "distance_bc"},
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "area"},
    ],
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(registry=InMemoryRegistry({problem.id: problem}))
    instance = engine.instantiate(problem.id, seed=42)
    p = instance.params

    print(f"A = ({p['x1']}, {p['y1']})")
    print(f"B = ({p['x2']}, {p['y2']})")
    print(f"C = ({p['x3']}, {p['y3']})")
    print()
    print(f"Midpoint of BC : ({p['midpoint_x']}, {p['midpoint_y']})")
    print(f"Gradient of AC : {p['gradient_ac']}")
    print(f"Distance BC    : {p['distance_bc']}")
    print(f"Area           : {p['area']}")
    print()

    def show(label, *answers):
        attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
        r = instance.verifier.rate(attempt)
        print(
            f"{label}: {r.marks_awarded}/{r.marks_possible}  is_correct={r.is_correct}"
        )

    show(
        "All correct (canonical values)",
        p["midpoint_x"],
        p["midpoint_y"],
        p["gradient_ac"],
        p["distance_bc"],
        p["area"],
    )
    show(
        "Wrong gradient only          ",
        p["midpoint_x"],
        p["midpoint_y"],
        p["gradient_ac"] + 1,
        p["distance_bc"],
        p["area"],
    )
    # Demonstrate that unsimplified sqrt is accepted
    dist_sq = int((p["x3"] - p["x2"]) ** 2 + (p["y3"] - p["y2"]) ** 2)
    show(
        f"Distance as sqrt({dist_sq}) (unsimplified)",
        p["midpoint_x"],
        p["midpoint_y"],
        p["gradient_ac"],
        f"sqrt({dist_sq})",
        p["area"],
    )
