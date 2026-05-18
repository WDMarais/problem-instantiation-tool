"""
Reference example: trigonometry — three question variants (P2 Q4, 23 marks).

Design decisions demonstrated:

- trig_cast_ratios: Picks a Pythagorean triple (opp, adj, hyp) and a quadrant,
  then applies the CAST sign rules to derive the exact sin/cos/tan ratios.
  Answers are SymPy Rationals (e.g. -3/5), always in lowest terms because the
  triple legs are already coprime. Three param_key steps for sin, cos, tan.
  Swapping opp/adj doubles the variety from four triples to eight distinct shapes.

- trig_equation: Uses a precomputed lookup table of seventeen (trig, n, θ) cases
  where trig(n·β) = exact_special_value and β is a clean integer in [5°, 85°].
  The inner angle θ is always a multiple of 15° (the Gr10 special angles).
  Answer is sympy.Integer(beta_deg); symbolic_equality then accepts "20", 20, or
  sympy.Integer(20) from the student.
  Only n ∈ {2, 3} is included — n=1 without a shift is trivially solved by
  inspection; the non-trivial step is dividing by n after applying the inverse trig.

- trig_special_angles: Constructs a two-term expression f₁(θ₁) OP f₂(θ₂) from
  the exact special-angle values for sin/cos/tan/cosec/cot at 30°, 45°, 60°, 90°.
  OP ∈ {+, −, ×, ÷}. The _is_nice guard rejects results involving √6 (i.e., the
  product of a √2-term and a √3-term); only rational, √2, or √3 results are kept.
  This matches SA Gr10 exam scope: answers are always in ℚ[√2, √3].
  The canonical is a simplified SymPy expression; symbolic_equality accepts any
  algebraically equivalent student submission.
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import Problem

# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

_TRIPLES = [(3, 4, 5), (5, 12, 13), (8, 15, 17), (7, 24, 25)]

# (sign_x, sign_y) per quadrant
_QUAD_SIGNS = {1: (1, 1), 2: (-1, 1), 3: (-1, -1), 4: (1, -1)}

# Precomputed exact values for the special-angles expression problem.
# Key: (func_name, angle_deg).  Values that are 0 or undefined are excluded.
_FUNC_LAMBDAS = {
    "sin": sympy.sin,
    "cos": sympy.cos,
    "tan": sympy.tan,
    "cosec": lambda r: 1 / sympy.sin(r),
    "cot": lambda r: sympy.cos(r) / sympy.sin(r),
}

_SPECIAL_VALUES: dict[tuple[str, int], sympy.Basic] = {}
for _fname, _fn in _FUNC_LAMBDAS.items():
    for _deg in [30, 45, 60, 90]:
        _rad = sympy.pi * _deg / 180
        try:
            _v = sympy.simplify(_fn(_rad))
        except Exception:
            continue
        if _v.is_infinite or not _v.is_real or _v == 0:
            continue
        _SPECIAL_VALUES[(_fname, _deg)] = _v

_SPECIAL_KEYS = list(_SPECIAL_VALUES.keys())

# Precomputed trig-equation cases: trig(n·β) = exact_value, β integer degrees.
_EQ_CASES: list[tuple[str, int, int, sympy.Basic, int]] = []
_EQ_FN = {"sin": sympy.sin, "cos": sympy.cos, "tan": sympy.tan}
for _tname, _tfn in _EQ_FN.items():
    for _n in [2, 3]:
        for _theta in [30, 45, 60, 90]:
            if _theta % _n != 0:
                continue
            _beta = _theta // _n
            if not (5 <= _beta <= 85):
                continue
            _val = sympy.simplify(_tfn(sympy.pi * _theta / 180))
            if _val.is_infinite or _val == 0:
                continue
            _EQ_CASES.append((_tname, _n, _theta, _val, _beta))


def _is_nice(expr: sympy.Basic) -> bool:
    """Return True iff expr is real, finite, and involves only √2 and/or √3."""
    if not expr.is_real:
        return False
    if expr.is_infinite:
        return False
    for p in expr.atoms(sympy.Pow):
        if p.exp == sympy.Rational(1, 2) and p.base not in (
            sympy.Integer(2),
            sympy.Integer(3),
        ):
            return False
    return True


# ---------------------------------------------------------------------------
# 1. trig_cast_ratios
#    Pythagorean triple + quadrant  →  sin θ, cos θ, tan θ  (three param_key steps)
# ---------------------------------------------------------------------------


def _gen_trig_cast(rng: random.Random) -> dict:
    opp, adj, hyp = rng.choice(_TRIPLES)
    if rng.random() < 0.5:
        opp, adj = adj, opp  # double the variety
    quadrant = rng.randint(1, 4)
    sx, sy = _QUAD_SIGNS[quadrant]
    x_val = sx * adj
    y_val = sy * opp
    return {
        "opp": opp,
        "adj": adj,
        "hyp": hyp,
        "quadrant": quadrant,
        "x": x_val,
        "y": y_val,
        "answer_sin": sympy.Rational(y_val, hyp),
        "answer_cos": sympy.Rational(x_val, hyp),
        "answer_tan": sympy.Rational(y_val, x_val),
    }


trig_cast_ratios = Problem(
    id="trig_cast_ratios",
    type_id="trigonometry",
    name="Find sin θ, cos θ, tan θ given a point on the terminal arm",
    artifact_type="practice",
    problem_spec=_gen_trig_cast,
    verifier_spec=[
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "answer_sin"},
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "answer_cos"},
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "answer_tan"},
    ],
)


# ---------------------------------------------------------------------------
# 2. trig_equation
#    trig(n·β) = exact_val  →  β in degrees  (integer, from lookup table)
# ---------------------------------------------------------------------------


def _gen_trig_equation(rng: random.Random) -> dict:
    tname, n, theta, val, beta = rng.choice(_EQ_CASES)
    return {
        "trig": tname,
        "n": n,
        "rhs": val,
        "theta": theta,  # inner special angle (for worked solution reference)
        "answer": sympy.Integer(beta),
    }


trig_equation = Problem(
    id="trig_equation",
    type_id="trigonometry",
    name="Solve a trigonometric equation with a multiplied angle",
    artifact_type="practice",
    problem_spec=_gen_trig_equation,
    verifier_spec={"kind": "symbolic_equality", "marks_possible": 1},
)


# ---------------------------------------------------------------------------
# 3. trig_special_angles
#    f₁(θ₁) OP f₂(θ₂)  →  exact value in ℚ[√2, √3]
# ---------------------------------------------------------------------------


def _gen_trig_special_angles(rng: random.Random) -> dict:
    ops = ["+", "-", "*", "/"]
    while True:
        key1 = rng.choice(_SPECIAL_KEYS)
        key2 = rng.choice(_SPECIAL_KEYS)
        op = rng.choice(ops)
        v1 = _SPECIAL_VALUES[key1]
        v2 = _SPECIAL_VALUES[key2]

        if op == "+":
            result = v1 + v2
        elif op == "-":
            result = v1 - v2
        elif op == "*":
            result = v1 * v2
        else:
            result = v1 / v2

        result = sympy.simplify(result)

        if not _is_nice(result):
            continue
        if result == 0:  # subtraction of equal terms is trivially boring
            continue

        func1, angle1 = key1
        func2, angle2 = key2
        return {
            "func1": func1,
            "angle1": angle1,
            "func2": func2,
            "angle2": angle2,
            "op": op,
            "answer": result,
        }


trig_special_angles = Problem(
    id="trig_special_angles",
    type_id="trigonometry",
    name="Evaluate a trigonometric expression using special angle exact values",
    artifact_type="practice",
    problem_spec=_gen_trig_special_angles,
    verifier_spec={"kind": "symbolic_equality", "marks_possible": 1},
)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    all_problems = {
        p.id: p for p in [trig_cast_ratios, trig_equation, trig_special_angles]
    }
    engine = Engine(registry=InMemoryRegistry(all_problems))

    def show(label, instance, *answers):
        attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
        r = instance.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  is_correct={r.is_correct}"
        )

    # --- trig_cast_ratios ---
    print("=== trig_cast_ratios ===")
    inst = engine.instantiate(trig_cast_ratios.id, seed=42)
    p = inst.params
    print(f"  Point P({p['x']}, {p['y']}), r={p['hyp']}  (Quadrant {p['quadrant']})")
    sin_c, cos_c, tan_c = inst.verifier.canonicals
    print(f"  sin θ = {sin_c},  cos θ = {cos_c},  tan θ = {tan_c}")
    show("All correct           ", inst, sin_c, cos_c, tan_c)
    show("sin wrong (positive)  ", inst, abs(sin_c), cos_c, tan_c)
    show("All wrong signs       ", inst, -sin_c, -cos_c, -tan_c)

    print()

    # --- trig_equation (show the exam-like tan case) ---
    print("=== trig_equation (all 17 cases at a glance) ===")
    seen = set()
    for seed in range(200):
        inst = engine.instantiate(trig_equation.id, seed=seed)
        p = inst.params
        key = (p["trig"], p["n"])
        if key not in seen:
            seen.add(key)
            beta = inst.verifier.canonicals[0]
            print(f"  {p['trig']}({p['n']}·β) = {p['rhs']}  →  β = {beta}°")
    print()

    # verify correct answer always scores
    inst = engine.instantiate(trig_equation.id, seed=3)  # tan(3β) = √3, β=20
    p = inst.params
    print(f"  Focus: {p['trig']}({p['n']}·β) = {p['rhs']}")
    ans = inst.verifier.canonicals[0]
    show("Correct (20)   ", inst, ans)
    show("Wrong (60)     ", inst, 60)
    show("Wrong (rhs val)", inst, p["rhs"])

    print()

    # --- trig_special_angles ---
    print("=== trig_special_angles (sample) ===")
    for seed in [1, 5, 12, 20, 31]:
        inst = engine.instantiate(trig_special_angles.id, seed=seed)
        p = inst.params
        ans = inst.verifier.canonicals[0]
        print(
            f"  {p['func1']} {p['angle1']}° {p['op']} {p['func2']} {p['angle2']}°  =  {ans}"
        )
        r = inst.verifier.rate(SolutionAttempt(steps=[SubmittedStep(ans)]))
        assert r.is_correct
    print("  (all verified correct)")
