"""
Data types for acquisition sheets.

This module is the contract between content authors (the sheet data files)
and renderers (content/renderers/). All renderer inputs are defined here.

All LaTeX strings use KaTeX-compatible syntax.
"""

from __future__ import annotations

from dataclasses import dataclass, field


class LayoutOverflowError(ValueError):
    pass


@dataclass(frozen=True)
class ThreeStep:
    """One worked example: equation → operation → result."""

    equation: str
    operation: str
    result: str


@dataclass(frozen=True)
class FourStep:
    """One worked example with an intermediate form (e.g. a/x=b → a=bx → x=a/b)."""

    equation: str
    operation: str
    intermediate: str
    result: str
    model_ref: str = "ax = b"


@dataclass(frozen=True)
class FiveStep:
    """Two chained operations: equation → op1 → mid-form → op2 → result."""

    equation: str
    op1: str
    mid: str
    op2: str
    result: str


@dataclass(frozen=True)
class SixStep:
    """Three chained operations: equation → op1 → mid1 → op2 → mid2 → result."""

    equation: str
    op1: str
    mid1: str
    op2: str
    mid2: str
    result: str


@dataclass(frozen=True)
class CollapsedEx:
    """One collapsed shorthand example: equation ⟹ answer."""

    equation: str
    answer: str


@dataclass(frozen=True)
class PracticeEx:
    """One own-work problem. answer=None means no answer is printed.

    Layouts (mutually exclusive, checked in order):
    - equation2 set: two equation lines + "x = [inline box]" answer slot.
    - definition + call_expr set: definition on top, "call_expr = [inline box]" below.
    - default: single equation line + full-width answer box.
    """

    equation: str
    answer: str | None
    definition: str | None = None
    call_expr: str | None = None
    equation2: str | None = None
    answer_var: str = "x"  # variable shown in "answer_var = [box]" for equation2 layout


# Empirically verified limits for the A4 grid layout.
_MAX_DETAILED_THREE = 8  # 2-col × 4 rows, 3-step entries
_MAX_DETAILED_FOUR = 6  # 2-col × 3 rows, 4-step entries
_MAX_DETAILED_FIVE = 4  # 2-col × 2 rows, 5-step entries
_MAX_DETAILED_SIX = 4  # 2-col × 2 rows, 6-step entries (verify visually)
_MAX_COLLAPSED = 12  # 3-col × 4 rows
_MAX_PRACTICE = 18  # 4-col × 4 rows default; 3-col × 6 rows with practice_cols=3


@dataclass
class SheetData:
    title: str
    caption: str
    detailed: list[ThreeStep | FourStep | FiveStep | SixStep]
    collapsed: list[CollapsedEx]
    practice: list[PracticeEx]
    output_name: str = field(default="sheet.html")
    practice_intro: str = field(default="")
    practice_cols: int = field(default=4)

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        if not self.detailed:
            raise LayoutOverflowError("detailed list must not be empty")

        first_type = type(self.detailed[0])
        if not all(type(d) is first_type for d in self.detailed):
            raise LayoutOverflowError(
                "All detailed examples must be the same type (ThreeStep, FourStep, FiveStep, or SixStep)"
            )

        if first_type is ThreeStep and len(self.detailed) > _MAX_DETAILED_THREE:
            raise LayoutOverflowError(
                f"ThreeStep layout fits at most {_MAX_DETAILED_THREE} detailed examples; "
                f"got {len(self.detailed)}"
            )
        if first_type is FourStep and len(self.detailed) > _MAX_DETAILED_FOUR:
            raise LayoutOverflowError(
                f"FourStep layout fits at most {_MAX_DETAILED_FOUR} detailed examples; "
                f"got {len(self.detailed)}"
            )
        if first_type is FiveStep and len(self.detailed) > _MAX_DETAILED_FIVE:
            raise LayoutOverflowError(
                f"FiveStep layout fits at most {_MAX_DETAILED_FIVE} detailed examples; "
                f"got {len(self.detailed)}"
            )
        if first_type is SixStep and len(self.detailed) > _MAX_DETAILED_SIX:
            raise LayoutOverflowError(
                f"SixStep layout fits at most {_MAX_DETAILED_SIX} detailed examples; "
                f"got {len(self.detailed)}"
            )

        if len(self.collapsed) > _MAX_COLLAPSED:
            raise LayoutOverflowError(
                f"Collapsed section fits at most {_MAX_COLLAPSED} examples; "
                f"got {len(self.collapsed)}"
            )

        if len(self.practice) > _MAX_PRACTICE:
            raise LayoutOverflowError(
                f"Practice section fits at most {_MAX_PRACTICE} problems; "
                f"got {len(self.practice)}"
            )
