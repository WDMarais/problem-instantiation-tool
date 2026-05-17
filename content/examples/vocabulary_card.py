"""
Reference example: vocabulary card (exact_equality with normalisation).

Design decisions demonstrated:
- exact_equality is appropriate when the answer is a fixed string with no
  algebraic equivalent — pinyin has one correct romanisation per syllable,
  not a family of symbolically equal expressions.
- normalize: ["tone_marks", "whitespace"] accepts ni hao / nǐ hǎo / Ni Hao
  as equivalent. Tone mark stripping is the minimal concession for keyboard
  entry; case-folding is always applied (it's free and never wrong here).
  Whitespace normalisation collapses multiple spaces and trims, so "nǐ  hǎo"
  and "nǐ hǎo" are the same.
- The generator puts `answer` (pinyin) in params alongside the question
  params (hanzi, meaning). exact_equality picks params["answer"] as the
  canonical; the other params exist for the consumer to render the card front.
- This is a code generator because the vocabulary list is a runtime value,
  not a range. Dict specs only describe parameter spaces via *_range keys;
  arbitrary choice from a list requires a callable.
"""

from __future__ import annotations

import random

from problem_instantiation_tool.schemas import Problem

_VOCAB = [
    {"hanzi": "你好", "meaning": "hello", "pinyin": "nǐ hǎo"},
    {"hanzi": "谢谢", "meaning": "thank you", "pinyin": "xiè xie"},
    {"hanzi": "再见", "meaning": "goodbye", "pinyin": "zài jiàn"},
    {"hanzi": "老师", "meaning": "teacher", "pinyin": "lǎo shī"},
    {"hanzi": "学生", "meaning": "student", "pinyin": "xué shēng"},
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
        "normalize": ["tone_marks", "whitespace"],
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

    for label, answer in [
        ("Tones correct  ", p["answer"]),
        (
            "Tones stripped ",
            p["answer"]
            .replace("ǐ", "i")
            .replace("ǎ", "a")
            .replace("è", "e")
            .replace("ì", "i")
            .replace("ā", "a")
            .replace("ē", "e")
            .replace("ù", "u")
            .replace("ō", "o")
            .replace("ī", "i"),
        ),
        ("Wrong answer   ", "wrong"),
    ]:
        attempt = SolutionAttempt(steps=[SubmittedStep(answer)])
        r = instance.verifier.rate(attempt)
        print(
            f"{label}: {r.marks_awarded}/{r.marks_possible}  is_correct={r.is_correct}"
        )
