"""
Quadratic sequences (Tₙ = an² + bn + c): the six solving archetypes.

Each generator is checked by *re-deriving* the answer independently of the
generator's own arithmetic — recovering a, b, c from the presented terms via the
difference method a student would use — then round-tripping it through the verifier
and smoke-rendering the template. find_n additionally asserts the load-bearing
scope property (unique positive-integer term index) that its F1 predicate enforces.
"""

import sympy

from content.examples.quadratic_sequence import (
    consecutive_diff,
    find_n,
    find_term,
    next_terms,
    nth_term_formula,
    shift_negative,
)
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep
from worksheets.generate import (
    BUNDLES,
    PROBLEMS,
    template_quad_consecutive_diff,
    template_quad_find_n,
    template_quad_find_term,
    template_quad_next_terms,
    template_quad_nth_term_formula,
    template_quad_shift_negative,
)

_ALL = [
    next_terms,
    nth_term_formula,
    find_term,
    find_n,
    consecutive_diff,
    shift_negative,
]
_n = sympy.Symbol("n")


def _eng():
    return Engine(registry=InMemoryRegistry({p.id: p for p in _ALL}))


def _rate(inst, *answers):
    return inst.verifier.rate(
        SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
    )


def _abc_from_terms(t1, t2, t3):
    """Recover a, b, c from three terms the way a student would — independent of the
    generator's stored coefficients."""
    d1, d2 = t2 - t1, t3 - t2
    a = (d2 - d1) // 2
    b = d1 - 3 * a
    c = t1 - a - b
    return a, b, c


# --- generator correctness (re-derived answers) -----------------------------


def _for_seed(prob, seed):
    return _eng().instantiate(prob.id, seed=seed).params


def test_nth_term_formula_recovers_abc_and_is_genuinely_quadratic():
    for seed in range(30):
        p = _for_seed(nth_term_formula, seed)
        a, b, c = _abc_from_terms(p["t1"], p["t2"], p["t3"])
        assert (a, b, c) == (p["a"], p["b"], p["c"])
        assert a != 0, "a == 0 would not be a quadratic sequence"
        # second difference is constant and equals 2a across all four terms
        terms = [p["t1"], p["t2"], p["t3"], p["t4"]]
        d1 = [terms[i + 1] - terms[i] for i in range(3)]
        d2 = [d1[i + 1] - d1[i] for i in range(2)]
        assert d2[0] == d2[1] == 2 * a
        assert sympy.simplify(p["answer"] - (a * _n**2 + b * _n + c)) == 0


def test_next_terms_extend_the_constant_second_difference():
    for seed in range(30):
        p = _for_seed(next_terms, seed)
        shown = p["terms_shown"]
        d1 = [shown[i + 1] - shown[i] for i in range(3)]
        sd = d1[1] - d1[0]
        assert d1[2] - d1[1] == sd  # constant second difference
        assert p["next_1"] == shown[-1] + (d1[2] + sd)
        assert p["next_2"] == p["next_1"] + (d1[2] + 2 * sd)


def test_find_term_matches_substitution():
    for seed in range(30):
        p = _for_seed(find_term, seed)
        a, b, c = _abc_from_terms(p["t1"], p["t2"], p["t3"])
        nt = p["n_target"]
        assert p["answer"] == a * nt * nt + b * nt + c


def test_find_n_answer_is_the_unique_positive_integer_term():
    for seed in range(30):
        p = _for_seed(find_n, seed)
        a, b, c, target, ans = p["a"], p["b"], p["c"], p["target"], p["answer"]
        assert a * ans * ans + b * ans + c == target
        # strictly increasing for n ≥ 1 (a > 0, b ≥ 0 ⇒ vertex at n ≤ 0), so the
        # target is reached by exactly one positive-integer term index.
        assert a > 0 and b >= 0
        hits = [n for n in range(1, 100) if a * n * n + b * n + c == target]
        assert hits == [ans]


# --- verifier round-trips ---------------------------------------------------


def test_nth_term_accepts_equivalent_forms_and_rejects_wrong():
    inst = _eng().instantiate(nth_term_formula.id, seed=1)
    a, b, c = inst.params["a"], inst.params["b"], inst.params["c"]
    # expanded and factored-out forms are algebraically equal ⇒ both full marks
    assert _rate(inst, a * _n**2 + b * _n + c).is_correct
    assert _rate(inst, sympy.expand(a * (_n**2) + b * _n + c)).is_correct
    assert not _rate(inst, a * _n**2 + b * _n + c + 1).is_correct


def test_next_terms_partial_and_full():
    inst = _eng().instantiate(next_terms.id, seed=2)
    n1, n2 = inst.params["next_1"], inst.params["next_2"]
    assert _rate(inst, n1, n2).marks_awarded == 2
    partial = _rate(inst, n1, n2 + 1)
    assert partial.marks_awarded == 1 and not partial.is_correct


def test_single_answer_problems_reject_wrong():
    eng = _eng()
    for prob in (find_term, find_n):
        inst = eng.instantiate(prob.id, seed=3)
        assert not _rate(inst, int(inst.params["answer"]) + 1).is_correct


# --- consecutive_diff (first-difference → larger term) ----------------------


def test_consecutive_diff_answer_is_the_larger_consecutive_term():
    eng = _eng()
    for seed in range(200):
        p = eng.instantiate(consecutive_diff.id, seed=seed).params
        # re-derive a, b, c from the presented terms, independent of the generator
        a, b, c = _abc_from_terms(p["t1"], p["t2"], p["t3"])

        def term(k):
            return a * k * k + b * k + c

        n = p["n_index"]
        # the stored difference really is T_{n+1} − T_n, and it is positive so the
        # larger of the two consecutive terms is indeed T_{n+1}
        assert p["diff"] == term(n + 1) - term(n)
        assert p["diff"] > 0
        assert p["larger_term"] == term(n + 1) > term(n)


def test_consecutive_diff_index_is_the_unique_solution():
    # the first difference 2an + (a+b) is strictly increasing (a > 0), so no other
    # index yields the same difference — the item is unambiguous
    eng = _eng()
    for seed in range(120):
        p = eng.instantiate(consecutive_diff.id, seed=seed).params
        a, b = p["a"], p["b"]
        n = p["n_index"]
        for other in range(1, 30):
            if other != n:
                assert 2 * a * other + a + b != p["diff"]


def test_consecutive_diff_verifier_splits_one_plus_two():
    inst = _eng().instantiate(consecutive_diff.id, seed=7)
    p = inst.params
    assert _rate(inst, p["n_index"], p["larger_term"]).marks_awarded == 3
    # index right, term wrong → 1 of 3
    only_n = _rate(inst, p["n_index"], p["larger_term"] + 1)
    assert only_n.marks_awarded == 1 and not only_n.is_correct
    # index wrong, term right → 2 of 3
    only_term = _rate(inst, p["n_index"] + 1, p["larger_term"])
    assert only_term.marks_awarded == 2 and not only_term.is_correct


# --- shift_negative (add m; only interior window negative → interval answer) --


def test_shift_negative_answer_matches_an_independent_derivation():
    eng = _eng()
    for seed in range(200):
        p = eng.instantiate(shift_negative.id, seed=seed).params
        a, h, d = p["a"], p["h"], p["d"]

        def term(n):
            return a * (n - h) ** 2 + d

        # boundary T_1 = T_last, interior max T_2; answer −T_1 ≤ m < −T_2
        assert p["m_low"] == -term(1) and p["m_high"] == -term(2)
        assert p["m_low"] < p["m_high"]  # non-empty
        assert p["solution_set"] == sympy.Interval(
            p["m_low"], p["m_high"], left_open=False, right_open=True
        )
        assert p["last"] == 2 * h - 1


def test_shift_negative_is_a_genuine_quadratic_sequence():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(shift_negative.id, seed=seed).params
        t = p["terms_shown"]
        second_diff = (t[2] - t[1]) - (t[1] - t[0])
        assert second_diff == 2 * p["a"] and second_diff != 0


def test_shift_negative_verifier_two_plus_one_split():
    inst = _eng().instantiate(shift_negative.id, seed=4)
    p = inst.params
    assert _rate(inst, p["boundary_values"], p["solution_set"]).marks_awarded == 3
    # one threshold right (1 of 2) + interval right (1) = 2
    one_thresh = _rate(inst, frozenset({p["m_low"]}), p["solution_set"])
    assert one_thresh.marks_awarded == 2 and not one_thresh.is_correct


def test_shift_negative_endpoint_openness_is_graded():
    # the interval is closed at −T_1 but OPEN at −T_2 (strict <). Submitting a
    # fully-closed interval must lose the set mark.
    inst = _eng().instantiate(shift_negative.id, seed=4)
    p = inst.params
    closed = sympy.Interval(p["m_low"], p["m_high"], left_open=False, right_open=False)
    r = _rate(inst, p["boundary_values"], closed)
    assert r.marks_awarded == 2 and not r.is_correct  # thresholds ok, set wrong


# --- templates + wiring -----------------------------------------------------


def test_templates_render_full_and_short():
    eng = _eng()
    cases = [
        (next_terms.id, template_quad_next_terms),
        (nth_term_formula.id, template_quad_nth_term_formula),
        (find_term.id, template_quad_find_term),
        (find_n.id, template_quad_find_n),
        (consecutive_diff.id, template_quad_consecutive_diff),
        (shift_negative.id, template_quad_shift_negative),
    ]
    for pid, tmpl in cases:
        params = eng.instantiate(pid, seed=4).params
        for detail in ("full", "short"):
            card = tmpl(params, detail=detail)
            assert card.instruction
            assert card.display_math
            assert card.worked_steps


def test_find_n_template_shows_the_rejected_root():
    inst = _eng().instantiate(find_n.id, seed=5)
    card = template_quad_find_n(inst.params, detail="full")
    assert any("reject" in s for s in card.worked_steps)


def test_types_registered_and_in_bundles():
    ids = {
        "quad_seq_next_terms",
        "quad_seq_nth_term_formula",
        "quad_seq_find_term",
        "quad_seq_find_n",
        "quad_seq_consecutive_diff",
        "quad_seq_shift_negative",
    }
    assert ids <= set(PROBLEMS)
    assert "quad_seq_nth_term_unlabeled" in PROBLEMS
    dedicated = {pid for pid, _ in BUNDLES["quadratic_sequences"]}
    assert ids <= dedicated
    full = {pid for pid, _ in BUNDLES["sequences_full"]}
    assert ids <= full
    mixed = {pid for pid, _ in BUNDLES["sequences_mixed"]}
    assert "quad_seq_nth_term_unlabeled" in mixed
