"""
Smoke test: exercise the engine against real nsc_papers content definitions.

Run with:  uv run python main.py
"""

from __future__ import annotations

import traceback
from dataclasses import dataclass

from problem_instantiation_tool.engine import Engine
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


# ---------------------------------------------------------------------------
# Candidate problems derived directly from nsc_papers algebra.yaml
# ---------------------------------------------------------------------------


def build_problems() -> dict[str, Problem]:
    problems: dict[str, Problem] = {}

    # quadratic_factor — uses set_equality (we have this); leading_coeff_range is extra
    problems["nsc_quadratic_factor"] = Problem(
        id="nsc_quadratic_factor",
        type_id="quadratic_equation",
        name="Solve a factorisable quadratic (integer roots)",
        artifact_type="srs_card",
        problem_spec={
            "kind": "quadratic_factor",
            "root_range": [-10, 10],
            "leading_coeff_range": [1, 3],
        },
        verifier_spec={"kind": "set_equality", "marks_possible": 1},
    )

    # arith_seq_nth_term — uses symbolic_equality (NOT yet a known kind in our verifier)
    problems["nsc_arith_seq"] = Problem(
        id="nsc_arith_seq",
        type_id="arithmetic_sequence",
        name="Calculate the nth term of an arithmetic sequence",
        artifact_type="srs_card",
        problem_spec={
            "kind": "sequence_nth_term",
            "sequence_type": "arithmetic",
            "a_range": [-15, 30],
            "d_range": [1, 12],
            "n_range": [5, 25],
        },
        verifier_spec={"kind": "symbolic_equality", "marks_possible": 1},
    )

    # quadratic_formula — uses numeric_approx (NOT yet implemented)
    problems["nsc_quadratic_formula"] = Problem(
        id="nsc_quadratic_formula",
        type_id="quadratic_equation",
        name="Solve a quadratic using the formula (irrational roots, 2 d.p.)",
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
    )

    return problems


def main() -> None:
    problems = build_problems()
    engine = Engine(registry=InMemoryRegistry(problems))
    results: list[Result] = []

    # --- 1. Construction (Problem() call itself) ---
    for pid in ["nsc_quadratic_factor", "nsc_arith_seq", "nsc_quadratic_formula"]:
        label = f"construct:{pid}"
        try:
            _ = problems[pid]
            results.append(Result(label, True, "ok"))
        except Exception as e:
            results.append(Result(label, False, f"{type(e).__name__}: {e}"))

    # --- 2. Instantiation ---
    for pid in problems:
        results.append(
            run(
                f"instantiate:{pid}",
                lambda p=pid: str(engine.instantiate(p, seed=42).params),
            )
        )

    # --- 3. Round-trip: instantiate + rate the canonical solution ---
    def roundtrip(pid: str) -> str:
        instance = engine.instantiate(pid, seed=42)
        rating = instance.verifier.rate(instance.solution)
        assert rating.is_correct, f"canonical solution rated as incorrect: {rating}"
        return f"params={instance.params}  marks={rating.marks_awarded}/{rating.marks_possible}"

    for pid in problems:
        results.append(run(f"roundtrip:{pid}", lambda p=pid: roundtrip(p)))

    # --- 4. Reconstruction from params ---
    def reconstruct(pid: str) -> str:
        fresh = engine.instantiate(pid, seed=42)
        recon = engine.instantiate(pid, params=fresh.params)
        assert recon.params == fresh.params
        rating = recon.verifier.rate(recon.solution)
        assert rating.is_correct
        return f"params={recon.params}"

    for pid in problems:
        results.append(run(f"reconstruct:{pid}", lambda p=pid: reconstruct(p)))

    # --- 5. Known-correct answer acceptance ---
    # Checks that a value we know is the right answer IS accepted.
    # This catches silent fallthrough where canonical = first param (e.g. "arithmetic")
    # and a legitimately correct numeric answer would be rejected.
    known_correct: dict[str, object] = {
        # set_equality: frozenset of roots
        "nsc_quadratic_factor": frozenset({10, -7}),
        # symbolic_equality → should accept T_5 = a + (n-1)d = 25 + 4*2 = 33
        # (params are {'sequence_type':'arithmetic', 'a':25, 'd':2, 'n':5} at seed=42)
        "nsc_arith_seq": 33,
        # numeric_approx → should accept a root of x² - 10x + 8 = 0 ≈ 9.13
        # (params are {'a':1, 'b':-10, 'c':8} at seed=42)
        "nsc_quadratic_formula": 9.13,
    }

    def known_correct_accepted(pid: str) -> str:
        instance = engine.instantiate(pid, seed=42)
        answer = known_correct[pid]
        attempt = SolutionAttempt(steps=[SubmittedStep(answer)])
        rating = instance.verifier.rate(attempt)
        assert rating.is_correct, (
            f"known-correct answer {answer!r} was NOT accepted — "
            f"verifier kind may be silently broken (params={instance.params}, "
            f"canonical={instance.verifier.canonicals})"
        )
        return f"known-correct {answer!r} accepted"

    for pid in problems:
        results.append(
            run(f"known_correct:{pid}", lambda p=pid: known_correct_accepted(p))
        )

    # --- 6. Wrong-answer rejection: a wrong submission must NOT be rated correct ---
    # This catches verifiers that silently fall through to a wrong kind and
    # always return is_correct because they compare canonical to itself.: a wrong submission must NOT be rated correct ---
    # This catches verifiers that silently fall through to a wrong kind and
    # always return is_correct because they compare canonical to itself.
    def wrong_answer_rejected(pid: str) -> str:
        instance = engine.instantiate(pid, seed=42)
        # Submit a deliberately wrong value for every step
        wrong = SolutionAttempt(steps=[SubmittedStep("WRONG_ANSWER_99999")])
        rating = instance.verifier.rate(wrong)
        assert not rating.is_correct, (
            f"VERIFIER SILENT FAILURE: wrong answer rated as correct — "
            f"verifier kind may not be implemented (params={instance.params})"
        )
        return f"wrong answer correctly rejected (marks={rating.marks_awarded}/{rating.marks_possible})"

    for pid in problems:
        results.append(
            run(f"wrong_rejected:{pid}", lambda p=pid: wrong_answer_rejected(p))
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
        print(f"\nGaps to address:")
        seen: set[str] = set()
        for r in failed:
            # Extract just the error type + first line for deduplication
            key = r.detail.split("\n")[0]
            if key not in seen:
                seen.add(key)
                print(f"  - {key}")


if __name__ == "__main__":
    main()
