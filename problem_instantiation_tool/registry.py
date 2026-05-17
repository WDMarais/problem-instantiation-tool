from typing import TYPE_CHECKING, Protocol, runtime_checkable

from .exceptions import ProblemNotFoundError

if TYPE_CHECKING:
    from .schemas import Problem


@runtime_checkable
class ContentRegistry(Protocol):
    def get(self, problem_id: str) -> "Problem": ...
    def version(self) -> str: ...


class InMemoryRegistry:
    def __init__(self, problems: dict[str, "Problem"]) -> None:
        self._problems = problems

    def get(self, problem_id: str) -> "Problem":
        try:
            return self._problems[problem_id]
        except KeyError:
            raise ProblemNotFoundError(problem_id)

    def version(self) -> str:
        return "in-memory-1.0"
