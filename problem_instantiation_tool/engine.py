from typing import Any

from .exceptions import AttemptValidationError, ProblemNotFoundError
from .schemas import Problem, ProblemInstance, SolutionAttempt, SubmittedStep


class Engine:
    def __init__(self, registry) -> None:
        self._registry = registry

    def instantiate(
        self,
        spec_or_id: str | Problem,
        *,
        seed: int | None = None,
        params: dict[str, Any] | None = None,
    ) -> ProblemInstance:
        raise NotImplementedError
