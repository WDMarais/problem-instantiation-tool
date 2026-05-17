from __future__ import annotations

import random
from typing import Any

from .exceptions import (
    AttemptValidationError,
    InstantiationError,
    ParamsIncompatibleError,
)
from .schemas import (
    ArtifactType,
    Difficulty,
    Problem,
    ProblemInstance,
    ProvidedStep,
    SolutionAttempt,
    SubmittedStep,
)

_DIFFICULTY_TIERS = [
    Difficulty.routine,
    Difficulty.standard,
    Difficulty.challenging,
    Difficulty.non_routine,
]


def _one_tier_below(difficulty: Difficulty) -> Difficulty:
    idx = _DIFFICULTY_TIERS.index(difficulty)
    return _DIFFICULTY_TIERS[max(0, idx - 1)]


def _dict_generator(spec_dict: dict, rng: random.Random) -> dict:
    params: dict = {}
    for k, v in spec_dict.items():
        if k == "kind":
            continue
        if k.endswith("_range"):
            base = k[: -len("_range")]
            if base == "root":
                params["root1"] = rng.randint(v[0], v[1])
                params["root2"] = rng.randint(v[0], v[1])
            else:
                params[base] = rng.randint(v[0], v[1])
        elif not isinstance(v, (dict, list)):
            params[k] = v
    return params


class Engine:
    def __init__(self, registry) -> None:
        self._registry = registry

    def _run_generator(self, spec: Problem, rng: random.Random) -> dict:
        if callable(spec.problem_spec):
            return spec.problem_spec(rng)
        return _dict_generator(spec.problem_spec, rng)

    def _get_signature(self, spec: Problem) -> set[str]:
        if spec.param_names is not None:
            return set(spec.param_names)
        params = self._run_generator(spec, random.Random(0))
        return set(params.keys())

    def instantiate(
        self,
        spec_or_id: str | Problem,
        *,
        seed: int | None = None,
        params: dict[str, Any] | None = None,
    ) -> ProblemInstance:
        from .verifier import build_verifier_chain

        # 1. Resolve spec
        if isinstance(spec_or_id, str):
            spec = self._registry.get(spec_or_id)
        else:
            spec = spec_or_id

        # 2. Mutual exclusion
        if seed is not None and params is not None:
            raise AttemptValidationError(0, "seed and params are mutually exclusive")

        # 3. Mode dispatch
        if params is not None:
            current_sig = self._get_signature(spec)
            if set(params.keys()) != current_sig:
                raise ParamsIncompatibleError(spec.id, params, current_sig)
            resolved_params = dict(params)
            resolved_seed = None
        else:
            if seed is None:
                seed = random.randint(0, 2**31 - 1)
            rng = random.Random(seed)
            try:
                resolved_params = self._run_generator(spec, rng)
            except Exception as e:
                raise InstantiationError(spec.id, e) from e
            resolved_seed = seed

        # 4. Gap-fill difficulty defaulting
        current_spec = spec
        if spec.artifact_type == ArtifactType.gap_fill and spec.difficulty is None:
            source = self._registry.get(spec.source_id)
            computed = _one_tier_below(source.difficulty)
            current_spec = spec.model_copy(update={"difficulty": computed})

        # 5. Build verifier
        verifier = build_verifier_chain(current_spec.verifier_spec, resolved_params)

        # 6. Build solution (all SubmittedStep, values = canonicals)
        n = len(verifier.canonicals)
        solution = SolutionAttempt(
            steps=[SubmittedStep(verifier.canonicals[i]) for i in range(n)]
        )

        # 7. Build presented_attempt for gap_fill only
        if current_spec.artifact_type == ArtifactType.gap_fill:
            blank_set = set(current_spec.blank_steps or [])
            pa_steps = [
                None if i in blank_set else ProvidedStep(verifier.canonicals[i])
                for i in range(n)
            ]
            presented_attempt: SolutionAttempt | None = SolutionAttempt(steps=pa_steps)
        else:
            presented_attempt = None

        return ProblemInstance(
            spec=current_spec,
            params=resolved_params,
            solution=solution,
            verifier=verifier,
            seed=resolved_seed,
            presented_attempt=presented_attempt,
        )
