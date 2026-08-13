"""
Calculus, archetype 6 — ``motion_calculus``.

The oracle re-derives the kinematics independently: velocity as s′, the time of
maximum velocity by solving s″(t)=0, and the maximum velocity by evaluating v
there. It confirms that a(t*)=0 and that the velocity really has a maximum
(v″ = a′ < 0) rather than a minimum. Distribution tests guard integer answers and
that the time of maximum velocity is physical (t* > 0).
"""

import sympy

from content.examples.motion_calculus import motion_calculus
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

_t = sympy.Symbol("t")


def _eng():
    return Engine(registry=InMemoryRegistry({motion_calculus.id: motion_calculus}))


def _rate(inst, *answers):
    steps = [SubmittedStep(a) for a in answers]
    return inst.verifier.rate(SolutionAttempt(steps=steps))


def _s(p):
    return p["alpha"] * _t**3 + p["beta"] * _t**2 + p["gamma"] * _t + p["delta"]


# --- generator correctness (independent oracle) -----------------------------


def test_velocity_is_the_first_derivative():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(motion_calculus.id, seed=seed).params
        assert sympy.simplify(sympy.diff(_s(p), _t) - p["velocity"]) == 0, seed


def test_time_of_max_velocity_solves_acceleration_zero():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(motion_calculus.id, seed=seed).params
        accel = sympy.diff(_s(p), _t, 2)
        roots = sympy.solve(accel, _t)
        assert roots == [p["t_max"]], (seed, p["displacement_latex"])


def test_max_velocity_is_v_at_that_time():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(motion_calculus.id, seed=seed).params
        assert p["velocity"].subs(_t, p["t_max"]) == p["max_velocity"], seed


def test_stationary_point_is_a_velocity_maximum():
    eng = _eng()
    for seed in range(80):
        p = eng.instantiate(motion_calculus.id, seed=seed).params
        # velocity''  = acceleration' < 0  ⇒  velocity has a maximum, not a minimum
        assert sympy.diff(p["velocity"], _t, 2) < 0, seed


def test_distribution_is_physical_and_integer():
    eng = _eng()
    seen_t = set()
    for seed in range(120):
        p = eng.instantiate(motion_calculus.id, seed=seed).params
        assert p["t_max"] > 0, seed  # a physical (positive) time
        assert isinstance(p["max_velocity"], int), seed
        assert p["alpha"] < 0, seed
        seen_t.add(p["t_max"])
    assert len(seen_t) >= 3


# --- verifier round-trips ---------------------------------------------------


def test_full_marks_on_all_three_steps():
    inst = _eng().instantiate(motion_calculus.id, seed=1)
    p = inst.params
    r = _rate(inst, p["velocity"], p["t_max"], p["max_velocity"])
    assert r.is_correct and r.marks_awarded == 3


def test_velocity_right_time_wrong_keeps_one_mark():
    inst = _eng().instantiate(motion_calculus.id, seed=1)
    p = inst.params
    r = _rate(inst, p["velocity"], p["t_max"] + 2, p["max_velocity"] + 9)
    assert r.marks_awarded == 1 and not r.is_correct


def test_equivalent_velocity_form_is_accepted():
    inst = _eng().instantiate(motion_calculus.id, seed=2)
    p = inst.params
    expanded = p["velocity"].expand() + 0  # a trivially-equal rearrangement
    r = _rate(inst, expanded, p["t_max"], p["max_velocity"])
    assert r.is_correct and r.marks_awarded == 3


def test_all_wrong_scores_zero():
    inst = _eng().instantiate(motion_calculus.id, seed=1)
    r = _rate(inst, sympy.Integer(0), 99, 99)
    assert r.marks_awarded == 0
