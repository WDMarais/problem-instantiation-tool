class ProblemEngineError(Exception):
    pass


class ProblemNotFoundError(ProblemEngineError):
    def __init__(self, problem_id: str) -> None:
        super().__init__(problem_id)
        self.problem_id = problem_id


class InstantiationError(ProblemEngineError):
    def __init__(self, problem_id: str, cause: Exception) -> None:
        super().__init__(problem_id)
        self.problem_id = problem_id
        self.cause = cause


class ParamsIncompatibleError(ProblemEngineError):
    def __init__(
        self,
        problem_id: str,
        stored_params: dict,
        current_signature: set[str],
    ) -> None:
        super().__init__(problem_id)
        self.problem_id = problem_id
        self.stored_params = stored_params
        self.current_signature = current_signature


class AttemptValidationError(ProblemEngineError):
    def __init__(self, step_index: int, reason: str = "") -> None:
        super().__init__(step_index, reason)
        self.step_index = step_index
        self.reason = reason
