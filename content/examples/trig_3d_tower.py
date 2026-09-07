"""
3-D trigonometry — the vertical-tower chain (P2 Q8).

F is the foot of a vertical tower FT. A and B lie in the same horizontal plane as
F. Given AB, the two base angles of the ground triangle (FÂB, FB̂A) and the angle
of elevation of T from A, three sub-parts fan out:

  8.1 AF, by the sine rule in the horizontal triangle AFB,
  8.2 "show that TF = AF·tan θ" — the right-triangle relation (FT ⟂ the ground),
  8.3 the tower height TF.

The chain is exact once the givens are fixed: everything reduces to the sine rule
in △AFB then tan θ in the vertical right-triangle △AFT. 8.2 states the relation the
question asks the candidate to *derive*, so its value is given away by design —
it is hand-marked (auto 0), like a "show that" always is. 8.1 and 8.3 are graded
numerically (lengths are irrational; a decimal tolerance accepts calculator work).
A cabinet-oblique wireframe orients the solid; points are lettered and the given
angles labelled, so nothing an answer asks for is read off the drawing.
"""

from __future__ import annotations

import math
import random

from problem_instantiation_tool.schemas import CorpusAnchor, Problem


def _generate(rng: random.Random) -> dict:
    for _ in range(400):
        alpha = rng.randint(35, 70)  # FÂB, the base angle at A
        beta = rng.randint(35, 70)  # FB̂A, the base angle at B
        if alpha == beta:  # keep AF ≠ BF so the two sides read distinctly
            continue
        if alpha + beta > 145:  # third angle F̂ ≥ 35° — a non-degenerate triangle
            continue
        theta = rng.randint(25, 60)  # angle of elevation of T from A
        d = rng.randint(20, 70)  # AB, in metres

        third = 180 - alpha - beta
        af = d * math.sin(math.radians(beta)) / math.sin(math.radians(third))
        bf = d * math.sin(math.radians(alpha)) / math.sin(math.radians(third))
        tf = af * math.tan(math.radians(theta))

        return {
            "alpha": alpha,
            "beta": beta,
            "theta": theta,
            "d": d,
            "angle_F": third,
            "answer_AF": round(af, 2),
            "answer_BF": round(bf, 2),
            "answer_TF": round(tf, 2),
        }
    raise RuntimeError("trig_3d_tower: no valid instance found")


problem = Problem(
    id="trig_3d_tower",
    type_id="trig_3d",
    name="3-D trig (vertical tower): AF by sine rule, then height TF",
    artifact_type="practice",
    problem_spec=_generate,
    verifier_spec=[
        {
            "kind": "numeric_equality",
            "marks_possible": 3,
            "param_key": "answer_AF",
            "tolerance": 0.5,
        },
        # 8.2 "show that TF = AF·tan θ" gives the relation in the question — there is
        # nothing numeric for the engine to grade; it is a hand-marked derivation.
        {
            "kind": "numeric_equality",
            "marks_possible": 3,
            "param_key": "answer_TF",
            "tolerance": 0.5,
        },
    ],
    corpus_anchor=CorpusAnchor(
        paper="2025 May/June P2",
        question="8",
        marks=8,
    ),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(registry=InMemoryRegistry({problem.id: problem}))
    inst = engine.instantiate(problem.id, seed=42)
    p = inst.params
    print(f"AB={p['d']} m  A={p['alpha']}  B={p['beta']}  F={p['angle_F']}")
    print(f"elevation theta={p['theta']}")
    print(f"AF={p['answer_AF']} m  BF={p['answer_BF']} m  TF={p['answer_TF']} m")

    attempt = SolutionAttempt(
        steps=[SubmittedStep(p["answer_AF"]), SubmittedStep(p["answer_TF"])]
    )
    res = inst.verifier.rate(attempt)
    print(f"all correct: {res.marks_awarded}/{res.marks_possible} ok={res.is_correct}")
