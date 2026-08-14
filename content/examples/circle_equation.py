"""
Analytic geometry (circle), archetype 4 — ``circle_equation``.

Given a circle in the general form  x² + y² + Dx + Ey + F = 0, find the
coordinates of its **centre** and the length of its **radius** by completing the
square:  (x + D/2)² + (y + E/2)² = (D/2)² + (E/2)² − F, so the centre is
(−D/2, −E/2) and the radius is √((D/2)² + (E/2)² − F).

Completing the square in x and in y are two separate operations, so centre_x and
centre_y are graded independently (1 mark each); the radius is the third mark.
The radius is graded with ``symbolic_equality``, which is generous by default:
√50, the simplified 5√2, and a calculator decimal like 7.07 all score. (A
variant that tests surd manipulation would set ``require_exact_form`` on the
radius step, so 7.07 loses the mark — not done here, where any correct value is
accepted.)

**Construction** is backward from an integer centre (h, k) and an integer
*radius-squared* r² (not the radius): the equation is (x−h)² + (y−k)² = r², i.e.
D = −2h, E = −2k, F = h² + k² − r², all integers. r² is drawn from a plain
integer range, so the radius is √50, √17, or a clean 5 as the draw falls — no
cosmetic clamping toward perfect squares.
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

_x, _y = sympy.symbols("x y")


def _gen(rng: random.Random) -> dict:
    h = rng.randint(-6, 6)
    k = rng.randint(-6, 6)
    radius_sq = rng.randint(2, 40)

    D = -2 * h
    E = -2 * k
    F = h * h + k * k - radius_sq

    equation_poly = _x**2 + _y**2 + D * _x + E * _y + F
    radius = sympy.sqrt(radius_sq)

    return {
        "D": D,
        "E": E,
        "F": F,
        "centre_x": h,
        "centre_y": k,
        "radius": radius,
        "radius_sq": radius_sq,
        "equation_poly": equation_poly,
        "equation_latex": rf"{sympy.latex(equation_poly)} = 0",
    }


circle_equation = Problem(
    id="circle_equation",
    type_id="circle_equation",
    name="Centre and radius of a circle from its general-form equation",
    artifact_type="practice",
    problem_spec=_gen,
    verifier_spec=[
        {"kind": "numeric_equality", "marks_possible": 1, "param_key": "centre_x"},
        {"kind": "numeric_equality", "marks_possible": 1, "param_key": "centre_y"},
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "radius"},
    ],
    corpus_anchor=CorpusAnchor(
        paper="2023 Nov P2",
        question="4.2–4.6",  # centre/radius part of the 18-mark circle block
        # standalone sub-part mark not in our provenance notes → left unset
    ),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(registry=InMemoryRegistry({circle_equation.id: circle_equation}))

    def show(label, inst, *answers):
        attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
        r = inst.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  "
            f"is_correct={r.is_correct}"
        )

    for seed in range(4):
        inst = engine.instantiate(circle_equation.id, seed=seed)
        p = inst.params
        print(f"=== seed {seed} ===")
        print(f"  {p['equation_latex']}")
        print(f"  centre=({p['centre_x']},{p['centre_y']})  radius={p['radius']}")
        show("all correct  ", inst, p["centre_x"], p["centre_y"], p["radius"])
        # sign slip: forgetting centre = -D/2 (using +D/2) is the classic error
        show("centre signs ", inst, -p["centre_x"], -p["centre_y"], p["radius"])
        # unsimplified radius still scores
        show(
            "radius as √r²",
            inst,
            p["centre_x"],
            p["centre_y"],
            sympy.sqrt(p["radius_sq"]),
        )
