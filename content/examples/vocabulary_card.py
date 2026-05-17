"""
Reference example: vocabulary card (exact_equality with pinyin normalisation).

Design decisions demonstrated:
- The canonical is stored in tone-number format ("ni3 hao3"), not diacritic
  format ("nǐ hǎo"). Tone numbers are the natural keyboard-entry format;
  diacritics require special input methods most students don't have.
- normalize: ["pinyin", "whitespace"] converts any diacritic input to
  tone-number form before comparing, so both "nǐ hǎo" and "ni3 hao3" match
  the canonical. Tone accuracy is preserved: "ni4 hao4" does not match.
- Neutral tone variants (bare syllable, trailing 0, trailing 5) all
  canonicalise to 5, so "xie xie", "xie5 xie5", and "xie0 xie0" are
  equivalent and all accepted.
- exact_equality is the right verifier here: pinyin has one conventional
  romanisation per syllable with no algebraically equivalent forms.
  symbolic_equality (SymPy) would be wrong — there's no mathematical
  equivalence to exploit.
- hanzi and meaning sit in params for the consumer to render the card front.
  The verifier only touches params["answer"].
"""

from __future__ import annotations

import random

from problem_instantiation_tool.schemas import Problem

# Canonicals are in tone-number format — the natural input format.
_VOCAB = [
    {"hanzi": "你好", "meaning": "hello", "pinyin": "ni3 hao3"},
    {"hanzi": "谢谢", "meaning": "thank you", "pinyin": "xie4 xie5"},
    {"hanzi": "再见", "meaning": "goodbye", "pinyin": "zai4 jian4"},
    {"hanzi": "老师", "meaning": "teacher", "pinyin": "lao3 shi1"},
    {"hanzi": "学生", "meaning": "student", "pinyin": "xue2 sheng1"},
]


def _generate(rng: random.Random) -> dict:
    entry = rng.choice(_VOCAB)
    return {
        "hanzi": entry["hanzi"],
        "meaning": entry["meaning"],
        "answer": entry["pinyin"],
    }


problem = Problem(
    id="chinese_pinyin_card",
    type_id="vocabulary",
    name="Produce the pinyin for a Chinese character",
    artifact_type="srs_card",
    problem_spec=_generate,
    verifier_spec={
        "kind": "exact_equality",
        "marks_possible": 1,
        "normalize": ["pinyin", "whitespace"],
    },
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(registry=InMemoryRegistry({problem.id: problem}))
    instance = engine.instantiate(problem.id, seed=42)
    p = instance.params
    print(f"Question : What is the pinyin for {p['hanzi']} ({p['meaning']})?")
    print(f"Canonical: {instance.verifier.canonicals[0]}")
    print()

    def show(label, answer, inst=instance):
        attempt = SolutionAttempt(steps=[SubmittedStep(answer)])
        r = inst.verifier.rate(attempt)
        print(
            f"{label}: {r.marks_awarded}/{r.marks_possible}  is_correct={r.is_correct}"
        )

    # 你好 — tone numbers, diacritics, wrong tones
    show("Tone numbers (canonical) ", "ni3 hao3")
    show("Diacritics               ", "nǐ hǎo")
    show("Wrong tones              ", "ni4 hao4")
    show("Wrong answer             ", "wrong")
    print()

    # 谢谢 — neutral tone: bare, 0, and 5 are all equivalent
    xie_xie = next(e for e in _VOCAB if e["hanzi"] == "谢谢")
    xie_instance = engine.instantiate(
        problem.id,
        params={
            "hanzi": xie_xie["hanzi"],
            "meaning": xie_xie["meaning"],
            "answer": xie_xie["pinyin"],
        },
    )
    print(
        f"Question : What is the pinyin for {xie_xie['hanzi']} ({xie_xie['meaning']})?"
    )
    print(f"Canonical: {xie_instance.verifier.canonicals[0]}")
    print()
    show("Tone numbers (xie4 xie5)", "xie4 xie5", xie_instance)
    show("Neutral as 0             ", "xie4 xie0", xie_instance)
    show("Neutral bare             ", "xie4 xie", xie_instance)
    show("Diacritics               ", "xiè xie", xie_instance)
