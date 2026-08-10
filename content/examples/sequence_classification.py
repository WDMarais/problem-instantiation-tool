"""
Identify-the-sequence-type — the classification atom.

Every *labelled* sequences problem ("the arithmetic sequence …") hands the
student the classification for free. But solving a sequence problem is really
``classify ∘ apply-method``: you must first decide arithmetic vs geometric to
know whether to reach for ``a, d`` or ``a, r``. This problem drills the first
half in isolation — present four terms, ask which kind of sequence it is.

Answer space is arithmetic / geometric / quadratic / neither. ``quadratic`` is a
constant, non-zero *second* difference — the discriminator you reach for once first
differences turn out not to be constant. ``neither`` is sampled as a *near-miss* —
an arithmetic run with one term nudged off — so the discriminator actually has to
be applied to every gap, not eyeballed from the first two. It is rejection-checked
to be none of the *named* types: not arithmetic (constant first difference), not
geometric (constant ratio), and not quadratic (constant second difference).
"""

from __future__ import annotations

import random
from fractions import Fraction

from problem_instantiation_tool.schemas import Problem

TYPES = ("arithmetic", "geometric", "quadratic", "neither")


def first_differences(terms: list[int]) -> list[int]:
    return [terms[i + 1] - terms[i] for i in range(len(terms) - 1)]


def is_arithmetic(terms: list[int]) -> bool:
    """Constant first difference (includes d=0 — a constant sequence)."""
    return len(set(first_differences(terms))) == 1


def is_geometric(terms: list[int]) -> bool:
    """Constant ratio. A term of 0 makes the ratio undefined → not geometric."""
    if any(x == 0 for x in terms):
        return False
    ratios = [Fraction(terms[i + 1], terms[i]) for i in range(len(terms) - 1)]
    return len(set(ratios)) == 1


def is_quadratic(terms: list[int]) -> bool:
    """Constant, non-zero second difference (a genuine quadratic sequence)."""
    d2 = first_differences(first_differences(terms))
    return len(set(d2)) == 1 and d2[0] != 0


_D_CHOICES = [d for d in range(-9, 10) if d != 0]
_A_GEO = [a for a in range(-6, 7) if a != 0]
_R_CHOICES = (-3, -2, 2, 3)
_PERTURB = (-3, -2, 2, 3)
_QUAD_A = (-2, -1, 1, 2, 3)  # a ≠ 0 ⇒ genuine quadratic (non-constant 1st diff)


def _arithmetic_terms(rng: random.Random) -> list[int]:
    a = rng.randint(-12, 12)
    d = rng.choice(_D_CHOICES)
    return [a + i * d for i in range(4)]


def _geometric_terms(rng: random.Random) -> list[int]:
    a = rng.choice(_A_GEO)
    r = rng.choice(_R_CHOICES)
    return [a * r**i for i in range(4)]


def _quadratic_terms(rng: random.Random) -> list[int]:
    """Tₙ = an² + bn + c with a ≠ 0 — constant, non-zero second difference (2a).
    Rejection-checked so the draw isn't also geometric (a term of 0 or a coincident
    ratio) and shows at least three distinct terms."""
    for _ in range(200):
        a = rng.choice(_QUAD_A)
        b = rng.randint(-6, 6)
        c = rng.randint(-6, 6)
        terms = [a * n * n + b * n + c for n in range(1, 5)]
        if is_geometric(terms):
            continue
        if len(set(terms)) < 3:
            continue
        return terms
    raise RuntimeError(  # pragma: no cover - sampler practically never exhausts
        "could not sample a 'quadratic' sequence in 200 tries"
    )


def _neither_terms(rng: random.Random) -> list[int]:
    """An arithmetic run with one interior/last term nudged off — plausible to the
    eye, but none of arithmetic/geometric/quadratic. Rejection-sampled."""
    for _ in range(200):
        a = rng.randint(-8, 10)
        d = rng.choice(_D_CHOICES)
        terms = [a + i * d for i in range(4)]
        idx = rng.randint(1, 3)
        terms[idx] += rng.choice(_PERTURB)
        if is_arithmetic(terms) or is_geometric(terms) or is_quadratic(terms):
            continue
        if len(set(terms)) < 3:
            continue
        return terms
    raise RuntimeError(  # pragma: no cover - sampler practically never exhausts
        "could not sample a 'neither' sequence in 200 tries"
    )


_BUILDERS = {
    "arithmetic": _arithmetic_terms,
    "geometric": _geometric_terms,
    "quadratic": _quadratic_terms,
    "neither": _neither_terms,
}


def _gen_classify(rng: random.Random) -> dict:
    kind = rng.choice(TYPES)
    terms = _BUILDERS[kind](rng)
    return {
        "t1": terms[0],
        "t2": terms[1],
        "t3": terms[2],
        "t4": terms[3],
        "answer": kind,
    }


identify_sequence_type = Problem(
    id="identify_sequence_type",
    type_id="sequence_classification",
    name="Identify whether a sequence is arithmetic, geometric or neither",
    artifact_type="practice",
    problem_spec=_gen_classify,
    verifier_spec={"kind": "exact_equality", "marks_possible": 1},
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(
        registry=InMemoryRegistry({identify_sequence_type.id: identify_sequence_type})
    )
    for seed in range(8):
        inst = engine.instantiate(identify_sequence_type.id, seed=seed)
        p = inst.params
        terms = [p["t1"], p["t2"], p["t3"], p["t4"]]
        r = inst.verifier.rate(SolutionAttempt(steps=[SubmittedStep(p["answer"])]))
        print(f"{terms}  → {p['answer']:<10}  ok={r.is_correct}")
