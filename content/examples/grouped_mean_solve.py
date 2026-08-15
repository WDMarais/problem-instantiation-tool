"""
Statistics, archetype 3 — ``grouped_mean_solve``.

Given a grouped frequency table with one **unknown frequency k** and the stated
**estimated mean** x̄, find k. The estimated mean of grouped data is
x̄ = Σ(f·midpoint) / Σf, so with one frequency unknown this is a single linear
equation in k:

    (Σ_known f·m + k·m_j) / (Σ_known f + k) = x̄   ⇒
    k = (x̄·Σ_known f − Σ_known f·m) / (m_j − x̄).

One gradable answer — the whole-number frequency k. Unlike regression/mean-σ this
is an algebra skill, not a calculator read-off, so k is graded as an exact
integer (no tolerance).

**Construction** is backward and semantically constrained: choose an integer
target mean and integer known frequencies, then keep only draws where k comes out
a positive integer. That is not cosmetic rounding — a frequency *is* a count, so
a non-integer k would be a broken problem, exactly the way a vertical line breaks
the gradient archetypes. The class of the unknown never has midpoint equal to x̄
(that would divide by zero).
"""

from __future__ import annotations

import random

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

# Class midpoints (width-10 intervals: 10<x≤20 → 15, 20<x≤30 → 25, …).
_MIDPOINTS = [15, 25, 35, 45, 55]


def _gen(rng: random.Random) -> dict:
    c = len(_MIDPOINTS)
    while True:
        xbar = rng.randint(28, 45)  # a whole-number estimated mean, mid-span
        j = rng.randrange(c)  # the class with the unknown frequency
        if _MIDPOINTS[j] == xbar:  # would divide by zero
            continue

        known = {i: rng.randint(3, 20) for i in range(c) if i != j}
        sum_f = sum(known.values())
        sum_fm = sum(f * _MIDPOINTS[i] for i, f in known.items())

        num = xbar * sum_f - sum_fm
        den = _MIDPOINTS[j] - xbar
        if num % den != 0:
            continue
        k = num // den
        if not (1 <= k <= 40):  # a sensible, positive whole frequency
            continue
        break

    frequencies = [known.get(i) for i in range(c)]  # None at the unknown class
    frequencies[j] = None

    lo = [m - 5 for m in _MIDPOINTS]
    hi = [m + 5 for m in _MIDPOINTS]
    rows = " \\\\ ".join(
        f"{lo[i]}<x\\le {hi[i]} & {'k' if i == j else frequencies[i]}" for i in range(c)
    )
    table_latex = (
        r"\begin{array}{c|c}\text{interval} & f \\ \hline " + rows + r"\end{array}"
    )

    return {
        "midpoints": _MIDPOINTS,
        "frequencies": frequencies,  # None marks the unknown class
        "unknown_index": j,
        "mean_given": xbar,
        "unknown_frequency": k,
        "table_latex": table_latex,
    }


grouped_mean_solve = Problem(
    id="grouped_mean_solve",
    type_id="grouped_mean_solve",
    name="Unknown frequency in a grouped table from the estimated mean",
    artifact_type="practice",
    problem_spec=_gen,
    verifier_spec=[
        {
            "kind": "numeric_equality",
            "marks_possible": 1,
            "param_key": "unknown_frequency",
        },
    ],
    corpus_anchor=CorpusAnchor(
        paper="2023 Nov P2",
        question="2.4",  # find k from the estimated mean
        # the paper scores 4 method marks (set up Σfm, form the equation, solve);
        # our answer-level scheme grades the single value k, so marks left unset.
    ),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(
        registry=InMemoryRegistry({grouped_mean_solve.id: grouped_mean_solve})
    )

    def show(label, inst, *answers):
        attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
        r = inst.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  "
            f"is_correct={r.is_correct}"
        )

    for seed in range(4):
        inst = engine.instantiate(grouped_mean_solve.id, seed=seed)
        p = inst.params
        j = p["unknown_index"]
        shown = [("k" if i == j else p["frequencies"][i]) for i in range(5)]
        print(f"=== seed {seed} ===")
        print(f"  midpoints : {p['midpoints']}")
        print(f"  freqs     : {shown}   mean = {p['mean_given']}")
        print(f"  k = {p['unknown_frequency']}")
        show("correct k", inst, p["unknown_frequency"])
        # forgetting to include k in Σf (dividing by Σ_known f only) → wrong k
        show("wrong k  ", inst, p["unknown_frequency"] + 2)
