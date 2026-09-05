"""
Probability × expected value — ``game_expected_payout`` (P1 Q10.2).

A fun-park game: roll a fair die and draw a card. A player wins on an odd roll AND a
picture card, so the win probability is the product of two independent events,

    P(win) = P(odd) · P(picture) = 3/6 · 16/52 = 2/13.

The owner wants a fixed percentage profit on the hour's takings, so the payout pool is
the complementary fraction of the revenue, and the maximum amount payable to each
winner is that pool shared over the *expected* number of winners:

    revenue          = players · price
    payout_pool      = (1 − profit) · revenue
    expected_winners = players · P(win)
    max_payout       = payout_pool / expected_winners

``players`` is drawn as a multiple of 13 so the expected winners is a whole number
(as the memo needs), and the parameter pools keep ``max_payout`` a clean two-decimal
rand amount. Everything is exact SymPy ``Rational``. Well-posed by construction, so no
F1 scope predicate.

Engine-graded canonical total = 2 of the 6 headline marks: P(win) and the final
max payout — the two values a marker circles. Forming the revenue, the payout pool and
the expected-winner count are the hand-marked method lines. Both graded values use
``symbolic_equality`` (accepts the fraction 2/13 or the two-decimal rand).
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import CorpusAnchor, Problem

# A standard die (odd faces 1,3,5) and a 52-card deck with 16 picture cards fix
# P(win) = 1/2 · 4/13 = 2/13 exactly; the exam varies the money, not the game.
_DIE_SIDES = 6
_ODD_FACES = 3
_DECK = 52
_PICTURE = 16  # 4 suits × 4 picture cards

_PLAYERS = (130, 156, 182, 208, 234, 260)  # 13 × {10, 12, 14, 16, 18, 20}
_PRICE = (5, 10, 15, 20)  # rand per game
_PROFIT = (  # target profit as a fraction of revenue
    sympy.Rational(1, 2),
    sympy.Rational(3, 5),
    sympy.Rational(7, 10),
    sympy.Rational(4, 5),
)


def _gen(rng: random.Random) -> dict:
    players = rng.choice(_PLAYERS)
    price = rng.choice(_PRICE)
    profit = rng.choice(_PROFIT)

    p_odd = sympy.Rational(_ODD_FACES, _DIE_SIDES)
    p_picture = sympy.Rational(_PICTURE, _DECK)
    p_win = p_odd * p_picture  # 2/13

    revenue = players * price
    payout_pool = (1 - profit) * revenue
    expected_winners = players * p_win  # whole number: players ÷ 13 is integer
    max_payout = payout_pool / expected_winners

    return {
        "die_sides": _DIE_SIDES,
        "odd_faces": _ODD_FACES,
        "deck": _DECK,
        "picture": _PICTURE,
        "players": players,
        "price": price,
        "profit": profit,
        "p_odd": p_odd,
        "p_picture": p_picture,
        "p_win": p_win,  # 10.2 checkpoint
        "revenue": revenue,
        "payout_pool": payout_pool,
        "expected_winners": int(expected_winners),
        "max_payout": max_payout,  # 10.2 final answer
    }


game_expected_payout = Problem(
    id="game_expected_payout",
    type_id="game_expected_payout",
    name="Fun-park game — max payout per winner from win probability and profit target",
    artifact_type="practice",
    problem_spec=_gen,
    verifier_spec=[
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "p_win"},
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "max_payout"},
    ],
    corpus_anchor=CorpusAnchor(
        paper="2025 May/June P1",
        question="10.2",
        marks=6,
    ),
)


if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    engine = Engine(
        registry=InMemoryRegistry({game_expected_payout.id: game_expected_payout})
    )
    for seed in (1, 7, 13):
        inst = engine.instantiate(game_expected_payout.id, seed=seed)
        p = inst.params
        print(
            f"seed {seed}: players={p['players']} price=R{p['price']} "
            f"profit={p['profit']} → P(win)={p['p_win']} pool=R{p['payout_pool']} "
            f"winners={p['expected_winners']} max=R{float(p['max_payout']):.2f}"
        )
        attempt = SolutionAttempt(
            steps=[SubmittedStep(p["p_win"]), SubmittedStep(p["max_payout"])]
        )
        r = inst.verifier.rate(attempt)
        print(f"  all-correct → {r.marks_awarded}/{r.marks_possible} ok={r.is_correct}")
