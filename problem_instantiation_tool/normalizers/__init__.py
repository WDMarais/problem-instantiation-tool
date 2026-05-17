"""
Optional normalizers for consumer-side input format conversion.

These are opt-in utilities — producers list them in verifier_spec normalize
fields, or call them directly before constructing SolutionAttempt. They are
separate from the core engine because they encode domain-specific knowledge
(e.g. Chinese pinyin conventions) rather than general correctness logic.
"""

from .pinyin import normalize as normalize_pinyin

__all__ = ["normalize_pinyin"]
