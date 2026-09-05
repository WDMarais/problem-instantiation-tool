"""
Counting & probability — ``digit_count_exactly_one`` (the shared-stem Q11).

One range of three-digit numbers carries both sub-parts:

    11.1  How many numbers in [t00+1, 999] have exactly one digit equal to t?   (4)
    11.2  P(a number in the range does NOT satisfy 11.1)                        (3)

The range starts just above ``t00`` so the hundreds digit runs over {t, …, 9}. Counting
"exactly one t" over [t00, 999] and then removing ``t00`` itself (its digits are t,0,0 —
one t):

    H = t, T ≠ t, U ≠ t : 1 · 9 · 9        = 81
    H ≠ t, T = t, U ≠ t : (9−t) · 1 · 9    = 9(9−t)
    H ≠ t, T ≠ t, U = t : (9−t) · 9 · 1    = 9(9−t)
    count[t00,999] = 81 + 18(9−t);  remove t00  ⇒  answer_11_1 = 80 + 18(9−t)

For t = 5 this is 80 + 72 = 152, matching the source. The range holds
``total = 999 − 100t`` numbers, so the complement probability is

    answer_11_2 = (total − answer_11_1) / total.

Both answers are exact (integer count; SymPy ``Rational`` probability). This is a
COMPOUND (shared-stem) problem — one instance drives both sub-parts off the same ``t``
so 11.2's total and complement use the very count 11.1 asks for. Well-posed for every
``t``, so no F1 scope predicate.

Engine-graded canonical total = 2: the count (11.1) and the probability (11.2), one
mark each. The casework lines (11.1) and the total/complement setup (11.2) are
hand-marked method the engine cannot see behind the final values.
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

_T_CHOICES = (2, 3, 4, 5, 6, 7)  # target digit; range [t00+1, 999], hundreds ∈ {t..9}


def _gen(rng: random.Random) -> dict:
    t = rng.choice(_T_CHOICES)
    start = 100 * t + 1
    end = 999
    total = end - start + 1  # 999 − 100t
    count = 80 + 18 * (9 - t)  # exactly one t in [start, 999]
    prob_not = sympy.Rational(total - count, total)
    return {
        "t": t,
        "start": start,
        "end": end,
        "total": total,
        "answer_11_1": count,
        "answer_11_2": prob_not,
    }


digit_count_exactly_one = Problem(
    id="digit_count_exactly_one",
    type_id="digit_count_exactly_one",
    name="Three-digit numbers with exactly one given digit — count + complement",
    artifact_type="practice",
    problem_spec=_gen,
    verifier_spec=[
        {"kind": "numeric_equality", "marks_possible": 1, "param_key": "answer_11_1"},
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "answer_11_2"},
    ],
    corpus_anchor=CorpusAnchor(
        paper="2025 May/June P1",
        question="11",  # shared stem, 11.1 + 11.2
        marks=7,
    ),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(
        registry=InMemoryRegistry({digit_count_exactly_one.id: digit_count_exactly_one})
    )

    def _brute(t: int, start: int) -> int:
        return sum(1 for n in range(start, 1000) if str(n).count(str(t)) == 1)

    for seed in (1, 3, 5, 7):
        inst = engine.instantiate(digit_count_exactly_one.id, seed=seed)
        p = inst.params
        ok = _brute(p["t"], p["start"]) == p["answer_11_1"]
        print(
            f"seed {seed}: t={p['t']} range [{p['start']},999] "
            f"count={p['answer_11_1']} (brute ok={ok}) "
            f"P(not)={p['answer_11_2']} (~{float(p['answer_11_2']):.2f})"
        )
        attempt = SolutionAttempt(
            steps=[SubmittedStep(p["answer_11_1"]), SubmittedStep(p["answer_11_2"])]
        )
        r = inst.verifier.rate(attempt)
        print(f"  all-correct → {r.marks_awarded}/{r.marks_possible} ok={r.is_correct}")
