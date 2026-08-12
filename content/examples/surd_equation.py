"""
Q1 Algebra Extensions, archetype 2 — ``surd_equation``.

Solve  √(a·x + b) = s·x + c  (s = ±1).  Squaring both sides is a *non-reversible*
step: it can manufacture roots that solve the squared quadratic but not the
original equation (because a principal square root is non-negative, so the RHS
must be too). The assessed skill is therefore **extraneous-root rejection** — not
the algebra of solving the quadratic. So the answer is decomposed into:

  1. the **candidate roots** — the roots of the squared quadratic
     (``set_equality``, 2 marks, partial credit), and
  2. the **valid roots** — those that survive the check against the original
     (``set_equality``, 1 mark) — the rejection skill in isolation.

This is the same value-plus-reason shape as ``quadratic_inequality``: step 2 is a
*structural reason* (did this candidate survive the check?) that a plain value
verifier can't express. See memory ``project-quadratic-inequality-region-signal``.

**Construction (backward, so squaring stays clean).** Pick integer candidate
roots p < q and build the equation to have exactly them: from
√(a·x+b) = s·x+c, squaring gives x² + (2sc−a)x + (c²−b) = 0, so setting that to
(x−p)(x−q) fixes a = 2sc + p + q and b = c² − pq. Every candidate then satisfies
a·t+b = (s·t+c)² by construction, so the surd is always defined, and a root is
valid **iff s·t + c ≥ 0** (the RHS is non-negative). The RHS sign s is drawn ±1
so the extraneous root is the smaller one as often as the larger — squaring
teaches no "reject the smaller root" shortcut.
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

_x = sympy.Symbol("x")


def _gen(rng: random.Random) -> dict:
    while True:
        p = rng.randint(-6, 6)
        q = rng.randint(-6, 6)
        if p == q:
            continue
        p, q = sorted((p, q))
        s = rng.choice([1, -1])

        # 70% one extraneous (the teaching case), 30% both valid.
        if rng.random() < 0.7:
            # exactly one of s·p+c, s·q+c is negative
            c_range = range(-q, -p) if s == 1 else range(p, q)
        else:
            c_range = range(-p, -p + 5) if s == 1 else range(q, q + 5)
        c = rng.choice(list(c_range))

        a = 2 * s * c + p + q
        b = c * c - p * q
        if a == 0:
            continue  # √(constant) = line is degenerate, not a surd equation

        candidates = (p, q)
        valid = tuple(t for t in candidates if s * t + c >= 0)
        if not valid:
            continue  # keep a non-empty solution set for this first cut
        break

    inner = a * _x + b
    rhs = s * _x + c
    extraneous = tuple(t for t in candidates if t not in valid)

    return {
        "a": a,
        "b": b,
        "c": c,
        "s": s,
        "candidate_roots": frozenset(candidates),
        "valid_roots": frozenset(valid),
        "extraneous_roots": frozenset(extraneous),
        "equation_latex": rf"\sqrt{{{sympy.latex(inner)}}} = {sympy.latex(rhs)}",
    }


surd_equation = Problem(
    id="surd_equation",
    type_id="surd_equation",
    name="Solve a surd equation √(ax+b)=±x+c (solve + reject extraneous roots)",
    artifact_type="practice",
    problem_spec=_gen,
    verifier_spec=[
        {"kind": "set_equality", "marks_possible": 2, "param_key": "candidate_roots"},
        {"kind": "set_equality", "marks_possible": 1, "param_key": "valid_roots"},
    ],
    corpus_anchor=CorpusAnchor(
        paper="2024 Nov P1",
        question="1.1.5",
        # marks left unset: the paper's 4th mark is the squaring-setup method line,
        # which an answer-grading engine can't allocate until Level-2 per-line marks
        # land (deferred). We grade the two answer-values: candidates (2) + valid (1).
    ),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(registry=InMemoryRegistry({surd_equation.id: surd_equation}))

    def show(label, inst, *answers):
        attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
        r = inst.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  "
            f"is_correct={r.is_correct}"
        )

    for seed in (2, 4, 5):
        inst = engine.instantiate(surd_equation.id, seed=seed)
        p = inst.params
        print(f"=== seed {seed} ===")
        print(f"  Solve     : {p['equation_latex']}")
        print(f"  Candidates: {sorted(p['candidate_roots'])}")
        print(
            f"  Valid     : {sorted(p['valid_roots'])}   "
            f"Extraneous: {sorted(p['extraneous_roots'])}"
        )
        show("Solve + reject correctly", inst, p["candidate_roots"], p["valid_roots"])
        show(
            "Forgot to reject        ",
            inst,
            p["candidate_roots"],
            p["candidate_roots"],
        )
