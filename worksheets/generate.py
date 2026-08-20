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

from content.examples.analytic_geometry_triangle import (
    problem as analytic_geometry_triangle,
)
from content.examples.angle_between_lines import angle_between_lines
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
from content.examples.circle_equation import circle_equation
from content.examples.circle_tangent import circle_tangent
from content.examples.compound_periodic import (
    appreciation,
    compound_amount,
    compound_principal,
    compound_rate,
)
from content.examples.concavity_inflection import concavity_inflection
from content.examples.counting_arrangements import (
    counting_all,
    counting_not_together,
    counting_together,
)
from content.examples.cubic_stationary_points import cubic_stationary_points
from content.examples.depreciation import (
    depreciation_amount,
    depreciation_rate,
    depreciation_to_zero,
)
from content.examples.derivative_first_principles import derivative_first_principles
from content.examples.derivative_rules import derivative_rules
from content.examples.discriminant_nature import discriminant_nature
from content.examples.exponent_laws import (
    exponent_algebraic_simplify,
    exponent_variable_simplify,
)
from content.examples.exponential_equation import exponential_equation
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
from content.examples.grouped_mean_solve import grouped_mean_solve
from content.examples.independent_events import (
    independent_decide,
    independent_intersection,
    independent_union,
)
from content.examples.line_equation import line_equation
from content.examples.linear_equation import problem as linear_add_pos_problem
from content.examples.linear_equations import (
    linear_double_inequality,
    linear_expand,
    linear_literal,
    linear_rational,
    simultaneous_2x2,
)
from content.examples.mean_stddev import mean_stddev
from content.examples.monic_factorise import problem as monic_factorise_problem
from content.examples.motion_calculus import motion_calculus
from content.examples.nominal_effective import (
    effective_to_nominal,
    nominal_to_effective,
)
from content.examples.nonlinear_simultaneous import nonlinear_simultaneous
from content.examples.optimisation_solve import optimisation_solve
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
from content.examples.probability_venn import (
    prob_count_intersection,
    prob_venn_intersection,
)
from content.examples.quadratic_inequality import quadratic_inequality
from content.examples.quadratic_roots import problem as quadratic_factor_problem
from content.examples.quadratic_sequence import (
    find_n as quad_find_n,
)
from content.examples.quadratic_sequence import (
    find_term as quad_find_term,
)
from content.examples.quadratic_sequence import (
    next_terms as quad_next_terms,
)
from content.examples.quadratic_sequence import (
    nth_term_formula as quad_nth_term_formula,
)
from content.examples.rform_skills import (
    rform_find_phi,
    rform_find_R,
    rform_match_coefficients,
    rform_solve,
)
from content.examples.sequence_classification import (
    admissible_types,
    identify_sequence_type,
    is_arithmetic,
    is_geometric,
    possible_sequence_types,
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
from content.examples.statistics_grouped import problem as stats_grouped
from content.examples.statistics_one_var import problem as stats_one_var
from content.examples.surd_equation import surd_equation
from content.examples.tangent_line import tangent_line
from content.examples.tree_probability import (
    tree_draw_both,
    tree_draw_one_each,
    tree_total_probability,
)
from content.examples.triangle_angles import (
    triangle_angle_sum,
    triangle_exterior,
    triangle_isosceles,
)
from content.examples.trig import (
    trig_cast_ratios,
    trig_equation,
    trig_special_angles,
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
from content.scope_predicates import PREDICATES
from problem_instantiation_tool.engine import Engine
from problem_instantiation_tool.exceptions import ScopeViolationError
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


def _signed(n) -> str:
    """'+ 5' / '- 3/2' — a signed (possibly Rational) coefficient as a LaTeX term."""
    mag = sympy.latex(abs(n))
    return f"- {mag}" if n < 0 else f"+ {mag}"


def _par(n) -> str:
    """Parenthesise a negative operand so a sum reads '3 + (-6)', not '3+-6'."""
    return f"({n})" if n < 0 else f"{n}"


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


# ── sequences & series: quadratic templates ─────────────────────────────────────


def _quad_formula_latex(a: int, b: int, c: int) -> str:
    """LaTeX for Tₙ = an² + bn + c with signs tidied by SymPy."""
    n = sympy.Symbol("n")
    return sympy.latex(
        sympy.Integer(a) * n**2 + sympy.Integer(b) * n + sympy.Integer(c)
    )


def template_quad_nth_term_formula(
    params: dict, detail: str = "full", labeled: bool = True
) -> ProblemCard:
    a, b, c = params["a"], params["b"], params["c"]
    t1, t2, t3, t4 = params["t1"], params["t2"], params["t3"], params["t4"]
    d1, d2, d3 = t2 - t1, t3 - t2, t4 - t3
    ans = sympy.latex(params["answer"])
    if detail == "full":
        steps = [
            rf"\Delta:\ {d1},\ {d2},\ {d3}\qquad \Delta^2:\ {d2 - d1},\ {d3 - d2}",
            rf"2a = {2 * a} \;\Rightarrow\; a = {a}",
            rf"3a + b = {d1} \;\Rightarrow\; b = {b}",
            rf"a + b + c = {t1} \;\Rightarrow\; c = {c}",
            rf"T_n = {ans}",
        ]
    else:
        steps = [rf"a = {a},\ b = {b},\ c = {c}", rf"T_n = {ans}"]
    return ProblemCard(
        instruction=(
            f"Determine the general term $T_n$ of {_seq_noun('quadratic', labeled)}:"
        ),
        display_math=_seq_display([t1, t2, t3, t4]),
        worked_steps=steps,
    )


def template_quad_find_term(
    params: dict, detail: str = "full", labeled: bool = True
) -> ProblemCard:
    a, b, c = params["a"], params["b"], params["c"]
    t1, t2, t3 = params["t1"], params["t2"], params["t3"]
    nt, ans = params["n_target"], params["answer"]
    d1, d2 = t2 - t1, t3 - t2
    f_l = _quad_formula_latex(a, b, c)
    if detail == "full":
        steps = [
            rf"\Delta:\ {d1},\ {d2}\qquad \Delta^2 = {d2 - d1} \;\Rightarrow\; a = {a}",
            rf"3a + b = {d1},\ \ a + b + c = {t1} \;\Rightarrow\; b = {b},\ c = {c}",
            rf"T_n = {f_l}",
            rf"T_{{{nt}}} = {ans}",
        ]
    else:
        steps = [rf"T_n = {f_l}", rf"T_{{{nt}}} = {ans}"]
    return ProblemCard(
        instruction=(
            rf"Calculate the ${nt}^{{\text{{th}}}}$ term, $T_{{{nt}}}$, "
            f"of {_seq_noun('quadratic', labeled)}:"
        ),
        display_math=_seq_display([t1, t2, t3]),
        worked_steps=steps,
    )


def template_quad_next_terms(params: dict, detail: str = "full") -> ProblemCard:
    shown = params["terms_shown"]
    n1, n2 = params["next_1"], params["next_2"]
    d1 = [shown[i + 1] - shown[i] for i in range(3)]
    sd = d1[1] - d1[0]  # constant second difference = 2a
    step_a, step_b = d1[2] + sd, d1[2] + 2 * sd
    if detail == "full":
        steps = [
            rf"\Delta:\ {d1[0]},\ {d1[1]},\ {d1[2]}\qquad \Delta^2 = {sd}",
            rf"T_5 = {shown[-1]} + ({d1[2]} + {sd}) = {n1}",
            rf"T_6 = {n1} + ({step_a} + {sd}) = {n2}",
        ]
    else:
        steps = [rf"\Delta^2 = {sd};\quad {n1},\ {n2}"]
    _ = step_b  # second next-difference, shown inline above
    return ProblemCard(
        instruction="Write down the next two terms of the quadratic sequence:",
        display_math=_seq_display(shown),
        worked_steps=steps,
    )


def template_quad_find_n(params: dict, detail: str = "full") -> ProblemCard:
    a, b, c = params["a"], params["b"], params["c"]
    t1, t2, t3 = params["t1"], params["t2"], params["t3"]
    target, ans = params["target"], params["answer"]
    or_l = sympy.latex(params["other_root"])
    f_l = _quad_formula_latex(a, b, c)
    quad_l = _quad_formula_latex(a, b, c - target)
    if detail == "full":
        steps = [
            rf"T_n = {f_l}",
            rf"{f_l} = {target} \;\Rightarrow\; {quad_l} = 0",
            rf"n = {ans} \quad\text{{or}}\quad n = {or_l}\ (\text{{reject}},\ n>0)",
            rf"n = {ans}",
        ]
    else:
        steps = [rf"{f_l} = {target} \;\Rightarrow\; n = {ans}"]
    return ProblemCard(
        instruction=rf"Which term of the quadratic sequence is equal to ${target}$?",
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
    if answer == "quadratic":
        # first differences are not constant, but the second differences are:
        # a constant, non-zero second difference is the quadratic signature.
        d2 = [d[1] - d[0], d[2] - d[1]]
        second_line = (
            rf"\Delta^2: {d[1]} - ({d[0]}) = {d2[0]},\quad "
            rf"{d[2]} - ({d[1]}) = {d2[1]}"
        )
        return [
            diff_line,
            second_line,
            rf"\text{{constant 2nd difference }} = {d2[0]}"
            r" \;\Rightarrow\; \textbf{quadratic}",
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
            "arithmetic, geometric, quadratic or neither:"
        ),
        display_math=_seq_display(terms),
        worked_steps=steps,
    )


def _possible_reason(terms: list[int]) -> list[str]:
    """Run each discriminator as a *consistency* test on the three shown terms, then
    conclude with the set of types that survive. Each line shows the actual check a
    student would perform (differences / ratios / second difference)."""
    d = [terms[i + 1] - terms[i] for i in range(2)]
    lines: list[str] = []

    arith = is_arithmetic(terms)
    arith_verdict = "constant" if arith else "not constant"
    arith_tail = "could be arithmetic" if arith else "not arithmetic"
    lines.append(
        rf"\Delta:\ {d[0]},\ {d[1]}\ (\text{{{arith_verdict}}})"
        rf" \;\Rightarrow\; \text{{{arith_tail}}}"
    )

    if all(x != 0 for x in terms):
        ratios = [sympy.Rational(terms[i + 1], terms[i]) for i in range(2)]
        geo = is_geometric(terms)
        geo_tail = "could be geometric" if geo else "not geometric"
        lines.append(
            rf"\tfrac{{T_2}}{{T_1}} = {sympy.latex(ratios[0])},\ "
            rf"\tfrac{{T_3}}{{T_2}} = {sympy.latex(ratios[1])}"
            rf" \;\Rightarrow\; \text{{{geo_tail}}}"
        )
    else:
        lines.append(r"\text{a term is } 0 \;\Rightarrow\; \text{not geometric}")

    sd = d[1] - d[0]
    quad_tail = (
        "could be quadratic" if sd != 0 else "second difference 0: not quadratic"
    )
    lines.append(rf"\Delta^2 = {sd} \;\Rightarrow\; \text{{{quad_tail}}}")

    order = ["arithmetic", "geometric", "quadratic"]
    admissible = [t for t in order if t in admissible_types(terms)]
    body = r",\ ".join(rf"\text{{{name}}}" for name in admissible)
    lines.append(rf"\therefore\ \{{\,{body}\,\}}")
    return lines


def template_possible_sequence_types(params: dict, detail: str = "full") -> ProblemCard:
    terms = [params["t1"], params["t2"], params["t3"]]
    reason = _possible_reason(terms)
    steps = reason if detail == "full" else [reason[-1]]
    return ProblemCard(
        instruction=(
            "These are the first three terms of a sequence. State which of "
            "arithmetic, geometric or quadratic the sequence could be — "
            "list every type it is still consistent with:"
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
    """Rand amount as LaTeX in SA/DBE convention: space-grouped thousands and a
    decimal comma, e.g. ``R1 500,00``. The thousands separator is a math thin
    space; the decimal comma is braced (``{,}``) so KaTeX doesn't add the
    punctuation space that would read as ``1 500, 00``."""
    body = f"{x:,.{dp}f}".replace(",", r"\,").replace(".", "{,}")
    return rf"\text{{R}}\,{body}"


def _rand(x: float, dp: int = 2) -> str:
    """Plain-text Rand amount in SA/DBE convention (space-grouped thousands,
    decimal comma) for prose instructions, e.g. ``R1 500,00``."""
    body = f"{x:,.{dp}f}".replace(",", " ").replace(".", ",")
    return f"R{body}"


def _dec(x: float) -> str:
    """A decimal to at most 6 places, trailing zeros trimmed (for rates i = r/100m),
    in SA convention: decimal comma, braced (``{,}``) so KaTeX omits the
    punctuation space (``0{,}03375``)."""
    return f"{x:.6f}".rstrip("0").rstrip(".").replace(".", "{,}")


def _num(x) -> str:
    """Plain-text number in SA convention (decimal comma) for prose, e.g. a rate
    ``13.5`` → ``13,5``. Integers are unchanged."""
    return f"{x}".replace(".", ",")


def _numtex(x) -> str:
    """A number for LaTeX math in SA convention: decimal comma braced (``{,}``) so
    KaTeX omits the punctuation space, e.g. ``13.5`` → ``13{,}5``."""
    return f"{x}".replace(".", "{,}")


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
        rf"i = \frac{{{_numtex(r)}\%}}{{{m}}} = {_dec(i)}, "
        rf"\quad N = {m}\times{n} = {periods}",
        r"A = P(1 + i)^{N}",
        sub,
        rf"A = {_zar(ans)}",
    ]
    return ProblemCard(
        instruction=(
            f"{_rand(p, 0)} is invested at {_num(r)}% p.a. compounded {_COMP_WORD[m]} "
            f"for {n} years. Determine the accumulated amount."
        ),
        display_math="",
        worked_steps=full if detail == "full" else [rf"{sub} = {_zar(ans)}"],
    )


def template_compound_principal(params: dict, detail: str = "full") -> ProblemCard:
    a, r, m = params["target_amount"], params["rate"], params["compounding"]
    n, periods, i = params["years"], params["periods"], params["per_period_rate"]
    ans = params["answer"]
    sub = rf"P = \frac{{{_zar(a, 0)}}}{{(1 + {_dec(i)})^{{{periods}}}}}"
    full = [
        rf"i = \frac{{{_numtex(r)}\%}}{{{m}}} = {_dec(i)}, \quad N = {periods}",
        r"P = \frac{A}{(1 + i)^{N}}",
        sub,
        rf"P = {_zar(ans)}",
    ]
    return ProblemCard(
        instruction=(
            f"What amount, invested now at {_num(r)}% p.a. compounded {_COMP_WORD[m]}, "
            f"grows to {_rand(a, 0)} in {n} years?"
        ),
        display_math="",
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
        rf"r = i \times {m} \times 100 = {_numtex(ans)}\%",
    ]
    return ProblemCard(
        instruction=(
            f"{_rand(p, 0)} grows to {_rand(a)} in {n} years with interest "
            f"compounded {_COMP_WORD[m]}. Determine the nominal annual interest rate."
        ),
        display_math="",
        worked_steps=full if detail == "full" else [full[1], rf"r = {_numtex(ans)}\%"],
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
            f"An item costing {_rand(price, 0)} rises in price by {_num(r)}% per year. "
            f"What will it cost in {n} years?"
        ),
        display_math="",
        worked_steps=full if detail == "full" else [rf"{sub} = {_zar(ans)}"],
    )


# ── finance / annuities: nominal ↔ effective templates ──────────────────────────


def template_nominal_to_effective(params: dict, detail: str = "full") -> ProblemCard:
    i_nom, m, ans = params["nominal_rate"], params["compounding"], params["answer"]
    full = [
        r"1 + i_{\text{eff}} = \left(1 + \frac{i^{(m)}}{m}\right)^{m}",
        rf"1 + i_{{\text{{eff}}}} = "
        rf"\left(1 + \frac{{{_numtex(i_nom)}\%}}{{{m}}}\right)^{{{m}}}",
        rf"i_{{\text{{eff}}}} = {_numtex(ans)}\%",
    ]
    return ProblemCard(
        instruction=(
            f"Convert a nominal rate of {_num(i_nom)}% p.a. compounded {_COMP_WORD[m]} "
            f"to an effective annual rate."
        ),
        display_math="",
        worked_steps=full
        if detail == "full"
        else [rf"i_{{\text{{eff}}}} = {_numtex(ans)}\%"],
    )


def template_effective_to_nominal(params: dict, detail: str = "full") -> ProblemCard:
    i_eff, m, ans = params["effective_rate"], params["compounding"], params["answer"]
    full = [
        r"1 + i_{\text{eff}} = \left(1 + \frac{i^{(m)}}{m}\right)^{m}",
        rf"i^{{(m)}} = {m}\left[(1 + {_numtex(i_eff / 100)})^{{1/{m}}} - 1\right]",
        rf"i^{{(m)}} = {_numtex(ans)}\%",
    ]
    return ProblemCard(
        instruction=(
            f"Convert an effective annual rate of {_num(i_eff)}% to a nominal rate "
            f"compounded {_COMP_WORD[m]}."
        ),
        display_math="",
        worked_steps=full if detail == "full" else [rf"i^{{(m)}} = {_numtex(ans)}\%"],
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
        rf"i = \frac{{{_numtex(r)}\%}}{{{m}}} = {_dec(i)}, \quad N = {periods}",
        rf"F = x\cdot\frac{{(1 + i)^{{N}} - 1}}{{i}}{due}",
        sub,
        rf"F = {_zar(ans)}",
    ]
    return ProblemCard(
        instruction=(
            f"{_rand(x)} is deposited {_timing_phrase(timing, m)} at {_num(r)}% p.a. "
            f"compounded {_COMP_WORD[m]} for {n} years. Determine the future value."
        ),
        display_math="",
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
        rf"i = \frac{{{_numtex(r)}\%}}{{{m}}} = {_dec(i)}, \quad N = {periods}",
        rf"x = \frac{{F\cdot i}}{{(1 + i)^{{N}} - 1}}{due}",
        sub,
        rf"x = {_zar(ans)}",
    ]
    return ProblemCard(
        instruction=(
            f"What regular deposit, made {_timing_phrase(timing, m)}, accumulates "
            f"to {_rand(a, 0)} in {n} years at {_num(r)}% p.a. compounded "
            f"{_COMP_WORD[m]}?"
        ),
        display_math="",
        worked_steps=full if detail == "full" else [rf"{sub} = {_zar(ans)}"],
    )


def template_fv_annuity_n(params: dict, detail: str = "full") -> ProblemCard:
    x, r, m = params["deposit"], params["rate"], params["compounding"]
    a, i, ans = params["target_amount"], params["per_period_rate"], params["answer"]
    solved = math.log(1 + a * i / x) / math.log(1 + i)
    full = [
        rf"F = x\cdot\frac{{(1 + i)^{{n}} - 1}}{{i}}, \quad i = {_dec(i)}",
        r"n = \frac{\ln\left(1 + \frac{F\,i}{x}\right)}{\ln(1 + i)}",
        rf"n \approx {_numtex(f'{solved:.2f}')} \;\Rightarrow\; "
        rf"n = {ans}\ \text{{deposits (round up)}}",
    ]
    return ProblemCard(
        instruction=(
            f"How many deposits of {_rand(x)} reach at least {_rand(a)} at "
            f"{_num(r)}% p.a. compounded {_COMP_WORD[m]}?"
        ),
        display_math="",
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
        rf"i = \frac{{{_numtex(r)}\%}}{{{m}}} = {_dec(i)}, \quad N = {periods}",
        rf"P = x\cdot\frac{{1 - (1 + i)^{{-N}}}}{{i}}{due}",
        sub,
        rf"P = {_zar(ans)}",
    ]
    return ProblemCard(
        instruction=(
            f"A loan is repaid by payments of {_rand(x)} {_timing_phrase(timing, m)} "
            f"at {_num(r)}% p.a. compounded {_COMP_WORD[m]} over {n} years. Determine "
            f"the loan amount (present value)."
        ),
        display_math="",
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
        rf"i = \frac{{{_numtex(r)}\%}}{{{m}}} = {_dec(i)}, \quad N = {periods}",
        rf"x = \frac{{P\cdot i}}{{1 - (1 + i)^{{-N}}}}{due}",
        sub,
        rf"x = {_zar(ans)}",
    ]
    return ProblemCard(
        instruction=(
            f"A loan of {_rand(p, 0)} is repaid by equal payments "
            f"{_timing_phrase(timing, m)} over {n} years at {_num(r)}% p.a. compounded "
            f"{_COMP_WORD[m]}. Determine the payment."
        ),
        display_math="",
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
        rf"n \approx {_numtex(f'{solved:.2f}')} \;\Rightarrow\; "
        rf"n = {ans}\ \text{{payments ({rounding})}}",
    ]
    if mode == "loan":
        instruction = (
            f"A loan of {_rand(pv)} is repaid by payments of {_rand(x)} at "
            f"{_num(r)}% p.a. compounded {_COMP_WORD[m]}. How many payments clear "
            f"the loan?"
        )
    else:
        instruction = (
            f"A fund of {_rand(pv)} allows withdrawals of {_rand(x)} at "
            f"{_num(r)}% p.a. compounded {_COMP_WORD[m]}. How many full "
            f"withdrawals are possible?"
        )
    return ProblemCard(
        instruction=instruction,
        display_math="",
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
            f"A loan of {_rand(p, 0)} is repaid by {periods} payments of {_rand(x)} "
            f"(at {_num(r)}% p.a. compounded {_COMP_WORD[m]} over {n} years). "
            f"Determine the total interest paid."
        ),
        display_math="",
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
            f"A {_rand(p, 0)} asset depreciates at {_num(r)}% p.a. on a {word} basis. "
            f"Determine its book value after {n} years."
        ),
        display_math="",
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
        rf"i = \frac{{1 - A/P}}{{{n}}} \;\Rightarrow\; r = {_numtex(ans)}\%",
    ]
    return ProblemCard(
        instruction=(
            f"A {_rand(p, 0)} asset depreciates on a straight-line basis to "
            f"{_rand(a)} after {n} years. Determine the annual depreciation rate."
        ),
        display_math="",
        worked_steps=full if detail == "full" else [rf"r = {_numtex(ans)}\%"],
    )


def template_depreciation_to_zero(params: dict, detail: str = "full") -> ProblemCard:
    p, r, ans = params["book_price"], params["rate"], params["answer"]
    full = [
        r"A = P(1 - i\cdot n) = 0",
        rf"n = \frac{{1}}{{i}} = \frac{{100}}{{{_numtex(r)}}} = {_dec(100 / r)}",
        rf"n = {ans}\ \text{{years (round up)}}",
    ]
    return ProblemCard(
        instruction=(
            f"A {_rand(p, 0)} asset depreciates at {_num(r)}% p.a. on a straight-line "
            f"basis. After how many years is its book value zero?"
        ),
        display_math="",
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
quad_nth_unlabeled = _unlabeled_variant(
    quad_nth_term_formula, "quad_seq_nth_term_unlabeled"
)


# ── linear-equation family templates (ladder 1) ─────────────────────────────────


def _term(coeff: int, sym: str) -> str:
    """A signed leading term: '3x', '-x', 'x'. For the FIRST term of an expression."""
    if coeff == 1:
        return sym
    if coeff == -1:
        return f"-{sym}"
    return f"{coeff}{sym}"


def _add_term(coeff: int, sym: str) -> str:
    """A trailing term joined with its own sign: '+ 3y', '- y', '' (when 0)."""
    if coeff == 0:
        return ""
    if coeff == 1:
        return f"+ {sym}"
    if coeff == -1:
        return f"- {sym}"
    return f"+ {coeff}{sym}" if coeff > 0 else f"- {abs(coeff)}{sym}"


def _add_const(v: int) -> str:
    """A trailing constant with its own sign: '+ 5', '- 3', '' (when 0)."""
    if v == 0:
        return ""
    return f"+ {v}" if v > 0 else f"- {abs(v)}"


def _paren(v: int) -> str:
    """Wrap a negative in parentheses for substitution: '(-4)', '3'."""
    return f"({v})" if v < 0 else f"{v}"


def _lead(a: int) -> str:
    """A leading coefficient prefix: '' for 1, '-' for -1, else the number."""
    if a == 1:
        return ""
    if a == -1:
        return "-"
    return f"{a}"


def template_linear_add_pos(params: dict, detail: str = "full") -> ProblemCard:
    a, b, ans = params["a"], params["b"], params["answer"]
    steps = [rf"x = {b} - {a}", rf"x = {ans}"]
    return ProblemCard(
        instruction="Solve for $x$:",
        display_math=rf"x + {a} = {b}",
        worked_steps=steps,
    )


def template_linear_expand(params: dict, detail: str = "full") -> ProblemCard:
    a, b, c, d, e = (params[k] for k in ("a", "b", "c", "d", "e"))
    ans = params["answer"]
    lhs_const = a + b * d  # a + bd  (constant after distributing -b·(cx - d))
    x_coeff = -b * c  # coefficient of x on the LHS after expanding
    rhs_const = e  # RHS is -(x - e) = -x + e
    collected_coeff = x_coeff + 1  # move -x from RHS: (-bc + 1)x
    collected_const = rhs_const - lhs_const
    full = [
        rf"{a} - {b * c}x + {b * d} = -x + {e}",
        rf"{lhs_const} {_add_term(x_coeff, 'x')} = -x + {e}",
        rf"{_term(collected_coeff, 'x')} = {collected_const}",
        rf"x = {ans}",
    ]
    short = full[-2:]
    return ProblemCard(
        instruction="Solve for $x$:",
        display_math=rf"{a} - {b}({c}x - {d}) = -(x - {e})",
        worked_steps=full if detail == "full" else short,
    )


def template_linear_literal(params: dict, detail: str = "full") -> ProblemCard:
    a, b, c, ans = params["a"], params["b"], params["c"], params["answer"]
    full = [
        rf"{_term(a, 'x')} - {_term(c, 'x')} = {b}q",
        rf"{_term(a - c, 'x')} = {b}q",
        rf"x = {sympy.latex(ans)}",
    ]
    short = full[-2:]
    return ProblemCard(
        instruction="Solve for $x$ in terms of $q$:",
        display_math=rf"{_term(a, 'x')} - {b}q = {_term(c, 'x')}",
        worked_steps=full if detail == "full" else short,
    )


def template_linear_rational(params: dict, detail: str = "full") -> ProblemCard:
    A, B, p, q = params["A"], params["B"], params["p"], params["q"]
    num_coeff, num_const = params["rhs_quad_coeff"], params["rhs_const"]
    ans = params["answer"]
    lhs = rf"\frac{{{_term(A, 'x')}}}{{x - {p}}} + \frac{{{_term(B, 'x')}}}{{x - {q}}}"
    rhs = rf"\frac{{{num_coeff}x^2 {_add_const(num_const)}}}{{(x - {p})(x - {q})}}"
    lin_coeff = -(A * q + B * p)  # coefficient of x once the x² terms cancel
    full = [
        rf"\text{{Restrictions: }} x \neq {p}, \; x \neq {q}",
        # multiply both sides by the LCD (x−p)(x−q)
        rf"{_term(A, 'x')}(x - {q}) + {_term(B, 'x')}(x - {p}) "
        rf"= {num_coeff}x^2 {_add_const(num_const)}",
        # expand the left side — the x² term matches the right side
        rf"{num_coeff}x^2 {_add_term(lin_coeff, 'x')} = {num_coeff}x^2 "
        rf"{_add_const(num_const)}",
        # subtract {num_coeff}x² from both sides — the x² terms cancel
        rf"{_term(lin_coeff, 'x')} = {num_const}",
        rf"x = {sympy.latex(ans)}",
    ]
    short = full[-2:]
    return ProblemCard(
        instruction="Solve for $x$ (state any restrictions):",
        display_math=rf"{lhs} = {rhs}",
        worked_steps=full if detail == "full" else short,
    )


def template_linear_double_inequality(
    params: dict, detail: str = "full"
) -> ProblemCard:
    a, b, p, q = params["a"], params["b"], params["p"], params["q"]
    lo, hi = params["answer_lower"], params["answer_upper"]
    # Subtract b from all three parts, then divide by a. Dividing by a negative reverses
    # both inequalities (so the constructed bounds are already min/max ordered).
    p2, q2 = p - b, q - b
    full = []
    if b != 0:  # skip the subtraction step when there's nothing to subtract
        full.append(rf"{p2} < {_term(a, 'x')} < {q2}")
    full.append(
        rf"\text{{divide all parts by }} {a} \text{{, reversing the inequalities}}"
        if a < 0
        else rf"\text{{divide all parts by }} {a}"
    )
    full.append(rf"{lo} < x < {hi}")
    short = full[-2:]
    return ProblemCard(
        instruction="Solve for $x$:",
        display_math=rf"{p} < {_term(a, 'x')} {_add_const(b)} < {q}",
        worked_steps=full if detail == "full" else short,
    )


def template_simultaneous_2x2(params: dict, detail: str = "full") -> ProblemCard:
    a, b, c = params["a"], params["b"], params["c"]
    d, e, f = params["d"], params["e"], params["f"]
    x_ans, y_ans = params["answer_x"], params["answer_y"]
    eq1 = rf"{_term(a, 'x')} {_add_term(b, 'y')} = {c}"
    eq2 = rf"{_term(d, 'x')} {_add_term(e, 'y')} = {f}"
    # NB: KaTeX does not support \tag inside a cases environment — it throws and the
    # whole block falls back to raw source. Label the rows with an inline \quad (n).
    system = rf"\begin{{cases}} {eq1} \quad (1) \\ {eq2} \quad (2) \end{{cases}}"
    # Eliminate x: scale (1) by d and (2) by a so both have x-coefficient ad, then
    # subtract. (1)×d − (2)×a  ⇒  (bd − ae)y = cd − af.
    dmul = f"({d})" if d < 0 else f"{d}"
    amul = f"({a})" if a < 0 else f"{a}"
    y_coeff = b * d - a * e
    y_rhs = c * d - a * f
    dy = int(y_ans)  # answer_y is a sympy.Integer
    full = [
        rf"\text{{Eliminate }} x:\ (1)\times {dmul},\ (2)\times {amul}",
        rf"{_term(a * d, 'x')} {_add_term(b * d, 'y')} = {c * d}",
        rf"{_term(a * d, 'x')} {_add_term(a * e, 'y')} = {a * f}",
        rf"\text{{Subtract: }} {_term(y_coeff, 'y')} = {y_rhs} "
        rf"\;\Rightarrow\; y = {sympy.latex(y_ans)}",
        rf"\text{{Substitute into (1): }} {_term(a, 'x')} {_add_const(b * dy)} = {c} "
        rf"\;\Rightarrow\; x = {sympy.latex(x_ans)}",
        rf"x = {sympy.latex(x_ans)}, \quad y = {sympy.latex(y_ans)}",
    ]
    short = full[-2:]
    return ProblemCard(
        instruction="Solve the system for $x$ and $y$:",
        display_math=system,
        worked_steps=full if detail == "full" else short,
    )


# ── quadratics family templates (ladder 2) ──────────────────────────────────────


def template_quadratic_factor(params: dict, detail: str = "full") -> ProblemCard:
    a = params["leading_coeff"]
    r1, r2 = sorted([params["root1"], params["root2"]])

    def _factor(r: int) -> str:  # (x − r), or just x when r == 0
        return "x" if r == 0 else rf"(x {_add_const(-r)})"

    def _zero(r: int) -> str:  # x − r = 0, or x = 0 when r == 0
        return "x = 0" if r == 0 else rf"x {_add_const(-r)} = 0"

    display = rf"{_lead(a)}{_factor(r1)}{_factor(r2)} = 0"
    full = [
        rf"{_zero(r1)} \;\text{{ or }}\; {_zero(r2)}",
        rf"x = {r1} \;\text{{ or }}\; x = {r2}",
    ]
    return ProblemCard(
        instruction="Solve for $x$:",
        display_math=display,
        worked_steps=full if detail == "full" else full[-1:],
    )


def template_quadratic_inequality(params: dict, detail: str = "full") -> ProblemCard:
    a = params["a"]
    lo, hi = params["root1"], params["root2"]  # generator stores these sorted lo, hi
    opens = "upwards" if a > 0 else "downwards"
    full = [
        rf"\text{{critical values: }} x = {lo} \;\text{{ or }}\; x = {hi}",
        rf"\text{{the parabola opens {opens}, so the solution lies "
        rf"{params['region']} the critical values}}",
        params["solution_latex"],
    ]
    return ProblemCard(
        instruction="Solve for $x$:",
        display_math=params["polynomial_latex"],
        worked_steps=full if detail == "full" else full[-2:],
    )


_NATURE_PHRASE = {
    "non_real": r"\Delta < 0 \;\Rightarrow\; \text{the roots are non-real}",
    "real_equal": r"\Delta = 0 \;\Rightarrow\; \text{the roots are real and equal}",
    "real_unequal_rational": (
        r"\Delta > 0 \text{ and a perfect square} \;\Rightarrow\; "
        r"\text{real, unequal, rational}"
    ),
    "real_unequal_irrational": (
        r"\Delta > 0 \text{, not a perfect square} \;\Rightarrow\; "
        r"\text{real, unequal, irrational}"
    ),
}


def template_discriminant_nature(params: dict, detail: str = "full") -> ProblemCard:
    a, b, c = params["a"], params["b"], params["c"]
    disc = params["discriminant"]
    full = [
        rf"\Delta = b^2 - 4ac = {_paren(b)}^2 - 4{_paren(a)}{_paren(c)} = {disc}",
        _NATURE_PHRASE[params["nature"]],
    ]
    return ProblemCard(
        instruction="Determine the nature of the roots:",
        display_math=params["quadratic_latex"],
        worked_steps=full if detail == "full" else full,
    )


def template_surd_equation(params: dict, detail: str = "full") -> ProblemCard:
    a, b, c, s = params["a"], params["b"], params["c"], params["s"]
    cands = sorted(params["candidate_roots"])
    valids = sorted(params["valid_roots"])
    rhs = rf"{_term(s, 'x')} {_add_const(c)}"
    # squared quadratic: x² + (2sc − a)x + (c² − b) = 0
    sq_x = 2 * s * c - a
    sq_c = c * c - b
    cand_str = r" \;\text{ or }\; ".join(rf"x = {t}" for t in cands)
    valid_str = r" \;\text{ or }\; ".join(rf"x = {t}" for t in valids)
    full = [
        rf"\text{{square both sides: }} {a}x {_add_const(b)} = ({rhs})^2",
        rf"x^2 {_add_term(sq_x, 'x')} {_add_const(sq_c)} = 0",
        rf"\text{{candidate roots: }} {cand_str}",
        rf"\text{{keep only where }} {rhs} \ge 0",
        rf"\therefore {valid_str}",
    ]
    return ProblemCard(
        instruction="Solve for $x$ (reject any extraneous roots):",
        display_math=params["equation_latex"],
        worked_steps=full if detail == "full" else full[-3:],
    )


def template_nonlinear_simultaneous(params: dict, detail: str = "full") -> ProblemCard:
    m, k, p, q = params["m"], params["k"], params["p"], params["q"]
    (x1, y1), (x2, y2) = sorted(params["solution_pairs"])
    display = (
        rf"{params['line_latex']} \quad \text{{and}} \quad {params['parabola_latex']}"
    )
    full = [
        rf"\text{{equate: }} x^2 {_add_term(p, 'x')} {_add_const(q)} "
        rf"= {_term(m, 'x')} {_add_const(k)}",
        rf"x^2 {_add_term(p - m, 'x')} {_add_const(q - k)} = 0",
        rf"x = {x1} \;\text{{ or }}\; x = {x2}",
        rf"\text{{substitute into }} y = {_term(m, 'x')} {_add_const(k)}:\; "
        rf"({x1},\, {y1}) \;\text{{ and }}\; ({x2},\, {y2})",
    ]
    return ProblemCard(
        instruction="Solve the system simultaneously:",
        display_math=display,
        worked_steps=full if detail == "full" else full[-2:],
    )


# ── probability templates (ladder 5) ─────────────────────────────────────────
#
# All values are exact (SymPy Integers / Rationals); worked_steps show the counting
# principle or probability identity substituted, then the closed value. The two Venn
# "find the intersection" types are solve-for-unknown (F1-gated); the rest are
# forward-compute from a menu (no F1 surface).


def template_counting_all(params: dict, detail: str = "full") -> ProblemCard:
    n = params["n"]
    ans = params["answer"]
    full = [
        rf"\text{{arrange }} {n} \text{{ distinct objects in a row: }} {n}!",
        rf"{n}! = {sympy.latex(ans)}",
    ]
    return ProblemCard(
        instruction=(
            f"In how many different ways can {n} different "
            f"{params['noun_plural']} be arranged {params['setting']}?"
        ),
        display_math=rf"\text{{objects: }} {', '.join(params['labels'])}",
        worked_steps=full if detail == "full" else full[-1:],
    )


def template_counting_together(params: dict, detail: str = "full") -> ProblemCard:
    n, k = params["n"], params["block_size"]
    des = params["designated"]
    ans = params["answer"]
    units = n - k + 1
    full = [
        rf"\text{{treat the {k} designated objects as one block}} "
        rf"\Rightarrow {units} \text{{ units}}",
        rf"\text{{units arrange in }} {units}!,\ \text{{block internally in }} {k}!",
        rf"{k}! \times {units}! = {sympy.latex(ans)}",
    ]
    return ProblemCard(
        instruction=(
            f"The {n} {params['noun_plural']} are arranged {params['setting']}. "
            f"In how many ways can this be done if {', '.join(des)} must stay "
            f"together?"
        ),
        display_math=rf"\text{{objects: }} {', '.join(params['labels'])}",
        worked_steps=full if detail == "full" else full[-2:],
    )


def template_counting_not_together(params: dict, detail: str = "full") -> ProblemCard:
    n = params["n"]
    des = params["designated"]
    ans = params["answer"]
    full = [
        rf"\text{{total arrangements: }} {n}!",
        rf"\text{{with {des[0]} and {des[1]} adjacent (as a block): }} "
        rf"2 \times ({n}-1)!",
        rf"{n}! - 2\times {n - 1}! = {sympy.latex(ans)}",
    ]
    return ProblemCard(
        instruction=(
            f"The {n} {params['noun_plural']} are arranged {params['setting']}. "
            f"In how many ways can this be done if {des[0]} and {des[1]} are "
            f"never next to each other?"
        ),
        display_math=rf"\text{{objects: }} {', '.join(params['labels'])}",
        worked_steps=full if detail == "full" else full[-2:],
    )


def template_independent_intersection(
    params: dict, detail: str = "full"
) -> ProblemCard:
    pa, pb, ans = params["p_a"], params["p_b"], params["answer"]
    full = [
        r"P(A \cap B) = P(A)\cdot P(B)",
        rf"= {sympy.latex(pa)} \times {sympy.latex(pb)} = {sympy.latex(ans)}",
    ]
    return ProblemCard(
        instruction=r"$A$ and $B$ are independent events. Determine $P(A \cap B)$.",
        display_math=rf"P(A) = {sympy.latex(pa)}, \quad P(B) = {sympy.latex(pb)}",
        worked_steps=full if detail == "full" else full[-1:],
    )


def template_independent_union(params: dict, detail: str = "full") -> ProblemCard:
    pa, pb, ans = params["p_a"], params["p_b"], params["answer"]
    full = [
        r"P(A \cup B) = P(A) + P(B) - P(A)\cdot P(B)",
        rf"= {sympy.latex(pa)} + {sympy.latex(pb)} "
        rf"- {sympy.latex(pa)}\times {sympy.latex(pb)}",
        rf"= {sympy.latex(ans)}",
    ]
    return ProblemCard(
        instruction=r"$A$ and $B$ are independent events. Determine $P(A \cup B)$.",
        display_math=rf"P(A) = {sympy.latex(pa)}, \quad P(B) = {sympy.latex(pb)}",
        worked_steps=full if detail == "full" else full[-2:],
    )


def template_independent_decide(params: dict, detail: str = "full") -> ProblemCard:
    pa, pb, pab = params["p_a"], params["p_b"], params["p_ab"]
    prod, verdict = params["product"], params["verdict"]
    concl = "independent" if verdict == "independent" else "not independent"
    rel = "=" if verdict == "independent" else r"\neq"
    full = [
        rf"P(A)\cdot P(B) = {sympy.latex(pa)} \times {sympy.latex(pb)} "
        rf"= {sympy.latex(prod)}",
        rf"P(A \cap B) = {sympy.latex(pab)}",
        rf"{sympy.latex(prod)} {rel} {sympy.latex(pab)} \;\Rightarrow\; "
        rf"\text{{{concl}}}",
    ]
    return ProblemCard(
        instruction=(
            r"Calculate $P(A)\cdot P(B)$ and hence state whether $A$ and $B$ are "
            r"independent."
        ),
        display_math=(
            rf"P(A) = {sympy.latex(pa)},\quad P(B) = {sympy.latex(pb)},\quad "
            rf"P(A \cap B) = {sympy.latex(pab)}"
        ),
        worked_steps=full if detail == "full" else full[-2:],
    )


def template_prob_venn_intersection(params: dict, detail: str = "full") -> ProblemCard:
    pa, pb, paub = params["p_a"], params["p_b"], params["p_aub"]
    ans = params["answer"]
    full = [
        r"P(A \cap B) = P(A) + P(B) - P(A \cup B)",
        rf"= {sympy.latex(pa)} + {sympy.latex(pb)} - {sympy.latex(paub)} "
        rf"= {sympy.latex(ans)}",
    ]
    return ProblemCard(
        instruction=r"For events $A$ and $B$, determine $P(A \cap B)$.",
        display_math=(
            rf"P(A) = {sympy.latex(pa)},\quad P(B) = {sympy.latex(pb)},\quad "
            rf"P(A \cup B) = {sympy.latex(paub)}"
        ),
        worked_steps=full if detail == "full" else full[-1:],
    )


def template_prob_count_intersection(params: dict, detail: str = "full") -> ProblemCard:
    nt, na, nb, nn = (
        params["n_total"],
        params["n_a"],
        params["n_b"],
        params["n_neither"],
    )
    ans = params["answer"]
    n_aub = nt - nn
    full = [
        rf"n(A \cup B) = n(\text{{total}}) - n(\text{{neither}}) "
        rf"= {nt} - {nn} = {n_aub}",
        rf"n(A \cap B) = n(A) + n(B) - n(A \cup B) "
        rf"= {na} + {nb} - {n_aub} = {sympy.latex(ans)}",
    ]
    return ProblemCard(
        instruction=(
            f"In a group of {nt} people, {na} do activity $A$, {nb} do activity "
            f"$B$, and {nn} do neither. How many do both?"
        ),
        display_math=(
            rf"n(A) = {na},\quad n(B) = {nb},\quad "
            rf"n(\text{{neither}}) = {nn},\quad n(\text{{total}}) = {nt}"
        ),
        worked_steps=full if detail == "full" else full[-1:],
    )


def template_tree_total_probability(params: dict, detail: str = "full") -> ProblemCard:
    p, q1, q2 = (
        params["p_branch1"],
        params["p_success_given1"],
        params["p_success_given2"],
    )
    ans = params["answer"]
    one_minus_p = 1 - p
    full = [
        r"P(\text{success}) = p\cdot q_1 + (1-p)\cdot q_2",
        rf"= {sympy.latex(p)}\times {sympy.latex(q1)} "
        rf"+ {sympy.latex(one_minus_p)}\times {sympy.latex(q2)}",
        rf"= {sympy.latex(ans)}",
    ]
    return ProblemCard(
        instruction=(
            f"A two-stage experiment involves {params['setting']}. Using the "
            f"branch probabilities below, find $P(\\text{{{params['outcome']}}})$."
        ),
        display_math=(
            rf"P(\text{{first branch}}) = {sympy.latex(p)},\quad "
            rf"q_1 = {sympy.latex(q1)},\quad q_2 = {sympy.latex(q2)}"
        ),
        worked_steps=full if detail == "full" else full[-2:],
    )


def template_tree_draw_both(params: dict, detail: str = "full") -> ProblemCard:
    ca, cb, item = params["colour_a"], params["colour_b"], params["item"]
    ra, rb, n = params["count_a"], params["count_b"], params["n_total"]
    target = params["target_colour"]
    t = ra if target == ca else rb
    ans = params["answer"]
    full = [
        rf"P(\text{{both {target}}}) = \frac{{{t}}}{{{n}}}\times "
        rf"\frac{{{t}-1}}{{{n}-1}}",
        rf"= \frac{{{t}}}{{{n}}}\times \frac{{{t - 1}}}{{{n - 1}}} "
        rf"= {sympy.latex(ans)}",
    ]
    return ProblemCard(
        instruction=(
            f"A bag holds {ra} {ca} and {rb} {cb} {item}. Two are drawn at random "
            f"without replacement. Find the probability that both are {target}."
        ),
        display_math=rf"{ra}\ \text{{{ca}}},\ {rb}\ \text{{{cb}}}\ \text{{{item}}}",
        worked_steps=full if detail == "full" else full[-1:],
    )


def template_tree_draw_one_each(params: dict, detail: str = "full") -> ProblemCard:
    ca, cb, item = params["colour_a"], params["colour_b"], params["item"]
    ra, rb, n = params["count_a"], params["count_b"], params["n_total"]
    ans = params["answer"]
    full = [
        rf"P(\text{{one of each}}) = \frac{{{ra}}}{{{n}}}\times \frac{{{rb}}}{{{n}-1}} "
        rf"+ \frac{{{rb}}}{{{n}}}\times \frac{{{ra}}}{{{n}-1}}",
        rf"= \frac{{2\times {ra}\times {rb}}}{{{n}\times {n - 1}}} "
        rf"= {sympy.latex(ans)}",
    ]
    return ProblemCard(
        instruction=(
            f"A bag holds {ra} {ca} and {rb} {cb} {item}. Two are drawn at random "
            f"without replacement. Find the probability of drawing one of each "
            f"colour."
        ),
        display_math=rf"{ra}\ \text{{{ca}}},\ {rb}\ \text{{{cb}}}\ \text{{{item}}}",
        worked_steps=full if detail == "full" else full[-1:],
    )


# ── statistics (ladder 6) ───────────────────────────────────────────────────────


def _dataset_latex(data: list, per_row: int = 10) -> str:
    """A raw dataset as a left-aligned array, chunked so long lists wrap.

    A single-line ``$$13,\\ 17,\\ …$$`` is one unbreakable KaTeX box and runs off
    the page for n=25/30. Breaking every ``per_row`` values into array rows keeps
    it inside the margin while reading as one comma-separated list.
    """
    cells = [f"{x}," for x in data[:-1]] + [str(data[-1])]
    rows = [cells[i : i + per_row] for i in range(0, len(cells), per_row)]
    body = r" \\ ".join(r"\ ".join(row) for row in rows)
    return r"\begin{array}{l}" + body + r"\end{array}"


def _grouped_table_latex(intervals: list[tuple[int, int]], freqs: list) -> str:
    """A two-column interval/frequency array with SA-convention '\\le x <' labels."""
    rows = r" \\ ".join(
        rf"{a} \le x < {b} & {f}" for (a, b), f in zip(intervals, freqs)
    )
    return r"\begin{array}{c|c}\text{interval} & f \\ \hline " + rows + r"\end{array}"


def template_grouped_mean_solve(params: dict, detail: str = "full") -> ProblemCard:
    mids = params["midpoints"]
    freqs = params["frequencies"]  # None at the unknown class
    j = params["unknown_index"]
    xbar = params["mean_given"]
    k = params["unknown_frequency"]
    m_j = mids[j]
    sum_kf = sum(f for i, f in enumerate(freqs) if i != j)
    sum_kfm = sum(f * mids[i] for i, f in enumerate(freqs) if i != j)
    rhs = xbar * sum_kf - sum_kfm  # (m_j − x̄)·k = rhs
    coeff = m_j - xbar
    full = [
        r"\bar{x} = \frac{\sum f\cdot x}{\sum f}",
        rf"\sum_{{\text{{known}}}} f = {sum_kf}, \quad "
        rf"\sum_{{\text{{known}}}} f\cdot x = {sum_kfm}",
        rf"\frac{{{sum_kfm} + {m_j}k}}{{{sum_kf} + k}} = {xbar}",
        rf"{sum_kfm} + {m_j}k = {xbar}({sum_kf} + k)",
        rf"({m_j} - {xbar})k = {xbar}\cdot {sum_kf} - {sum_kfm} = {rhs}",
        rf"k = \frac{{{rhs}}}{{{coeff}}} = {k}",
    ]
    return ProblemCard(
        instruction=(
            r"The grouped frequency table has one unknown frequency $k$. The "
            rf"estimated mean of the data is ${xbar}$. Determine $k$."
        ),
        display_math=params["table_latex"],
        worked_steps=full if detail == "full" else full[-2:],
    )


def template_mean_stddev(params: dict, detail: str = "full") -> ProblemCard:
    data, n = params["data"], params["n"]
    mean_dec = round(float(params["mean"]), 2)
    sigma = round(float(params["stddev"]), 2)
    within = params["within_1sd"]
    lo = round(mean_dec - sigma, 2)
    hi = round(mean_dec + sigma, 2)
    full = [
        rf"\bar{{x}} = \frac{{\sum x}}{{n}} = \frac{{{sum(data)}}}{{{n}}} = {mean_dec}",
        r"\sigma = \sqrt{\frac{\sum (x - \bar{x})^2}{n}} \approx " + f"{sigma}",
        rf"[\,\bar{{x}} - \sigma,\ \bar{{x}} + \sigma\,] = [{lo};\ {hi}]",
        rf"\text{{values in this interval}} = {within}",
    ]
    return ProblemCard(
        instruction=(
            r"For the data set below, calculate the mean $\bar{x}$, the "
            r"(population) standard deviation $\sigma$, and the number of data "
            r"values within one standard deviation of the mean."
        ),
        display_math=_dataset_latex(params["data"]),
        worked_steps=full if detail == "full" else full[-2:],
    )


def template_stats_one_var(params: dict, detail: str = "full") -> ProblemCard:
    n = params["n"]
    mode = sympy.latex(params["mode"])
    median = sympy.latex(params["median"])
    q1, q3 = sympy.latex(params["q1"]), sympy.latex(params["q3"])
    rng = sympy.latex(params["data_range"])
    data = params["data"]
    pct = round(params["pct_above_q3"], 1)
    full = [
        rf"\text{{mode}} = {mode}\quad(\text{{most frequent value}})",
        rf"\text{{median: position }} \tfrac{{{n}+1}}{{2}} "
        rf"\;\Rightarrow\; \text{{median}} = {median}",
        rf"Q_1 = {q1}, \quad Q_3 = {q3}",
        rf"\text{{range}} = {data[-1]} - {data[0]} = {rng}",
        rf"\%\text{{ above }} Q_3 \approx {pct}\%",
    ]
    return ProblemCard(
        instruction=(
            rf"For the ordered data set below (${n}$ values), determine the mode, "
            r"median, quartiles $Q_1$ and $Q_3$, the range, and the percentage of "
            r"data above $Q_3$."
        ),
        display_math=_dataset_latex(params["data"]),
        worked_steps=full if detail == "full" else full[-3:],
    )


def template_stats_grouped(params: dict, detail: str = "full") -> ProblemCard:
    intervals, freqs, total = params["intervals"], params["freqs"], params["total"]
    p = params["percentile_p"]
    pct_pos = p / 100 * total
    modal_freq = params["modal_freq"]
    least = params["least_freq_class"].replace("≤", r"\le ")
    pct_class = params["percentile_class"].replace("≤", r"\le ")
    angle = params["pie_angle"]
    full = [
        rf"\text{{least frequency }} = {min(freqs)} "
        rf"\;\Rightarrow\; {least}",
        rf"{p}\% \times {total} = {pct_pos:g}\text{{th value}} "
        rf"\;\Rightarrow\; {pct_class}",
        rf"\text{{pie angle}} = \frac{{{modal_freq}}}{{{total}}} \times 360^\circ "
        rf"= {angle}^\circ",
        r"\text{histogram: draw a bar per interval at its frequency}",
    ]
    return ProblemCard(
        instruction=(
            rf"The grouped frequency table below summarises the data. State the "
            rf"least-frequent class, the class containing the ${p}$th percentile, "
            rf"and the angle of the modal class in a pie chart. Then draw the "
            rf"histogram."
        ),
        display_math=_grouped_table_latex(intervals, freqs),
        worked_steps=full if detail == "full" else full[:3],
    )


# ── analytic geometry (ladder 7) ──────────────────────────────────────────────
def template_analytic_geometry_triangle(
    params: dict, detail: str = "full"
) -> ProblemCard:
    x1, y1 = params["x1"], params["y1"]
    x2, y2 = params["x2"], params["y2"]
    x3, y3 = params["x3"], params["y3"]
    mx, my = sympy.latex(params["midpoint_x"]), sympy.latex(params["midpoint_y"])
    grad = sympy.latex(params["gradient_ac"])
    dist = sympy.latex(params["distance_bc"])
    dist_sq = (x3 - x2) ** 2 + (y3 - y2) ** 2
    area = sympy.latex(params["area"])
    area2 = x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2)
    full = [
        rf"M_{{BC}} = \left(\frac{{{x2} + {_par(x3)}}}{{2}},\ "
        rf"\frac{{{y2} + {_par(y3)}}}{{2}}\right) = ({mx},\ {my})",
        rf"m_{{AC}} = \frac{{{y3}-({y1})}}{{{x3}-({x1})}} = {grad}",
        rf"BC = \sqrt{{({x3}-({x2}))^2 + ({y3}-({y2}))^2}} "
        rf"= \sqrt{{{dist_sq}}} = {dist}",
        rf"\text{{area}} = \tfrac12\left|{x1}({y2}-({y3})) + {x2}({y3}-({y1})) "
        rf"+ {x3}({y1}-({y2}))\right| = \tfrac12\left|{area2}\right| = {area}",
    ]
    return ProblemCard(
        instruction=(
            r"For $\triangle ABC$ with the vertices shown, find the midpoint of "
            r"$BC$, the gradient of $AC$, the length of $BC$, and the area of the "
            r"triangle."
        ),
        display_math=(rf"A({x1},\,{y1}),\quad B({x2},\,{y2}),\quad C({x3},\,{y3})"),
        worked_steps=full if detail == "full" else full[1:],
    )


def template_line_equation(params: dict, detail: str = "full") -> ProblemCard:
    relation = params["relation"]
    mL = sympy.latex(params["given_gradient"])
    req = sympy.latex(params["required_gradient"])
    c = sympy.latex(params["c"])
    px, py = params["px"], params["py"]
    if relation == "parallel":
        grad_step = rf"m = m_L = {mL}\quad(\text{{parallel}})"
    else:
        grad_step = rf"m = -\frac{{1}}{{m_L}} = {req}\quad(\text{{perpendicular}})"
    full = [
        rf"m_L = {mL}",
        grad_step,
        rf"c = {py} - ({req})({px}) = {c}",
        params["equation_latex"],
    ]
    return ProblemCard(
        instruction=(
            rf"Find the equation of the line through $P{params['point_latex']}$ that "
            rf"is {relation} to the line $L$ through the two points shown."
        ),
        display_math=rf"L:\ {params['given_line_latex']}",
        worked_steps=full if detail == "full" else full[1:],
    )


def template_circle_equation(params: dict, detail: str = "full") -> ProblemCard:
    D, E, F = params["D"], params["E"], params["F"]
    h, k = params["centre_x"], params["centre_y"]
    r = sympy.latex(params["radius"])
    rsq = params["radius_sq"]
    hh = sympy.Rational(D, 2)
    ee = sympy.Rational(E, 2)
    full = [
        rf"(x^2 {_signed(D)}x) + (y^2 {_signed(E)}y) = {-F}",
        rf"\left(x {_signed(hh)}\right)^2 + "
        rf"\left(y {_signed(ee)}\right)^2 = {rsq}",
        rf"\text{{centre}} = \left(-\tfrac{{{D}}}{{2}},\ -\tfrac{{{E}}}{{2}}\right) "
        rf"= ({h},\ {k})",
        rf"r = \sqrt{{{rsq}}} = {r}",
    ]
    return ProblemCard(
        instruction=(
            r"Find the coordinates of the centre and the length of the radius of "
            r"the circle by completing the square."
        ),
        display_math=params["equation_latex"],
        worked_steps=full if detail == "full" else full[2:],
    )


def template_circle_tangent(params: dict, detail: str = "full") -> ProblemCard:
    h, k = params["h"], params["k"]
    px, py = params["px"], params["py"]
    rg = sympy.latex(params["radius_gradient"])
    tg = sympy.latex(params["tangent_gradient"])
    c = sympy.latex(params["c"])
    full = [
        rf"m_{{CP}} = \frac{{{py}-({k})}}{{{px}-({h})}} = {rg}",
        rf"m_{{\text{{tan}}}} = -\frac{{1}}{{m_{{CP}}}} = {tg}",
        rf"c = {py} - ({tg})({px}) = {c}",
        params["tangent_latex"],
    ]
    return ProblemCard(
        instruction=(
            rf"$P{params['point_latex']}$ lies on the circle with centre "
            rf"${params['centre_latex']}$. Find the equation of the tangent to the "
            rf"circle at $P$."
        ),
        display_math=(rf"{params['centre_latex']},\quad {params['point_latex']}"),
        worked_steps=full if detail == "full" else full[1:],
    )


def template_angle_between_lines(params: dict, detail: str = "full") -> ProblemCard:
    m1, m2 = sympy.latex(params["m1"]), sympy.latex(params["m2"])
    t1, t2 = params["theta1"], params["theta2"]
    ab = params["angle_between"]
    full = [
        rf"m_{{AB}} = {m1},\quad m_{{CD}} = {m2}",
        rf"\theta_1 = \tan^{{-1}} m_{{AB}} = {t1}^\circ,\quad "
        rf"\theta_2 = \tan^{{-1}} m_{{CD}} = {t2}^\circ",
        rf"\theta = |\theta_1 - \theta_2| \to {ab}^\circ\ (\text{{acute}})",
    ]
    return ProblemCard(
        instruction=(
            r"Find the acute angle between lines $AB$ and $CD$, working through "
            r"their inclinations."
        ),
        display_math=(
            rf"AB:\ {params['line_ab_latex']} \\ CD:\ {params['line_cd_latex']}"
        ),
        worked_steps=full if detail == "full" else full[1:],
    )


# ── calculus (ladder 8) ───────────────────────────────────────────────────────
def template_derivative_first_principles(
    params: dict, detail: str = "full"
) -> ProblemCard:
    a, b, c = params["a"], params["b"], params["c"]
    quo = sympy.latex(params["quotient"])
    der = params["derivative_latex"]
    _xh, _hh = sympy.symbols("x h")
    fxh = sympy.expand(a * (_xh + _hh) ** 2 + b * (_xh + _hh) + c)
    full = [
        r"f'(x) = \lim_{h \to 0} \dfrac{f(x+h) - f(x)}{h}",
        rf"f(x+h) = {sympy.latex(fxh)}",
        rf"\dfrac{{f(x+h) - f(x)}}{{h}} = {quo}",
        rf"f'(x) = \lim_{{h \to 0}}\left({quo}\right) = {der}",
    ]
    return ProblemCard(
        instruction=r"Determine $f'(x)$ from first principles.",
        display_math=params["function_latex"],
        worked_steps=full if detail == "full" else full[1:],
    )


def template_derivative_rules(params: dict, detail: str = "full") -> ProblemCard:
    a_plain, n_plain = params["a_plain"], params["n_plain"]
    a_surd = params["a_surd"]
    a_recip, n_recip = params["a_recip"], params["n_recip"]
    const = params["const"]
    der = params["derivative_latex"]
    rewrite = (
        rf"f(x) = {a_plain}x^{{{n_plain}}} {_signed(a_surd)}x^{{1/2}} "
        rf"{_signed(a_recip)}x^{{-{n_recip}}} {_signed(const)}"
    )
    full = [
        rewrite,
        rf"f'(x) = {der}",
    ]
    return ProblemCard(
        instruction=(
            r"Differentiate $f$. Rewrite each surd and quotient term as a power "
            r"of $x$ first."
        ),
        display_math=params["function_latex"],
        worked_steps=full if detail == "full" else full[1:],
    )


def template_tangent_line(params: dict, detail: str = "full") -> ProblemCard:
    a, b, c, d = params["a"], params["b"], params["c"], params["d"]
    x0, y0, grad = params["x0"], params["y0"], params["gradient"]
    _xt = sympy.Symbol("x")
    fprime = sympy.latex(sympy.diff(a * _xt**3 + b * _xt**2 + c * _xt + d, _xt))
    k = y0 - grad * x0
    full = [
        rf"f'(x) = {fprime}",
        rf"m = f'({x0}) = {grad}",
        rf"y_0 = f({x0}) = {y0}",
        rf"c = {y0} - ({grad})({x0}) = {k}",
        params["tangent_latex"],
    ]
    return ProblemCard(
        instruction=(
            rf"Find the equation of the tangent to $f$ at ${params['point_latex']}$."
        ),
        display_math=params["function_latex"],
        worked_steps=full if detail == "full" else full[1:],
    )


def template_cubic_stationary_points(params: dict, detail: str = "full") -> ProblemCard:
    a, b, c, d = params["a"], params["b"], params["c"], params["d"]
    der = params["derivative_latex"]
    _xc = sympy.Symbol("x")
    fpp = sympy.latex(sympy.diff(a * _xc**3 + b * _xc**2 + c * _xc + d, _xc, 2))
    xs = sorted(params["stationary_x"])
    coords = sorted(params["tp_coords"])
    labels = dict(params["classification"])
    x_str = r",\ ".join(str(xv) for xv in xs)
    coord_str = r",\quad ".join(rf"({xv},\ {yv})" for xv, yv in coords)
    class_str = r",\quad ".join(
        rf"f''({xv}) {'<' if labels[xv] == 'local_max' else '>'} 0 "
        rf"\Rightarrow \text{{{labels[xv].replace('_', ' ')}}}"
        for xv in xs
    )
    full = [
        rf"f'(x) = {der}",
        rf"f'(x) = 0 \Rightarrow x = {x_str}",
        rf"\text{{turning points:}}\ {coord_str}",
        rf"f''(x) = {fpp}",
        class_str,
    ]
    return ProblemCard(
        instruction=(
            r"Find the turning points of $f$ and classify each as a local maximum "
            r"or minimum."
        ),
        display_math=params["function_latex"],
        worked_steps=full if detail == "full" else full[1:],
    )


def template_optimisation_solve(params: dict, detail: str = "full") -> ProblemCard:
    xo, vo = params["optimal_x"], params["optimal_value"]
    full = [
        rf"Q'(x) = {params['derivative_latex']}",
        rf"Q'(x) = 0 \Rightarrow x = {xo}",
        rf"Q({xo}) = {vo}\quad(\text{{minimum}})",
    ]
    return ProblemCard(
        instruction=(
            r"For the quantity $Q(x)$ with $x > 0$, find the value of $x$ that "
            r"minimises $Q$, and the minimum value."
        ),
        display_math=params["function_latex"],
        worked_steps=full if detail == "full" else full[1:],
    )


def template_motion_calculus(params: dict, detail: str = "full") -> ProblemCard:
    t_max, vmax = params["t_max"], params["max_velocity"]
    full = [
        rf"v(t) = s'(t) = {params['velocity_latex']}",
        rf"a(t) = s''(t) = {params['acceleration_latex']}",
        rf"a(t) = 0 \Rightarrow t = {t_max}\ \text{{s}}",
        rf"v({t_max}) = {vmax}\ \text{{m/s}}\quad(\text{{maximum velocity}})",
    ]
    return ProblemCard(
        instruction=(
            r"A body has displacement $s(t)$ metres after $t$ seconds. Find its "
            r"velocity, and its maximum velocity (where the acceleration is zero)."
        ),
        display_math=params["displacement_latex"],
        worked_steps=full if detail == "full" else full[1:],
    )


def template_concavity_inflection(params: dict, detail: str = "full") -> ProblemCard:
    xi, yi = params["inflection_x"], params["inflection_y"]
    fpp = params["second_derivative_latex"]
    a = params["a"]
    rel = ">" if a > 0 else "<"
    word = "concave up" if a > 0 else "concave down"
    full = [
        rf"f''(x) = {fpp}",
        rf"f''(x) = 0 \Rightarrow x = {xi}",
        rf"\text{{inflection point}}\ ({xi},\ {yi})",
        rf"x > {xi}:\ f''(x) {rel} 0 \Rightarrow \text{{{word}}}",
    ]
    return ProblemCard(
        instruction=(
            r"Determine the point of inflection of $f$ and describe its concavity."
        ),
        display_math=params["function_latex"],
        worked_steps=full if detail == "full" else full[1:],
    )


# ── trigonometry (ladder 9) ───────────────────────────────────────────────────
_FN_TEX = {
    "sin": r"\sin",
    "cos": r"\cos",
    "tan": r"\tan",
    "cosec": r"\csc",
    "cot": r"\cot",
}
_OP_TEX = {"+": "+", "-": "-", "*": r"\times", "/": r"\div"}
_FN_SYMPY = {
    "sin": sympy.sin,
    "cos": sympy.cos,
    "tan": sympy.tan,
    "cosec": lambda a: 1 / sympy.sin(a),
    "cot": lambda a: sympy.cos(a) / sympy.sin(a),
}


def _special_val_latex(fn: str, deg: int) -> str:
    """Exact special-angle value of fn(deg°) as LaTeX (e.g. cos 30° → √3/2)."""
    rad = sympy.pi * deg / 180
    return sympy.latex(sympy.simplify(_FN_SYMPY[fn](rad)))


def template_trig_cast_ratios(params: dict, detail: str = "full") -> ProblemCard:
    x, y, r = params["x"], params["y"], params["hyp"]
    sin_l = sympy.latex(params["answer_sin"])
    cos_l = sympy.latex(params["answer_cos"])
    tan_l = sympy.latex(params["answer_tan"])
    full = [
        rf"r = \sqrt{{({x})^2 + ({y})^2}} = {r}",
        rf"\sin\theta = \dfrac{{y}}{{r}} = {sin_l}",
        rf"\cos\theta = \dfrac{{x}}{{r}} = {cos_l}",
        rf"\tan\theta = \dfrac{{y}}{{x}} = {tan_l}",
    ]
    return ProblemCard(
        instruction=(
            r"The point $P$ lies on the terminal arm of $\theta$. "
            r"Determine $\sin\theta$, $\cos\theta$ and $\tan\theta$."
        ),
        display_math=rf"P({x};\ {y})",
        worked_steps=full if detail == "full" else full[1:],
    )


def template_trig_equation(params: dict, detail: str = "full") -> ProblemCard:
    fn, n, theta = params["trig"], params["n"], params["theta"]
    beta = int(params["answer"])
    rhs_l = sympy.latex(params["rhs"])
    lhs = rf"\{fn}({n}\beta)"
    # Domain nβ ∈ [0°, 90°] keeps the ratio monotonic → the solution is unique.
    full = [
        rf"{lhs} = {rhs_l} \Rightarrow {n}\beta = {theta}^\circ",
        rf"\beta = \dfrac{{{theta}^\circ}}{{{n}}} = {beta}^\circ",
    ]
    return ProblemCard(
        instruction=rf"Solve for $\beta \in [0°;\ {90 // n}°]$:",
        display_math=rf"{lhs} = {rhs_l}",
        worked_steps=full if detail == "full" else full[1:],
    )


def template_trig_special_angles(params: dict, detail: str = "full") -> ProblemCard:
    f1, a1 = params["func1"], params["angle1"]
    f2, a2 = params["func2"], params["angle2"]
    op_tex = _OP_TEX[params["op"]]
    t1 = rf"{_FN_TEX[f1]} {a1}^\circ"
    t2 = rf"{_FN_TEX[f2]} {a2}^\circ"
    v1 = _special_val_latex(f1, a1)
    v2 = _special_val_latex(f2, a2)
    ans_l = sympy.latex(params["answer"])
    expr = rf"{t1} {op_tex} {t2}"
    full = [
        rf"{expr} = {v1} {op_tex} {v2}",
        rf"= {ans_l}",
    ]
    return ProblemCard(
        instruction="Evaluate without a calculator, leaving the answer in exact form:",
        display_math=expr,
        worked_steps=full if detail == "full" else full[1:],
    )


# ── exponents & surds (ladder 10) ─────────────────────────────────────────────
def _cdot(coef: int, tex: str) -> str:
    """Coefficient in front of a power, dropping a unit coefficient (3·2^n, 2^n)."""
    return tex if coef == 1 else rf"{coef} \cdot {tex}"


def _pn_exp(p: int, off: int) -> str:
    """Linear exponent p·n + off as LaTeX ('n+3', '2n', '2n+1')."""
    base = "n" if p == 1 else rf"{p}n"
    return rf"{base}+{off}" if off > 0 else base


def template_exponent_variable_simplify(
    params: dict, detail: str = "full"
) -> ProblemCard:
    b, p, k, m = params["base"], params["p"], params["k"], params["m"]
    a, c, d = params["a"], params["c"], params["d"]
    denom_base = params["denom_base"]
    pn_a, pn_c, pn_d = _pn_exp(p, a), _pn_exp(p, c), _pn_exp(p, d)
    num = rf"{_cdot(k, f'{b}^{{{pn_a}}}')} - {_cdot(m, f'{b}^{{{pn_c}}}')}"
    den = rf"{denom_base}^{{n}}" if d == 0 else rf"{denom_base}^{{n}} \cdot {b}^{{{d}}}"
    inner = k * b ** (a - c)
    bcd = b ** (c - d)
    factored = rf"{_cdot(k, f'{b}^{{{a - c}}}')} - {m}"
    full = [
        rf"= \dfrac{{{b}^{{{pn_c}}}\left({factored}\right)}}{{{b}^{{{pn_d}}}}}",
        rf"= {b}^{{{c} - {d}}}\left({factored}\right)",
        rf"= {bcd} \times ({inner} - {m}) = {params['answer']}",
    ]
    return ProblemCard(
        instruction="Simplify to a single value (n is a natural number):",
        display_math=rf"\dfrac{{{num}}}{{{den}}}",
        worked_steps=full if detail == "full" else full[1:],
    )


def template_exponent_algebraic_simplify(
    params: dict, detail: str = "full"
) -> ProblemCard:
    ck, k, a, b_c, c_c, t = (
        params["Ck"],
        params["k"],
        params["a"],
        params["B"],
        params["C"],
        params["t"],
    )
    a2 = 2 * a
    ans_tex = "0" if t == 0 else (rf"x^{{-{a2}}}" if t == 1 else rf"{t}x^{{-{a2}}}")
    full = [
        rf"= {c_c}^{{-1}}x^{{-{a}}} \cdot {b_c}x^{{-{a}}} - x^{{-{a2}}}",
        rf"= \dfrac{{{b_c}}}{{{c_c}}}x^{{-{a2}}} - x^{{-{a2}}}",
        rf"= \left(\dfrac{{{b_c}}}{{{c_c}}} - 1\right)x^{{-{a2}}} = {ans_tex}",
    ]
    display = (
        rf"\left({ck}x^{{{k * a}}}\right)^{{-\frac{{1}}{{{k}}}}} "
        rf"\cdot {b_c}x^{{-{a}}} - x^{{-{a2}}}"
    )
    return ProblemCard(
        instruction="Simplify, leaving the answer with positive exponents (x > 0):",
        display_math=display,
        worked_steps=full if detail == "full" else full[1:],
    )


def template_exponential_equation(params: dict, detail: str = "full") -> ProblemCard:
    k = params["base"]
    b, c = params["b_coef"], params["c_coef"]
    cands = sorted(params["candidate_u"])
    valid = sorted(params["valid_u"])
    rejected = sorted(params["rejected_u"])
    quad = "u^2"
    if b:
        quad += " + u" if b == 1 else " - u" if b == -1 else rf" {_signed(b)}u"
    if c:
        quad += rf" {_signed(c)}"
    quad += " = 0"
    steps = [
        rf"\text{{Let }} u = {k}^{{x}}\ (u > 0):\quad {quad}",
        r"\text{ or }".join(rf"u = {u}" for u in cands),
    ]
    if rejected:
        rej = r",\ ".join(str(u) for u in rejected)
        steps.append(rf"{rej} \le 0 \Rightarrow \text{{reject }}({k}^x > 0)")
    for u in valid:
        m, v = 0, 1
        while v < u:
            v *= k
            m += 1
        steps.append(rf"{k}^x = {u} \Rightarrow x = {m}")
    return ProblemCard(
        instruction=r"Solve for $x$:",
        display_math=params["equation_latex"],
        worked_steps=steps if detail == "full" else steps[1:],
    )


PROBLEMS: dict[str, WorksheetEntry] = {
    identify_sequence_type.id: WorksheetEntry(
        problem=identify_sequence_type,
        template=template_identify_sequence_type,
    ),
    possible_sequence_types.id: WorksheetEntry(
        problem=possible_sequence_types,
        template=template_possible_sequence_types,
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
    quad_nth_unlabeled.id: WorksheetEntry(
        problem=quad_nth_unlabeled,
        template=partial(template_quad_nth_term_formula, labeled=False),
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
    quad_next_terms.id: WorksheetEntry(
        problem=quad_next_terms,
        template=template_quad_next_terms,
    ),
    quad_nth_term_formula.id: WorksheetEntry(
        problem=quad_nth_term_formula,
        template=template_quad_nth_term_formula,
    ),
    quad_find_term.id: WorksheetEntry(
        problem=quad_find_term,
        template=template_quad_find_term,
    ),
    quad_find_n.id: WorksheetEntry(
        problem=quad_find_n,
        template=template_quad_find_n,
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
    # ── trigonometry family (ladder 9) ──
    trig_cast_ratios.id: WorksheetEntry(
        problem=trig_cast_ratios,
        template=template_trig_cast_ratios,
    ),
    trig_equation.id: WorksheetEntry(
        problem=trig_equation,
        template=template_trig_equation,
    ),
    trig_special_angles.id: WorksheetEntry(
        problem=trig_special_angles,
        template=template_trig_special_angles,
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
    # ── linear-equation family (ladder 1) ──
    linear_add_pos_problem.id: WorksheetEntry(
        problem=linear_add_pos_problem,
        template=template_linear_add_pos,
    ),
    linear_expand.id: WorksheetEntry(
        problem=linear_expand,
        template=template_linear_expand,
    ),
    linear_literal.id: WorksheetEntry(
        problem=linear_literal,
        template=template_linear_literal,
    ),
    linear_rational.id: WorksheetEntry(
        problem=linear_rational,
        template=template_linear_rational,
    ),
    linear_double_inequality.id: WorksheetEntry(
        problem=linear_double_inequality,
        template=template_linear_double_inequality,
    ),
    simultaneous_2x2.id: WorksheetEntry(
        problem=simultaneous_2x2,
        template=template_simultaneous_2x2,
    ),
    # ── quadratics family (ladder 2) ──
    quadratic_factor_problem.id: WorksheetEntry(
        problem=quadratic_factor_problem,
        template=template_quadratic_factor,
    ),
    quadratic_inequality.id: WorksheetEntry(
        problem=quadratic_inequality,
        template=template_quadratic_inequality,
    ),
    discriminant_nature.id: WorksheetEntry(
        problem=discriminant_nature,
        template=template_discriminant_nature,
    ),
    surd_equation.id: WorksheetEntry(
        problem=surd_equation,
        template=template_surd_equation,
    ),
    nonlinear_simultaneous.id: WorksheetEntry(
        problem=nonlinear_simultaneous,
        template=template_nonlinear_simultaneous,
    ),
    # ── exponents & surds family (ladder 10) ──
    exponent_variable_simplify.id: WorksheetEntry(
        problem=exponent_variable_simplify,
        template=template_exponent_variable_simplify,
    ),
    exponent_algebraic_simplify.id: WorksheetEntry(
        problem=exponent_algebraic_simplify,
        template=template_exponent_algebraic_simplify,
    ),
    exponential_equation.id: WorksheetEntry(
        problem=exponential_equation,
        template=template_exponential_equation,
    ),
    counting_all.id: WorksheetEntry(
        problem=counting_all,
        template=template_counting_all,
    ),
    counting_together.id: WorksheetEntry(
        problem=counting_together,
        template=template_counting_together,
    ),
    counting_not_together.id: WorksheetEntry(
        problem=counting_not_together,
        template=template_counting_not_together,
    ),
    independent_intersection.id: WorksheetEntry(
        problem=independent_intersection,
        template=template_independent_intersection,
    ),
    independent_union.id: WorksheetEntry(
        problem=independent_union,
        template=template_independent_union,
    ),
    independent_decide.id: WorksheetEntry(
        problem=independent_decide,
        template=template_independent_decide,
    ),
    prob_venn_intersection.id: WorksheetEntry(
        problem=prob_venn_intersection,
        template=template_prob_venn_intersection,
    ),
    prob_count_intersection.id: WorksheetEntry(
        problem=prob_count_intersection,
        template=template_prob_count_intersection,
    ),
    tree_total_probability.id: WorksheetEntry(
        problem=tree_total_probability,
        template=template_tree_total_probability,
    ),
    tree_draw_both.id: WorksheetEntry(
        problem=tree_draw_both,
        template=template_tree_draw_both,
    ),
    tree_draw_one_each.id: WorksheetEntry(
        problem=tree_draw_one_each,
        template=template_tree_draw_one_each,
    ),
    # ── statistics family (ladder 6) ──
    grouped_mean_solve.id: WorksheetEntry(
        problem=grouped_mean_solve,
        template=template_grouped_mean_solve,
    ),
    mean_stddev.id: WorksheetEntry(
        problem=mean_stddev,
        template=template_mean_stddev,
    ),
    stats_one_var.id: WorksheetEntry(
        problem=stats_one_var,
        template=template_stats_one_var,
    ),
    stats_grouped.id: WorksheetEntry(
        problem=stats_grouped,
        template=template_stats_grouped,
    ),
    # ── analytic geometry family (ladder 7) ──
    analytic_geometry_triangle.id: WorksheetEntry(
        problem=analytic_geometry_triangle,
        template=template_analytic_geometry_triangle,
    ),
    angle_between_lines.id: WorksheetEntry(
        problem=angle_between_lines,
        template=template_angle_between_lines,
    ),
    line_equation.id: WorksheetEntry(
        problem=line_equation,
        template=template_line_equation,
    ),
    circle_equation.id: WorksheetEntry(
        problem=circle_equation,
        template=template_circle_equation,
    ),
    circle_tangent.id: WorksheetEntry(
        problem=circle_tangent,
        template=template_circle_tangent,
    ),
    # ── calculus family (ladder 8) ──
    derivative_first_principles.id: WorksheetEntry(
        problem=derivative_first_principles,
        template=template_derivative_first_principles,
    ),
    derivative_rules.id: WorksheetEntry(
        problem=derivative_rules,
        template=template_derivative_rules,
    ),
    tangent_line.id: WorksheetEntry(
        problem=tangent_line,
        template=template_tangent_line,
    ),
    cubic_stationary_points.id: WorksheetEntry(
        problem=cubic_stationary_points,
        template=template_cubic_stationary_points,
    ),
    optimisation_solve.id: WorksheetEntry(
        problem=optimisation_solve,
        template=template_optimisation_solve,
    ),
    motion_calculus.id: WorksheetEntry(
        problem=motion_calculus,
        template=template_motion_calculus,
    ),
    concavity_inflection.id: WorksheetEntry(
        problem=concavity_inflection,
        template=template_concavity_inflection,
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
        ("possible_sequence_types", 1),
        ("arith_seq_nth_term_unlabeled", 1),
        ("geo_seq_nth_term_unlabeled", 1),
        ("quad_seq_nth_term_unlabeled", 1),
        ("geo_seq_find_term_unlabeled", 1),
        ("arith_seq_find_term_unlabeled", 1),
    ],
    # Full sequences & series revision across a few A4 pages: classification,
    # both sequence types (incl. the two-terms and mean/next-term skills), and
    # the series family (sums, sigma, find-n). ~18 problems.
    "sequences_full": [
        ("identify_sequence_type", 2),
        ("possible_sequence_types", 1),
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
        ("quad_seq_next_terms", 1),
        ("quad_seq_nth_term_formula", 1),
        ("quad_seq_find_term", 1),
        ("quad_seq_find_n", 1),
        ("arith_series_sum", 1),
        ("arith_series_find_n", 1),
        ("arith_series_sigma", 1),
        ("geo_series_finite", 1),
        ("geo_series_infinite", 1),
    ],
    # Quadratic sequences (Tₙ = an² + bn + c) in method order: extend the pattern
    # via the constant second difference, recover the general term, evaluate a far
    # term, then solve "which term = V" (a quadratic in n).
    "quadratic_sequences": [
        ("identify_sequence_type", 1),
        ("quad_seq_next_terms", 1),
        ("quad_seq_nth_term_formula", 2),
        ("quad_seq_find_term", 1),
        ("quad_seq_find_n", 1),
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


# The finance/annuities section of the official DBE Paper-1 formula sheet, which
# is stable year-to-year and supplied to every candidate. Rendered ONCE at the
# front of a finance worksheet so the formula is available but not printed on any
# single problem — mirroring the exam, where choosing the right formula off this
# sheet is itself part of the skill.
_DBE_FINANCE_FORMULAE: list[tuple[str, str]] = [
    (r"A = P(1 + ni)", "Simple growth (straight-line)"),
    (r"A = P(1 - ni)", "Simple decay / straight-line depreciation"),
    (r"A = P(1 + i)^{n}", "Compound growth"),
    (r"A = P(1 - i)^{n}", "Compound decay (reducing-balance)"),
    (
        r"1 + i_{\text{eff}} = \left(1 + \dfrac{i^{(m)}}{m}\right)^{m}",
        "Nominal $\\leftrightarrow$ effective rate",
    ),
    (
        r"F = \dfrac{x\left[(1 + i)^{n} - 1\right]}{i}",
        "Future value of an annuity",
    ),
    (
        r"P = \dfrac{x\left[1 - (1 + i)^{-n}\right]}{i}",
        "Present value of an annuity",
    ),
]


def _formula_sheet_for(problem_ids: list[str]) -> list[tuple[str, str]] | None:
    """The formula sheet to print for a worksheet, chosen from the problems it
    contains. Any finance problem pulls in the DBE finance sheet; other content
    carries its givens on the card and needs no sheet (returns None)."""
    if any(pid.startswith("finance_") for pid in problem_ids):
        return _DBE_FINANCE_FORMULAE
    return None


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

/* ── formula sheet: a leading reference page, own A4 sheet ── */
.formula-sheet {
    width: 210mm;
    min-height: 297mm;
    margin: 8mm auto;
    padding: 22mm 24mm 18mm;
    background: #fff;
    page-break-after: always;
    break-after: page;
}
.formula-list {
    display: flex;
    flex-direction: column;
    gap: 4mm;
    margin-top: 4mm;
}
.formula-row {
    display: flex;
    align-items: baseline;
    gap: 6mm;
    padding-bottom: 3mm;
    border-bottom: 1px solid #eee;
}
.formula-tex { flex: 0 0 62mm; font-size: 1.15em; }
.formula-desc { font-size: 10.5pt; color: #555; }
.formula-note {
    margin-top: 9mm;
    font-size: 9.5pt;
    font-style: italic;
    color: #777;
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
    .page          { margin: 0; }
    .answer-key    { margin: 0; }
    .formula-sheet { margin: 0; }
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


def _tex_html(body: str) -> str:
    """Escape a LaTeX math body for safe embedding between HTML $$…$$ delimiters.

    KaTeX auto-render reads text-node content *after* the browser's HTML parser
    has run, so a raw ``<`` (e.g. ``10<x``) is consumed as an open tag and the
    closing ``$$`` is swallowed — the whole block then shows as literal source.
    Escaping ``&``/``<``/``>`` to entities makes the parser leave them alone; the
    browser decodes them back to the real characters in the text node, so KaTeX
    still sees ``<`` (a relation) and ``&`` (an array column separator).
    """
    return body.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


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
    # display_math is the problem's givens for sequences/algebra/geometry, but is
    # blank for finance (the stem is self-contained; the formula lives on the
    # front sheet), so the equation row is omitted when there's nothing to show.
    equation = (
        f'<div class="problem-equation">$${_tex_html(card.display_math)}$$</div>'
        if card.display_math
        else ""
    )
    return (
        '<div class="problem">'
        f'<div class="problem-label">Question {n}{marks}</div>'
        f'<div class="problem-instruction">{card.instruction}</div>'
        f"{equation}"
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


def _formula_sheet_html(title: str, rows: list[tuple[str, str]]) -> str:
    items = "".join(
        f'<div class="formula-row">'
        f'<div class="formula-tex">$${_tex_html(tex)}$$</div>'
        f'<div class="formula-desc">{desc}</div>'
        f"</div>"
        for tex, desc in rows
    )
    return (
        '<section class="formula-sheet">'
        '<div class="page-header">'
        f"<h1>{title} — Formula Sheet</h1>"
        "<span>Provided</span>"
        "</div>"
        f'<div class="formula-list">{items}</div>'
        '<p class="formula-note">These formulae are provided. Part of the skill '
        "is choosing the right one — none are printed alongside the questions.</p>"
        "</section>\n"
    )


def _answer_key_html(cards: list[ProblemCard]) -> str:
    def _steps_html(steps: list[str]) -> str:
        return "".join(f"<div>${_tex_html(s)}$</div>" for s in steps)

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


def build_html(
    title: str,
    cards: list[ProblemCard],
    per_page: int = 2,
    formula_sheet: list[tuple[str, str]] | None = None,
) -> str:
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
    sheet = _formula_sheet_html(title, formula_sheet) if formula_sheet else ""
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="UTF-8">\n'
        f"<title>{title}</title>\n"
        f"{_KATEX}\n"
        f"<style>{_CSS}</style>\n"
        "</head>\n<body>\n"
        + sheet
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
    # F1 runtime gate. If this problem type declares an in-scope predicate, an
    # out-of-scope draw is rejected exactly like a duplicate — dropped and retried —
    # so a pedagogically-wrong instance never reaches the worksheet. A type with no
    # predicate is drawn uniqueness-only, identical to before. The predicate reads the
    # *presented* instance, independent of construction (see scope_predicates.py).
    predicate = PREDICATES.get(problem_id)
    seen: set[str] = set()
    result: list[dict] = []
    for _ in range(n):
        params = None
        fallback = None  # last in-scope (or, ungated, last) candidate — see below
        for _ in range(max_retries):
            candidate = engine.instantiate(problem_id, seed=rng.randint(0, 2**31))
            if predicate is not None and predicate(candidate):
                continue  # out of scope: reject like a duplicate, keep drawing
            fallback = (
                candidate  # in scope (or ungated): safe to emit if uniqueness fails
            )
            key = str(
                sorted(
                    (k, v) for k, v in candidate.params.items() if isinstance(v, str)
                )
            )
            if key not in seen:
                seen.add(key)
                params = candidate.params
                break
        if params is None:
            if fallback is None:
                # Every draw was out of scope. Never silently emit one — raise loudly
                # with the last instance's reasons (a genuine authoring bug: the draw
                # space and the predicate disagree). Only reachable when gated.
                raise ScopeViolationError(
                    candidate.spec.id,
                    dict(candidate.params),
                    predicate(candidate),
                    seed=candidate.seed,
                )
            # Ran out of *unique* in-scope draws — uniqueness is best-effort, so emit
            # an in-scope duplicate rather than fail (unchanged for ungated types).
            params = fallback.params
        result.append(params)
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
        problem_ids = [pid for pid, _ in BUNDLES[args.bundle]]
    else:
        if args.n is None:
            ap.error("provide N (number of problems) or --bundle")
        entry = PROBLEMS[args.problem]
        long_count = args.long_count if args.long_count is not None else args.n
        cards = _generate_cards(engine, entry, rng, args.n, long_count)
        label = f"{args.n} problems ({args.problem})"
        problem_ids = [args.problem]

    html = build_html(
        args.title,
        cards,
        per_page=args.per_page,
        formula_sheet=_formula_sheet_for(problem_ids),
    )
    html_path = Path(args.output)
    html_path.write_text(html, encoding="utf-8")
    print(f"Wrote {label} → {args.output}")

    if args.pdf:
        pdf_path = html_path.with_suffix(".pdf")
        html_to_pdf(html_path, pdf_path)
        print(f"Wrote PDF → {pdf_path}")


if __name__ == "__main__":
    main()
