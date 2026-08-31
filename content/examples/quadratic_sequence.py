"""
Reference example: quadratic sequence — Tₙ = an² + bn + c.

Mirrors arithmetic_sequence.py / geometric_sequence.py in structure (one Problem
per exam sub-competency, symbolic_equality throughout). The defining property is a
*constant, non-zero second difference* equal to 2a; every method below is that fact
applied.

Six archetypes:
- next_terms: extend the pattern using the constant second difference alone — the
  introductory skill, needs no closed form.
- nth_term_formula: the load-bearing one. From four terms recover a, b, c via
  2a = (second difference), 3a + b = (first first-difference), a + b + c = T₁.
  The canonical is a SymPy expression in n; symbolic_equality accepts any
  algebraically equivalent form.
- find_term: a specific larger term T_k — the student must derive the closed form
  first, then substitute (numeric answer).
- find_n: which term equals a given value — solve a quadratic in n. Draws are
  constrained (a > 0, b ≥ 0) so the sequence is strictly increasing for n ≥ 1;
  the parabola's other root is then negative and the positive integer term index
  is unique (no ± ambiguity for the student to adjudicate).
- consecutive_diff: two consecutive terms differ by a given D — set the (linear)
  first-difference 2an + (a+b) = D, solve the single index n, then evaluate the
  larger term T_{n+1}. The 2025 M/J P1 Q3.2 archetype.
- shift_negative: add m to every term; find the m-range that makes only the
  interior window negative. Answer is a half-open interval, graded by the
  set_solution kind. The 2025 M/J P1 Q3.3 archetype.
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

_n = sympy.Symbol("n")

# a ≠ 0 (else it is not quadratic); kept small so 2a and the printed terms stay
# legible on a page. b, c span both signs for variety.
_A_RANGE = [-2, -1, 1, 2, 3]
_B_RANGE = list(range(-6, 7))
_C_RANGE = list(range(-6, 7))


def _terms(a: int, b: int, c: int, count: int) -> list[int]:
    return [a * k * k + b * k + c for k in range(1, count + 1)]


def _answer_expr(a: int, b: int, c: int) -> sympy.Expr:
    return sympy.Integer(a) * _n**2 + sympy.Integer(b) * _n + sympy.Integer(c)


# ---------------------------------------------------------------------------
# 1. next_terms — extend via the constant second difference
# ---------------------------------------------------------------------------


def _gen_next_terms(rng: random.Random) -> dict:
    a = rng.choice(_A_RANGE)
    b = rng.choice(_B_RANGE)
    c = rng.choice(_C_RANGE)
    shown = _terms(a, b, c, 4)
    return {
        "a": a,
        "b": b,
        "c": c,
        "terms_shown": shown,
        "next_1": a * 25 + b * 5 + c,  # T₅
        "next_2": a * 36 + b * 6 + c,  # T₆
        "variant": f"quadnext:{a}:{b}:{c}",
    }


next_terms = Problem(
    id="quad_seq_next_terms",
    type_id="quadratic_sequence",
    name="Give the next two terms of a quadratic sequence",
    artifact_type="practice",
    problem_spec=_gen_next_terms,
    verifier_spec=[
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "next_1"},
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "next_2"},
    ],
)


# ---------------------------------------------------------------------------
# 2. nth_term_formula — recover Tₙ = an² + bn + c from four terms
# ---------------------------------------------------------------------------


def _gen_nth_term_formula(rng: random.Random) -> dict:
    a = rng.choice(_A_RANGE)
    b = rng.choice(_B_RANGE)
    c = rng.choice(_C_RANGE)
    shown = _terms(a, b, c, 4)
    d1 = shown[1] - shown[0]  # first first-difference = 3a + b
    return {
        "a": a,
        "b": b,
        "c": c,
        "t1": shown[0],
        "t2": shown[1],
        "t3": shown[2],
        "t4": shown[3],
        "first_diff": d1,
        "second_diff": 2 * a,
        "variant": f"quadnth:{a}:{b}:{c}",
        "answer": _answer_expr(a, b, c),
    }


nth_term_formula = Problem(
    id="quad_seq_nth_term_formula",
    type_id="quadratic_sequence",
    name="Write the general term Tₙ for a quadratic sequence",
    artifact_type="practice",
    problem_spec=_gen_nth_term_formula,
    # 3 marks matches the NSC allocation for a "determine Tₙ" item (e.g. 2025 M/J
    # P1 Q3.1); the earlier 4 was an ad-hoc single-answer weight (no corpus anchor
    # pinned it) — recalibrated down, like arith_seq's nth-term.
    verifier_spec={"kind": "symbolic_equality", "marks_possible": 3},
)


# ---------------------------------------------------------------------------
# 3. find_term — evaluate a specific larger term T_k
# ---------------------------------------------------------------------------


def _gen_find_term(rng: random.Random) -> dict:
    a = rng.choice(_A_RANGE)
    b = rng.choice(_B_RANGE)
    c = rng.choice(_C_RANGE)
    n_target = rng.randint(10, 20)
    shown = _terms(a, b, c, 3)
    return {
        "a": a,
        "b": b,
        "c": c,
        "t1": shown[0],
        "t2": shown[1],
        "t3": shown[2],
        "second_diff": 2 * a,
        "n_target": n_target,
        "variant": f"quadfind:{a}:{b}:{c}:{n_target}",
        "answer": a * n_target * n_target + b * n_target + c,
    }


find_term = Problem(
    id="quad_seq_find_term",
    type_id="quadratic_sequence",
    name="Calculate a specific term Tₙ of a quadratic sequence",
    artifact_type="practice",
    problem_spec=_gen_find_term,
    verifier_spec={"kind": "symbolic_equality", "marks_possible": 3},
)


# ---------------------------------------------------------------------------
# 4. find_n — which term equals a given value (solve a quadratic in n)
# ---------------------------------------------------------------------------


def _gen_find_n(rng: random.Random) -> dict:
    """a > 0 and b ≥ 0 ⇒ the vertex sits at n = -b/(2a) ≤ 0, so the sequence is
    strictly increasing for n ≥ 1. The value at n_target is therefore reached by a
    single positive integer term index; the quadratic's other root is negative and
    the student rejects it, so 'which term' has one unambiguous answer."""
    a = rng.choice([1, 2])
    b = rng.randint(0, 6)
    c = rng.randint(-4, 6)
    n_target = rng.randint(4, 9)
    target = a * n_target * n_target + b * n_target + c
    shown = _terms(a, b, c, 3)
    return {
        "a": a,
        "b": b,
        "c": c,
        "t1": shown[0],
        "t2": shown[1],
        "t3": shown[2],
        "second_diff": 2 * a,
        "target": target,
        "other_root": sympy.Rational(-b, a) - n_target,  # < 0, rejected
        "variant": f"quadfindn:{a}:{b}:{c}:{n_target}",
        "answer": n_target,
    }


find_n = Problem(
    id="quad_seq_find_n",
    type_id="quadratic_sequence",
    name="Find which term of a quadratic sequence equals a given value",
    artifact_type="practice",
    problem_spec=_gen_find_n,
    verifier_spec={"kind": "symbolic_equality", "marks_possible": 4},
)


# ---------------------------------------------------------------------------
# 5. consecutive_diff — two consecutive terms differ by D; find the larger term
# ---------------------------------------------------------------------------


def _gen_consecutive_diff(rng: random.Random) -> dict:
    """The first difference T_{n+1} − T_n = 2a·n + (a + b) is *linear* and, for
    a > 0, strictly increasing in n — so a given positive difference D fixes a
    single index n, and the larger of the two consecutive terms is T_{n+1}. Draw
    a > 0 and an index far enough along that D is clearly positive while the terms
    stay exam-sized."""
    a = rng.choice([1, 2, 3])
    b = rng.randint(-6, 6)
    c = rng.randint(-6, 6)
    n = rng.randint(8, 16)  # the smaller index; T_{n+1} is the larger term
    diff = 2 * a * n + a + b  # T_{n+1} − T_n, strictly positive here
    larger = a * (n + 1) ** 2 + b * (n + 1) + c
    shown = _terms(a, b, c, 4)
    return {
        "a": a,
        "b": b,
        "c": c,
        "t1": shown[0],
        "t2": shown[1],
        "t3": shown[2],
        "t4": shown[3],
        "terms_shown": shown,
        "second_diff": 2 * a,
        "diff": diff,
        "n_index": n,
        "larger_term": larger,
        "variant": f"quaddiff:{a}:{b}:{c}:{n}",
    }


consecutive_diff = Problem(
    id="quad_seq_consecutive_diff",
    type_id="quadratic_sequence",
    name=(
        "Find the larger of two consecutive quadratic-sequence terms "
        "given their difference"
    ),
    artifact_type="practice",
    problem_spec=_gen_consecutive_diff,
    # Mirrors the NSC 3-mark split: the index n from the first-difference equation
    # (1) and the larger term itself (2).
    verifier_spec=[
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "n_index"},
        {"kind": "symbolic_equality", "marks_possible": 2, "param_key": "larger_term"},
    ],
    corpus_anchor=CorpusAnchor(
        paper="2025 May/June P1",
        question="3.2",
        marks=3,
    ),
)


# ---------------------------------------------------------------------------
# 6. shift_negative — add m to every term; find m so only the interior window is
#    negative. Answer is a half-open interval (needs the set_solution kind).
# ---------------------------------------------------------------------------


def _gen_shift_negative(rng: random.Random) -> dict:
    """Vertex form T_n = a(n − h)² + d (a > 0, integer axis h, min term d > 0), so
    the sequence is symmetric about n = h: T_1 = T_{2h−1} are the window boundary
    and T_2 = T_{2h−2} the largest interior term. Adding m, "only the terms
    between T_1 and T_{2h−1} are negative" needs the interior max negative and the
    boundary non-negative:  −T_1 ≤ m < −T_2. The two thresholds are the graded
    values; the interval (closed at −T_1, open at −T_2) is the graded set."""
    a = rng.choice([1, 2])
    h = rng.choice([3, 4])  # window T_1..T_{2h-1}: T_1..T_5 or T_1..T_7
    d = rng.randint(1, 6)  # the minimum term T_h, kept positive
    last = 2 * h - 1

    def term(n: int) -> int:
        return a * (n - h) ** 2 + d

    t_boundary = term(1)  # = T_1 = T_{last}
    t_interior = term(2)  # = T_2 = T_{last-1}, the largest interior term
    m_low = -t_boundary  # m ≥ m_low keeps the boundary non-negative
    m_high = -t_interior  # m < m_high pushes the interior negative

    b = -2 * a * h
    c = a * h * h + d
    n_sym = sympy.Symbol("n")
    general_term = sympy.Integer(a) * n_sym**2 + sympy.Integer(b) * n_sym + c

    return {
        "a": a,
        "h": h,
        "d": d,
        "b": b,
        "c": c,
        "last": last,
        "terms_shown": [term(k) for k in range(1, 5)],
        "t_boundary": t_boundary,
        "t_interior": t_interior,
        "m_low": m_low,
        "m_high": m_high,
        "boundary_values": frozenset({m_low, m_high}),
        "solution_set": sympy.Interval(m_low, m_high, left_open=False, right_open=True),
        "general_term_latex": sympy.latex(general_term),
        "variant": f"quadshift:{a}:{h}:{d}",
    }


shift_negative = Problem(
    id="quad_seq_shift_negative",
    type_id="quadratic_sequence",
    name=(
        "Find the m-range that makes only a quadratic sequence's "
        "interior terms negative"
    ),
    artifact_type="practice",
    problem_spec=_gen_shift_negative,
    # NSC 3-mark split: the two m-thresholds (2, partial) + the interval itself,
    # endpoint openness graded (1). The interval answer is why set_solution exists.
    verifier_spec=[
        {"kind": "set_equality", "marks_possible": 2, "param_key": "boundary_values"},
        {"kind": "set_solution", "marks_possible": 1, "param_key": "solution_set"},
    ],
    corpus_anchor=CorpusAnchor(
        paper="2025 May/June P1",
        question="3.3",
        marks=3,
    ),
)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    all_problems = {
        p.id: p
        for p in [
            next_terms,
            nth_term_formula,
            find_term,
            find_n,
            consecutive_diff,
            shift_negative,
        ]
    }
    engine = Engine(registry=InMemoryRegistry(all_problems))

    def show_result(label, instance, *answers):
        attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
        r = instance.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  "
            f"is_correct={r.is_correct}"
        )

    print("=== quad nth_term_formula ===")
    inst = engine.instantiate(nth_term_formula.id, seed=1)
    p = inst.params
    print(f"  Sequence: {p['t1']}, {p['t2']}, {p['t3']}, {p['t4']}, ...")
    print(f"  2nd difference = {p['second_diff']}")
    print(f"  Canonical: {inst.verifier.canonicals[0]}")
    show_result("Correct an²+bn+c", inst, p["answer"])

    print("\n=== quad next_terms ===")
    inst = engine.instantiate(next_terms.id, seed=1)
    p = inst.params
    print(f"  Shown: {p['terms_shown']}")
    show_result("Both correct", inst, p["next_1"], p["next_2"])

    print("\n=== quad find_term ===")
    inst = engine.instantiate(find_term.id, seed=1)
    p = inst.params
    print(f"  a={p['a']}, b={p['b']}, c={p['c']}, find T_{p['n_target']}")
    show_result("Correct", inst, p["answer"])

    print("\n=== quad find_n ===")
    inst = engine.instantiate(find_n.id, seed=1)
    p = inst.params
    print(f"  which term = {p['target']}? (other root {p['other_root']})")
    show_result("Correct", inst, p["answer"])
