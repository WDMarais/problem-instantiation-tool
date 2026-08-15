from __future__ import annotations

import unicodedata
from typing import Any

import sympy

from .exceptions import AttemptValidationError, CanonicalResolutionError
from .schemas import (
    MistakeType,
    ProvidedStep,
    SolutionAttempt,
    SolutionRating,
    StepRating,
    SubmittedStep,
    ValidationMode,
)


def _to_sympy(val: Any) -> sympy.Basic:
    if isinstance(val, sympy.Basic):
        return val
    if isinstance(val, bool):
        return sympy.Integer(1) if val else sympy.Integer(0)
    if isinstance(val, (int, float)):
        return sympy.sympify(val)
    if isinstance(val, str):
        try:
            return sympy.sympify(val)
        except Exception:
            return sympy.Symbol(val)
    return sympy.sympify(val)


def _sympy_equal(a: Any, b: Any) -> bool:
    try:
        diff = sympy.simplify(_to_sympy(a) - _to_sympy(b))
        return diff == 0
    except Exception:
        return a == b


# Generous defaults for the symbolic grader's decimal fallback (see
# _numeric_close). Chosen to accept a calculator answer rounded to 2 decimals
# (e.g. 7.07 for √50, 1.41 for √2) while rejecting a sloppier 1-dp value. A
# problem that tests exact/surd form sets ``require_exact_form`` to opt out.
_DECIMAL_ABS_TOL = 5e-3
_DECIMAL_REL_TOL = 1e-3


def _numeric_close(student: Any, canonical: Any, spec: "_StepSpec") -> bool:
    """Fallback for ``symbolic_equality``: does the student's *decimal* match the
    canonical *number* within tolerance?

    Only fires when both sides evaluate to a finite real number — a symbolic
    answer with a free symbol (e.g. a tangent line ``m·x + c``) is not float-able,
    so ``float(...)`` raises and this returns ``False``, leaving such graders
    strictly symbolic. This is how "√50 and 7.07 both score" without loosening
    equation/expression grading.
    """
    try:
        s = float(_to_sympy(student))
        c = float(_to_sympy(canonical))
    except (TypeError, ValueError):
        return False
    if s != s or c != c or s in (float("inf"), float("-inf")):  # NaN / inf guard
        return False
    abs_tol = spec.tolerance or _DECIMAL_ABS_TOL
    rel_tol = spec.rel_tol or _DECIMAL_REL_TOL
    diff = abs(s - c)
    return diff <= abs_tol or diff <= rel_tol * abs(c)


def _eval_symbolic(
    expr: sympy.Basic,
    ca_values: dict[int, Any],
    depends_on: list[int],
) -> Any:
    subs = {
        sympy.Symbol(f"step{j}_result"): _to_sympy(ca_values[j]) for j in depends_on
    }
    result = expr.subs(subs)
    if result.is_Number:
        return int(result) if result.is_Integer else float(result)
    return result


def _answer_param(params: dict, kind: str, key: str) -> Any:
    """Resolve the canonical answer from a conventional key (``answer``/``correct``).

    Falls back to the sole param when there is exactly one (unambiguous). Raises
    rather than silently grabbing the first of several — guessing an answer out of
    {sequence_type, a, d, n} is how a verifier ends up comparing 33 to 'arithmetic'.
    """
    if key in params:
        return params[key]
    if len(params) == 1:
        return next(iter(params.values()))
    raise CanonicalResolutionError(
        kind,
        list(params.keys()),
        f"no '{key}' param and {len(params)} params are ambiguous; add an "
        f"'{key}' param to the generator or a 'param_key' to the verifier spec",
    )


def _set_canonical(params: dict) -> frozenset:
    """Canonical answer set for set_equality.

    Prefers the ``root*`` convention (root1, root2, ...). Falls back to the sole
    param when there is exactly one (a collection becomes the set; a scalar a
    singleton). Raises rather than the old ``frozenset(params.values())`` guess,
    which silently swept unrelated fields (e.g. leading_coeff) into the answer.
    """
    root_vals = [v for k, v in params.items() if k.startswith("root")]
    if root_vals:
        return frozenset(root_vals)
    if len(params) == 1:
        sole = next(iter(params.values()))
        if isinstance(sole, (set, frozenset, list, tuple)):
            return frozenset(sole)
        return frozenset({sole})
    raise CanonicalResolutionError(
        "set_equality",
        list(params.keys()),
        "no 'root*' params; cannot tell which fields form the answer set — name "
        "them root1/root2/... or give the verifier a 'param_key'",
    )


def _value_and_reason_canonical(spec: dict, params: dict) -> dict:
    """Canonical for the compound ``value_and_reason`` step: ``{"value","reason"}``.

    Resolves the value from ``value_key`` (default ``answer``) and the reason *id*
    from ``reason_key`` (default ``reason``), and validates that id against the
    closed ``reason_set`` up front — a reason id the set doesn't know is an
    authoring bug, surfaced at instantiation rather than silently mis-graded.
    """
    vkey = spec.get("value_key", "answer")
    rkey = spec.get("reason_key", "reason")
    for k in (vkey, rkey):
        if k not in params:
            raise CanonicalResolutionError(
                "value_and_reason",
                list(params.keys()),
                f"names '{k}' but the generator produced no such param",
            )
    reason_set = spec.get("reason_set")
    if not isinstance(reason_set, dict) or not reason_set:
        raise CanonicalResolutionError(
            "value_and_reason",
            list(params.keys()),
            "requires a non-empty 'reason_set' dict {canonical_id: [surfaces]}",
        )
    reason_id = params[rkey]
    if reason_id not in reason_set:
        raise CanonicalResolutionError(
            "value_and_reason",
            list(reason_set.keys()),
            f"canonical reason id '{reason_id}' is not a key in the reason_set",
        )
    return {"value": params[vkey], "reason": reason_id}


def _compute_canonicals(specs: list[dict], params: dict) -> list[Any]:
    canonicals: list[Any] = []
    for spec in specs:
        depends_on = spec.get("depends_on")
        symbolic_expr_str = spec.get("symbolic_expr")
        kind = spec.get("kind", "symbolic_equality")

        if depends_on is not None and symbolic_expr_str is not None:
            expr = sympy.sympify(symbolic_expr_str)
            prior = {j: canonicals[j] for j in depends_on}
            canonical = _eval_symbolic(expr, prior, depends_on)
        elif "param_key" in spec:
            key = spec["param_key"]
            if key not in params:
                raise CanonicalResolutionError(
                    kind,
                    list(params.keys()),
                    f"verifier names param_key '{key}', but the generator "
                    f"produced no such param",
                )
            canonical = params[key]
        elif kind == "mcq":
            canonical = _answer_param(params, kind, "correct")
        elif kind == "exact_equality":
            canonical = _answer_param(params, kind, "answer")
        elif kind == "self_graded":
            canonical = True
        elif kind == "set_equality":
            canonical = _set_canonical(params)
        elif kind == "value_and_reason":
            canonical = _value_and_reason_canonical(spec, params)
        elif not params:
            canonical = 0
        else:  # symbolic_equality, numeric_equality, and unknown kinds
            canonical = _answer_param(params, kind, "answer")

        canonicals.append(canonical)
    return canonicals


def _extract_student_set(value: Any) -> frozenset:
    if isinstance(value, frozenset):
        return value
    if isinstance(value, set):
        return frozenset(value)
    if isinstance(value, dict):
        for v in value.values():
            if isinstance(v, (set, frozenset)):
                return frozenset(v)
        return frozenset(value.values())
    return frozenset({value})


def _normalize_string(value: str, normalize: list[str]) -> str:
    s = unicodedata.normalize("NFC", value).lower()
    if "pinyin" in normalize:
        from .normalizers.pinyin import normalize as _pinyin_normalize

        s = _pinyin_normalize(s)
    if "accents" in normalize or "tone_marks" in normalize:
        s = unicodedata.normalize("NFD", s)
        s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    if "whitespace" in normalize:
        s = " ".join(s.split())
    return s


class _StepSpec:
    def __init__(self, spec_dict: dict, canonical: Any) -> None:
        self.kind: str = spec_dict.get("kind", "symbolic_equality")
        self.marks_possible: int = spec_dict.get("marks_possible", 1)
        self.canonical = canonical
        self.depends_on: list[int] | None = spec_dict.get("depends_on")
        raw_expr = spec_dict.get("symbolic_expr")
        self.symbolic_expr: sympy.Basic | None = (
            sympy.sympify(raw_expr) if raw_expr is not None else None
        )
        self.normalize: list[str] = spec_dict.get("normalize", [])
        self.tolerance: float = spec_dict.get("tolerance", 0.0)
        self.rel_tol: float = spec_dict.get("rel_tol", 0.0)
        self.partial_credit: bool = spec_dict.get("partial_credit", True)
        # symbolic_equality accepts a decimal equivalent of a numeric answer by
        # default (generous, matching DBE marking). A problem that requires exact
        # / surd form ("leave your answer in simplest surd form") sets this True.
        self.require_exact_form: bool = spec_dict.get("require_exact_form", False)
        # value_and_reason compound step (see _rate_submitted_step): the value
        # facet reuses an existing comparator; the reason facet is closed-set
        # membership against reason_set, split into value_marks + reason_marks.
        self.value_kind: str = spec_dict.get("value_kind", "symbolic_equality")
        self.value_marks: int = spec_dict.get("value_marks", 1)
        self.reason_set: dict = spec_dict.get("reason_set") or {}
        self.reason_marks: int = spec_dict.get(
            "reason_marks", self.marks_possible - self.value_marks
        )


def _value_facet_ok(student: Any, canonical: Any, spec: "_StepSpec") -> bool:
    """The value half of a value_and_reason step, via an existing comparator."""
    kind = spec.value_kind
    if kind == "numeric_equality":
        try:
            c = float(canonical)
            diff = abs(float(student) - c)
        except (TypeError, ValueError):
            return False
        return diff <= spec.tolerance or diff <= spec.rel_tol * abs(c)
    if kind == "exact_equality":
        return _normalize_string(str(student), spec.normalize) == _normalize_string(
            str(canonical), spec.normalize
        )
    # symbolic_equality (default) — same generous decimal fallback as a plain step
    ok = _sympy_equal(student, canonical)
    if not ok and not spec.require_exact_form:
        ok = _numeric_close(student, canonical, spec)
    return ok


def _reason_facet_ok(
    student_reason: Any, canonical_id: Any, reason_set: dict, normalize: list[str]
) -> bool:
    """The reason half: closed-set membership, not NLP. A phrasing outside the
    curated alias list for this reason id is wrong — the fix is to widen the
    list, never to fuzzy-match."""
    accepted = {_normalize_string(str(s), normalize) for s in reason_set[canonical_id]}
    return _normalize_string(str(student_reason), normalize) in accepted


def _rate_submitted_step(
    spec: _StepSpec,
    student_value: Any,
    ca_values: dict[int, Any],
    validation_mode: ValidationMode,
    step_index: int,
) -> tuple[MistakeType, int]:
    kind = spec.kind

    if kind == "self_graded":
        if not isinstance(student_value, bool):
            raise AttemptValidationError(
                step_index,
                f"SelfGraded expects bool, got {type(student_value).__name__}",
            )
        if student_value:
            return MistakeType.correct, spec.marks_possible
        return MistakeType.computation_error, 0

    if kind == "mcq":
        if str(student_value) == str(spec.canonical):
            return MistakeType.correct, spec.marks_possible
        return MistakeType.computation_error, 0

    if kind == "exact_equality":
        student_norm = _normalize_string(str(student_value), spec.normalize)
        canonical_norm = _normalize_string(str(spec.canonical), spec.normalize)
        if student_norm == canonical_norm:
            return MistakeType.correct, spec.marks_possible
        return MistakeType.computation_error, 0

    if kind == "set_equality":
        student_set = _extract_student_set(student_value)
        canonical_set = frozenset(spec.canonical)
        if student_set == canonical_set:
            return MistakeType.correct, spec.marks_possible
        if spec.partial_credit and spec.marks_possible > 1:
            matched = len(student_set & canonical_set)
            if matched > 0:
                return MistakeType.computation_error, min(matched, spec.marks_possible)
        return MistakeType.computation_error, 0

    if kind == "value_and_reason":
        if (
            not isinstance(student_value, dict)
            or "value" not in student_value
            or "reason" not in student_value
        ):
            raise AttemptValidationError(
                step_index,
                "value_and_reason expects a {'value': ..., 'reason': ...} dict",
            )
        canonical = spec.canonical
        value_ok = _value_facet_ok(student_value["value"], canonical["value"], spec)
        reason_ok = _reason_facet_ok(
            student_value["reason"],
            canonical["reason"],
            spec.reason_set,
            spec.normalize,
        )
        if spec.partial_credit and spec.marks_possible > 1:
            marks = value_ok * spec.value_marks + reason_ok * spec.reason_marks
            if value_ok and reason_ok:
                return MistakeType.correct, marks
            if value_ok:  # right number, wrong/missing theorem — the S/R signal
                return MistakeType.semantic_error, marks
            return MistakeType.computation_error, marks
        # fused: both facets required for the mark (DBE "unjustified → no mark")
        if value_ok and reason_ok:
            return MistakeType.correct, spec.marks_possible
        if value_ok:
            return MistakeType.semantic_error, 0
        return MistakeType.computation_error, 0

    if kind == "numeric_equality":
        try:
            diff = abs(float(student_value) - float(spec.canonical))
            rel_band = spec.rel_tol * abs(float(spec.canonical))
            if diff <= spec.tolerance or diff <= rel_band:
                return MistakeType.correct, spec.marks_possible
        except (TypeError, ValueError):
            pass
        return MistakeType.computation_error, 0

    # symbolic_equality (and unknown kinds — fall through to symbolic comparison)
    is_canonical_match = _sympy_equal(student_value, spec.canonical)
    if not is_canonical_match and not spec.require_exact_form:
        # generous default: accept a calculator decimal for a numeric answer
        # (no-op for symbolic/expression answers — see _numeric_close)
        is_canonical_match = _numeric_close(student_value, spec.canonical, spec)

    if spec.depends_on is None or spec.symbolic_expr is None:
        if is_canonical_match:
            return MistakeType.correct, spec.marks_possible
        return MistakeType.computation_error, 0

    # CA step: compute ca_canonical
    ca_canonical = _eval_symbolic(spec.symbolic_expr, ca_values, spec.depends_on)
    is_ca_match = _sympy_equal(student_value, ca_canonical)
    ca_equals_canonical = _sympy_equal(ca_canonical, spec.canonical)

    # When ProvidedStep reset the chain, ca_canonical == canonical → treat as
    # independent step
    if ca_equals_canonical:
        if is_canonical_match:
            return MistakeType.correct, spec.marks_possible
        return MistakeType.computation_error, 0

    # Full CA logic
    if is_canonical_match and is_ca_match:
        return MistakeType.correct, spec.marks_possible
    if not is_canonical_match and is_ca_match:
        return MistakeType.ca_correct, spec.marks_possible
    if is_canonical_match and not is_ca_match:
        if validation_mode == ValidationMode.LENIENT:
            return MistakeType.correct, spec.marks_possible
        return MistakeType.semantic_error, 0
    return MistakeType.semantic_error, 0


class VerifierChain:
    def __init__(self, step_specs: list[_StepSpec]) -> None:
        self._step_specs = step_specs
        self.canonicals: list[Any] = [s.canonical for s in step_specs]

    def rate(
        self,
        attempt: SolutionAttempt,
        *,
        validation_mode: ValidationMode = ValidationMode.LENIENT,
    ) -> SolutionRating:
        ca_values: dict[int, Any] = {}
        step_ratings: list[StepRating] = []

        n = min(len(attempt.steps), len(self._step_specs))
        for i in range(n):
            step = attempt.steps[i]
            spec = self._step_specs[i]

            if step is None:
                raise AttemptValidationError(i, "None only valid in presented_attempt")

            if isinstance(step, ProvidedStep):
                ca_values[i] = step.value
                continue

            if isinstance(step, SubmittedStep):
                mistake_type, marks_awarded = _rate_submitted_step(
                    spec, step.value, ca_values, validation_mode, i
                )
                ca_values[i] = step.value
                step_ratings.append(
                    StepRating(
                        index=i,
                        marks_awarded=marks_awarded,
                        marks_possible=spec.marks_possible,
                        mistake_type=mistake_type,
                        verifier_type=spec.kind,
                    )
                )

        total_awarded = sum(r.marks_awarded for r in step_ratings)
        total_possible = sum(r.marks_possible for r in step_ratings)
        return SolutionRating(
            steps=step_ratings,
            marks_awarded=total_awarded,
            marks_possible=total_possible,
            is_correct=total_awarded == total_possible,
        )


def build_verifier_chain(
    verifier_spec: dict | list[dict],
    params: dict,
) -> VerifierChain:
    specs = verifier_spec if isinstance(verifier_spec, list) else [verifier_spec]
    canonicals = _compute_canonicals(specs, params)
    step_specs = [_StepSpec(spec, can) for spec, can in zip(specs, canonicals)]
    return VerifierChain(step_specs)
