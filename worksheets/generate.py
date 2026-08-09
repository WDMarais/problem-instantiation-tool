#!/usr/bin/env python3
"""
Minimal HTML worksheet generator.

Usage (from project root):
    .venv/bin/python worksheets/generate.py 10
    .venv/bin/python worksheets/generate.py 10 --seed 42 --title "Revision: Quadratics"
    .venv/bin/python worksheets/generate.py 10 --per-page 3 --output out.html

Extensibility:
  - Add a problem type: write template_<id>(params) -> ProblemCard, register in
    TEMPLATES and REGISTRY.
  - When you have 3+ generators, split into _templates.py + _renderer.py;
    the ProblemCard dataclass and build_html() signature stay the same.
"""

from __future__ import annotations

import argparse
import math
import random
import subprocess
import sys
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Callable

import sympy

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from content.examples.arithmetic_sequence import (
    find_missing as arith_find_missing,
)
from content.examples.arithmetic_sequence import (
    find_n as arith_find_n,
)
from content.examples.arithmetic_sequence import (
    find_term as arith_find_term,
)
from content.examples.arithmetic_sequence import (
    from_two_terms as arith_from_two_terms,
)
from content.examples.arithmetic_sequence import (
    next_terms as arith_next_terms,
)
from content.examples.arithmetic_sequence import (
    nth_term_formula as arith_nth_term_formula,
)
from content.examples.compound_periodic import (
    appreciation,
    compound_amount,
    compound_principal,
    compound_rate,
)
from content.examples.depreciation import (
    depreciation_amount,
    depreciation_rate,
    depreciation_to_zero,
)
from content.examples.factorise_skills import (
    factor_pairs_for_display,
    factorise_constraints,
    factorise_enumerate,
    factorise_sign_case,
)
from content.examples.future_value_annuity import (
    fv_annuity_amount,
    fv_annuity_deposit,
    fv_annuity_n,
)
from content.examples.geometric_sequence import (
    find_missing as geo_find_missing,
)
from content.examples.geometric_sequence import (
    find_n as geo_find_n,
)
from content.examples.geometric_sequence import (
    find_term as geo_find_term,
)
from content.examples.geometric_sequence import (
    from_two_terms as geo_from_two_terms,
)
from content.examples.geometric_sequence import (
    next_terms as geo_next_terms,
)
from content.examples.geometric_sequence import (
    nth_term_formula as geo_nth_term_formula,
)
from content.examples.monic_factorise import problem as monic_factorise_problem
from content.examples.nominal_effective import (
    effective_to_nominal,
    nominal_to_effective,
)
from content.examples.parallelogram_angles import (
    parallelogram_alternate,
    parallelogram_cointerior,
    parallelogram_opposite,
)
from content.examples.present_value_annuity import (
    pv_annuity_amount,
    pv_annuity_n,
    pv_annuity_payment,
    pv_annuity_total_interest,
)
from content.examples.rform_skills import (
    rform_find_phi,
    rform_find_R,
    rform_match_coefficients,
    rform_solve,
)
from content.examples.sequence_classification import (
    identify_sequence_type,
)
from content.examples.series import (
    arithmetic_series_sum,
    geometric_series_finite,
    geometric_series_infinite,
)
from content.examples.series import (
    find_n_from_sum as arith_series_find_n,
)
from content.examples.series import (
    sigma_evaluate as arith_series_sigma,
)
from content.examples.triangle_angles import (
    triangle_angle_sum,
    triangle_exterior,
    triangle_isosceles,
)
from content.examples.trig_graph_properties import (
    trig_graph_amplitude,
    trig_graph_decreasing,
    trig_graph_range,
    trig_graph_solve,
)
from content.examples.zero_product_rule import (
    atomic_shuffled_n,
    zero_product_atomic,
    zero_product_extension,
    zero_product_standard,
)
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.registry import InMemoryRegistry
from problem_instantiation_tool.schemas import Problem
from render.geometry import (
    Angle,
    GeometryFigure,
    Point,
    Pose,
    Segment,
    render_figure,
)
from render.graph import render_trig_graph

# ── data models ───────────────────────────────────────────────────────────────


@dataclass
class WorksheetEntry:
    problem: object  # Problem
    template: Callable[[dict], "ProblemCard"]
    sequence_fn: Callable | None = None  # opt-in O(n) generation; None → retry fallback


@dataclass
class ProblemCard:
    instruction: str  # plain text; inline math in $...$
    display_math: str  # LaTeX body for the display equation (without $$ delimiters)
    worked_steps: list[
        str
    ]  # LaTeX bodies for each solution step (without $ delimiters)
    graph_svg: str | None = None  # inline SVG string; None if no graph
    marks: int | None = None  # total marks; set by _generate_cards from the spec


# ── problem templates ─────────────────────────────────────────────────────────


def _poly_latex(b: int, c: int) -> str:
    """LaTeX for x^2 + bx + c, handling signs and unit coefficients."""
    b_term = (
        ""
        if b == 0
        else "+ x"
        if b == 1
        else "- x"
        if b == -1
        else f"+ {b}x"
        if b > 0
        else f"- {abs(b)}x"
    )
    c_term = "" if c == 0 else f"+ {c}" if c > 0 else f"- {abs(c)}"
    return f"x^2 {b_term} {c_term}".strip()


def _factor_eq(r: int) -> str:
    """'x ± |r| = 0' with sign normalised (avoids 'x - -4 = 0')."""
    return f"x - {r} = 0" if r >= 0 else f"x + {abs(r)} = 0"


def template_monic_factorise(params: dict, detail: str = "full") -> ProblemCard:
    b, c = params["b"], params["c"]
    r1, r2 = sorted([params["root1"], params["root2"]])
    factor_sum = r1 + r2  # = -b
    factor_prod = c  # = mn

    factored_eq = sympy.latex(params["answer"]) + " = 0"
    solutions = rf"x = {r1} \quad \text{{or}} \quad x = {r2}"

    if detail == "full":
        # "-(m+n) = b ⟹ m+n = -b" makes the one sign flip in the method explicit.
        step_conditions = (
            rf"-(m+n) = {b} \;\Rightarrow\; m+n = {factor_sum}"
            rf", \quad mn = {factor_prod}"
        )
        # Zero-product property: show each factor = 0 so the root is transparent.
        # Note: space before {_factor_eq(...)} is required — \quad followed directly
        # by a letter is parsed as an unknown command (e.g. \quadx).
        zero_step = (
            rf"{_factor_eq(r1)} \;\Rightarrow\; x = {r1}"
            rf" \quad \text{{or}} \quad "
            rf"{_factor_eq(r2)} \;\Rightarrow\; x = {r2}"
        )
        steps = [
            r"(x-m)(x-n) = x^2 - (m+n)x + mn",
            step_conditions,
            rf"m = {r1}, \quad n = {r2}",
            factored_eq,
            zero_step,
            solutions,
        ]
    else:  # short — conditions + zero-product, skip the derivation scaffolding
        zero_step = (
            rf"{_factor_eq(r1)} \;\Rightarrow\; x = {r1}"
            rf" \quad \text{{or}} \quad "
            rf"{_factor_eq(r2)} \;\Rightarrow\; x = {r2}"
        )
        steps = [
            rf"m+n = {factor_sum}, \quad mn = {factor_prod}",
            factored_eq,
            zero_step,
            solutions,
        ]

    return ProblemCard(
        instruction="Factorise completely, then solve for $x$:",
        display_math=_poly_latex(b, c) + " = 0",
        worked_steps=steps,
    )


def template_zero_product_atomic(params: dict, **_) -> ProblemCard:
    eq = params["equation_latex"]
    root = params["root_latex"]
    return ProblemCard(
        instruction="State the root:",
        display_math=eq,
        worked_steps=[rf"{eq} \;\Rightarrow\; x = {root}"],
    )


def template_zero_product_standard(params: dict, **_) -> ProblemCard:
    m, n = params["m_latex"], params["n_latex"]
    zero_step = (
        rf"x - {m} = 0 \;\Rightarrow\; x = {m}"
        rf" \quad \text{{or}} \quad "
        rf"x - {n} = 0 \;\Rightarrow\; x = {n}"
    )
    return ProblemCard(
        instruction="State all roots — you do not need to evaluate these expressions:",
        display_math=rf"(x - {m})(x - {n}) = 0",
        worked_steps=[
            zero_step,
            rf"x = {m} \quad \text{{or}} \quad x = {n}",
        ],
    )


def template_zero_product_extension(params: dict, **_) -> ProblemCard:
    p, q = params["p"], params["q"]
    p_sign = "+" if p > 0 else "-"
    p_abs = abs(p)
    q_str = "i" if q == 1 else rf"{q}i"
    neg_p = -p
    return ProblemCard(
        instruction=(
            r"State the root — you do not need to know what $i$ means, "
            r"just apply the rule:"
        ),
        display_math=rf"(x {p_sign} {p_abs} + {q_str}) = 0",
        worked_steps=[
            rf"x {p_sign} {p_abs} + {q_str} = 0 \;\Rightarrow\; x = {neg_p} - {q_str}"
        ],
    )


def template_factorise_constraints(params: dict, **_) -> ProblemCard:
    b, c = params["b"], params["c"]
    mn = int(params["answer_mn"])
    m_plus_n = int(params["answer_m_plus_n"])
    return ProblemCard(
        instruction=r"Using $(x-m)(x-n) = x^2-(m+n)x+mn$, write down $mn$ and $m+n$:",
        display_math=_poly_latex(b, c) + " = 0",
        worked_steps=[
            rf"-(m+n) = {b} \;\Rightarrow\; m+n = {m_plus_n}",
            rf"mn = {mn}",
        ],
    )


def template_factorise_sign_case(params: dict, **_) -> ProblemCard:
    mn, s = params["mn"], params["m_plus_n"]
    case = params["sign_case"]
    if case == "both_positive":
        reasoning = (
            rf"mn = {mn} > 0 \Rightarrow \text{{same sign}};"
            rf"\; m+n = {s} > 0 \Rightarrow \text{{both positive}}"
        )
    elif case == "both_negative":
        reasoning = (
            rf"mn = {mn} > 0 \Rightarrow \text{{same sign}};"
            rf"\; m+n = {s} < 0 \Rightarrow \text{{both negative}}"
        )
    else:
        reasoning = rf"mn = {mn} < 0 \Rightarrow \text{{opposite signs}}"
    return ProblemCard(
        instruction=(
            "What are the signs of m and n?\n"
            "(A) both positive  (B) both negative  (C) opposite signs"
        ),
        display_math=rf"mn = {mn}, \quad m+n = {s}",
        worked_steps=[reasoning],
    )


def template_factorise_enumerate(params: dict, **_) -> ProblemCard:
    mn, s = params["mn"], params["m_plus_n"]
    sign_label = params["sign_label"]
    r1, r2 = sorted([int(params["root1"]), int(params["root2"])])
    pairs = factor_pairs_for_display(mn, s)

    def _entry(a: int, b: int) -> str:
        check = r" \checkmark" if a + b == s else ""
        return rf"({a},\,{b})\!\to\!{a + b}{check}"

    table = r",\; ".join(_entry(a, b) for a, b in pairs)
    return ProblemCard(
        instruction=f"Find m and n — sign case: {sign_label}:",
        display_math=rf"mn = {mn}, \quad m+n = {s}",
        worked_steps=[
            table,
            rf"m = {r1}, \quad n = {r2}",
        ],
    )


def template_trig_graph_amplitude(params: dict, **_) -> ProblemCard:
    a, b = params["a"], params["b"]
    svg = render_trig_graph(params["graph"])
    return ProblemCard(
        instruction="From the graph, state the values of a and b.",
        display_math=r"f(x) = a\sin(nx),\quad g(x) = b\cos(nx)",
        worked_steps=[rf"a = {a}", rf"b = {b}"],
        graph_svg=svg,
    )


def template_trig_graph_range(params: dict, **_) -> ProblemCard:
    fn, a, n, q = params["fn"], params["a"], params["n"], params["q"]
    expr, inner = params["expr_latex"], params["inner_latex"]
    theta = params["theta"]
    mn, mx = int(params["answer_min"]), int(params["answer_max"])
    period_deg = 360 // n
    graph = {
        "curves": [
            {
                "id": "f",
                "func": fn,
                "amplitude": a,
                "period_deg": period_deg,
                "phase_shift_deg": theta,
                "offset": q,
            }
        ],
        "x_domain_deg": [0, period_deg],
    }
    svg = render_trig_graph(graph, range_band=(mn, mx))
    steps = [rf"-1 \leq {inner} \leq 1"]
    if a > 1:
        steps.append(rf"-{a} \leq {a}{inner} \leq {a}")
    if q != 0:
        steps.append(rf"{mn} \leq {expr} \leq {mx}")
    steps.append(rf"\text{{range}} = [{mn};\; {mx}]")
    return ProblemCard(
        instruction="State the range of $f$.",
        display_math=rf"f(x) = {expr}",
        worked_steps=steps,
        graph_svg=svg,
    )


def template_trig_graph_decreasing(params: dict, **_) -> ProblemCard:
    fn, a, n, q = params["fn"], params["a"], params["n"], params["q"]
    expr = params["expr_latex"]
    dl, du = params["domain_lower"], params["domain_upper"]
    lo, hi = int(params["answer_lower"]), int(params["answer_upper"])
    period_deg = 360 // n
    graph = {
        "curves": [
            {
                "id": "f",
                "func": fn,
                "amplitude": a,
                "period_deg": period_deg,
                "offset": q,
            }
        ],
        "x_domain_deg": [dl, du],
    }
    svg = render_trig_graph(graph, highlight_x=(lo, hi))
    steps = [
        (
            rf"f \text{{ is maximum at }} x={lo}^\circ "
            rf"\text{{ and minimum at }} x={hi}^\circ"
        ),
        rf"a = {a} > 0"
        + (rf",\; q = {q}" if q != 0 else "")
        + r"\text{ do not change the decreasing interval}",
        rf"f \text{{ is strictly decreasing on }} ({lo}^\circ,\; {hi}^\circ)",
    ]
    return ProblemCard(
        instruction=(
            f"For x ∈ [{dl}°, {du}°], state the interval on which f is "
            f"strictly decreasing."
        ),
        display_math=rf"f(x) = {expr}",
        worked_steps=steps,
        graph_svg=svg,
    )


def template_trig_graph_solve(params: dict, **_) -> ProblemCard:
    a, b, n, k = params["a"], params["b"], params["n"], params["k"]
    x1, x2 = params["answer_x1"], params["answer_x2"]
    period = params["period"]
    R_sym = sympy.sqrt(a**2 + b**2)
    R_latex = sympy.latex(R_sym)
    R_val = float(R_sym)
    phi = math.degrees(math.atan2(b, a))
    alpha = math.degrees(math.asin(k / R_val))
    np = "" if n == 1 else str(n)  # prefix for nx in the argument
    a_str = "" if a == 1 else str(a)
    b_str = "" if b == 1 else str(b)
    svg = render_trig_graph(params["graph"])
    steps = [
        (
            rf"R^2 = {a_str if a_str else 1}^2 + {b_str if b_str else 1}^2 "
            rf"= {a**2} + {b**2} = {a**2 + b**2} "
            rf"\;\Rightarrow\; R = {R_latex}"
        ),
        (
            rf"\tan\varphi = \tfrac{{{b}}}{{{a}}} "
            rf"\;\Rightarrow\; \varphi \approx {phi:.1f}^\circ"
        ),
        rf"{R_latex}\sin({np}x - {phi:.1f}^\circ) = {k}",
        (
            rf"\sin({np}x - {phi:.1f}^\circ) = \tfrac{{{k}}}{{{R_latex}}} "
            rf"\;\Rightarrow\; {np}x - {phi:.1f}^\circ \approx {alpha:.1f}^\circ"
            rf"\text{{ or }}{180 - alpha:.1f}^\circ"
        ),
    ]
    if n > 1:
        nx1, nx2 = round(x1 * n, 1), round(x2 * n, 1)
        steps.append(
            rf"{np}x \approx {nx1:.1f}^\circ\quad\text{{or}}\quad "
            rf"{np}x \approx {nx2:.1f}^\circ"
        )
    steps.append(
        rf"x \approx {x1:.1f}^\circ\quad\text{{or}}\quad x \approx {x2:.1f}^\circ"
    )
    return ProblemCard(
        instruction=f"Solve for x ∈ [0°, {period}°]:",
        display_math=rf"{a_str}\sin({np}x) - {b_str}\cos({np}x) = {k}"
        if n > 1
        else rf"{a_str}\sin x - {b_str}\cos x = {k}",
        worked_steps=steps,
        graph_svg=svg,
    )


def _parallelogram_pts(
    angle_a_deg: float, base: float, side: float, labels: dict
) -> dict:
    """Parallelogram with roles A→B→C→D (A bottom-left, anticlockwise) and the
    interior angle at role A equal to angle_a_deg. Layout coords, y-up. Pose
    (rotation, scale, reflection) is applied later by the renderer. Point *names*
    stay the role keys (referenced by Angle/Segment); `labels` is the letter each
    role shows the student, so the naming can vary without touching the geometry."""
    th = math.radians(angle_a_deg)
    dx, dy = side * math.cos(th), side * math.sin(th)
    return {
        "A": Point("A", 0.0, 0.0, label=labels["A"]),
        "B": Point("B", base, 0.0, label=labels["B"]),
        "C": Point("C", base + dx, dy, label=labels["C"]),
        "D": Point("D", dx, dy, label=labels["D"]),
    }


def _pgram_geometry(params: dict) -> dict:
    """Shared figure inputs from params: posed points + sides + Pose."""
    pts = _parallelogram_pts(
        params["angle_a_deg"], params["base"], params["side"], params["labels"]
    )
    return {
        "pts": pts,
        "sides": _parallelogram_sides(),
        "pose": Pose(**params["pose"]),
    }


def _parallelogram_sides() -> list[Segment]:
    # single chevron: AB ∥ DC ; double chevron: AD ∥ BC
    return [
        Segment("A", "B", arrows=1),
        Segment("D", "C", arrows=1),
        Segment("A", "D", arrows=2),
        Segment("B", "C", arrows=2),
    ]


def template_parallelogram_cointerior(params: dict, **_) -> ProblemCard:
    given = params["given_deg"]
    ans = int(params["answer"])
    lab = params["labels"]
    a, b, c, d = lab["A"], lab["B"], lab["C"], lab["D"]
    g = _pgram_geometry(params)
    fig = GeometryFigure(
        points=list(g["pts"].values()),
        segments=g["sides"],
        angles=[
            Angle("A", "B", "D", label=f"{given}°"),
            Angle("B", "A", "C", label="x"),
        ],
        pose=g["pose"],
    )
    return ProblemCard(
        instruction=(
            rf"${a}{b}{c}{d}$ is a parallelogram. Determine the size of "
            rf"$\hat{{{b}}}$, giving a reason."
        ),
        display_math=rf"\hat{{{a}}} = {given}^\circ",
        worked_steps=[
            (
                rf"\hat{{{a}}} + \hat{{{b}}} = 180^\circ \quad "
                rf"(\text{{co-interior }} \angle\text{{s}};\ {a}{d} \parallel {b}{c})"
            ),
            rf"\hat{{{b}}} = 180^\circ - {given}^\circ = {ans}^\circ",
        ],
        graph_svg=render_figure(fig),
    )


def template_parallelogram_opposite(params: dict, **_) -> ProblemCard:
    given = params["given_deg"]
    ans = int(params["answer"])
    lab = params["labels"]
    a, b, c, d = lab["A"], lab["B"], lab["C"], lab["D"]
    g = _pgram_geometry(params)
    fig = GeometryFigure(
        points=list(g["pts"].values()),
        segments=g["sides"],
        angles=[
            Angle("A", "B", "D", label=f"{given}°"),
            Angle("C", "B", "D", label="x"),
        ],
        pose=g["pose"],
    )
    return ProblemCard(
        instruction=(
            rf"${a}{b}{c}{d}$ is a parallelogram. Determine the size of "
            rf"$\hat{{{c}}}$, giving a reason."
        ),
        display_math=rf"\hat{{{a}}} = {given}^\circ",
        worked_steps=[
            (
                rf"\hat{{{c}}} = \hat{{{a}}} \quad "
                rf"(\text{{opposite }} \angle\text{{s of a }} \parallel^{{\text{{m}}}})"
            ),
            rf"\hat{{{c}}} = {ans}^\circ",
        ],
        graph_svg=render_figure(fig),
    )


def template_parallelogram_alternate(params: dict, **_) -> ProblemCard:
    given = params["given_deg"]
    ans = int(params["answer"])
    lab = params["labels"]
    a, b, c, d = lab["A"], lab["B"], lab["C"], lab["D"]
    g = _pgram_geometry(params)
    fig = GeometryFigure(
        points=list(g["pts"].values()),
        segments=g["sides"] + [Segment("A", "C")],
        angles=[
            Angle("C", "D", "A", label=f"{given}°"),
            Angle("A", "B", "C", label="x"),
        ],
        pose=g["pose"],
    )
    return ProblemCard(
        instruction=(
            rf"${a}{b}{c}{d}$ is a parallelogram with diagonal ${a}{c}$. "
            rf"Determine ${b}\hat{{{a}}}{c}$, giving a reason."
        ),
        display_math=rf"{d}\hat{{{c}}}{a} = {given}^\circ",
        worked_steps=[
            (
                rf"{b}\hat{{{a}}}{c} = {d}\hat{{{c}}}{a} \quad "
                rf"(\text{{alternate }} \angle\text{{s}};\ {a}{b} \parallel {d}{c})"
            ),
            rf"{b}\hat{{{a}}}{c} = {ans}^\circ",
        ],
        graph_svg=render_figure(fig),
    )


def _triangle_pts(angle_a_deg: float, angle_b_deg: float, base: float) -> dict:
    """Triangle ABC with A at the origin and B at (base, 0), interior angle
    angle_a_deg at A and angle_b_deg at B. C is placed by the sine rule so the
    figure is to-scale (a similarity Pose then keeps every drawn angle faithful)."""
    a = math.radians(angle_a_deg)
    ac = (
        base
        * math.sin(math.radians(angle_b_deg))
        / math.sin(math.radians(angle_a_deg + angle_b_deg))
    )
    return {
        "A": Point("A", 0.0, 0.0),
        "B": Point("B", base, 0.0),
        "C": Point("C", ac * math.cos(a), ac * math.sin(a)),
    }


def _triangle_sides() -> list[Segment]:
    return [Segment("A", "B"), Segment("B", "C"), Segment("C", "A")]


def template_triangle_angle_sum(params: dict, **_) -> ProblemCard:
    alpha, beta = params["alpha_deg"], params["beta_deg"]
    ans = int(params["answer"])
    pts = _triangle_pts(alpha, beta, params["base"])
    fig = GeometryFigure(
        points=list(pts.values()),
        segments=_triangle_sides(),
        angles=[
            Angle("A", "B", "C", label=f"{alpha}°"),
            Angle("B", "C", "A", label=f"{beta}°"),
            Angle("C", "A", "B", label="x"),
        ],
        pose=Pose(**params["pose"]),
    )
    return ProblemCard(
        instruction=(
            r"In $\triangle ABC$, determine the size of $\hat{C}$, "
            r"giving a reason."
        ),
        display_math=rf"\hat{{A}} = {alpha}^\circ,\quad \hat{{B}} = {beta}^\circ",
        worked_steps=[
            (
                r"\hat{A} + \hat{B} + \hat{C} = 180^\circ \quad "
                r"(\angle\text{s of a } \triangle)"
            ),
            rf"\hat{{C}} = 180^\circ - {alpha}^\circ - {beta}^\circ = {ans}^\circ",
        ],
        graph_svg=render_figure(fig),
    )


def template_triangle_isosceles(params: dict, **_) -> ProblemCard:
    base_angle = params["base_angle_deg"]
    ans = int(params["answer"])
    pts = _triangle_pts(params["apex_deg"], base_angle, params["base"])
    fig = GeometryFigure(
        points=list(pts.values()),
        # AB = AC, marked with single ticks; the apex is at A.
        segments=[
            Segment("A", "B", ticks=1),
            Segment("C", "A", ticks=1),
            Segment("B", "C"),
        ],
        angles=[
            Angle("B", "C", "A", label=f"{base_angle}°"),
            Angle("A", "B", "C", label="x"),
        ],
        pose=Pose(**params["pose"]),
    )
    return ProblemCard(
        instruction=(
            r"In $\triangle ABC$, $AB = AC$. Determine the size of $\hat{A}$, "
            r"giving reasons."
        ),
        display_math=rf"\hat{{B}} = {base_angle}^\circ",
        worked_steps=[
            (
                rf"\hat{{C}} = \hat{{B}} = {base_angle}^\circ \quad "
                rf"(\angle\text{{s opp equal sides}};\ AB = AC)"
            ),
            (
                rf"\hat{{A}} = 180^\circ - 2({base_angle}^\circ) = {ans}^\circ "
                rf"\quad (\angle\text{{s of a }} \triangle)"
            ),
        ],
        graph_svg=render_figure(fig),
    )


def template_triangle_exterior(params: dict, **_) -> ProblemCard:
    alpha, gamma = params["alpha_deg"], params["gamma_deg"]
    ans = int(params["answer"])
    base = params["base"]
    pts = _triangle_pts(alpha, params["interior_b_deg"], base)
    pts["P"] = Point("P", base * 1.45, 0.0)  # AB extended past B
    fig = GeometryFigure(
        points=list(pts.values()),
        segments=_triangle_sides() + [Segment("B", "P")],
        angles=[
            Angle("A", "B", "C", label=f"{alpha}°"),
            Angle("C", "A", "B", label=f"{gamma}°"),
            Angle("B", "C", "P", label="x"),
        ],
        pose=Pose(**params["pose"]),
    )
    return ProblemCard(
        instruction=(
            r"$AB$ is extended to $P$. Determine the size of $C\hat{B}P$, "
            r"giving a reason."
        ),
        display_math=rf"\hat{{A}} = {alpha}^\circ,\quad \hat{{C}} = {gamma}^\circ",
        worked_steps=[
            (
                r"C\hat{B}P = \hat{A} + \hat{C} \quad "
                r"(\text{ext } \angle \text{ of } \triangle)"
            ),
            rf"C\hat{{B}}P = {alpha}^\circ + {gamma}^\circ = {ans}^\circ",
        ],
        graph_svg=render_figure(fig),
    )


def _ab_display(a: int, b: int) -> str:
    """LaTeX for a·sin x − b·cos x with coefficient-1 suppressed."""
    a_str = "" if a == 1 else str(a)
    b_str = "" if b == 1 else str(b)
    return rf"{a_str}\sin x - {b_str}\cos x"


def template_rform_match_coefficients(params: dict, **_) -> ProblemCard:
    a, b = params["a"], params["b"]
    return ProblemCard(
        instruction=(
            r"Using $\sin(A-B) = \sin A\cos B - \cos A\sin B$, "
            r"expand $R\sin(x-\varphi)$ and match coefficients. "
            r"Fill in: $R\cos\varphi = \square$ and "
            r"$R\sin\varphi = \square$"
        ),
        display_math=_ab_display(a, b),
        worked_steps=[
            r"R\sin(x-\varphi) = R\cos\varphi\cdot\sin x - R\sin\varphi\cdot\cos x",
            rf"R\cos\varphi = {a},\quad R\sin\varphi = {b}",
        ],
    )


def template_rform_find_R(params: dict, **_) -> ProblemCard:
    a, b = params["a"], params["b"]
    R_latex = sympy.latex(sympy.sqrt(a**2 + b**2))
    return ProblemCard(
        instruction=r"Square both equations and add them to find $R$:",
        display_math=rf"R\cos\varphi = {a},\quad R\sin\varphi = {b}",
        worked_steps=[
            rf"(R\cos\varphi)^2 + (R\sin\varphi)^2 = {a}^2 + {b}^2",
            rf"R^2(\cos^2\varphi + \sin^2\varphi) = {a**2 + b**2}",
            rf"R^2 = {a**2 + b**2} \;\Rightarrow\; R = {R_latex}",
        ],
    )


def template_rform_find_phi(params: dict, **_) -> ProblemCard:
    a, b = params["a"], params["b"]
    phi = math.degrees(math.atan2(b, a))
    return ProblemCard(
        instruction=r"Divide the second equation by the first to find $\varphi$:",
        display_math=rf"R\cos\varphi = {a},\quad R\sin\varphi = {b}",
        worked_steps=[
            (
                rf"\frac{{R\sin\varphi}}{{R\cos\varphi}} = \frac{{{b}}}{{{a}}} "
                rf"\;\Rightarrow\; \tan\varphi = \frac{{{b}}}{{{a}}}"
            ),
            rf"\varphi = \arctan\frac{{{b}}}{{{a}}} \approx {phi:.1f}^\circ",
        ],
    )


def template_rform_solve(params: dict, **_) -> ProblemCard:
    phi = params["phi_deg"]
    k = params["k"]
    x1, x2 = params["answer_x1"], params["answer_x2"]
    R_latex = sympy.latex(params["R_sym"])
    R_val = float(params["R_sym"])
    alpha = math.degrees(math.asin(k / R_val))
    return ProblemCard(
        instruction=r"Solve for $x \in [0°, 360°]$:",
        display_math=rf"{R_latex}\sin(x - {phi:.1f}^\circ) = {k}",
        worked_steps=[
            rf"\sin(x - {phi:.1f}^\circ) = \tfrac{{{k}}}{{{R_latex}}}",
            (
                rf"x - {phi:.1f}^\circ \approx {alpha:.1f}^\circ"
                rf"\text{{ or }}{180 - alpha:.1f}^\circ"
            ),
            rf"x \approx {x1:.1f}^\circ\quad\text{{or}}\quad x \approx {x2:.1f}^\circ",
        ],
    )


# ── sequences & series: display helpers ────────────────────────────────────────


def _seq_display(terms: list) -> str:
    """Semicolon-separated sequence terms with a trailing ellipsis (NSC style)."""
    body = r";\ ".join(sympy.latex(sympy.sympify(t)) for t in terms)
    return body + r";\ \dots"


def _seq_noun(word: str, labeled: bool) -> str:
    """ "the arithmetic sequence" when labelled, else "the sequence" — so an
    unlabelled variant forces the student to classify before choosing a method."""
    return f"the {word} sequence" if labeled else "the sequence"


def _series_display(terms: list) -> str:
    """Sign-aware '+'-joined series terms with a trailing ellipsis."""
    parts = [sympy.latex(sympy.sympify(terms[0]))]
    for t in terms[1:]:
        s = sympy.latex(sympy.sympify(t))
        if s.startswith("-"):
            parts.append(" - " + s[1:].lstrip())
        else:
            parts.append(" + " + s)
    return "".join(parts) + r" + \dots"


# ── sequences & series: arithmetic templates ────────────────────────────────────


def template_arith_nth_term_formula(
    params: dict, detail: str = "full", labeled: bool = True
) -> ProblemCard:
    a, d = params["a"], params["d"]
    ans = sympy.latex(params["answer"])
    if detail == "full":
        steps = [
            rf"a = {a}, \quad d = {d}",
            r"T_n = a + (n-1)d",
            rf"T_n = {a} + (n-1)({d})",
            rf"T_n = {ans}",
        ]
    else:
        steps = [rf"a = {a}, \quad d = {d}", rf"T_n = {ans}"]
    return ProblemCard(
        instruction=(
            f"Determine the general term $T_n$ of {_seq_noun('arithmetic', labeled)}:"
        ),
        display_math=_seq_display([params["t1"], params["t2"], params["t3"]]),
        worked_steps=steps,
    )


def template_arith_find_term(
    params: dict, detail: str = "full", labeled: bool = True
) -> ProblemCard:
    a, d, nt, ans = params["a"], params["d"], params["n_target"], params["answer"]
    t1, t2, t3 = a, a + d, a + 2 * d
    if detail == "full":
        steps = [
            rf"a = {a}, \quad d = {d}",
            r"T_n = a + (n-1)d",
            rf"T_{{{nt}}} = {a} + ({nt}-1)({d})",
            rf"T_{{{nt}}} = {ans}",
        ]
    else:
        steps = [rf"T_{{{nt}}} = {a} + ({nt}-1)({d}) = {ans}"]
    return ProblemCard(
        instruction=(
            rf"Calculate the ${nt}^{{\text{{th}}}}$ term, $T_{{{nt}}}$, "
            f"of {_seq_noun('arithmetic', labeled)}:"
        ),
        display_math=_seq_display([t1, t2, t3]),
        worked_steps=steps,
    )


def template_arith_find_n(params: dict, detail: str = "full") -> ProblemCard:
    a, d, target, ans = params["a"], params["d"], params["target"], params["answer"]
    t1, t2, t3 = a, a + d, a + 2 * d
    if detail == "full":
        steps = [
            rf"a = {a}, \quad d = {d}",
            rf"T_n = {a} + (n-1)({d}) = {target}",
            rf"n = {ans}",
        ]
    else:
        steps = [rf"{a} + (n-1)({d}) = {target} \;\Rightarrow\; n = {ans}"]
    return ProblemCard(
        instruction=rf"Which term of the arithmetic sequence is equal to ${target}$?",
        display_math=_seq_display([t1, t2, t3]),
        worked_steps=steps,
    )


def template_arith_find_missing(params: dict, detail: str = "full") -> ProblemCard:
    tb, ta, ans = params["t_before"], params["t_after"], params["answer"]
    if detail == "full":
        steps = [
            r"x = \frac{T_{k-1} + T_{k+1}}{2} \quad (\text{arithmetic mean})",
            rf"x = \frac{{{tb} + ({ta})}}{{2}}",
            rf"x = {ans}",
        ]
    else:
        steps = [rf"x = \frac{{{tb} + ({ta})}}{{2}} = {ans}"]
    return ProblemCard(
        instruction="Determine the missing term $x$ in the arithmetic sequence:",
        display_math=rf"{tb};\ x;\ {ta}",
        worked_steps=steps,
    )


def template_arith_next_terms(params: dict, detail: str = "full") -> ProblemCard:
    d, shown = params["d"], params["terms_shown"]
    n1, n2 = params["next_1"], params["next_2"]
    last = shown[-1]
    if detail == "full":
        steps = [
            rf"d = {shown[1]} - ({shown[0]}) = {d}",
            rf"T_{{next}} = {last} + ({d}) = {n1}",
            rf"{n1} + ({d}) = {n2}",
        ]
    else:
        steps = [rf"d = {d}; \quad {n1},\ {n2}"]
    return ProblemCard(
        instruction="Write down the next two terms of the arithmetic sequence:",
        display_math=_seq_display(shown),
        worked_steps=steps,
    )


# ── sequences & series: geometric templates ─────────────────────────────────────


def template_geo_nth_term_formula(
    params: dict, detail: str = "full", labeled: bool = True
) -> ProblemCard:
    a, r = params["a"], params["r"]
    ans = sympy.latex(params["answer"])
    if detail == "full":
        steps = [
            rf"a = {a}, \quad r = {r}",
            r"T_n = a \cdot r^{\,n-1}",
            rf"T_n = ({a})({r})^{{\,n-1}}",
            rf"T_n = {ans}",
        ]
    else:
        steps = [rf"a = {a}, \quad r = {r}", rf"T_n = {ans}"]
    return ProblemCard(
        instruction=(
            f"Determine the general term $T_n$ of {_seq_noun('geometric', labeled)}:"
        ),
        display_math=_seq_display([params["t1"], params["t2"], params["t3"]]),
        worked_steps=steps,
    )


def template_geo_find_term(
    params: dict, detail: str = "full", labeled: bool = True
) -> ProblemCard:
    a, r, nt, ans = params["a"], params["r"], params["n_target"], params["answer"]
    t1, t2, t3 = a, a * r, a * r * r
    if detail == "full":
        steps = [
            rf"a = {a}, \quad r = {r}",
            r"T_n = a \cdot r^{\,n-1}",
            rf"T_{{{nt}}} = ({a})({r})^{{{nt}-1}}",
            rf"T_{{{nt}}} = {ans}",
        ]
    else:
        steps = [rf"T_{{{nt}}} = ({a})({r})^{{{nt}-1}} = {ans}"]
    return ProblemCard(
        instruction=(
            rf"Calculate the ${nt}^{{\text{{th}}}}$ term, $T_{{{nt}}}$, "
            f"of {_seq_noun('geometric', labeled)}:"
        ),
        display_math=_seq_display([t1, t2, t3]),
        worked_steps=steps,
    )


# ── sequences & series: classification atom ─────────────────────────────────────


def _classify_reason(terms: list[int], answer: str) -> list[str]:
    """Worked reason for the classification: the actual difference/ratio tests a
    student would run, concluding with the type in bold."""
    d = [terms[i + 1] - terms[i] for i in range(3)]
    diff_line = rf"T_2 - T_1 = {d[0]},\quad T_3 - T_2 = {d[1]},\quad T_4 - T_3 = {d[2]}"
    if answer == "arithmetic":
        return [
            diff_line,
            rf"\text{{constant difference }} d = {d[0]}"
            r" \;\Rightarrow\; \textbf{arithmetic}",
        ]
    if answer == "geometric":
        ratios = [sympy.Rational(terms[i + 1], terms[i]) for i in range(3)]
        ratio_line = (
            rf"\tfrac{{T_2}}{{T_1}} = {sympy.latex(ratios[0])},\quad "
            rf"\tfrac{{T_3}}{{T_2}} = {sympy.latex(ratios[1])},\quad "
            rf"\tfrac{{T_4}}{{T_3}} = {sympy.latex(ratios[2])}"
        )
        return [
            ratio_line,
            rf"\text{{constant ratio }} r = {sympy.latex(ratios[0])}"
            r" \;\Rightarrow\; \textbf{geometric}",
        ]
    # neither: first differences are enough to rule out arithmetic; note the ratio
    # is not constant either (shown only when every term is non-zero).
    lines = [diff_line]
    if all(x != 0 for x in terms[:3]):
        ratios = [sympy.Rational(terms[i + 1], terms[i]) for i in range(3)]
        lines.append(
            rf"\tfrac{{T_2}}{{T_1}} = {sympy.latex(ratios[0])},\quad "
            rf"\tfrac{{T_3}}{{T_2}} = {sympy.latex(ratios[1])}"
        )
    lines.append(
        r"\text{no constant difference or ratio} \;\Rightarrow\; \textbf{neither}"
    )
    return lines


def template_identify_sequence_type(params: dict, detail: str = "full") -> ProblemCard:
    terms = [params["t1"], params["t2"], params["t3"], params["t4"]]
    reason = _classify_reason(terms, params["answer"])
    steps = reason if detail == "full" else [reason[-1]]
    return ProblemCard(
        instruction=(
            "State, giving a reason, whether the following sequence is "
            "arithmetic, geometric or neither:"
        ),
        display_math=_seq_display(terms),
        worked_steps=steps,
    )


# ── sequences & series: series-sum templates ────────────────────────────────────


def template_arith_series_sum(params: dict, detail: str = "full") -> ProblemCard:
    a, d, n, ans = params["a"], params["d"], params["n"], params["answer"]
    t1, t2, t3 = a, a + d, a + 2 * d
    if detail == "full":
        steps = [
            rf"a = {a}, \quad d = {d}, \quad n = {n}",
            r"S_n = \frac{n}{2}\left[\,2a + (n-1)d\,\right]",
            rf"S_{{{n}}} = \frac{{{n}}}{{2}}\left[\,2({a}) + ({n}-1)({d})\,\right]",
            rf"S_{{{n}}} = {ans}",
        ]
    else:
        steps = [
            r"S_n = \frac{n}{2}\left[\,2a + (n-1)d\,\right]",
            rf"S_{{{n}}} = {ans}",
        ]
    return ProblemCard(
        instruction=(
            rf"Calculate the sum of the first ${n}$ terms of the arithmetic series:"
        ),
        display_math=_series_display([t1, t2, t3]),
        worked_steps=steps,
    )


def template_geo_series_finite(params: dict, detail: str = "full") -> ProblemCard:
    a, r, n, ans = params["a"], params["r"], params["n"], params["answer"]
    t1, t2, t3 = a, a * r, a * r * r
    if detail == "full":
        steps = [
            rf"a = {a}, \quad r = {r}, \quad n = {n}",
            r"S_n = \frac{a\left(r^{\,n} - 1\right)}{r - 1}",
            rf"S_{{{n}}} = \frac{{({a})\left({r}^{{{n}}} - 1\right)}}{{{r} - 1}}",
            rf"S_{{{n}}} = {ans}",
        ]
    else:
        steps = [
            r"S_n = \frac{a\left(r^{\,n} - 1\right)}{r - 1}",
            rf"S_{{{n}}} = {ans}",
        ]
    return ProblemCard(
        instruction=(
            rf"Calculate the sum of the first ${n}$ terms of the geometric series:"
        ),
        display_math=_series_display([t1, t2, t3]),
        worked_steps=steps,
    )


def template_geo_series_infinite(params: dict, detail: str = "full") -> ProblemCard:
    a, r, ans = params["a"], params["r"], params["answer"]
    r_l, ans_l, abs_r_l = sympy.latex(r), sympy.latex(ans), sympy.latex(abs(r))
    t1, t2, t3 = a, a * r, a * r * r
    if detail == "full":
        steps = [
            rf"a = {a}, \quad r = {r_l}",
            rf"|r| = {abs_r_l} < 1 \;\Rightarrow\; S_\infty \text{{ exists}}",
            r"S_\infty = \frac{a}{1 - r}",
            rf"S_\infty = \frac{{{a}}}{{1 - \left({r_l}\right)}}",
            rf"S_\infty = {ans_l}",
        ]
    else:
        steps = [
            r"S_\infty = \frac{a}{1 - r}",
            rf"S_\infty = \frac{{{a}}}{{1 - \left({r_l}\right)}} = {ans_l}",
        ]
    return ProblemCard(
        instruction=r"Calculate $S_\infty$ of the convergent geometric series:",
        display_math=_series_display([t1, t2, t3]),
        worked_steps=steps,
    )


# ── sequences & series: expansion batch ─────────────────────────────────────────


def template_arith_from_two_terms(params: dict, detail: str = "full") -> ProblemCard:
    a, d, p, q = params["a"], params["d"], params["p"], params["q"]
    tp, tq = params["tp"], params["tq"]
    if detail == "full":
        steps = [
            rf"T_{{{p}}} = a + {p - 1}d = {tp}",
            rf"T_{{{q}}} = a + {q - 1}d = {tq}",
            rf"({q} - {p})d = {tq} - ({tp}) \;\Rightarrow\; d = {d}",
            rf"a = {tp} - {p - 1}({d}) = {a}",
        ]
    else:
        steps = [rf"d = {d}, \quad a = {a}"]
    return ProblemCard(
        instruction=(
            rf"In an arithmetic sequence $T_{{{p}}} = {tp}$ and $T_{{{q}}} = {tq}$. "
            r"Determine $a$ and $d$."
        ),
        display_math=rf"T_{{{p}}} = {tp}, \quad T_{{{q}}} = {tq}",
        worked_steps=steps,
    )


def template_geo_from_two_terms(params: dict, detail: str = "full") -> ProblemCard:
    a, r, p, q = params["a"], params["r"], params["p"], params["q"]
    tp, tq = params["tp"], params["tq"]
    gap = q - p
    ratio = sympy.Rational(tq, tp)
    if detail == "full":
        steps = [
            rf"\frac{{T_{{{q}}}}}{{T_{{{p}}}}} = r^{{{q}-{p}}} "
            rf"= \frac{{{tq}}}{{{tp}}} = {sympy.latex(ratio)}",
            rf"r^{{{gap}}} = {sympy.latex(ratio)} \;\Rightarrow\; r = {r}",
            rf"a = \frac{{T_{{{p}}}}}{{r^{{{p - 1}}}}} = {a}",
        ]
    else:
        steps = [rf"r = {r}, \quad a = {a}"]
    return ProblemCard(
        instruction=(
            rf"In a geometric sequence $T_{{{p}}} = {tp}$ and $T_{{{q}}} = {tq}$. "
            r"Determine $a$ and $r$."
        ),
        display_math=rf"T_{{{p}}} = {tp}, \quad T_{{{q}}} = {tq}",
        worked_steps=steps,
    )


def template_geo_find_missing(params: dict, detail: str = "full") -> ProblemCard:
    tb, ta, ans = params["t_before"], params["t_after"], params["answer"]
    if detail == "full":
        steps = [
            r"x^2 = T_{k-1} \cdot T_{k+1} \quad (\text{geometric mean})",
            rf"x^2 = ({tb})({ta}) = {tb * ta}",
            rf"x = \sqrt{{{tb * ta}}} = {ans}",
        ]
    else:
        steps = [rf"x = \sqrt{{({tb})({ta})}} = {ans}"]
    return ProblemCard(
        instruction=(
            "Determine the positive value of $x$ for which the following are three "
            "consecutive terms of a geometric sequence:"
        ),
        display_math=rf"{tb};\ x;\ {ta}",
        worked_steps=steps,
    )


def template_geo_find_n(params: dict, detail: str = "full") -> ProblemCard:
    a, r, target, ans = params["a"], params["r"], params["target"], params["answer"]
    t1, t2, t3 = a, a * r, a * r * r
    if detail == "full":
        steps = [
            rf"a = {a}, \quad r = {r}",
            rf"T_n = ({a})({r})^{{\,n-1}} = {target}",
            rf"({r})^{{\,n-1}} = {target // a} \;\Rightarrow\; n = {ans}",
        ]
    else:
        steps = [rf"({a})({r})^{{\,n-1}} = {target} \;\Rightarrow\; n = {ans}"]
    return ProblemCard(
        instruction=rf"Which term of the geometric sequence is equal to ${target}$?",
        display_math=_seq_display([t1, t2, t3]),
        worked_steps=steps,
    )


def template_geo_next_terms(params: dict, detail: str = "full") -> ProblemCard:
    r, shown = params["r"], params["terms_shown"]
    n1, n2 = params["next_1"], params["next_2"]
    last = shown[-1]
    if detail == "full":
        steps = [
            rf"r = \frac{{{shown[1]}}}{{{shown[0]}}} = {r}",
            rf"T_{{next}} = ({last})({r}) = {n1}",
            rf"({n1})({r}) = {n2}",
        ]
    else:
        steps = [rf"r = {r}; \quad {n1},\ {n2}"]
    return ProblemCard(
        instruction="Write down the next two terms of the geometric sequence:",
        display_math=_seq_display(shown),
        worked_steps=steps,
    )


def template_arith_series_find_n(params: dict, detail: str = "full") -> ProblemCard:
    a, d, sn, ans = params["a"], params["d"], params["sn"], params["answer"]
    if detail == "full":
        steps = [
            rf"a = {a}, \quad d = {d}",
            r"S_n = \frac{n}{2}\left[\,2a + (n-1)d\,\right]",
            rf"{sn} = \frac{{n}}{{2}}\left[\,2({a}) + (n-1)({d})\,\right]",
            rf"n = {ans} \quad (n > 0)",
        ]
    else:
        steps = [rf"\tfrac{{n}}{{2}}[2({a}) + (n-1)({d})] = {sn} \Rightarrow n = {ans}"]
    return ProblemCard(
        instruction=(
            rf"The sum of the first $n$ terms of an arithmetic series is ${sn}$. "
            r"Determine the value of $n$."
        ),
        display_math=_series_display([a, a + d, a + 2 * d]),
        worked_steps=steps,
    )


def template_arith_series_sigma(params: dict, detail: str = "full") -> ProblemCard:
    p, q, n, ans = params["p"], params["q"], params["n"], params["answer"]
    term = rf"{p}k {'+' if q >= 0 else '-'} {abs(q)}" if q else rf"{p}k"
    sigma = rf"\sum_{{k=1}}^{{{n}}}\left({term}\right)"
    if detail == "full":
        steps = [
            rf"{sigma} = {p}\sum_{{k=1}}^{{{n}}} k + \sum_{{k=1}}^{{{n}}} {q}",
            rf"= {p}\cdot\frac{{{n}({n}+1)}}{{2}} + ({q})({n})",
            rf"= {ans}",
        ]
    else:
        steps = [rf"{sigma} = {ans}"]
    return ProblemCard(
        instruction="Evaluate:",
        display_math=sigma,
        worked_steps=steps,
    )


# ── finance / annuities: display helpers ────────────────────────────────────────


def _zar(x: float, dp: int = 2) -> str:
    """Rand amount as LaTeX: R with thin-space thousands and dp decimals."""
    s = f"{x:,.{dp}f}".replace(",", r"\,")
    return rf"\text{{R}}\,{s}"


def _dec(x: float) -> str:
    """A decimal to at most 6 places, trailing zeros trimmed (for rates i = r/100m)."""
    return f"{x:.6f}".rstrip("0").rstrip(".")


_COMP_WORD = {1: "annually", 4: "quarterly", 12: "monthly"}
_PERIOD_WORD = {1: "year", 4: "quarter", 12: "month"}


def _timing_phrase(timing: str, m: int) -> str:
    """ "at the end of each month" (ordinary) / "start of each month" (due)."""
    edge = "start" if timing == "due" else "end"
    return f"at the {edge} of each {_PERIOD_WORD.get(m, 'period')}"


# ── finance / annuities: compound-interest templates ────────────────────────────


def template_compound_amount(params: dict, detail: str = "full") -> ProblemCard:
    p, r, m = params["principal"], params["rate"], params["compounding"]
    n = params["years"]
    periods, i = params["periods"], params["per_period_rate"]
    ans = params["answer"]
    sub = rf"A = {_zar(p, 0)}(1 + {_dec(i)})^{{{periods}}}"
    full = [
        rf"i = \frac{{{r}\%}}{{{m}}} = {_dec(i)}, \quad N = {m}\times{n} = {periods}",
        r"A = P(1 + i)^{N}",
        sub,
        rf"A = {_zar(ans)}",
    ]
    return ProblemCard(
        instruction=(
            f"R{p:,} is invested at {r}% p.a. compounded {_COMP_WORD[m]} for "
            f"{n} years. Determine the accumulated amount."
        ),
        display_math=r"A = P(1 + i)^{N}",
        worked_steps=full if detail == "full" else [rf"{sub} = {_zar(ans)}"],
    )


def template_compound_principal(params: dict, detail: str = "full") -> ProblemCard:
    a, r, m = params["target_amount"], params["rate"], params["compounding"]
    n, periods, i = params["years"], params["periods"], params["per_period_rate"]
    ans = params["answer"]
    sub = rf"P = \frac{{{_zar(a, 0)}}}{{(1 + {_dec(i)})^{{{periods}}}}}"
    full = [
        rf"i = \frac{{{r}\%}}{{{m}}} = {_dec(i)}, \quad N = {periods}",
        r"P = \frac{A}{(1 + i)^{N}}",
        sub,
        rf"P = {_zar(ans)}",
    ]
    return ProblemCard(
        instruction=(
            f"What amount, invested now at {r}% p.a. compounded {_COMP_WORD[m]}, "
            f"grows to R{a:,} in {n} years?"
        ),
        display_math=r"P = \dfrac{A}{(1 + i)^{N}}",
        worked_steps=full if detail == "full" else [rf"{sub} = {_zar(ans)}"],
    )


def template_compound_rate(params: dict, detail: str = "full") -> ProblemCard:
    p, a, m = params["principal"], params["amount"], params["compounding"]
    n, periods, ans = params["years"], params["periods"], params["answer"]
    ratio = a / p
    i = ans / (100 * m)
    full = [
        r"A = P(1 + i)^{N}",
        rf"(1 + i)^{{{periods}}} = \frac{{A}}{{P}} = {_dec(ratio)}",
        rf"i = {_dec(ratio)}^{{1/{periods}}} - 1 = {_dec(i)}",
        rf"r = i \times {m} \times 100 = {ans}\%",
    ]
    return ProblemCard(
        instruction=(
            f"R{p:,} grows to R{a:,.2f} in {n} years with interest compounded "
            f"{_COMP_WORD[m]}. Determine the nominal annual interest rate."
        ),
        display_math=r"A = P(1 + i)^{N}",
        worked_steps=full if detail == "full" else [full[1], rf"r = {ans}\%"],
    )


def template_appreciation(params: dict, detail: str = "full") -> ProblemCard:
    price, r, n, ans = (
        params["price"],
        params["rate"],
        params["years"],
        params["answer"],
    )
    sub = rf"A = {_zar(price, 0)}(1 + {_dec(r / 100)})^{{{n}}}"
    full = [r"A = P(1 + i)^{n}", sub, rf"A = {_zar(ans)}"]
    return ProblemCard(
        instruction=(
            f"An item costing R{price:,} rises in price by {r}% per year. "
            f"What will it cost in {n} years?"
        ),
        display_math=r"A = P(1 + i)^{n}",
        worked_steps=full if detail == "full" else [rf"{sub} = {_zar(ans)}"],
    )


# ── finance / annuities: nominal ↔ effective templates ──────────────────────────


def template_nominal_to_effective(params: dict, detail: str = "full") -> ProblemCard:
    i_nom, m, ans = params["nominal_rate"], params["compounding"], params["answer"]
    full = [
        r"1 + i_{\text{eff}} = \left(1 + \frac{i^{(m)}}{m}\right)^{m}",
        rf"1 + i_{{\text{{eff}}}} = \left(1 + \frac{{{i_nom}\%}}{{{m}}}\right)^{{{m}}}",
        rf"i_{{\text{{eff}}}} = {ans}\%",
    ]
    return ProblemCard(
        instruction=(
            f"Convert a nominal rate of {i_nom}% p.a. compounded {_COMP_WORD[m]} "
            f"to an effective annual rate."
        ),
        display_math=r"1 + i_{\text{eff}} = \left(1 + \frac{i^{(m)}}{m}\right)^{m}",
        worked_steps=full if detail == "full" else [rf"i_{{\text{{eff}}}} = {ans}\%"],
    )


def template_effective_to_nominal(params: dict, detail: str = "full") -> ProblemCard:
    i_eff, m, ans = params["effective_rate"], params["compounding"], params["answer"]
    full = [
        r"1 + i_{\text{eff}} = \left(1 + \frac{i^{(m)}}{m}\right)^{m}",
        rf"i^{{(m)}} = {m}\left[(1 + {i_eff / 100})^{{1/{m}}} - 1\right]",
        rf"i^{{(m)}} = {ans}\%",
    ]
    return ProblemCard(
        instruction=(
            f"Convert an effective annual rate of {i_eff}% to a nominal rate "
            f"compounded {_COMP_WORD[m]}."
        ),
        display_math=r"1 + i_{\text{eff}} = \left(1 + \frac{i^{(m)}}{m}\right)^{m}",
        worked_steps=full if detail == "full" else [rf"i^{{(m)}} = {ans}\%"],
    )


# ── finance / annuities: future-value annuity templates ─────────────────────────


def template_fv_annuity_amount(params: dict, detail: str = "full") -> ProblemCard:
    x, r, m = params["deposit"], params["rate"], params["compounding"]
    n, periods, timing = params["years"], params["periods"], params["timing"]
    ans, i = params["answer"], params["rate"] / (100 * params["compounding"])
    due = r"\times(1 + i)" if timing == "due" else ""
    sub = (
        rf"F = {_zar(x)}\cdot\frac{{(1 + {_dec(i)})^{{{periods}}} - 1}}"
        rf"{{{_dec(i)}}}{due}"
    )
    full = [
        rf"i = \frac{{{r}\%}}{{{m}}} = {_dec(i)}, \quad N = {periods}",
        rf"F = x\cdot\frac{{(1 + i)^{{N}} - 1}}{{i}}{due}",
        sub,
        rf"F = {_zar(ans)}",
    ]
    return ProblemCard(
        instruction=(
            f"R{x:,.2f} is deposited {_timing_phrase(timing, m)} at {r}% p.a. "
            f"compounded {_COMP_WORD[m]} for {n} years. Determine the future value."
        ),
        display_math=r"F = x\cdot\dfrac{(1 + i)^{N} - 1}{i}",
        worked_steps=full if detail == "full" else [rf"{sub} = {_zar(ans)}"],
    )


def template_fv_annuity_deposit(params: dict, detail: str = "full") -> ProblemCard:
    a, r, m = params["target_amount"], params["rate"], params["compounding"]
    n, periods, timing = params["years"], params["periods"], params["timing"]
    ans, i = params["answer"], params["rate"] / (100 * params["compounding"])
    due = r"\div(1 + i)" if timing == "due" else ""
    sub = (
        rf"x = \frac{{{_zar(a, 0)}\times {_dec(i)}}}"
        rf"{{(1 + {_dec(i)})^{{{periods}}} - 1}}{due}"
    )
    full = [
        rf"i = \frac{{{r}\%}}{{{m}}} = {_dec(i)}, \quad N = {periods}",
        rf"x = \frac{{F\cdot i}}{{(1 + i)^{{N}} - 1}}{due}",
        sub,
        rf"x = {_zar(ans)}",
    ]
    return ProblemCard(
        instruction=(
            f"What regular deposit, made {_timing_phrase(timing, m)}, accumulates "
            f"to R{a:,} in {n} years at {r}% p.a. compounded {_COMP_WORD[m]}?"
        ),
        display_math=r"x = \dfrac{F\cdot i}{(1 + i)^{N} - 1}",
        worked_steps=full if detail == "full" else [rf"{sub} = {_zar(ans)}"],
    )


def template_fv_annuity_n(params: dict, detail: str = "full") -> ProblemCard:
    x, r, m = params["deposit"], params["rate"], params["compounding"]
    a, i, ans = params["target_amount"], params["per_period_rate"], params["answer"]
    solved = math.log(1 + a * i / x) / math.log(1 + i)
    full = [
        rf"F = x\cdot\frac{{(1 + i)^{{n}} - 1}}{{i}}, \quad i = {_dec(i)}",
        r"n = \frac{\ln\left(1 + \frac{F\,i}{x}\right)}{\ln(1 + i)}",
        rf"n \approx {solved:.2f} \;\Rightarrow\; "
        rf"n = {ans}\ \text{{deposits (round up)}}",
    ]
    return ProblemCard(
        instruction=(
            f"How many deposits of R{x:,.2f} reach at least R{a:,.2f} at {r}% "
            f"p.a. compounded {_COMP_WORD[m]}?"
        ),
        display_math=r"F = x\cdot\dfrac{(1 + i)^{n} - 1}{i}",
        worked_steps=full if detail == "full" else [full[-1]],
    )


# ── finance / annuities: present-value annuity templates ────────────────────────


def template_pv_annuity_amount(params: dict, detail: str = "full") -> ProblemCard:
    x, r, m = params["payment"], params["rate"], params["compounding"]
    n, periods, timing = params["years"], params["periods"], params["timing"]
    ans, i = params["answer"], params["rate"] / (100 * params["compounding"])
    due = r"\times(1 + i)" if timing == "due" else ""
    sub = (
        rf"P = {_zar(x)}\cdot\frac{{1 - (1 + {_dec(i)})^{{-{periods}}}}}"
        rf"{{{_dec(i)}}}{due}"
    )
    full = [
        rf"i = \frac{{{r}\%}}{{{m}}} = {_dec(i)}, \quad N = {periods}",
        rf"P = x\cdot\frac{{1 - (1 + i)^{{-N}}}}{{i}}{due}",
        sub,
        rf"P = {_zar(ans)}",
    ]
    return ProblemCard(
        instruction=(
            f"A loan is repaid by payments of R{x:,.2f} {_timing_phrase(timing, m)} "
            f"at {r}% p.a. compounded {_COMP_WORD[m]} over {n} years. Determine the "
            f"loan amount (present value)."
        ),
        display_math=r"P = x\cdot\dfrac{1 - (1 + i)^{-N}}{i}",
        worked_steps=full if detail == "full" else [rf"{sub} = {_zar(ans)}"],
    )


def template_pv_annuity_payment(params: dict, detail: str = "full") -> ProblemCard:
    p, r, m = params["loan_amount"], params["rate"], params["compounding"]
    n, periods, timing = params["years"], params["periods"], params["timing"]
    ans, i = params["answer"], params["rate"] / (100 * params["compounding"])
    due = r"\div(1 + i)" if timing == "due" else ""
    sub = (
        rf"x = \frac{{{_zar(p, 0)}\times {_dec(i)}}}"
        rf"{{1 - (1 + {_dec(i)})^{{-{periods}}}}}{due}"
    )
    full = [
        rf"i = \frac{{{r}\%}}{{{m}}} = {_dec(i)}, \quad N = {periods}",
        rf"x = \frac{{P\cdot i}}{{1 - (1 + i)^{{-N}}}}{due}",
        sub,
        rf"x = {_zar(ans)}",
    ]
    return ProblemCard(
        instruction=(
            f"A loan of R{p:,} is repaid by equal payments {_timing_phrase(timing, m)} "
            f"over {n} years at {r}% p.a. compounded {_COMP_WORD[m]}. Determine the "
            f"payment."
        ),
        display_math=r"x = \dfrac{P\cdot i}{1 - (1 + i)^{-N}}",
        worked_steps=full if detail == "full" else [rf"{sub} = {_zar(ans)}"],
    )


def template_pv_annuity_n(params: dict, detail: str = "full") -> ProblemCard:
    x, r, m = params["payment"], params["rate"], params["compounding"]
    pv, i, mode = params["present_value"], params["per_period_rate"], params["mode"]
    ans = params["answer"]
    solved = -math.log(1 - pv * i / x) / math.log(1 + i)
    rounding = "round up" if mode == "loan" else "round down"
    full = [
        rf"P = x\cdot\frac{{1 - (1 + i)^{{-n}}}}{{i}}, \quad i = {_dec(i)}",
        r"n = \frac{-\ln\left(1 - \frac{P\,i}{x}\right)}{\ln(1 + i)}",
        rf"n \approx {solved:.2f} \;\Rightarrow\; "
        rf"n = {ans}\ \text{{payments ({rounding})}}",
    ]
    if mode == "loan":
        instruction = (
            f"A loan of R{pv:,.2f} is repaid by payments of R{x:,.2f} at {r}% p.a. "
            f"compounded {_COMP_WORD[m]}. How many payments clear the loan?"
        )
    else:
        instruction = (
            f"A fund of R{pv:,.2f} allows withdrawals of R{x:,.2f} at {r}% p.a. "
            f"compounded {_COMP_WORD[m]}. How many full withdrawals are possible?"
        )
    return ProblemCard(
        instruction=instruction,
        display_math=r"P = x\cdot\dfrac{1 - (1 + i)^{-n}}{i}",
        worked_steps=full if detail == "full" else [full[-1]],
    )


def template_pv_annuity_total_interest(
    params: dict, detail: str = "full"
) -> ProblemCard:
    p, periods = params["loan_amount"], params["periods"]
    x, ans = params["instalment"], params["answer"]
    r, m, n = params["rate"], params["compounding"], params["years"]
    full = [
        r"\text{Total interest} = xN - P",
        rf"= {_zar(x)}\times {periods} - {_zar(p, 0)}",
        rf"= {_zar(x * periods)} - {_zar(p, 0)} = {_zar(ans)}",
    ]
    return ProblemCard(
        instruction=(
            f"A loan of R{p:,} is repaid by {periods} payments of R{x:,.2f} "
            f"(at {r}% p.a. compounded {_COMP_WORD[m]} over {n} years). Determine "
            f"the total interest paid."
        ),
        display_math=r"\text{Total interest} = xN - P",
        worked_steps=full if detail == "full" else [full[0], rf"= {_zar(ans)}"],
    )


# ── finance / annuities: depreciation templates ─────────────────────────────────


def template_depreciation_amount(params: dict, detail: str = "full") -> ProblemCard:
    p, r, n = params["book_price"], params["rate"], params["years"]
    model, ans = params["model"], params["answer"]
    if model == "straight_line":
        word = "straight-line"
        sub = rf"A = {_zar(p, 0)}(1 - {_dec(r / 100)}\times {n})"
        formula = r"A = P(1 - i\cdot n)"
    else:
        word = "reducing-balance"
        sub = rf"A = {_zar(p, 0)}(1 - {_dec(r / 100)})^{{{n}}}"
        formula = r"A = P(1 - i)^{n}"
    full = [formula, sub, rf"A = {_zar(ans)}"]
    return ProblemCard(
        instruction=(
            f"A R{p:,} asset depreciates at {r}% p.a. on a {word} basis. "
            f"Determine its book value after {n} years."
        ),
        display_math=formula,
        worked_steps=full if detail == "full" else [rf"{sub} = {_zar(ans)}"],
    )


def template_depreciation_rate(params: dict, detail: str = "full") -> ProblemCard:
    p, a, n, ans = (
        params["book_price"],
        params["book_value"],
        params["years"],
        params["answer"],
    )
    full = [
        r"A = P(1 - i\cdot n)",
        rf"{_zar(a)} = {_zar(p, 0)}(1 - i\times {n})",
        rf"i = \frac{{1 - A/P}}{{{n}}} \;\Rightarrow\; r = {ans}\%",
    ]
    return ProblemCard(
        instruction=(
            f"A R{p:,} asset depreciates on a straight-line basis to R{a:,.2f} "
            f"after {n} years. Determine the annual depreciation rate."
        ),
        display_math=r"A = P(1 - i\cdot n)",
        worked_steps=full if detail == "full" else [rf"r = {ans}\%"],
    )


def template_depreciation_to_zero(params: dict, detail: str = "full") -> ProblemCard:
    p, r, ans = params["book_price"], params["rate"], params["answer"]
    full = [
        r"A = P(1 - i\cdot n) = 0",
        rf"n = \frac{{1}}{{i}} = \frac{{100}}{{{r}}} = {_dec(100 / r)}",
        rf"n = {ans}\ \text{{years (round up)}}",
    ]
    return ProblemCard(
        instruction=(
            f"A R{p:,} asset depreciates at {r}% p.a. on a straight-line basis. "
            f"After how many years is its book value zero?"
        ),
        display_math=r"A = P(1 - i\cdot n) = 0",
        worked_steps=full if detail == "full" else [full[-1]],
    )


def _unlabeled_variant(problem, new_id: str):
    """A solving problem re-registered under a new id with its type word withheld
    from the prompt. Same generator, same verifier — only the instruction changes
    (via a labeled=False template), so the student must classify before solving."""
    return Problem(
        id=new_id,
        type_id=problem.type_id,
        name=f"{problem.name} (type unlabelled)",
        artifact_type=problem.artifact_type,
        problem_spec=problem.problem_spec,
        verifier_spec=problem.verifier_spec,
    )


arith_nth_unlabeled = _unlabeled_variant(
    arith_nth_term_formula, "arith_seq_nth_term_unlabeled"
)
geo_nth_unlabeled = _unlabeled_variant(
    geo_nth_term_formula, "geo_seq_nth_term_unlabeled"
)
arith_find_term_unlabeled = _unlabeled_variant(
    arith_find_term, "arith_seq_find_term_unlabeled"
)
geo_find_term_unlabeled = _unlabeled_variant(
    geo_find_term, "geo_seq_find_term_unlabeled"
)


PROBLEMS: dict[str, WorksheetEntry] = {
    identify_sequence_type.id: WorksheetEntry(
        problem=identify_sequence_type,
        template=template_identify_sequence_type,
    ),
    arith_nth_unlabeled.id: WorksheetEntry(
        problem=arith_nth_unlabeled,
        template=partial(template_arith_nth_term_formula, labeled=False),
    ),
    geo_nth_unlabeled.id: WorksheetEntry(
        problem=geo_nth_unlabeled,
        template=partial(template_geo_nth_term_formula, labeled=False),
    ),
    arith_find_term_unlabeled.id: WorksheetEntry(
        problem=arith_find_term_unlabeled,
        template=partial(template_arith_find_term, labeled=False),
    ),
    geo_find_term_unlabeled.id: WorksheetEntry(
        problem=geo_find_term_unlabeled,
        template=partial(template_geo_find_term, labeled=False),
    ),
    arith_nth_term_formula.id: WorksheetEntry(
        problem=arith_nth_term_formula,
        template=template_arith_nth_term_formula,
    ),
    arith_find_term.id: WorksheetEntry(
        problem=arith_find_term,
        template=template_arith_find_term,
    ),
    arith_find_n.id: WorksheetEntry(
        problem=arith_find_n,
        template=template_arith_find_n,
    ),
    arith_find_missing.id: WorksheetEntry(
        problem=arith_find_missing,
        template=template_arith_find_missing,
    ),
    arith_next_terms.id: WorksheetEntry(
        problem=arith_next_terms,
        template=template_arith_next_terms,
    ),
    geo_nth_term_formula.id: WorksheetEntry(
        problem=geo_nth_term_formula,
        template=template_geo_nth_term_formula,
    ),
    geo_find_term.id: WorksheetEntry(
        problem=geo_find_term,
        template=template_geo_find_term,
    ),
    arithmetic_series_sum.id: WorksheetEntry(
        problem=arithmetic_series_sum,
        template=template_arith_series_sum,
    ),
    geometric_series_finite.id: WorksheetEntry(
        problem=geometric_series_finite,
        template=template_geo_series_finite,
    ),
    geometric_series_infinite.id: WorksheetEntry(
        problem=geometric_series_infinite,
        template=template_geo_series_infinite,
    ),
    arith_from_two_terms.id: WorksheetEntry(
        problem=arith_from_two_terms,
        template=template_arith_from_two_terms,
    ),
    geo_from_two_terms.id: WorksheetEntry(
        problem=geo_from_two_terms,
        template=template_geo_from_two_terms,
    ),
    geo_find_missing.id: WorksheetEntry(
        problem=geo_find_missing,
        template=template_geo_find_missing,
    ),
    geo_find_n.id: WorksheetEntry(
        problem=geo_find_n,
        template=template_geo_find_n,
    ),
    geo_next_terms.id: WorksheetEntry(
        problem=geo_next_terms,
        template=template_geo_next_terms,
    ),
    arith_series_find_n.id: WorksheetEntry(
        problem=arith_series_find_n,
        template=template_arith_series_find_n,
    ),
    arith_series_sigma.id: WorksheetEntry(
        problem=arith_series_sigma,
        template=template_arith_series_sigma,
    ),
    monic_factorise_problem.id: WorksheetEntry(
        problem=monic_factorise_problem,
        template=template_monic_factorise,
    ),
    factorise_constraints.id: WorksheetEntry(
        problem=factorise_constraints,
        template=template_factorise_constraints,
    ),
    factorise_sign_case.id: WorksheetEntry(
        problem=factorise_sign_case,
        template=template_factorise_sign_case,
    ),
    factorise_enumerate.id: WorksheetEntry(
        problem=factorise_enumerate,
        template=template_factorise_enumerate,
    ),
    zero_product_atomic.id: WorksheetEntry(
        problem=zero_product_atomic,
        template=template_zero_product_atomic,
        sequence_fn=atomic_shuffled_n,
    ),
    zero_product_standard.id: WorksheetEntry(
        problem=zero_product_standard,
        template=template_zero_product_standard,
    ),
    zero_product_extension.id: WorksheetEntry(
        problem=zero_product_extension,
        template=template_zero_product_extension,
    ),
    trig_graph_amplitude.id: WorksheetEntry(
        problem=trig_graph_amplitude,
        template=template_trig_graph_amplitude,
    ),
    trig_graph_range.id: WorksheetEntry(
        problem=trig_graph_range,
        template=template_trig_graph_range,
    ),
    trig_graph_decreasing.id: WorksheetEntry(
        problem=trig_graph_decreasing,
        template=template_trig_graph_decreasing,
    ),
    trig_graph_solve.id: WorksheetEntry(
        problem=trig_graph_solve,
        template=template_trig_graph_solve,
    ),
    rform_match_coefficients.id: WorksheetEntry(
        problem=rform_match_coefficients,
        template=template_rform_match_coefficients,
    ),
    rform_find_R.id: WorksheetEntry(
        problem=rform_find_R,
        template=template_rform_find_R,
    ),
    rform_find_phi.id: WorksheetEntry(
        problem=rform_find_phi,
        template=template_rform_find_phi,
    ),
    rform_solve.id: WorksheetEntry(
        problem=rform_solve,
        template=template_rform_solve,
    ),
    parallelogram_cointerior.id: WorksheetEntry(
        problem=parallelogram_cointerior,
        template=template_parallelogram_cointerior,
    ),
    parallelogram_opposite.id: WorksheetEntry(
        problem=parallelogram_opposite,
        template=template_parallelogram_opposite,
    ),
    parallelogram_alternate.id: WorksheetEntry(
        problem=parallelogram_alternate,
        template=template_parallelogram_alternate,
    ),
    triangle_angle_sum.id: WorksheetEntry(
        problem=triangle_angle_sum,
        template=template_triangle_angle_sum,
    ),
    triangle_isosceles.id: WorksheetEntry(
        problem=triangle_isosceles,
        template=template_triangle_isosceles,
    ),
    triangle_exterior.id: WorksheetEntry(
        problem=triangle_exterior,
        template=template_triangle_exterior,
    ),
    compound_amount.id: WorksheetEntry(
        problem=compound_amount,
        template=template_compound_amount,
    ),
    compound_principal.id: WorksheetEntry(
        problem=compound_principal,
        template=template_compound_principal,
    ),
    compound_rate.id: WorksheetEntry(
        problem=compound_rate,
        template=template_compound_rate,
    ),
    appreciation.id: WorksheetEntry(
        problem=appreciation,
        template=template_appreciation,
    ),
    nominal_to_effective.id: WorksheetEntry(
        problem=nominal_to_effective,
        template=template_nominal_to_effective,
    ),
    effective_to_nominal.id: WorksheetEntry(
        problem=effective_to_nominal,
        template=template_effective_to_nominal,
    ),
    fv_annuity_amount.id: WorksheetEntry(
        problem=fv_annuity_amount,
        template=template_fv_annuity_amount,
    ),
    fv_annuity_deposit.id: WorksheetEntry(
        problem=fv_annuity_deposit,
        template=template_fv_annuity_deposit,
    ),
    fv_annuity_n.id: WorksheetEntry(
        problem=fv_annuity_n,
        template=template_fv_annuity_n,
    ),
    pv_annuity_amount.id: WorksheetEntry(
        problem=pv_annuity_amount,
        template=template_pv_annuity_amount,
    ),
    pv_annuity_payment.id: WorksheetEntry(
        problem=pv_annuity_payment,
        template=template_pv_annuity_payment,
    ),
    pv_annuity_n.id: WorksheetEntry(
        problem=pv_annuity_n,
        template=template_pv_annuity_n,
    ),
    pv_annuity_total_interest.id: WorksheetEntry(
        problem=pv_annuity_total_interest,
        template=template_pv_annuity_total_interest,
    ),
    depreciation_amount.id: WorksheetEntry(
        problem=depreciation_amount,
        template=template_depreciation_amount,
    ),
    depreciation_rate.id: WorksheetEntry(
        problem=depreciation_rate,
        template=template_depreciation_rate,
    ),
    depreciation_to_zero.id: WorksheetEntry(
        problem=depreciation_to_zero,
        template=template_depreciation_to_zero,
    ),
}

REGISTRY = {id: e.problem for id, e in PROBLEMS.items()}
TEMPLATES = {id: e.template for id, e in PROBLEMS.items()}

# Curated multi-topic worksheets: name → [(problem_id, count), ...]. A bundle
# produces one mixed paper spanning several archetypes, in listed order.
BUNDLES: dict[str, list[tuple[str, int]]] = {
    "sequences": [
        ("arith_seq_nth_term_formula", 1),
        ("arith_seq_find_term", 1),
        ("arith_seq_find_n", 1),
        ("geo_seq_nth_term_formula", 1),
        ("geo_seq_find_term", 1),
        ("arith_series_sum", 1),
        ("geo_series_finite", 1),
        ("geo_series_infinite", 1),
    ],
    # Classification-first: two isolated "which type?" drills, then unlabelled
    # solves that interleave arithmetic and geometric so the student must
    # classify (the withheld first half) before applying a method.
    "sequences_mixed": [
        ("identify_sequence_type", 2),
        ("arith_seq_nth_term_unlabeled", 1),
        ("geo_seq_nth_term_unlabeled", 1),
        ("geo_seq_find_term_unlabeled", 1),
        ("arith_seq_find_term_unlabeled", 1),
    ],
    # Full sequences & series revision across a few A4 pages: classification,
    # both sequence types (incl. the two-terms and mean/next-term skills), and
    # the series family (sums, sigma, find-n). ~18 problems.
    "sequences_full": [
        ("identify_sequence_type", 2),
        ("arith_seq_nth_term_formula", 1),
        ("arith_seq_find_term", 1),
        ("arith_seq_find_missing", 1),
        ("arith_seq_from_two_terms", 1),
        ("geo_seq_nth_term_formula", 1),
        ("geo_seq_find_term", 1),
        ("geo_seq_find_missing", 1),
        ("geo_seq_find_n", 1),
        ("geo_seq_next_terms", 1),
        ("geo_seq_from_two_terms", 1),
        ("arith_series_sum", 1),
        ("arith_series_find_n", 1),
        ("arith_series_sigma", 1),
        ("geo_series_finite", 1),
        ("geo_series_infinite", 1),
    ],
    # Gr12 finance & annuities revision spanning all five archetypes: compound
    # growth (+ solve-rate), nominal→effective, future- and present-value
    # annuities (incl. the load-bearing solve-N modes), and depreciation.
    "finance": [
        ("finance_compound_periodic_amount", 1),
        ("finance_compound_periodic_rate", 1),
        ("finance_nominal_to_effective", 1),
        ("finance_fv_annuity_amount", 1),
        ("finance_fv_annuity_n", 1),
        ("finance_pv_annuity_payment", 1),
        ("finance_pv_annuity_n", 1),
        ("finance_depreciation_amount", 1),
        ("finance_depreciation_to_zero", 1),
    ],
}


# ── HTML / CSS ────────────────────────────────────────────────────────────────

# $$ for display, $ for inline — works cleanly in controlled content with no
# prose dollar signs.  List $$ first so auto-render greedily matches it before $.
# NOTE: KaTeX is loaded from a CDN, so rendering (and --pdf) needs internet at
# open/print time.  Self-hosting for a fully offline artifact is deferred to a
# dedicated bundling commit.
_KATEX = """\
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"
  onload="renderMathInElement(document.body,{delimiters:[{left:'$$',right:'$$',display:true},{left:'$',right:'$',display:false}],throwOnError:false})">
</script>"""

_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }

body {
    font-family: Georgia, "Times New Roman", serif;
    background: #ddd;
    color: #111;
}

/* ── page shell: fixed A4 size, generous fixed padding ── */
.page {
    width: 210mm;
    height: 297mm;
    margin: 8mm auto;
    padding: 22mm 24mm 18mm;
    background: #fff;
    display: flex;
    flex-direction: column;
    overflow: hidden;           /* nothing spills past the page boundary */
    page-break-after: always;
    break-after: page;
}

.page-header {
    border-bottom: 1.5px solid #444;
    padding-bottom: 3.5mm;
    margin-bottom: 6mm;
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    flex-shrink: 0;
}
.page-header h1   { font-size: 12.5pt; font-weight: bold; }
.page-header span { font-size: 9pt; color: #666; }

/* problems stack from the top of the page; leftover height is whitespace.
   Boxes size to their content (no flex-stretch), so a box can never be
   inflated past the page edge and clipped. */
.problems {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 6mm;
    min-height: 0;
}

.problem {
    display: flex;
    flex-direction: column;
    border: 1px solid #bbb;
    border-radius: 2px;
    padding: 4.5mm 5.5mm 4mm;
    break-inside: avoid;
    page-break-inside: avoid;
}

.problem-label {
    font-size: 8.5pt;
    font-weight: bold;
    color: #777;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 2mm;
    flex-shrink: 0;
    display: flex;
    justify-content: space-between;
    align-items: baseline;
}
.problem-marks {
    font-weight: normal;
    text-transform: none;
    letter-spacing: 0;
    color: #999;
    font-style: italic;
}

.problem-instruction {
    font-size: 10.5pt;
    margin-bottom: 3mm;
    flex-shrink: 0;
}

.problem-equation {
    font-size: 1.2em;
    padding: 0 3mm 3.5mm;
    flex-shrink: 0;
}

/* ruled working space: fixed height (~4 lines) so boxes stay compact and the
   page never overflows. */
.working-space {
    height: 36mm;
    background-image: repeating-linear-gradient(
        to bottom,
        transparent 0, transparent 8.5mm,
        #ccc 8.5mm, #ccc 9mm
    );
}

/* ── answer key: not a fixed-height page, just a trailing block ── */
.answer-key {
    width: 210mm;
    margin: 8mm auto;
    padding: 22mm 24mm 18mm;
    background: #fff;
}
.answer-key h2 {
    font-size: 12.5pt;
    font-weight: bold;
    border-bottom: 1.5px solid #444;
    padding-bottom: 3.5mm;
    margin-bottom: 7mm;
}
.answer-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(80mm, 1fr));
    gap: 5mm 8mm;
}
.answer-row {
    display: flex;
    align-items: flex-start;
    gap: 2.5mm;
    font-size: 11pt;
}
.answer-num { font-weight: bold; color: #777; min-width: 7mm; padding-top: 0.15em; }
.answer-steps { display: flex; flex-direction: column; gap: 1.5mm; flex: 1; }
.answer-marks {
    font-weight: bold;
    color: #444;
    padding-top: 0.15em;
    padding-left: 2mm;
    white-space: nowrap;
}

/* graph + working-space side by side */
.problem-body {
    flex: 1;
    display: flex;
    gap: 4mm;
    min-height: 0;
}
.problem-graph-side {
    flex: 0 0 47%;
    line-height: 0;
}
.problem-graph-side svg { width: 100%; height: auto; }
.problem-body .working-space { min-height: 0; }

@media print {
    /* map each fixed 297mm .page onto exactly one physical sheet: no @page
       margin (the .page padding is the margin), no browser-added splitting. */
    @page       { size: A4; margin: 0; }
    body        { background: none; }
    .page       { margin: 0; }
    .answer-key { margin: 0; }
}
"""


def _working_height_mm(marks: int | None) -> int:
    """Ruled working height scaled to the mark load (~9mm per line): 2-mark (or
    unmarked) → 4 lines; 3 → 6; 4+ → 8. Keeps low-mark boxes compact while giving
    multi-step questions room to actually work in."""
    if not marks or marks <= 2:
        return 36
    if marks == 3:
        return 54
    return 72


def _problem_html(n: int, card: ProblemCard) -> str:
    if card.graph_svg:
        body = (
            '<div class="problem-body">'
            f'<div class="problem-graph-side">{card.graph_svg}</div>'
            '<div class="working-space"></div>'
            "</div>"
        )
    else:
        h = _working_height_mm(card.marks)
        body = f'<div class="working-space" style="height:{h}mm"></div>'
    marks = (
        f'<span class="problem-marks">({card.marks} '
        f"{'mark' if card.marks == 1 else 'marks'})</span>"
        if card.marks
        else ""
    )
    return (
        '<div class="problem">'
        f'<div class="problem-label">Question {n}{marks}</div>'
        f'<div class="problem-instruction">{card.instruction}</div>'
        f'<div class="problem-equation">$${card.display_math}$$</div>'
        f"{body}"
        "</div>"
    )


def _page_html(
    cards: list[ProblemCard],
    offset: int,
    page_n: int,
    total_pages: int,
    title: str,
) -> str:
    problems = "".join(_problem_html(offset + i + 1, c) for i, c in enumerate(cards))
    return (
        '<section class="page">'
        '<div class="page-header">'
        f"<h1>{title}</h1>"
        f"<span>Page {page_n} of {total_pages}</span>"
        "</div>"
        f'<div class="problems">{problems}</div>'
        "</section>\n"
    )


def _answer_key_html(cards: list[ProblemCard]) -> str:
    def _steps_html(steps: list[str]) -> str:
        return "".join(f"<div>${s}$</div>" for s in steps)

    def _marks_html(card: ProblemCard) -> str:
        if not card.marks:
            return ""
        return f'<span class="answer-marks">[{card.marks}]</span>'

    rows = "".join(
        f'<div class="answer-row">'
        f'<span class="answer-num">{i + 1}.</span>'
        f'<div class="answer-steps">{_steps_html(c.worked_steps)}</div>'
        f"{_marks_html(c)}"
        f"</div>"
        for i, c in enumerate(cards)
    )
    return (
        '<section class="answer-key">'
        "<h2>Worked Answers</h2>"
        f'<div class="answer-grid">{rows}</div>'
        "</section>\n"
    )


# Each problem box is ~68mm tall (label + instruction + equation + 36mm ruled
# space + padding + inter-box gap); a page has ~243mm of content height after the
# margins and header.  Beyond 3 boxes the last one is clipped by overflow:hidden.
_MAX_PER_PAGE = 3


def build_html(title: str, cards: list[ProblemCard], per_page: int = 2) -> str:
    if per_page > _MAX_PER_PAGE:
        print(
            f"warning: --per-page {per_page} exceeds the {_MAX_PER_PAGE}-box page "
            f"capacity; boxes past #{_MAX_PER_PAGE} will be clipped. "
            f"Use --per-page {_MAX_PER_PAGE} or fewer.",
            file=sys.stderr,
        )
    n_pages = math.ceil(len(cards) / per_page)
    pages = [
        _page_html(
            cards[p * per_page : (p + 1) * per_page],
            p * per_page,
            p + 1,
            n_pages,
            title,
        )
        for p in range(n_pages)
    ]
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="UTF-8">\n'
        f"<title>{title}</title>\n"
        f"{_KATEX}\n"
        f"<style>{_CSS}</style>\n"
        "</head>\n<body>\n"
        + "".join(pages)
        + _answer_key_html(cards)
        + "</body>\n</html>\n"
    )


# ── generation helpers ────────────────────────────────────────────────────────


def _generate_cards(
    engine: Engine,
    entry: WorksheetEntry,
    rng: random.Random,
    n: int,
    long_count: int,
) -> list[ProblemCard]:
    if entry.sequence_fn is not None:
        params_list = entry.sequence_fn(rng, n)
    else:
        params_list = _generate_unique_retry(engine, entry.problem.id, rng, n)
    marks = _problem_marks(entry.problem)
    cards = []
    for i in range(len(params_list)):
        card = entry.template(
            params_list[i], detail="full" if i < long_count else "short"
        )
        if card.marks is None:
            card.marks = marks
        cards.append(card)
    return cards


def _problem_marks(problem: object) -> int | None:
    """Total marks for a problem, summed across a multi-step verifier_spec.

    verifier_spec is either a single dict or a list of per-step dicts; each
    contributes ``marks_possible`` (default 1).  Returns None if absent.
    """
    spec = getattr(problem, "verifier_spec", None)
    if spec is None:
        return None
    steps = spec if isinstance(spec, list) else [spec]
    return sum(int(s.get("marks_possible", 1)) for s in steps)


def _generate_unique_retry(
    engine: Engine,
    problem_id: str,
    rng: random.Random,
    n: int,
    max_retries: int = 50,
) -> list[dict]:
    seen: set[str] = set()
    result: list[dict] = []
    for _ in range(n):
        params = None
        for _ in range(max_retries):
            candidate = engine.instantiate(problem_id, seed=rng.randint(0, 2**31))
            key = str(
                sorted(
                    (k, v) for k, v in candidate.params.items() if isinstance(v, str)
                )
            )
            if key not in seen:
                seen.add(key)
                params = candidate.params
                break
        result.append(params if params is not None else candidate.params)
    return result


# ── PDF export ────────────────────────────────────────────────────────────────


def _find_chrome() -> str | None:
    """Locate a Chrome/Chromium binary for headless PDF printing."""
    import shutil

    for name in (
        "chromium",
        "chromium-browser",
        "google-chrome",
        "google-chrome-stable",
        "chrome",
    ):
        found = shutil.which(name)
        if found:
            return found
    # Playwright-managed Chromium (installed in the user cache)
    cache = Path.home() / ".cache" / "ms-playwright"
    if cache.is_dir():
        matches = sorted(cache.glob("chromium*/chrome-linux*/chrome"))
        if matches:
            return str(matches[-1])
    return None


def html_to_pdf(html_path: Path, pdf_path: Path) -> None:
    """Render an HTML worksheet to PDF via headless Chrome.

    The HTML is fully self-contained (KaTeX inlined), so no network is needed;
    a virtual-time budget lets KaTeX finish typesetting before the print snapshot.
    """
    chrome = _find_chrome()
    if chrome is None:
        raise RuntimeError(
            "no Chrome/Chromium found for --pdf; install chromium or run "
            "'playwright install chromium'"
        )
    subprocess.run(
        [
            chrome,
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            "--no-pdf-header-footer",
            "--virtual-time-budget=5000",
            f"--print-to-pdf={pdf_path}",
            html_path.resolve().as_uri(),
        ],
        check=True,
        capture_output=True,
    )


# ── CLI ───────────────────────────────────────────────────────────────────────


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate an HTML practice worksheet.")
    ap.add_argument(
        "n",
        type=int,
        nargs="?",
        default=None,
        help="Number of problems (ignored when --bundle is given)",
    )
    ap.add_argument(
        "--bundle",
        default=None,
        choices=list(BUNDLES),
        help="Generate a curated multi-topic worksheet instead of N of one type",
    )
    ap.add_argument(
        "--problem",
        default="monic_factorise",
        choices=list(TEMPLATES),
        metavar="PROBLEM",
        help=f"Problem type: {', '.join(TEMPLATES)}",
    )
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--title", default="Factorisation Practice")
    ap.add_argument("--per-page", type=int, default=2, dest="per_page")
    ap.add_argument("--output", default="worksheet.html")
    ap.add_argument(
        "--pdf",
        action="store_true",
        help="Also render a PDF next to the HTML (via headless Chrome)",
    )
    ap.add_argument(
        "--long",
        type=int,
        default=None,
        dest="long_count",
        metavar="N",
        help=(
            "First N problems get full 6-step worked answer; "
            "rest use 3-step short form."
        ),
    )
    args = ap.parse_args()

    engine = Engine(registry=InMemoryRegistry(REGISTRY))
    rng = random.Random(args.seed)

    if args.bundle is not None:
        cards = []
        for pid, count in BUNDLES[args.bundle]:
            cards.extend(_generate_cards(engine, PROBLEMS[pid], rng, count, count))
        label = f"bundle '{args.bundle}' ({len(cards)} problems)"
    else:
        if args.n is None:
            ap.error("provide N (number of problems) or --bundle")
        entry = PROBLEMS[args.problem]
        long_count = args.long_count if args.long_count is not None else args.n
        cards = _generate_cards(engine, entry, rng, args.n, long_count)
        label = f"{args.n} problems ({args.problem})"

    html = build_html(args.title, cards, per_page=args.per_page)
    html_path = Path(args.output)
    html_path.write_text(html, encoding="utf-8")
    print(f"Wrote {label} → {args.output}")

    if args.pdf:
        pdf_path = html_path.with_suffix(".pdf")
        html_to_pdf(html_path, pdf_path)
        print(f"Wrote PDF → {pdf_path}")


if __name__ == "__main__":
    main()
