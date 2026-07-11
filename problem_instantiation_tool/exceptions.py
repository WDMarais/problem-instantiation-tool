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


class ScopeViolationError(ProblemEngineError):
    """A generated instance falls outside its declared in-scope predicate (F1): a
    mathematically valid but *pedagogically wrong* draw — non-integer params, roots
    out of the intended band, a discriminant that yields irrational/complex roots,
    etc. The memo would be correct for a problem the tutee should never have seen.

    Raised loudly so (a) a bad draw can never reach a tutee via the per-draw guard,
    and (b) the sweep fails in CI. The fix is in the *content*: tighten the
    generator's range or its predicate — never suppress it."""

    def __init__(
        self,
        problem_id: str,
        params: dict,
        reasons: list[str],
        seed: int | None = None,
    ) -> None:
        super().__init__(problem_id, reasons)
        self.problem_id = problem_id
        self.params = params
        self.reasons = reasons
        self.seed = seed


class CanonicalResolutionError(ProblemEngineError):
    """A verifier step could not determine its canonical answer from the params:
    no ``param_key``, no conventional answer key (``answer``/``correct``), and the
    params are ambiguous (more than one, so the answer cannot be guessed). The fix
    is in the *content* — name the answer param or give the verifier a ``param_key``
    — not to let the verifier silently pick an arbitrary field."""

    def __init__(self, kind: str, available_keys: list[str], reason: str = "") -> None:
        super().__init__(kind, available_keys, reason)
        self.kind = kind
        self.available_keys = available_keys
        self.reason = reason
