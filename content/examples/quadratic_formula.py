"""
Q1 Algebra, quadratic solved by formula — ``quadratic_formula``.

Solve  a·x² + b·x + c = 0  where the discriminant  D = b² − 4ac  is **positive
but not a perfect square**, so the quadratic does *not* factorise over the
integers and the quadratic formula is forced; the roots are irrational and
reported **correct to two decimal places**. This is the 2025 M/J P1 Q1.1.2
archetype (``3x² + 6x + 1 = 0``, 3 marks), a genuinely different skill from
``quadratic_factor`` (which is built to factorise into integer roots).

The answer decomposes into the two roots a marker reads off:

  1. the **smaller root** ``(−b − √D)/2a`` (``numeric_equality``, 1 mark), and
  2. the **larger root** ``(−b + √D)/2a`` (``numeric_equality``, 1 mark).

Each root is graded with a small absolute tolerance so a correctly-rounded 2-dp
answer (or a slightly more precise calculator decimal) is accepted — the
project's "accept calculator decimals for a numeric answer" rule. The paper's
3rd mark is the formula-substitution line, a method step with no verifier behind
it, marked by hand (see the ``auto_marks`` split in ``worksheets/paper.py``).

**Construction (forward, with rejection).** Draw a non-monic ``a`` and integer
``b, c``; keep only draws whose discriminant is positive and *not* a perfect
square (else it would factorise) and whose roots are exam-sized and distinct to
two decimals. No backward trick is possible here — irrational roots are the
whole point.
"""

from __future__ import annotations

import math
import random

from problem_instantiation_tool.schemas import CorpusAnchor, Problem


def _fmt_signed(coef: int, var: str) -> str:
    """A signed infix term like ' + 6x', ' - x', ' + 1' (empty when coef is 0)."""
    if coef == 0:
        return ""
    sign = "+" if coef > 0 else "-"
    mag = abs(coef)
    body = var if var and mag == 1 else f"{mag}{var}"
    return f" {sign} {body}"


def _gen(rng: random.Random) -> dict:
    while True:
        a = rng.randint(2, 5)
        b = rng.randint(-12, 12)
        c = rng.randint(-12, 12)
        disc = b * b - 4 * a * c
        if disc <= 0:
            continue
        root = math.isqrt(disc)
        if root * root == disc:
            continue  # perfect square → factorises → not a formula item
        sq = math.sqrt(disc)
        r_small = (-b - sq) / (2 * a)
        r_large = (-b + sq) / (2 * a)
        if abs(r_small) > 20 or abs(r_large) > 20:
            continue
        rs, rl = round(r_small, 2), round(r_large, 2)
        if rs == rl:
            continue  # must be distinct to two decimals
        break

    equation_latex = f"{a}x^2" + _fmt_signed(b, "x") + _fmt_signed(c, "") + " = 0"

    return {
        "a": a,
        "b": b,
        "c": c,
        "discriminant": disc,
        "root_small": rs,
        "root_large": rl,
        "equation_latex": equation_latex,
    }


quadratic_formula = Problem(
    id="quadratic_formula",
    type_id="quadratic_equation",
    name="Solve a non-factorisable quadratic by formula (roots to two decimals)",
    artifact_type="practice",
    problem_spec=_gen,
    verifier_spec=[
        {
            "kind": "numeric_equality",
            "marks_possible": 1,
            "param_key": "root_small",
            "tolerance": 0.01,
        },
        {
            "kind": "numeric_equality",
            "marks_possible": 1,
            "param_key": "root_large",
            "tolerance": 0.01,
        },
    ],
    corpus_anchor=CorpusAnchor(
        paper="2025 May/June P1",
        question="1.1.2",
        # marks left unset: the paper's 3rd mark is the formula-substitution line,
        # a method step with no verifier behind it. We grade the two roots (1 + 1).
    ),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(
        registry=InMemoryRegistry({quadratic_formula.id: quadratic_formula})
    )
    for seed in (0, 1, 2, 7):
        inst = engine.instantiate(quadratic_formula.id, seed=seed)
        p = inst.params
        print(f"=== seed {seed} ===")
        print(f"  Solve : {p['equation_latex']}   (D = {p['discriminant']})")
        print(f"  roots : {p['root_small']:.2f}, {p['root_large']:.2f}")
        attempt = SolutionAttempt(
            steps=[SubmittedStep(p["root_small"]), SubmittedStep(p["root_large"])]
        )
        r = inst.verifier.rate(attempt)
        print(f"  correct: {r.marks_awarded}/{r.marks_possible}  ok={r.is_correct}")
