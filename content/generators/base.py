"""
Base class for linear equation acquisition sheet generators.

Subclasses declare class-level metadata and implement gen().
The make_sheet assembly loop (Sections A/B/C) lives here once.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from fractions import Fraction
from random import Random

from content.generators import Kind
from content.sheet import CollapsedEx, FourStep, PracticeEx, SheetData, ThreeStep

_KIND_ORDER: tuple[Kind, ...] = (Kind.INTEGER, Kind.FRACTION, Kind.SYMBOL)
_SMALL_DENOMS: tuple[int, ...] = (2, 3, 4, 6)

# Excludes x (the unknown) and e i l o (visually ambiguous as numbers/operators).
_VAR_POOL: tuple[str, ...] = tuple("abcdfghkmnpqrstu")


def _fmt(f: Fraction) -> str:
    """Format a Fraction as a KaTeX string."""
    if f.denominator == 1:
        return str(f.numerator)
    sign = "-" if f < 0 else ""
    return rf"{sign}\tfrac{{{abs(f.numerator)}}}{{{f.denominator}}}"


class LinearGenerator(ABC):
    """
    Base for single-equation-type acquisition sheet generators.

    Subclasses declare class-level metadata and implement gen().
    make_sheet() assembles SheetData using the shared A/B/C pattern:
      Section A — n_detailed examples, ordered by kind (int → frac → sym)
      Section B — 12 collapsed examples, cycling kinds
      Section C — 16 practice problems, cycling kinds, alternating starred
    """

    title: str
    caption: str
    output_name: str
    n_detailed: int = 8
    # Per-kind share when all three kinds are active. None = equal split.
    detailed_share: dict[Kind, int] | None = None

    @abstractmethod
    def gen(self, kind: Kind, rng: Random) -> ThreeStep | FourStep:
        """Generate one worked example of the given kind."""
        ...

    def make_sheet(
        self,
        kinds: frozenset[Kind] = frozenset(Kind),
        *,
        seed: int | None = None,
    ) -> SheetData:
        rng = Random(seed)
        active = [k for k in _KIND_ORDER if k in kinds]

        if self.detailed_share is not None and set(active) == set(Kind):
            shares = self.detailed_share
        else:
            base, extra = divmod(self.n_detailed, len(active))
            shares = {k: base + (1 if i < extra else 0) for i, k in enumerate(active)}

        detailed: list[ThreeStep | FourStep] = [
            self.gen(kind, rng) for kind in active for _ in range(shares[kind])
        ]

        collapsed: list[CollapsedEx] = []
        for i in range(12):
            s = self.gen(active[i % len(active)], rng)
            collapsed.append(CollapsedEx(s.equation, s.result))

        practice: list[PracticeEx] = []
        for i in range(16):
            s = self.gen(active[i % len(active)], rng)
            practice.append(PracticeEx(s.equation, s.result if i % 2 == 0 else None))

        return SheetData(
            title=self.title,
            caption=self.caption,
            output_name=self.output_name,
            detailed=detailed,
            collapsed=collapsed,
            practice=practice,
        )
