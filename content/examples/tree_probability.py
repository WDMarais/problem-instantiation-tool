"""
Probability, tree diagrams — ``tree_probability`` (P1 Q10.2).

Two-stage experiments where branch probabilities multiply along a path and paths
to the same outcome add (the law of total probability):

- ``tree_total_probability`` — a first stage picks one of two branches with
  probability p / (1−p); a second stage succeeds with conditional probability
  q1 / q2. Find P(success) = p·q1 + (1−p)·q2.
- ``tree_draw_both``  — a bag holds r of one colour and s of another; two are
  drawn **without replacement**. Find P(both the named colour)
  = (r/N)·((r−1)/(N−1)).
- ``tree_draw_one_each`` — same bag; find P(one of each colour)
  = 2·r·s / (N·(N−1)).

The without-replacement draws are the classic tree question: the second branch's
probability depends on the first (the denominator drops from N to N−1). Counts are
kept small (N ≤ 9) so the whole ordered sample space (≤ 72 outcomes) can be
enumerated in the test as an independent check.

``total_probability`` draws its probabilities from a terminating-decimal pool so
p·q1 + (1−p)·q2 lands on an exact calculator value; ``symbolic_equality`` then
accepts the fraction or the decimal. All stored values are SymPy ``Rational``.
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

# Terminating-decimal probabilities (denominators in {2,4,5,10}); products and
# sums terminate too, so the total-probability answer is an exact decimal.
_NICE_P: tuple[sympy.Rational, ...] = (
    sympy.Rational(1, 4),
    sympy.Rational(1, 2),
    sympy.Rational(3, 4),
    sympy.Rational(1, 5),
    sympy.Rational(2, 5),
    sympy.Rational(3, 5),
    sympy.Rational(4, 5),
    sympy.Rational(3, 10),
    sympy.Rational(7, 10),
)

# (item plural, colour A, colour B) — display only; the maths is r of one kind,
# s of another. Never read by the verifier.
_BAG_CONTEXTS: tuple[tuple[str, str, str], ...] = (
    ("sweets", "red", "green"),
    ("marbles", "blue", "white"),
    ("chocolates", "milk", "dark"),
    ("pens", "black", "blue"),
    ("beads", "yellow", "red"),
)

_STAGE_CONTEXTS: tuple[tuple[str, str, str], ...] = (
    ("bag", "red ball", "picking a bag then drawing a ball"),
    ("route", "arriving on time", "choosing a route then arriving"),
    ("machine", "a working unit", "a unit coming off one of two machines"),
)


def _gen_total_probability(rng: random.Random) -> dict:
    p = rng.choice(_NICE_P)  # P(first branch)
    q1 = rng.choice(_NICE_P)  # P(success | first branch)
    q2 = rng.choice(_NICE_P)  # P(success | second branch)
    stage_noun, outcome, setting = rng.choice(_STAGE_CONTEXTS)
    return {
        "p_branch1": p,
        "p_success_given1": q1,
        "p_success_given2": q2,
        "stage_noun": stage_noun,
        "outcome": outcome,
        "setting": setting,
        "answer": p * q1 + (1 - p) * q2,  # law of total probability
    }


def _draw_context(rng: random.Random):
    item, colour_a, colour_b = rng.choice(_BAG_CONTEXTS)
    r = rng.randint(2, 5)  # count of colour A
    s = rng.randint(2, 5)  # count of colour B
    n = r + s
    return item, colour_a, colour_b, r, s, n


def _gen_draw_both(rng: random.Random) -> dict:
    item, colour_a, colour_b, r, s, n = _draw_context(rng)
    # target the more or less numerous colour at random, for variety
    if rng.random() < 0.5:
        target, t = colour_a, r
    else:
        target, t = colour_b, s
    return {
        "item": item,
        "colour_a": colour_a,
        "colour_b": colour_b,
        "count_a": r,
        "count_b": s,
        "n_total": n,
        "target_colour": target,
        # P(both target) drawing two without replacement
        "answer": sympy.Rational(t, n) * sympy.Rational(t - 1, n - 1),
    }


def _gen_draw_one_each(rng: random.Random) -> dict:
    item, colour_a, colour_b, r, s, n = _draw_context(rng)
    return {
        "item": item,
        "colour_a": colour_a,
        "colour_b": colour_b,
        "count_a": r,
        "count_b": s,
        "n_total": n,
        # P(one of each) = both orders: (r/N)(s/(N−1)) + (s/N)(r/(N−1))
        "answer": 2 * sympy.Rational(r * s, n * (n - 1)),
    }


tree_total_probability = Problem(
    id="tree_total_probability",
    type_id="tree_probability",
    name="Total probability across a two-stage tree (p·q1 + (1−p)·q2)",
    artifact_type="practice",
    problem_spec=_gen_total_probability,
    verifier_spec={"kind": "symbolic_equality", "marks_possible": 1},
    corpus_anchor=CorpusAnchor(paper="2023 Nov P1", question="10.2.2"),
)

tree_draw_both = Problem(
    id="tree_draw_both",
    type_id="tree_probability",
    name="P(both the same named colour) drawing two without replacement",
    artifact_type="practice",
    problem_spec=_gen_draw_both,
    verifier_spec={"kind": "symbolic_equality", "marks_possible": 1},
    corpus_anchor=CorpusAnchor(paper="2023 Nov P1", question="10.2.2"),
)

tree_draw_one_each = Problem(
    id="tree_draw_one_each",
    type_id="tree_probability",
    name="P(one of each colour) drawing two without replacement",
    artifact_type="practice",
    problem_spec=_gen_draw_one_each,
    verifier_spec={"kind": "symbolic_equality", "marks_possible": 1},
    corpus_anchor=CorpusAnchor(paper="2023 Nov P1", question="10.2.2"),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    problems = {
        p.id: p for p in [tree_total_probability, tree_draw_both, tree_draw_one_each]
    }
    engine = Engine(registry=InMemoryRegistry(problems))

    def show(label, inst, answer):
        attempt = SolutionAttempt(steps=[SubmittedStep(answer)])
        r = inst.verifier.rate(attempt)
        print(f"  {label}: {r.marks_awarded}/{r.marks_possible}  ok={r.is_correct}")

    inst = engine.instantiate("tree_total_probability", seed=4)
    p = inst.params
    ans = inst.verifier.canonicals[0]
    print(
        f"=== tree_total_probability ===  p={p['p_branch1']} "
        f"q1={p['p_success_given1']} q2={p['p_success_given2']}  answer={ans}"
    )
    show("correct (rational)", inst, ans)
    show("correct (decimal) ", inst, str(float(ans)))
    print()

    for pid in ("tree_draw_both", "tree_draw_one_each"):
        inst = engine.instantiate(pid, seed=4)
        p = inst.params
        ans = inst.verifier.canonicals[0]
        tail = (
            f"target={p['target_colour']}" if pid == "tree_draw_both" else "one of each"
        )
        print(
            f"=== {pid} ===  {p['count_a']} {p['colour_a']} + "
            f"{p['count_b']} {p['colour_b']}  ({tail})  answer={ans}"
        )
        show("correct           ", inst, ans)
        # the classic slip: drawing *with* replacement (denominator stays N)
        n = p["n_total"]
        if pid == "tree_draw_both":
            t = p["count_a"] if p["target_colour"] == p["colour_a"] else p["count_b"]
            with_repl = sympy.Rational(t, n) ** 2
        else:
            with_repl = 2 * sympy.Rational(p["count_a"] * p["count_b"], n * n)
        show("with replacement ✗", inst, with_repl)
        print()
