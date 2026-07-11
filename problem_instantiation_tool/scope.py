"""
F1 trust harness — the in-scope predicate, the per-draw guard, and the sweep.

The memo's *value* is trustworthy by construction (generators build the problem and
its answer consistently, in either direction). The one mathematical failure mode is
the **out-of-scope draw** (F1): an instance that is mathematically valid but
pedagogically wrong — non-integer params, roots outside the intended band, a
discriminant giving irrational/complex roots. See `mvp-scope.md` §1c/§1d.

An **in-scope predicate** turns F1 into a *checked* property. One predicate, two
consumers:

  - the **guard** (`assert_in_scope`) — a consumer calls it after `instantiate()`;
    a violation raises `ScopeViolationError` so a bad draw never reaches a tutee.
  - the **sweep** (`sweep` / `assert_scope_holds`) — a pytest instantiates a generator
    across the draw space and asserts the predicate holds for every instance, so an
    authoring bug fails in CI before any tutee sees it.

**A predicate must be non-tautological.** Express it on the *presented* problem (the
coefficients/terms the tutee sees) and check it *independently of construction*.
Asserting ``b² − 4c`` is a perfect square is vacuous for a generator that built the
polynomial from integer roots — it only earns its keep when it re-derives the property
from the presented coefficients. A predicate that merely restates what the generator
constructed catches nothing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable

from .engine import Engine
from .exceptions import ScopeViolationError
from .schemas import ProblemInstance

# A predicate reads a presented instance and returns human-readable reasons it is
# OUT of scope. Empty list == in scope. Kept as a plain Callable alias (not a Pydantic
# type): predicates live in the content layer and are never serialized across the
# engine boundary.
InScope = Callable[[ProblemInstance], list[str]]


def assert_in_scope(instance: ProblemInstance, predicate: InScope) -> None:
    """Per-draw guard. Raise ``ScopeViolationError`` if the instance is out of scope.

    A consumer (worksheet builder, SRS queue) calls this right after ``instantiate()``
    so a pedagogically-wrong draw can never be presented.
    """
    reasons = predicate(instance)
    if reasons:
        raise ScopeViolationError(
            instance.spec.id, dict(instance.params), reasons, seed=instance.seed
        )


def _param_key(params: dict) -> str:
    """Hashable identity for a draw; params may hold SymPy exprs/lists, so stringify."""
    return repr(sorted((k, str(v)) for k, v in params.items()))


@dataclass
class SweepReport:
    problem_id: str
    instances_drawn: int = 0
    distinct_params: int = 0
    # (seed, params, reasons) for each instance that violated the predicate
    violations: list[tuple[int, dict, list[str]]] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.violations

    def summary(self, max_shown: int = 5) -> str:
        head = (
            f"scope sweep [{self.problem_id}]: {self.instances_drawn} drawn, "
            f"{self.distinct_params} distinct, {len(self.violations)} out of scope"
        )
        if self.ok:
            return head + " — OK"
        lines = [head]
        for seed, params, reasons in self.violations[:max_shown]:
            lines.append(f"  seed={seed} params={params}")
            for r in reasons:
                lines.append(f"      · {r}")
        if len(self.violations) > max_shown:
            lines.append(f"  … and {len(self.violations) - max_shown} more")
        return "\n".join(lines)


def sweep(
    engine: Engine,
    problem_id: str,
    predicate: InScope,
    *,
    seeds: Iterable[int] = range(2000),
) -> SweepReport:
    """Instantiate ``problem_id`` across ``seeds`` and record every out-of-scope draw.

    Seed-sweeping is the pragmatic coverage strategy for today's generators (they draw
    from ``random.Random(seed)``); the reported ``distinct_params`` shows how much of
    the space was actually reached. For a generator that later exposes an enumerable
    param grid, pass the grid's covering seeds — the report shape is unchanged.
    """
    report = SweepReport(problem_id=problem_id)
    seen: set[str] = set()
    for s in seeds:
        instance = engine.instantiate(problem_id, seed=s)
        report.instances_drawn += 1
        seen.add(_param_key(instance.params))
        reasons = predicate(instance)
        if reasons:
            report.violations.append((s, dict(instance.params), reasons))
    report.distinct_params = len(seen)
    return report


def assert_scope_holds(
    engine: Engine,
    problem_id: str,
    predicate: InScope,
    *,
    seeds: Iterable[int] = range(2000),
    min_distinct: int = 1,
) -> SweepReport:
    """Terse pytest entry point: sweep, then assert no violations and real coverage.

    ``min_distinct`` guards against a vacuous green — a sweep that drew the same
    instance every time proves nothing. Returns the report for further assertions.
    """
    report = sweep(engine, problem_id, predicate, seeds=seeds)
    assert report.ok, report.summary()
    assert report.distinct_params >= min_distinct, (
        f"sweep explored only {report.distinct_params} distinct instance(s) "
        f"(< {min_distinct}); the green is vacuous"
    )
    return report
