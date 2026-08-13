"""
Q1 Algebra Extensions, archetype 5 — ``discriminant_nature``.

Given  a·x² + b·x + c = 0, compute the discriminant  Δ = b² − 4ac  and classify
the **nature of the roots**. The assessed skill is the classification itself —
reading Δ's sign, and (when Δ > 0) whether it is a perfect square — not solving
the quadratic. So the answer is decomposed into the two decisions a marker
rewards:

  1. the **discriminant value** Δ = b² − 4ac
     (``numeric_equality``, 1 mark), and
  2. the **nature** — one of four categories (``exact_equality``, 1 mark):
       ``non_real``                 (Δ < 0),
       ``real_equal``               (Δ = 0),
       ``real_unequal_rational``    (Δ > 0 and a perfect square),
       ``real_unequal_irrational``  (Δ > 0, not a perfect square).

This is the same value-plus-categorical-reason shape as ``quadratic_inequality``,
but the reason side is now a **four-way taxonomy with internal structure** (a
decision tree: sign first, then perfect-square) rather than a binary label. See
memory ``project-quadratic-inequality-region-signal``.

**Construction.** Each nature is built to order — rational/equal from integer
roots (``a·(x−p)(x−q)`` / ``a·(x−r)²``), non-real/irrational from a vertex form
``a·(x−h)² + v`` whose sign of ``a·v`` fixes the sign of Δ = −4av. The nature
*label*, though, is always re-derived from the actually-computed Δ (the single
source of truth), and the draw is retried until it matches the target — so a
construction slip can never mislabel an instance, only reject it.
"""

from __future__ import annotations

import math
import random

import sympy

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

_x = sympy.Symbol("x")

_NATURES = (
    "non_real",
    "real_equal",
    "real_unequal_rational",
    "real_unequal_irrational",
)


def _nature_of(a: int, b: int, c: int) -> str:
    """Classify the roots of a·x²+b·x+c from the discriminant alone."""
    disc = b * b - 4 * a * c
    if disc < 0:
        return "non_real"
    if disc == 0:
        return "real_equal"
    root = math.isqrt(disc)
    if root * root == disc:
        return "real_unequal_rational"
    return "real_unequal_irrational"


def _candidate(rng: random.Random, target: str) -> tuple[int, int, int]:
    a = rng.choice([-2, -1, 1, 2])
    if target == "real_unequal_rational":
        p = rng.randint(-5, 5)
        q = rng.randint(-5, 5)
        while q == p:
            q = rng.randint(-5, 5)
        b = -a * (p + q)
        c = a * p * q
    elif target == "real_equal":
        r = rng.randint(-5, 5)
        b = -2 * a * r
        c = a * r * r
    else:
        # vertex form a·(x−h)² + v → b = −2ah, c = a·h² + v, Δ = −4·a·v.
        h = rng.randint(-4, 4)
        m = rng.choice([1, 2, 3, 5, 6, 7])  # |v|; non-square magnitudes matter below
        # non_real wants a·v > 0 (Δ<0); irrational wants a·v < 0 (Δ>0, non-square).
        v = (
            m * (1 if a > 0 else -1)
            if target == "non_real"
            else m * (-1 if a > 0 else 1)
        )
        b = -2 * a * h
        c = a * h * h + v
    return a, b, c


def _gen(rng: random.Random) -> dict:
    target = rng.choice(_NATURES)
    while True:
        a, b, c = _candidate(rng, target)
        if a != 0 and _nature_of(a, b, c) == target:
            break

    disc = b * b - 4 * a * c
    quadratic = a * _x**2 + b * _x + c

    return {
        "a": a,
        "b": b,
        "c": c,
        "discriminant": disc,
        "nature": target,
        "quadratic_latex": sympy.latex(sympy.Eq(quadratic, 0)),
    }


discriminant_nature = Problem(
    id="discriminant_nature",
    type_id="discriminant_nature",
    name="Classify the nature of a quadratic's roots via the discriminant Δ=b²−4ac",
    artifact_type="practice",
    problem_spec=_gen,
    verifier_spec=[
        {"kind": "numeric_equality", "marks_possible": 1, "param_key": "discriminant"},
        {
            "kind": "exact_equality",
            "marks_possible": 1,
            "param_key": "nature",
            "normalize": ["whitespace"],
        },
    ],
    corpus_anchor=CorpusAnchor(
        paper="2025 May/June P1",
        question="5.2",
        marks=2,  # compute Δ (1) + state the nature (1)
    ),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(
        registry=InMemoryRegistry({discriminant_nature.id: discriminant_nature})
    )

    def show(label, inst, *answers):
        attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
        r = inst.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  "
            f"is_correct={r.is_correct}"
        )

    seen: set[str] = set()
    seed = 0
    while len(seen) < 4 and seed < 60:
        inst = engine.instantiate(discriminant_nature.id, seed=seed)
        p = inst.params
        if p["nature"] not in seen:
            seen.add(p["nature"])
            print(f"=== seed {seed} ({p['nature']}) ===")
            print(f"  Classify : {p['quadratic_latex']}")
            print(f"  Δ = {p['discriminant']}")
            show("Δ + nature correct ", inst, p["discriminant"], p["nature"])
            show("Nature right, Δ wrong", inst, p["discriminant"] + 1, p["nature"])
        seed += 1
