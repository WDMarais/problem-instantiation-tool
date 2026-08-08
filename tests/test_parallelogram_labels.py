"""
Vertex-labelling variety for the parallelogram angle-chases.

The geometry is defined by positional *roles* A→B→C→D (anticlockwise); the
letters shown to the student are a separate, randomised naming so they cannot
pattern-match on a fixed "ABCD". The naming lives in the generator (reproducible
param layer) and is consumed by the template for both the figure and the prose.
"""

import pytest

from content.examples.parallelogram_angles import (
    parallelogram_alternate,
    parallelogram_cointerior,
    parallelogram_opposite,
)
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from worksheets.generate import (
    template_parallelogram_alternate,
    template_parallelogram_cointerior,
    template_parallelogram_opposite,
)

_ALL = [parallelogram_cointerior, parallelogram_opposite, parallelogram_alternate]
_ROLES = ("A", "B", "C", "D")


def _engine():
    return Engine(registry=InMemoryRegistry({p.id: p for p in _ALL}))


@pytest.mark.parametrize("problem", _ALL, ids=[p.id for p in _ALL])
def test_generator_emits_four_distinct_role_letters(problem):
    """Every instance carries a `labels` map role→letter with four distinct,
    real letters covering all four roles."""
    inst = _engine().instantiate(problem.id, seed=3)
    labels = inst.params["labels"]
    assert set(labels) == set(_ROLES)
    letters = [labels[r] for r in _ROLES]
    assert len(set(letters)) == 4
    assert all(isinstance(x, str) and x.isalpha() and len(x) == 1 for x in letters)


@pytest.mark.parametrize("problem", _ALL, ids=[p.id for p in _ALL])
def test_labelling_varies_across_seeds(problem):
    """Across many seeds the naming is not always 'ABCD' — at least three
    distinct namings appear, so students can't overindex on the letters."""
    eng = _engine()
    namings = set()
    for seed in range(40):
        labels = eng.instantiate(problem.id, seed=seed).params["labels"]
        namings.add(tuple(labels[r] for r in _ROLES))
    assert len(namings) >= 3
    assert ("A", "B", "C", "D") != next(iter(namings)) or len(namings) > 1


_TEMPLATES = {
    parallelogram_cointerior.id: template_parallelogram_cointerior,
    parallelogram_opposite.id: template_parallelogram_opposite,
    parallelogram_alternate.id: template_parallelogram_alternate,
}


@pytest.mark.parametrize("problem", _ALL, ids=[p.id for p in _ALL])
def test_template_uses_mapped_letters_not_fixed_abcd(problem):
    """Force a PQRS naming: the instruction, the worked steps and the drawn
    figure must speak PQRS, never a stray hard-coded ABCD."""
    inst = _engine().instantiate(problem.id, seed=5)
    params = dict(inst.params)
    params["labels"] = {"A": "P", "B": "Q", "C": "R", "D": "S"}
    card = _TEMPLATES[problem.id](params)

    prose = (
        card.instruction + " " + " ".join(card.worked_steps) + " " + card.display_math
    )
    assert "ABCD" not in prose
    # the parallelogram is named by its four mapped letters, in role order
    assert "PQRS" in prose.replace("$", "")
    # figure labels come through too (P is role A, the given-angle vertex)
    assert ">P<" in card.graph_svg or ">P</text>" in card.graph_svg
    for stray in ("ABCD", ">A<", ">B<", ">C<", ">D<"):
        assert stray not in card.graph_svg


def test_two_namings_differ_between_seeds():
    """Sanity: two different seeds can produce two different namings (guards a
    generator that hard-pins one naming)."""
    eng = _engine()
    a = eng.instantiate(parallelogram_cointerior.id, seed=1).params["labels"]
    picks = {
        tuple(
            eng.instantiate(parallelogram_cointerior.id, seed=s).params["labels"][r]
            for r in _ROLES
        )
        for s in range(20)
    }
    assert len(picks) >= 2
    assert isinstance(a["A"], str)
