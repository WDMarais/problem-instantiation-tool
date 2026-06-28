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
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import sympy

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from content.examples.factorise_skills import (
    factor_pairs_for_display,
    factorise_constraints,
    factorise_enumerate,
    factorise_sign_case,
)
from content.examples.monic_factorise import problem as monic_factorise_problem
from content.examples.parallelogram_angles import (
    parallelogram_alternate,
    parallelogram_cointerior,
    parallelogram_opposite,
)
from content.examples.rform_skills import (
    rform_find_phi,
    rform_find_R,
    rform_match_coefficients,
    rform_solve,
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


def _parallelogram_pts(angle_a_deg: float, base: float, side: float) -> dict:
    """Parallelogram ABCD (A bottom-left, going A→B→C→D anticlockwise) with the
    interior angle at A equal to angle_a_deg. Layout coords, y-up. Pose (rotation,
    scale, reflection) is applied later by the renderer."""
    th = math.radians(angle_a_deg)
    dx, dy = side * math.cos(th), side * math.sin(th)
    return {
        "A": Point("A", 0.0, 0.0),
        "B": Point("B", base, 0.0),
        "C": Point("C", base + dx, dy),
        "D": Point("D", dx, dy),
    }


def _pgram_geometry(params: dict) -> dict:
    """Shared figure inputs from params: posed points + sides + Pose."""
    pts = _parallelogram_pts(params["angle_a_deg"], params["base"], params["side"])
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
            r"$ABCD$ is a parallelogram. Determine the size of $\hat{B}$, "
            r"giving a reason."
        ),
        display_math=rf"\hat{{A}} = {given}^\circ",
        worked_steps=[
            (
                r"\hat{A} + \hat{B} = 180^\circ \quad "
                r"(\text{co-interior } \angle\text{s};\ AD \parallel BC)"
            ),
            rf"\hat{{B}} = 180^\circ - {given}^\circ = {ans}^\circ",
        ],
        graph_svg=render_figure(fig),
    )


def template_parallelogram_opposite(params: dict, **_) -> ProblemCard:
    given = params["given_deg"]
    ans = int(params["answer"])
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
            r"$ABCD$ is a parallelogram. Determine the size of $\hat{C}$, "
            r"giving a reason."
        ),
        display_math=rf"\hat{{A}} = {given}^\circ",
        worked_steps=[
            (
                r"\hat{C} = \hat{A} \quad "
                r"(\text{opposite } \angle\text{s of a } \parallel^{\text{m}})"
            ),
            rf"\hat{{C}} = {ans}^\circ",
        ],
        graph_svg=render_figure(fig),
    )


def template_parallelogram_alternate(params: dict, **_) -> ProblemCard:
    given = params["given_deg"]
    ans = int(params["answer"])
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
            r"$ABCD$ is a parallelogram with diagonal $AC$. "
            r"Determine $B\hat{A}C$, giving a reason."
        ),
        display_math=rf"D\hat{{C}}A = {given}^\circ",
        worked_steps=[
            (
                r"B\hat{A}C = D\hat{C}A \quad "
                r"(\text{alternate } \angle\text{s};\ AB \parallel DC)"
            ),
            rf"B\hat{{A}}C = {ans}^\circ",
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


PROBLEMS: dict[str, WorksheetEntry] = {
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
}

REGISTRY = {id: e.problem for id, e in PROBLEMS.items()}
TEMPLATES = {id: e.template for id, e in PROBLEMS.items()}


# ── HTML / CSS ────────────────────────────────────────────────────────────────

# $$ for display, $ for inline — works cleanly in controlled content with no
# prose dollar signs.  List $$ first so auto-render greedily matches it before $.
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

/* problems flex-fills all remaining page height after the header */
.problems {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 5mm;
    min-height: 0;
}

.problem {
    flex: 1;
    display: flex;
    flex-direction: column;
    border: 1px solid #bbb;
    border-radius: 2px;
    padding: 4.5mm 5.5mm 3.5mm;
    min-height: 0;
}

.problem-label {
    font-size: 8.5pt;
    font-weight: bold;
    color: #777;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 2mm;
    flex-shrink: 0;
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

/* ruled working space: takes all remaining height inside the problem box */
.working-space {
    flex: 1;
    min-height: 55mm;
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
.answer-steps { display: flex; flex-direction: column; gap: 1.5mm; }

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
    body        { background: none; }
    .page       { margin: 0; }
    .answer-key { margin: 0; }
}
"""


def _problem_html(n: int, card: ProblemCard) -> str:
    if card.graph_svg:
        body = (
            '<div class="problem-body">'
            f'<div class="problem-graph-side">{card.graph_svg}</div>'
            '<div class="working-space"></div>'
            "</div>"
        )
    else:
        body = '<div class="working-space"></div>'
    return (
        '<div class="problem">'
        f'<div class="problem-label">Question {n}</div>'
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

    rows = "".join(
        f'<div class="answer-row">'
        f'<span class="answer-num">{i + 1}.</span>'
        f'<div class="answer-steps">{_steps_html(c.worked_steps)}</div>'
        f"</div>"
        for i, c in enumerate(cards)
    )
    return (
        '<section class="answer-key">'
        "<h2>Worked Answers</h2>"
        f'<div class="answer-grid">{rows}</div>'
        "</section>\n"
    )


def build_html(title: str, cards: list[ProblemCard], per_page: int = 2) -> str:
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
    return [
        entry.template(params_list[i], detail="full" if i < long_count else "short")
        for i in range(len(params_list))
    ]


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


# ── CLI ───────────────────────────────────────────────────────────────────────


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate an HTML practice worksheet.")
    ap.add_argument("n", type=int, help="Number of problems")
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

    entry = PROBLEMS[args.problem]
    engine = Engine(registry=InMemoryRegistry(REGISTRY))
    rng = random.Random(args.seed)
    long_count = args.long_count if args.long_count is not None else args.n

    cards = _generate_cards(engine, entry, rng, args.n, long_count)

    html = build_html(args.title, cards, per_page=args.per_page)
    Path(args.output).write_text(html, encoding="utf-8")
    print(f"Wrote {args.n} problems ({args.problem}) → {args.output}")


if __name__ == "__main__":
    main()
