from __future__ import annotations

import inspect
from enum import Enum
from typing import Any, Callable, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, field_serializer, model_validator

from .exceptions import AttemptValidationError


class ArtifactType(str, Enum):
    srs_card = "srs_card"
    practice = "practice"
    worked_example = "worked_example"
    gap_fill = "gap_fill"


class Difficulty(str, Enum):
    routine = "routine"
    standard = "standard"
    challenging = "challenging"
    non_routine = "non_routine"


class MistakeType(str, Enum):
    correct = "correct"
    ca_correct = "ca_correct"
    semantic_error = "semantic_error"
    computation_error = "computation_error"


class ValidationMode(str, Enum):
    LENIENT = "lenient"
    STRICT = "strict"


class ProvidedStep:
    def __init__(self, value: Any) -> None:
        self.value = value

    def __repr__(self) -> str:
        return f"ProvidedStep({self.value!r})"


class SubmittedStep:
    def __init__(self, value: Any) -> None:
        self.value = value

    def __repr__(self) -> str:
        return f"SubmittedStep({self.value!r})"


class SolutionAttempt(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    steps: list[Any]  # elements: ProvidedStep | SubmittedStep | None


class StepRating(BaseModel):
    index: int
    marks_awarded: int
    marks_possible: int
    mistake_type: MistakeType
    verifier_type: str


class SolutionRating(BaseModel):
    steps: list[StepRating]
    marks_awarded: int
    marks_possible: int
    is_correct: bool


@runtime_checkable
class Verifier(Protocol):
    def rate(
        self,
        attempt: SolutionAttempt,
        *,
        validation_mode: ValidationMode = ValidationMode.LENIENT,
    ) -> SolutionRating: ...


class Problem(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str
    type_id: str
    name: str
    artifact_type: ArtifactType
    problem_spec: dict | Callable
    verifier_spec: dict | list[dict]
    problem_structure: dict | None = None
    required_slots: list[str] | None = None
    difficulty: Difficulty | None = None
    source_id: str | None = None
    blank_steps: list[int] | None = None
    param_names: frozenset[str] | None = None

    @model_validator(mode="after")
    def _validate_artifact_constraints(self) -> Problem:
        if self.artifact_type == ArtifactType.srs_card:
            specs = (
                self.verifier_spec
                if isinstance(self.verifier_spec, list)
                else [self.verifier_spec]
            )
            if len(specs) > 2:
                raise ValueError(
                    "srs_card artifact_type allows at most 2 verifier steps"
                )
            for spec in specs:
                if spec.get("kind") == "self_graded":
                    raise ValueError(
                        f"srs_card artifact_type incompatible with SelfGraded verifier"
                        f" at step {specs.index(spec)}"
                    )
        if self.artifact_type == ArtifactType.gap_fill:
            if self.source_id is None:
                raise ValueError("gap_fill requires source_id")
            if self.blank_steps is None:
                raise ValueError("gap_fill requires blank_steps")
        return self

    @field_serializer("problem_spec")
    def _serialize_problem_spec(self, value: dict | Callable) -> dict:
        if callable(value):
            try:
                source = inspect.getsource(value)
            except (OSError, TypeError):
                source = ""
            return {
                "__type__": "callable",
                "qualname": getattr(value, "__qualname__", repr(value)),
                "source": source,
                "notes": getattr(value, "__doc__", "") or "",
            }
        return value


class ProblemInstance(BaseModel):
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    spec: Problem
    params: dict[str, Any]
    solution: SolutionAttempt
    verifier: Any  # typed as Verifier protocol; Any here avoids circular import
    seed: int | None
    presented_attempt: SolutionAttempt | None
