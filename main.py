"""
Smoke test: exercise the engine against real content generators, and assert that
malformed specs fail loudly.

Two halves:
  * REAL_PROBLEMS — actual content/examples generators (they compute answers).
    Each must instantiate, round-trip (the canonical solution is accepted),
    reconstruct from stored params, and reject a wrong answer.
  * GAP_MARKERS — deliberately incomplete dict specs whose canonical is ambiguous
    (the generator samples ranges but never computes an answer, and there is no
    param_key). The engine must refuse to guess and raise CanonicalResolutionError.
    A marker that *fires* is a PASS — it is a regression guard for that behaviour.

Run with:  uv run python main.py   (exit code 0 = all good, 1 = gaps)
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

from content.examples.arithmetic_sequence import (
    find_term,
    next_terms,
    nth_term_formula,
)
from content.examples.monic_factorise import problem as monic_factorise
from content.examples.quadratic_roots import problem as quadratic_factor
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.exceptions import CanonicalResolutionError
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import Problem, SolutionAttempt, SubmittedStep


@dataclass
class Result:
    label: str
    ok: bool
    detail: str


def run(label: str, fn) -> Result:
    try:
        detail = fn()
        return Result(label, True, detail or "ok")
    except Exception as e:
        return Result(label, False, f"{type(e).__name__}: {e}")


# --- Real content generators (computed answers; must all pass) ----------------
REAL_PROBLEMS: list[Problem] = [
    find_term,  # symbolic_equality, integer Tn
    nth_term_formula,  # symbolic_equality, expression in n
    next_terms,  # two-step, param_key per step
    quadratic_factor,  # set_equality (roots)
    monic_factorise,  # symbolic_equality (factorised form)
]


# --- Gap markers: specs that SHOULD fail loudly -------------------------------
# Incomplete YAML-style dict specs: the generator samples ranges but never
# computes an answer, so the canonical is ambiguous. The engine must raise
# CanonicalResolutionError rather than silently picking a wrong param. A marker
# that *fires* is a PASS — a regression guard for "the verifier refuses to guess".
def build_gap_markers() -> list[Problem]:
    return [
        Problem(
            id="gap_ambiguous_symbolic",
            type_id="arithmetic_sequence",
            name="Tn spec missing a computed answer (ambiguous canonical)",
            artifact_type="srs_card",
            problem_spec={
                "kind": "sequence_nth_term",
                "sequence_type": "arithmetic",
                "a_range": [-15, 30],
                "d_range": [1, 12],
                "n_range": [5, 25],
            },
            verifier_spec={"kind": "symbolic_equality", "marks_possible": 1},
        ),
        Problem(
            id="gap_ambiguous_numeric",
            type_id="quadratic_equation",
            name="Quadratic-formula spec missing computed roots (ambiguous)",
            artifact_type="srs_card",
            problem_spec={
                "kind": "quadratic_formula",
                "a_range": [1, 4],
                "b_range": [-10, 10],
                "c_range": [-15, 15],
            },
            verifier_spec={
                "kind": "numeric_equality",
                "tolerance": 0.005,
                "count": 2,
                "marks_possible": 1,
            },
        ),
        Problem(
            id="gap_ambiguous_set",
            type_id="quadratic_equation",
            name="set_equality spec with no root* params (ambiguous answer set)",
            artifact_type="srs_card",
            # no root* params, >1 field: the verifier must not sweep {a, b} into
            # the answer set — it must refuse to guess.
            problem_spec={"kind": "roots", "a_range": [1, 9], "b_range": [1, 9]},
            verifier_spec={"kind": "set_equality", "marks_possible": 1},
        ),
    ]


def main() -> None:
    engine = Engine(registry=InMemoryRegistry({p.id: p for p in REAL_PROBLEMS}))
    results: list[Result] = []

    # 1. Instantiation
    for p in REAL_PROBLEMS:
        results.append(
            run(
                f"instantiate:{p.id}",
                lambda p=p: str(engine.instantiate(p.id, seed=42).params),
            )
        )

    # 2. Round-trip: the canonical solution must be accepted
    def roundtrip(pid: str) -> str:
        inst = engine.instantiate(pid, seed=42)
        rating = inst.verifier.rate(inst.solution)
        assert rating.is_correct, f"canonical solution rated incorrect: {rating}"
        return f"marks={rating.marks_awarded}/{rating.marks_possible}"

    for p in REAL_PROBLEMS:
        results.append(run(f"roundtrip:{p.id}", lambda p=p: roundtrip(p.id)))

    # 3. Reconstruction from stored params
    def reconstruct(pid: str) -> str:
        fresh = engine.instantiate(pid, seed=42)
        recon = engine.instantiate(pid, params=fresh.params)
        assert recon.params == fresh.params
        assert recon.verifier.rate(recon.solution).is_correct
        return f"params={recon.params}"

    for p in REAL_PROBLEMS:
        results.append(run(f"reconstruct:{p.id}", lambda p=p: reconstruct(p.id)))

    # 4. Wrong-answer rejection
    def wrong_rejected(pid: str) -> str:
        inst = engine.instantiate(pid, seed=42)
        wrong = SolutionAttempt(steps=[SubmittedStep("WRONG_ANSWER_99999")])
        rating = inst.verifier.rate(wrong)
        assert not rating.is_correct, "wrong answer rated correct (verifier broken)"
        return f"rejected (marks={rating.marks_awarded}/{rating.marks_possible})"

    for p in REAL_PROBLEMS:
        results.append(run(f"wrong_rejected:{p.id}", lambda p=p: wrong_rejected(p.id)))

    # 5. Gap markers: instantiate MUST raise CanonicalResolutionError
    def gap_marker_fires(prob: Problem) -> str:
        try:
            engine.instantiate(prob, seed=42)
        except CanonicalResolutionError as e:
            return f"correctly refused to guess: {e.reason}"
        raise AssertionError(
            "expected CanonicalResolutionError, but instantiate succeeded "
            "(verifier silently guessed a canonical)"
        )

    for prob in build_gap_markers():
        results.append(
            run(f"gap_marker:{prob.id}", lambda prob=prob: gap_marker_fires(prob))
        )

    # --- Report ---
    print("\n=== Smoke test results ===\n")
    passed = [r for r in results if r.ok]
    failed = [r for r in results if not r.ok]

    for r in passed:
        print(f"  PASS  {r.label}")
        print(f"        {r.detail}")

    if failed:
        print()
        for r in failed:
            print(f"  FAIL  {r.label}")
            print(f"        {r.detail}")

    print(f"\n{len(passed)}/{len(results)} passed")
    if failed:
        print("\nGaps to address:")
        seen: set[str] = set()
        for r in failed:
            key = r.detail.split("\n")[0]
            if key not in seen:
                seen.add(key)
                print(f"  - {key}")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
