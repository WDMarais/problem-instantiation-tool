"""
Q1 Algebra Extensions, archetype 3 — ``exponential_equation``.

Solve  k^(2x) + b·k^x + c = 0  by the substitution  u = k^x.  The equation
becomes a quadratic  u² + b·u + c = 0; its roots are *candidate* substitution
values. But  k^x > 0  for every real x, so any **non-positive u is rejected**
before back-substituting  x = log_k(u).  The assessed skill is that guard plus
the variable-change round trip — not the quadratic algebra (that is
``quadratic_roots``, already built). So the answer is decomposed into the three
decisions a marker rewards:

  1. the **candidate u-values** — roots of the quadratic in u
     (``set_equality``, 2 marks, partial credit), and
  2. the **valid u-values** — those with u > 0, the rejection guard in isolation
     (``set_equality``, 1 mark), and
  3. the **x-roots** — back-substituted  x = log_k(u)  for each valid u
     (``set_equality``, 1 mark).

This extends the value-plus-reason shape of ``surd_equation`` with a *new* twist:
the final answer lives in a **different variable** than the candidates. Step 2 is
the surd-style subset guard (valid ⊆ candidate); step 3 is the back-substitution
that surd never needed (its candidates were already in x). See memory
``project-quadratic-inequality-region-signal``.

**Construction (backward, so u stays a clean power of k).** Pick a small base
k ∈ {2, 3, 5} and build a monic quadratic in u with known roots: a valid root
u₁ = k^m (m a small non-negative integer, so x = m is a clean integer) and, in
the teaching case, a rejected root u₂ ≤ 0. Then b = −(u₁+u₂), c = u₁·u₂ are
integers. The rejected root is drawn from {−5, …, 0} — non-positive, so it
exercises the full "u ≤ 0" rejection, not just "u < 0".

**The false-shortcut guard.** A rejected non-positive root is *always* smaller
than the valid positive one, so "reject the smaller root" would pass every
single-rejection item by accident. The generator therefore draws a both-valid
case (~30%) — two positive powers of k, *both* kept, two x-answers — so the
smaller root must sometimes be retained. Same honesty device as ``surd_equation``.
"""

from __future__ import annotations

import random

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

_BASES = (2, 3, 5)


def _fmt_terms(terms: list[tuple[int, str]]) -> str:
    """Render signed polynomial terms. ``terms`` is (coefficient, latex factor);
    an empty factor is the constant term. Leading sign is bare, later terms get
    an infix ``+``/``-``; unit coefficients on a factor drop the ``1``."""
    out = ""
    for i, (coef, factor) in enumerate(terms):
        if coef == 0:
            continue
        magnitude = abs(coef)
        if factor:
            # \cdot is mandatory: the factor is a power whose base is a digit, so
            # "2" + "2^{x}" would read as "22^{x}" without a separator.
            body = factor if magnitude == 1 else rf"{magnitude} \cdot {factor}"
        else:
            body = str(magnitude)
        if i == 0:
            out += f"-{body}" if coef < 0 else body
        else:
            out += f" {'-' if coef < 0 else '+'} {body}"
    return out


def _gen(rng: random.Random) -> dict:
    k = rng.choice(_BASES)

    if rng.random() < 0.7:
        # teaching case: one valid power of k, one rejected non-positive root.
        m = rng.randint(0, 2)
        u1 = k**m
        u2 = rng.randint(-5, 0)  # non-positive → rejected (k^x can't be ≤ 0)
        candidates = (u2, u1)
        valid = (u1,)
        x_roots = (m,)
    else:
        # both-valid case: two positive powers of k, both kept (two x-answers).
        m1, m2 = rng.sample(range(0, 3), 2)
        u1, u2 = k**m1, k**m2
        candidates = tuple(sorted((u1, u2)))
        valid = candidates
        x_roots = (m1, m2)

    b_coef = -(candidates[0] + candidates[1])
    c_coef = candidates[0] * candidates[1]

    equation_latex = (
        _fmt_terms([(1, f"{k}^{{2x}}"), (b_coef, f"{k}^{{x}}"), (c_coef, "")]) + " = 0"
    )

    rejected = tuple(u for u in candidates if u not in valid)

    return {
        "base": k,
        "b_coef": b_coef,
        "c_coef": c_coef,
        "candidate_u": frozenset(candidates),
        "valid_u": frozenset(valid),
        "rejected_u": frozenset(rejected),
        "x_roots": frozenset(x_roots),
        "equation_latex": equation_latex,
    }


exponential_equation = Problem(
    id="exponential_equation",
    type_id="exponential_equation",
    name="Solve k^(2x)+b·k^x+c=0 via u=k^x (reject u≤0, then back-substitute)",
    artifact_type="practice",
    problem_spec=_gen,
    verifier_spec=[
        {"kind": "set_equality", "marks_possible": 2, "param_key": "candidate_u"},
        {"kind": "set_equality", "marks_possible": 1, "param_key": "valid_u"},
        {"kind": "set_equality", "marks_possible": 1, "param_key": "x_roots"},
    ],
    corpus_anchor=CorpusAnchor(
        paper="2025 Nov P1",
        question="1.1.4",
        marks=4,  # solve quadratic in u (2) + reject u≤0 (1) + back-substitute (1)
    ),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(
        registry=InMemoryRegistry({exponential_equation.id: exponential_equation})
    )

    def show(label, inst, *answers):
        attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
        r = inst.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  "
            f"is_correct={r.is_correct}"
        )

    for seed in (1, 3, 5):
        inst = engine.instantiate(exponential_equation.id, seed=seed)
        p = inst.params
        print(f"=== seed {seed} ===")
        print(f"  Solve     : {p['equation_latex']}")
        print(f"  Candidates: {sorted(p['candidate_u'])}   base={p['base']}")
        print(
            f"  Valid u   : {sorted(p['valid_u'])}   "
            f"Rejected: {sorted(p['rejected_u'])}   x: {sorted(p['x_roots'])}"
        )
        show(
            "Solve+reject+back-sub",
            inst,
            p["candidate_u"],
            p["valid_u"],
            p["x_roots"],
        )
        show(
            "Forgot to reject u≤0 ",
            inst,
            p["candidate_u"],
            p["candidate_u"],
            p["x_roots"],
        )
