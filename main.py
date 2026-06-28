"""
Smoke test: exercise the engine against real content/examples generators — each
must instantiate, round-trip (the canonical solution is accepted), reconstruct
from stored params, and reject a wrong answer.

The malformed-spec failure modes (the engine raising CanonicalResolutionError
rather than guessing a canonical) are guarded as proper pytest cases in
tests/test_failure_modes.py — this smoke test stays focused on real content.

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
