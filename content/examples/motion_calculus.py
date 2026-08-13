"""
Calculus, archetype 6 — ``motion_calculus``.

A body moves along a line with displacement  s(t) = α·t³ + β·t² + γ·t + δ  metres
after t seconds (t ≥ 0). Its **velocity** is v(t) = s′(t) and its **acceleration**
is a(t) = s″(t). The velocity is greatest when the acceleration is zero — so the
**maximum velocity** is found by solving a(t) = 0 and evaluating v there. (It is
the maximum *velocity*, not speed: v(t*) is the largest value of the velocity
function and may be negative — the body's greatest velocity while moving in the
negative direction — so the label stays correct regardless of sign.)

The answer is decomposed into the three rewarded steps:

  1. the **velocity function**  v(t) = s′(t)  (``symbolic_equality``, 1 mark);
  2. the **time of maximum velocity**  t : a(t) = 0  (``numeric_equality``, 1
     mark) — differentiate again, set s″(t) = 0; and
  3. the **maximum velocity**  v(t*)  (``numeric_equality``, 1 mark).

**Construction.** The leading coefficient α is negative, so the velocity
v(t) = 3α·t² + 2β·t + γ is a **downward** parabola — its stationary point (where
a(t) = 0) is a genuine *maximum*, matching "maximum speed at a = 0" rather than a
minimum. Working backward from an integer time t* : β = −3α·t*, so
a(t) = 6α·(t − t*) vanishes exactly at t*, and v(t*) = −3α·t*² + γ is an integer.
(The paper's wording is "maximum speed"; the anchor is a provenance pointer, and
our stem asks for the unambiguous maximum velocity.)
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

_t = sympy.Symbol("t")


def _gen(rng: random.Random) -> dict:
    alpha = rng.choice([-1, -2])  # negative ⇒ velocity has a maximum
    t_star = rng.randint(1, 4)  # the (integer) time of maximum velocity
    beta = -3 * alpha * t_star
    gamma = rng.randint(-5, 8)
    delta = rng.randint(-5, 8)

    s = alpha * _t**3 + beta * _t**2 + gamma * _t + delta
    velocity = sympy.diff(s, _t)
    acceleration = sympy.diff(s, _t, 2)
    max_velocity = int(velocity.subs(_t, t_star))

    return {
        "alpha": alpha,
        "beta": beta,
        "gamma": gamma,
        "delta": delta,
        "velocity": velocity,
        "t_max": t_star,
        "max_velocity": max_velocity,
        "displacement_latex": rf"s(t) = {sympy.latex(s)}",
        "velocity_latex": sympy.latex(velocity),
        "acceleration_latex": sympy.latex(acceleration),
    }


motion_calculus = Problem(
    id="motion_calculus",
    type_id="motion_calculus",
    name="Motion: velocity v=s′, maximum velocity where acceleration a=s″=0",
    artifact_type="practice",
    problem_spec=_gen,
    verifier_spec=[
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "velocity"},
        {"kind": "numeric_equality", "marks_possible": 1, "param_key": "t_max"},
        {"kind": "numeric_equality", "marks_possible": 1, "param_key": "max_velocity"},
    ],
    corpus_anchor=CorpusAnchor(
        paper="2024 Nov P1",
        question="10.1",
        marks=3,  # v(t) (1) + time at a=0 (1) + maximum velocity (1)
    ),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(registry=InMemoryRegistry({motion_calculus.id: motion_calculus}))

    def show(label, inst, *answers):
        attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
        r = inst.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  "
            f"is_correct={r.is_correct}"
        )

    for seed in range(3):
        inst = engine.instantiate(motion_calculus.id, seed=seed)
        p = inst.params
        print(f"=== seed {seed} ===")
        print(f"  {p['displacement_latex']}")
        print(
            f"  v(t) = {p['velocity']}   t* = {p['t_max']}   "
            f"v_max = {p['max_velocity']}"
        )
        show("all correct     ", inst, p["velocity"], p["t_max"], p["max_velocity"])
        show("v ok, wrong time", inst, p["velocity"], p["t_max"] + 1, p["max_velocity"])
