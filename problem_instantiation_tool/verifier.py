from __future__ import annotations

import unicodedata
from typing import Any

import sympy

from .exceptions import AttemptValidationError
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
            canonical = params.get(spec["param_key"], 0)
        elif kind == "mcq":
            canonical = params.get("correct", next(iter(params.values()), None))
        elif kind == "exact_equality":
            canonical = params.get("answer", next(iter(params.values()), None))
        elif kind == "self_graded":
            canonical = True
        elif kind == "set_equality":
            root_vals = [v for k, v in params.items() if k.startswith("root")]
            canonical = (
                frozenset(root_vals) if root_vals else frozenset(params.values())
            )
        else:  # symbolic_equality (and unknown kinds)
            canonical = (
                params.get("answer", next(iter(params.values()), 0)) if params else 0
            )

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
        self.partial_credit: bool = spec_dict.get("partial_credit", True)


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

    if kind == "numeric_equality":
        tolerance = spec.tolerance
        try:
            if abs(float(student_value) - float(spec.canonical)) <= tolerance:
                return MistakeType.correct, spec.marks_possible
        except (TypeError, ValueError):
            pass
        return MistakeType.computation_error, 0

    # symbolic_equality (and unknown kinds — fall through to symbolic comparison)
    is_canonical_match = _sympy_equal(student_value, spec.canonical)

    if spec.depends_on is None or spec.symbolic_expr is None:
        if is_canonical_match:
            return MistakeType.correct, spec.marks_possible
        return MistakeType.computation_error, 0

    # CA step: compute ca_canonical
    ca_canonical = _eval_symbolic(spec.symbolic_expr, ca_values, spec.depends_on)
    is_ca_match = _sympy_equal(student_value, ca_canonical)
    ca_equals_canonical = _sympy_equal(ca_canonical, spec.canonical)

    # When ProvidedStep reset the chain, ca_canonical == canonical → treat as independent step
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
