"""
Probability, counting principle — ``counting_arrangements`` (P1 Q10.3).

Arrangements of ``n`` **distinct** objects in a row, graded as a single exact
integer. Three variants exercise the fundamental counting principle and the two
classic restriction techniques:

- ``counting_all``          — every arrangement:            n!
- ``counting_together``     — a named block of k stays together:  k!·(n−k+1)!
- ``counting_not_together`` — a named pair is never adjacent:      n! − 2·(n−1)!

The ``together`` count treats the k designated objects as one unit — (n−k+1)
units permute in (n−k+1)! ways, and the block permutes internally in k! ways. The
``not_together`` count is the complement of the two-object block (k = 2).

The objects are distinct, so there are no repeated-letter divisions to worry
about; the arithmetic is pure factorial. ``n`` is kept in [5, 8] so the answers
are exam-plausible and — the point of the test — an exhaustive
``itertools.permutations`` enumeration (≤ 8! = 40 320) can re-derive every count
by a completely different method than the closed form used here.

Nothing is clamped for cosmetics: ``n`` spans its whole band and the answer is
whatever the factorials give.
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

# Display-only framings — the maths is "n distinct objects in a row" regardless.
# (noun singular/plural, setting phrase). Pure surface variety, like the vertex
# namings in parallelogram_angles; never read by the verifier.
_CONTEXTS: tuple[tuple[str, str, str], ...] = (
    ("book", "books", "on a shelf"),
    ("learner", "learners", "in a row for a photograph"),
    ("car", "cars", "in a parking row"),
    ("trophy", "trophies", "on a display shelf"),
    ("friend", "friends", "on a bench"),
)

# Distinct single-object labels drawn without replacement (read as names/tags in
# the prose). O/I excluded (read as 0/1); enough for the max n = 8.
_LABELS = ("A", "B", "C", "D", "E", "F", "G", "H", "J", "K", "L", "M")


def _fact(k: int) -> sympy.Integer:
    return sympy.factorial(k)


def _gen_all(rng: random.Random) -> dict:
    n = rng.randint(5, 8)
    noun_sg, noun_pl, setting = rng.choice(_CONTEXTS)
    return {
        "n": n,
        "restriction": "all",
        "labels": list(rng.sample(_LABELS, n)),
        "noun_singular": noun_sg,
        "noun_plural": noun_pl,
        "setting": setting,
        "answer": _fact(n),
    }


def _gen_together(rng: random.Random) -> dict:
    n = rng.randint(5, 8)
    k = rng.randint(2, 3)  # size of the block that must stay together
    noun_sg, noun_pl, setting = rng.choice(_CONTEXTS)
    labels = list(rng.sample(_LABELS, n))
    return {
        "n": n,
        "restriction": "together",
        "block_size": k,
        "labels": labels,
        "designated": labels[:k],  # these k must be adjacent, in any order
        "noun_singular": noun_sg,
        "noun_plural": noun_pl,
        "setting": setting,
        "answer": _fact(k) * _fact(n - k + 1),
    }


def _gen_not_together(rng: random.Random) -> dict:
    n = rng.randint(5, 8)
    noun_sg, noun_pl, setting = rng.choice(_CONTEXTS)
    labels = list(rng.sample(_LABELS, n))
    return {
        "n": n,
        "restriction": "not_together",
        "labels": labels,
        "designated": labels[:2],  # these two must never be adjacent
        "noun_singular": noun_sg,
        "noun_plural": noun_pl,
        "setting": setting,
        "answer": _fact(n) - 2 * _fact(n - 1),  # total − (pair together)
    }


def _spec() -> list[dict]:
    return [{"kind": "numeric_equality", "marks_possible": 1, "param_key": "answer"}]


counting_all = Problem(
    id="counting_all",
    type_id="counting_arrangements",
    name="Total arrangements of distinct objects in a row (n!)",
    artifact_type="practice",
    problem_spec=_gen_all,
    verifier_spec=_spec(),
    corpus_anchor=CorpusAnchor(
        paper="2023 Nov P1",
        question="10.3.1",
        # answer-mark only; the exam's method/answer split is left unset.
    ),
)

counting_together = Problem(
    id="counting_together",
    type_id="counting_arrangements",
    name="Arrangements with a named block kept together (k!·(n−k+1)!)",
    artifact_type="practice",
    problem_spec=_gen_together,
    verifier_spec=_spec(),
    corpus_anchor=CorpusAnchor(
        paper="2023 Nov P1",
        question="10.3.2",
    ),
)

counting_not_together = Problem(
    id="counting_not_together",
    type_id="counting_arrangements",
    name="Arrangements with a named pair never adjacent (n! − 2·(n−1)!)",
    artifact_type="practice",
    problem_spec=_gen_not_together,
    verifier_spec=_spec(),
    corpus_anchor=CorpusAnchor(
        paper="2023 Nov P1",
        question="10.3.2",
    ),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    problems = {
        p.id: p for p in [counting_all, counting_together, counting_not_together]
    }
    engine = Engine(registry=InMemoryRegistry(problems))

    def show(label, inst, answer):
        attempt = SolutionAttempt(steps=[SubmittedStep(answer)])
        r = inst.verifier.rate(attempt)
        print(f"  {label}: {r.marks_awarded}/{r.marks_possible}  ok={r.is_correct}")

    for pid in problems:
        inst = engine.instantiate(pid, seed=3)
        p = inst.params
        ans = int(p["answer"])
        extra = ""
        if p["restriction"] != "all":
            extra = f"  designated={p['designated']}"
        print(f"=== {pid} ===  n={p['n']}  labels={p['labels']}{extra}")
        print(f"  answer = {ans}")
        show("correct", inst, ans)
        # the classic slip: forgetting the internal block permutation (drop k!)
        if p["restriction"] == "together":
            show("forgot k! block perm", inst, int(_fact(p["n"] - p["block_size"] + 1)))
        # or answering the *total* when a restriction was asked
        if p["restriction"] != "all":
            show("ignored restriction (n!)", inst, int(_fact(p["n"])))
