"""
Reference example: grouped data statistics (least-frequent class, percentile
class, modal-class pie angle, histogram).

Design decisions demonstrated:
- Interval labels use the SA convention "a ≤ x < b". exact_equality does a
  case-insensitive string match, so the student must reproduce this format
  exactly. In practice, a UI would provide a dropdown or multiple-choice
  selection, making format variation a non-issue. For programmatic submission,
  the canonical string from params["labels"] is the expected input.
- Frequencies are generated via stars-and-bars (n-1 distinct cut points in
  [1, total-1]) so that all intervals have frequency ≥ 1 and they sum exactly
  to total. Guards enforce a unique modal class and a unique least-frequent
  class; datasets with ties are resampled.
- The percentile question asks which class interval contains the pth percentile
  (p chosen from {40, 50, 60, 70}). The answer is the first interval where
  cumulative frequency ≥ p/100 × total. A guard resamples if this falls in the
  first interval (trivially obvious answer).
- Pie angle uses numeric_equality with tolerance 1° to accept rounding to the
  nearest degree.
- The histogram step is self_graded — the student confirms they drew it
  correctly against a reference. Drawn output cannot be auto-verified.
"""

from __future__ import annotations

import random

from problem_instantiation_tool.schemas import Problem


def _random_freqs(rng: random.Random, n: int, total: int) -> list[int]:
    cuts = sorted(rng.sample(range(1, total), n - 1))
    prev = 0
    result = []
    for c in cuts:
        result.append(c - prev)
        prev = c
    result.append(total - prev)
    return result


def _generate(rng: random.Random) -> dict:
    n_intervals = rng.randint(4, 5)
    lo = rng.choice([0, 10, 20, 30])
    width = rng.choice([10, 20])
    total = rng.choice([80, 100, 120])
    percentile_p = rng.choice([40, 50, 60, 70])

    while True:
        freqs = _random_freqs(rng, n_intervals, total)

        if freqs.count(max(freqs)) != 1:
            continue
        if freqs.count(min(freqs)) != 1:
            continue

        cumfreqs = []
        cf = 0
        for f in freqs:
            cf += f
            cumfreqs.append(cf)

        pct_pos = percentile_p / 100 * total
        pct_idx = next(i for i, cf in enumerate(cumfreqs) if cf >= pct_pos)
        if pct_idx == 0:
            continue  # trivially-obvious answer — resample

        break

    intervals = [(lo + i * width, lo + (i + 1) * width) for i in range(n_intervals)]
    labels = [f"{a} ≤ x < {b}" for a, b in intervals]
    modal_idx = freqs.index(max(freqs))
    least_idx = freqs.index(min(freqs))

    return {
        "intervals": intervals,
        "labels": labels,
        "freqs": freqs,
        "total": total,
        "modal_class": labels[modal_idx],
        "modal_freq": freqs[modal_idx],
        "least_freq_class": labels[least_idx],
        "percentile_p": percentile_p,
        "percentile_class": labels[pct_idx],
        "pie_angle": round(freqs[modal_idx] / total * 360),
    }


problem = Problem(
    id="stats_grouped",
    type_id="statistics",
    name="Least-frequent class, percentile class, and pie angle from a frequency table",
    artifact_type="practice",
    problem_spec=_generate,
    verifier_spec=[
        {
            "kind": "exact_equality",
            "marks_possible": 1,
            "param_key": "least_freq_class",
        },
        {
            "kind": "exact_equality",
            "marks_possible": 1,
            "param_key": "percentile_class",
        },
        {
            "kind": "numeric_equality",
            "marks_possible": 1,
            "param_key": "pie_angle",
            "tolerance": 1,
        },
        {"kind": "self_graded", "marks_possible": 1},
    ],
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(registry=InMemoryRegistry({problem.id: problem}))
    instance = engine.instantiate(problem.id, seed=42)
    p = instance.params

    print("Frequency table:")
    for label, freq in zip(p["labels"], p["freqs"]):
        bar = "█" * (freq // 2)
        print(f"  {label:15s}  {freq:3d}  {bar}")
    print(f"  Total: {p['total']}")
    print()
    print(f"Modal class           : {p['modal_class']}  (freq {p['modal_freq']})")
    print(f"Least-frequent class  : {p['least_freq_class']}")
    print(f"{p['percentile_p']}th percentile class : {p['percentile_class']}")
    print(f"Pie angle (modal)     : {p['pie_angle']}°")
    print()

    def show(label, *answers):
        attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
        r = instance.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  is_correct={r.is_correct}"
        )

    show(
        "All correct                          ",
        p["least_freq_class"],
        p["percentile_class"],
        p["pie_angle"],
        True,
    )
    show(
        "Wrong least-freq class               ",
        p["labels"][0],
        p["percentile_class"],
        p["pie_angle"],
        True,
    )
    show(
        "Pie angle off by 1° (within tol)     ",
        p["least_freq_class"],
        p["percentile_class"],
        p["pie_angle"] + 1,
        True,
    )
    show(
        "Pie angle off by 2° (outside tol)    ",
        p["least_freq_class"],
        p["percentile_class"],
        p["pie_angle"] + 2,
        True,
    )
    show(
        "Student marks histogram wrong        ",
        p["least_freq_class"],
        p["percentile_class"],
        p["pie_angle"],
        False,
    )
