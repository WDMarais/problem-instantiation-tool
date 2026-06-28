"""
Trig graph properties — four question variants (P2 Q6, 9 marks).

Expanded parameter space to cover the full range of Gr10 exam variation:
  - Amplitude a ∈ {1..5}, both sin and cos as the function under test
  - Period factor n ∈ {1, 2}: fn(nx), period = 360°/n
  - Vertical offset q ∈ {−3..3}: fn(nx) + q
  - Phase shift θ ∈ multiples of 45° for range only — phase shift does not
    affect range, so it probes whether students know that amplitude determines
    range, not where the cycle starts

trig_graph_amplitude  — graph-dependent placeholder (renderer needed)
trig_graph_range      — a·fn(nx+θ)+q: range is [q−a, q+a] regardless of fn, n, θ
trig_graph_decreasing — a·fn(nx)+q: decreasing interval depends on fn and n only;
                        domain chosen so the full interval is visible
trig_graph_solve      — a·sin(nx)−b·cos(nx)=k via R-formula; domain [0°, 360°/n]
"""

from __future__ import annotations

import math
import random

import sympy

from problem_instantiation_tool.schemas import Problem

_A_CHOICES = [1, 2, 3, 4, 5]
_N_CHOICES = [1, 2]
_Q_CHOICES = list(range(-3, 4))
_THETA_CHOICES = [0, 45, 90, 135, 180, 225, 270, 315]
_FN_CHOICES = ["sin", "cos"]
_A_SOLVE = [1, 2, 3]
_B_SOLVE = [1, 2, 3]


# ── LaTeX helpers ─────────────────────────────────────────────────────────────


def _trig_arg_latex(n: int, theta: int) -> str:
    """LaTeX for argument nx + theta (theta in degrees, 0 suppressed)."""
    n_part = "x" if n == 1 else f"{n}x"
    if theta == 0:
        return n_part
    sign, t = ("+", theta) if theta > 0 else ("-", -theta)
    return rf"{n_part} {sign} {t}^\circ"


def _inner_latex(fn: str, n: int, theta: int) -> str:
    """LaTeX for fn(arg) — no amplitude, no offset."""
    arg = _trig_arg_latex(n, theta)
    return rf"\{fn}({arg})" if (n > 1 or theta != 0) else rf"\{fn} x"


def _trig_expr_latex(fn: str, a: int, n: int, theta: int, q: int) -> str:
    """LaTeX for a·fn(nx+θ)+q."""
    inner = _inner_latex(fn, n, theta)
    coeff = "" if a == 1 else str(a)
    expr = f"{coeff}{inner}"
    if q > 0:
        expr += f" + {q}"
    elif q < 0:
        expr += f" - {abs(q)}"
    return expr


# ── graph encoding ────────────────────────────────────────────────────────────


def _graph_encoding(
    fn_f: str, a: int, fn_g: str, b: int, n: int, x_domain: tuple[int, int]
) -> dict:
    period = 360 // n
    return {
        "curves": [
            {"id": "f", "func": fn_f, "amplitude": a, "period_deg": period},
            {"id": "g", "func": fn_g, "amplitude": b, "period_deg": period},
        ],
        "x_domain_deg": list(x_domain),
    }


# ── 1. trig_graph_amplitude ────────────────────────────────────────────────────


def _gen_amplitude(rng: random.Random) -> dict:
    a = rng.choice(_A_CHOICES)
    b = rng.choice(_A_CHOICES)
    n = rng.choice(_N_CHOICES)
    period = 360 // n
    return {
        "a": a,
        "b": b,
        "n": n,
        "graph": _graph_encoding("sin", a, "cos", b, n, (-period, period)),
        "answer_a": sympy.Integer(a),
        "answer_b": sympy.Integer(b),
    }


trig_graph_amplitude = Problem(
    id="trig_graph_amplitude",
    type_id="trig_graph",
    name="Read amplitudes a and b from the graph of f=a·sin(nx), g=b·cos(nx)",
    artifact_type="practice",
    problem_spec=_gen_amplitude,
    verifier_spec=[
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "answer_a"},
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "answer_b"},
    ],
)


# ── 2. trig_graph_range ────────────────────────────────────────────────────────


def _gen_range(rng: random.Random) -> dict:
    fn = rng.choice(_FN_CHOICES)
    a = rng.choice(_A_CHOICES)
    n = rng.choice(_N_CHOICES)
    q = rng.choice(_Q_CHOICES)
    theta = rng.choice(_THETA_CHOICES)
    return {
        "fn": fn,
        "a": a,
        "n": n,
        "q": q,
        "theta": theta,
        "expr_latex": _trig_expr_latex(fn, a, n, theta, q),
        "inner_latex": _inner_latex(fn, n, theta),
        "answer_min": sympy.Integer(q - a),
        "answer_max": sympy.Integer(q + a),
    }


trig_graph_range = Problem(
    id="trig_graph_range",
    type_id="trig_graph",
    name="State the range of a·fn(nx+θ)+q",
    artifact_type="practice",
    problem_spec=_gen_range,
    verifier_spec=[
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "answer_min"},
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "answer_max"},
    ],
)


# ── 3. trig_graph_decreasing ───────────────────────────────────────────────────


def _decreasing_endpoints(fn: str, n: int) -> tuple[int, int]:
    """(lower, upper) of the first strictly decreasing interval in degrees."""
    if fn == "cos":
        return 0, 180 // n
    else:
        return 90 // n, 270 // n


def _decreasing_domain(fn: str, n: int) -> tuple[int, int]:
    """Domain that shows the full decreasing interval without ambiguity."""
    if fn == "cos":
        d = 180 // n
        return -d, d
    else:
        return 0, 360 // n


def _gen_decreasing(rng: random.Random) -> dict:
    fn = rng.choice(_FN_CHOICES)
    a = rng.choice(_A_CHOICES)
    n = rng.choice(_N_CHOICES)
    q = rng.choice(_Q_CHOICES)
    lower, upper = _decreasing_endpoints(fn, n)
    domain = _decreasing_domain(fn, n)
    return {
        "fn": fn,
        "a": a,
        "n": n,
        "q": q,
        "expr_latex": _trig_expr_latex(fn, a, n, 0, q),
        "domain_lower": domain[0],
        "domain_upper": domain[1],
        "answer_lower": sympy.Integer(lower),
        "answer_upper": sympy.Integer(upper),
    }


trig_graph_decreasing = Problem(
    id="trig_graph_decreasing",
    type_id="trig_graph",
    name="State the decreasing interval of a·fn(nx)+q within the shown domain",
    artifact_type="practice",
    problem_spec=_gen_decreasing,
    verifier_spec=[
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "answer_lower"},
        {"kind": "symbolic_equality", "marks_possible": 1, "param_key": "answer_upper"},
    ],
)


# ── 4. trig_graph_solve ────────────────────────────────────────────────────────


def _solve_x(a: int, b: int, n: int, k: int) -> tuple[float, float]:
    """Return (x1, x2) in degrees in [0°, 360°/n), sorted ascending."""
    R = math.sqrt(a**2 + b**2)
    phi = math.atan2(b, a)
    alpha = math.asin(k / R)
    period = 360.0 / n
    x1 = math.degrees(phi + alpha) / n % period
    x2 = math.degrees(phi + math.pi - alpha) / n % period
    return tuple(sorted([x1, x2]))


def _gen_solve(rng: random.Random) -> dict:
    while True:
        a = rng.choice(_A_SOLVE)
        b = rng.choice(_B_SOLVE)
        n = rng.choice(_N_CHOICES)
        R = math.sqrt(a**2 + b**2)
        k_max = math.floor(R - 1e-9)
        if k_max < 1:
            continue
        k = rng.randint(1, k_max)
        x1, x2 = _solve_x(a, b, n, k)
        period = 360 // n
        graph = _graph_encoding("sin", a, "cos", b, n, (0, period))
        graph["k_line"] = k
        return {
            "a": a,
            "b": b,
            "n": n,
            "k": k,
            "period": period,
            "graph": graph,
            "answer_x1": x1,
            "answer_x2": x2,
        }


trig_graph_solve = Problem(
    id="trig_graph_solve",
    type_id="trig_graph",
    name="Solve a·sin(nx)−b·cos(nx)=k for x ∈ [0°, 360°/n]",
    artifact_type="practice",
    problem_spec=_gen_solve,
    verifier_spec=[
        {
            "kind": "numeric_equality",
            "marks_possible": 1,
            "param_key": "answer_x1",
            "tolerance": 0.5,
        },
        {
            "kind": "numeric_equality",
            "marks_possible": 1,
            "param_key": "answer_x2",
            "tolerance": 0.5,
        },
    ],
)


# ── Demo ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    all_problems = {
        p.id: p
        for p in [
            trig_graph_amplitude,
            trig_graph_range,
            trig_graph_decreasing,
            trig_graph_solve,
        ]
    }
    engine = Engine(registry=InMemoryRegistry(all_problems))

    def show(label, instance, *answers):
        attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
        r = instance.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  "
            f"is_correct={r.is_correct}"
        )

    print("=== trig_graph_amplitude ===")
    inst = engine.instantiate(trig_graph_amplitude.id, seed=1)
    p = inst.params
    print(f"  f(x)={p['a']}·sin({p['n']}x),  g(x)={p['b']}·cos({p['n']}x)")
    a_c, b_c = inst.verifier.canonicals
    show("Correct  ", inst, a_c, b_c)
    show("b wrong  ", inst, a_c, int(b_c) + 1)

    print()

    print("=== trig_graph_range ===")
    inst = engine.instantiate(trig_graph_range.id, seed=1)
    p = inst.params
    print(f"  f(x) = {p['expr_latex']}")
    mn, mx = inst.verifier.canonicals
    print(f"  Range: [{mn}, {mx}]")
    show("Correct        ", inst, mn, mx)
    show("Swapped        ", inst, mx, mn)
    show("Forgot offset  ", inst, sympy.Integer(-p["a"]), sympy.Integer(p["a"]))

    print()

    print("=== trig_graph_decreasing ===")
    inst = engine.instantiate(trig_graph_decreasing.id, seed=1)
    p = inst.params
    print(
        f"  f(x) = {p['expr_latex']},"
        f"  domain [{p['domain_lower']}°, {p['domain_upper']}°]"
    )
    lo, hi = inst.verifier.canonicals
    print(f"  Decreasing on ({lo}°, {hi}°)")
    show("Correct  ", inst, lo, hi)
    show("Swapped  ", inst, hi, lo)

    print()

    print("=== trig_graph_solve ===")
    inst = engine.instantiate(trig_graph_solve.id, seed=1)
    p = inst.params
    print(
        f"  {p['a']}·sin({p['n']}x) − {p['b']}·cos({p['n']}x) = {p['k']},"
        f"  x ∈ [0°, {p['period']}°]"
    )
    x1, x2 = inst.verifier.canonicals
    print(f"  Solutions: x ≈ {x1:.2f}°,  x ≈ {x2:.2f}°")
    show("Both correct (exact)   ", inst, x1, x2)
    show("Both correct (rounded) ", inst, round(x1, 1), round(x2, 1))
    show("x1 off by 1°           ", inst, x1 + 1.0, x2)
    show("Both wrong             ", inst, x1 + 2.0, x2 + 2.0)
