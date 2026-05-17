"""
Pinyin normalizer — converts diacritic or bare pinyin to canonical tone-number form.

Normalisation contract
----------------------
Input may be any mix of:
  - diacritic vowels   nǐ hǎo
  - tone numbers       ni3 hao3
  - bare syllables     xie  (neutral tone)
  - trailing 0 or 5   xie0 / xie5  (neutral tone variants)

All forms are canonicalised to tone-number format with neutral tone as 5:
  nǐ hǎo  →  ni3 hao3
  xie     →  xie5
  xie0    →  xie5

Tone accuracy is preserved: ni4 hao4 does NOT match ni3 hao3.

Scope
-----
This normalizer handles student input format flexibility only — the
difference between keyboard-entry constraints (can't type ǐ) and the
canonical answer format (ni3 hao3). It is NOT about mathematical
equivalence; that's the engine's job via symbolic_equality / SymPy.

The reverse direction (tone numbers → diacritics) requires pinyin placement
rules (which vowel in a cluster gets the mark) and is never needed here.
"""

from __future__ import annotations

import re
import unicodedata

# Precomposed diacritic vowel → (plain base, tone number 1-4).
_DIACRITIC_TO_BASE_TONE: dict[str, tuple[str, int]] = {
    "ā": ("a", 1),
    "á": ("a", 2),
    "ǎ": ("a", 3),
    "à": ("a", 4),
    "ē": ("e", 1),
    "é": ("e", 2),
    "ě": ("e", 3),
    "è": ("e", 4),
    "ī": ("i", 1),
    "í": ("i", 2),
    "ǐ": ("i", 3),
    "ì": ("i", 4),
    "ō": ("o", 1),
    "ó": ("o", 2),
    "ǒ": ("o", 3),
    "ò": ("o", 4),
    "ū": ("u", 1),
    "ú": ("u", 2),
    "ǔ": ("u", 3),
    "ù": ("u", 4),
    "ǖ": ("ü", 1),
    "ǘ": ("ü", 2),
    "ǚ": ("ü", 3),
    "ǜ": ("ü", 4),
}

_NUMBERED_SYLLABLE = re.compile(r"^([a-züA-ZÜ]+)([0-5])$")


def _syllable_to_numbered(syllable: str) -> str:
    """Convert one space-delimited syllable to canonical tone-number form."""
    for diacritic, (base, tone) in _DIACRITIC_TO_BASE_TONE.items():
        if diacritic in syllable:
            return syllable.replace(diacritic, base) + str(tone)
    m = _NUMBERED_SYLLABLE.match(syllable)
    if m:
        tone = int(m.group(2))
        return m.group(1) + ("5" if tone == 0 else str(tone))
    return syllable + "5"  # bare syllable = neutral tone


def normalize(text: str) -> str:
    """Normalise a pinyin string to canonical tone-number form.

    Assumes syllables are space-delimited. Case-insensitive.
    """
    s = unicodedata.normalize("NFC", text).lower()
    return " ".join(_syllable_to_numbered(w) for w in s.split())
