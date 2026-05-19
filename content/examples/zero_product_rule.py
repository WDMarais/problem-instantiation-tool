"""
Zero-product property: three problem variants.

zero_product_atomic   — x + a = 0, root is −a. Tests the sign-flip rule for a single
                        term. The expression a is drawn from a pool of opaque values
                        (zig, grep, surds, trig-named, symbolic) to remove arithmetic
                        shortcuts and force structural reasoning.

zero_product_standard — (x − m)(x − n) = 0, roots are m and n. Always uses (x − expr)
                        form so roots ARE the expressions — no sign flip needed. Two
                        expressions drawn from the same opaque pool. Verified with
                        set_equality (order-independent, partial credit enabled).

zero_product_extension — (x + p + qi) = 0 with integers p, q. Root is −p − qi.
                         Applies the structural rule to a complex-looking expression;
                         no knowledge of i is expected. Gestures at conjugate pairs and
                         that the zero-product rule extends beyond real numbers.
"""

from __future__ import annotations

import random

import sympy

from problem_instantiation_tool.schemas import Problem

# ── expression pool ────────────────────────────────────────────────────────────
# Each entry: (latex_display_str, sympy_expr).
# sympy_expr must be atomic enough that sympy.simplify(e - e) == 0 holds for the
# symbolic_equality verifier.  Undefined SymPy functions satisfy this; so do
# SymPy symbols and algebraic expressions like 2*sqrt(3).

_zig = sympy.Function("zig")
_grep = sympy.Function("grep")
_sin_fn = sympy.Function("sin")  # opaque — prevents SymPy from evaluating to float
_cos_fn = sympy.Function("cos")

_POOL: list[tuple[str, sympy.Basic]] = [
    # Opaque made-up functions — no arithmetic shortcut possible
    (r"\text{zig}(3)", _zig(sympy.Integer(3))),
    (r"\text{zig}(-2)", _zig(sympy.Integer(-2))),
    (r"\text{grep}(5)", _grep(sympy.Integer(5))),
    (r"\text{grep}(-1)", _grep(sympy.Integer(-1))),
    # Surds — irrational, introduces the rule beyond integers
    (r"\sqrt{5}", sympy.sqrt(5)),
    (r"2\sqrt{3}", 2 * sympy.sqrt(3)),
    (r"\sqrt{7}", sympy.sqrt(7)),
    (r"3\sqrt{2}", 3 * sympy.sqrt(2)),
    # Trig-named (opaque undefined function — SymPy won't evaluate to a decimal)
    (r"\sin 30°", _sin_fn(sympy.Integer(30))),
    (r"\cos 45°", _cos_fn(sympy.Integer(45))),
    # Pure symbolic — leads naturally toward the general quadratic formula
    (r"p", sympy.Symbol("p")),
    (r"q", sympy.Symbol("q")),
    (r"\alpha", sympy.Symbol("alpha")),
]

_i_sym = sympy.Symbol("i")  # opaque imaginary unit for the extension variant


# ── generators ─────────────────────────────────────────────────────────────────


# Form builders for the atomic variant.
# Each returns (equation_latex, root_latex, root_sympy).
# Simple forms use one pool expression; compound forms use two.
# Compound equations are parenthesised to visually echo the standard variant.


def _simple_plus(a_lat: str, a: sympy.Basic) -> tuple[str, str, sympy.Basic]:
    return rf"x + {a_lat} = 0", rf"-{a_lat}", -a


def _simple_minus(a_lat: str, a: sympy.Basic) -> tuple[str, str, sympy.Basic]:
    return rf"x - {a_lat} = 0", a_lat, a


def _compound_plus_plus(
    a_lat: str, a: sympy.Basic, b_lat: str, b: sympy.Basic
) -> tuple[str, str, sympy.Basic]:
    # (x + a + b) = 0  →  root = −a − b
    return rf"(x + {a_lat} + {b_lat}) = 0", rf"-{a_lat} - {b_lat}", -a - b


def _compound_plus_minus(
    a_lat: str, a: sympy.Basic, b_lat: str, b: sympy.Basic
) -> tuple[str, str, sympy.Basic]:
    # (x + a − b) = 0  →  root = b − a
    return rf"(x + {a_lat} - {b_lat}) = 0", rf"{b_lat} - {a_lat}", b - a


def _compound_minus_plus(
    a_lat: str, a: sympy.Basic, b_lat: str, b: sympy.Basic
) -> tuple[str, str, sympy.Basic]:
    # (x − a + b) = 0  →  root = a − b
    return rf"(x - {a_lat} + {b_lat}) = 0", rf"{a_lat} - {b_lat}", a - b


def _compound_minus_minus(
    a_lat: str, a: sympy.Basic, b_lat: str, b: sympy.Basic
) -> tuple[str, str, sympy.Basic]:
    # (x − a − b) = 0  →  root = a + b
    return rf"(x - {a_lat} - {b_lat}) = 0", rf"{a_lat} + {b_lat}", a + b


_SIMPLE_BUILDERS = [_simple_plus, _simple_minus]
_COMPOUND_BUILDERS = [
    _compound_plus_plus,
    _compound_plus_minus,
    _compound_minus_plus,
    _compound_minus_minus,
]


def _gen_atomic(rng: random.Random) -> dict:
    # Equal probability: simple vs compound.
    if rng.random() < 0.5:
        builder = rng.choice(_SIMPLE_BUILDERS)
        a_lat, a = rng.choice(_POOL)
        eq_lat, root_lat, root = builder(a_lat, a)
    else:
        builder = rng.choice(_COMPOUND_BUILDERS)
        (a_lat, a), (b_lat, b) = rng.sample(_POOL, 2)
        eq_lat, root_lat, root = builder(a_lat, a, b_lat, b)
    return {
        "equation_latex": eq_lat,
        "root_latex": root_lat,
        "root": root,
    }


def _gen_standard(rng: random.Random) -> dict:
    (m_latex, m_expr), (n_latex, n_expr) = rng.sample(_POOL, 2)
    return {
        "m_latex": m_latex,
        "n_latex": n_latex,
        "root1": m_expr,
        "root2": n_expr,
    }


def _gen_extension(rng: random.Random) -> dict:
    p = rng.choice([x for x in range(-5, 6) if x != 0])
    q = rng.randint(1, 5)
    return {
        "p": p,
        "q": q,
        "root": -p - q * _i_sym,
    }


# ── Problem objects ────────────────────────────────────────────────────────────

zero_product_atomic = Problem(
    id="zero_product_atomic",
    type_id="zero_product",
    name="Given x + a = 0, state the root (single-term sign-flip)",
    artifact_type="practice",
    problem_spec=_gen_atomic,
    verifier_spec={
        "kind": "symbolic_equality",
        "marks_possible": 1,
        "param_key": "root",
    },
)

zero_product_standard = Problem(
    id="zero_product_standard",
    type_id="zero_product",
    name="Given (x − m)(x − n) = 0, state both roots (no sign flip; opaque expressions)",
    artifact_type="practice",
    problem_spec=_gen_standard,
    verifier_spec={"kind": "set_equality", "marks_possible": 2},
)

zero_product_extension = Problem(
    id="zero_product_extension",
    type_id="zero_product",
    name="Given (x + p + qi) = 0, state the root (structural rule applied to complex expression)",
    artifact_type="practice",
    problem_spec=_gen_extension,
    verifier_spec={
        "kind": "symbolic_equality",
        "marks_possible": 1,
        "param_key": "root",
    },
)


# ── Demo ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from problem_instantiation_tool.engine import Engine
    from problem_instantiation_tool.registry import InMemoryRegistry
    from problem_instantiation_tool.schemas import SolutionAttempt, SubmittedStep

    all_probs = {
        p.id: p
        for p in [zero_product_atomic, zero_product_standard, zero_product_extension]
    }
    engine = Engine(registry=InMemoryRegistry(all_probs))

    def show(label: str, instance, *answers) -> None:
        attempt = SolutionAttempt(steps=[SubmittedStep(a) for a in answers])
        r = instance.verifier.rate(attempt)
        print(
            f"  {label}: {r.marks_awarded}/{r.marks_possible}  is_correct={r.is_correct}"
        )

    print("=== zero_product_atomic ===")
    inst = engine.instantiate("zero_product_atomic", seed=42)
    p = inst.params
    print(f"  Equation : {p['equation_latex']}")
    print(f"  Root     : {p['root_latex']}")
    canon = inst.verifier.canonicals[0]
    show("Correct             ", inst, canon)
    show("Wrong (no sign flip)", inst, -canon)

    print()

    print("=== zero_product_standard ===")
    inst = engine.instantiate("zero_product_standard", seed=42)
    p = inst.params
    print(f"  Equation : (x - {p['m_latex']})(x - {p['n_latex']}) = 0")
    print(f"  Roots    : {p['root1']!r}, {p['root2']!r}")
    canon_set = inst.verifier.canonicals[0]
    show("Both correct         ", inst, canon_set)
    show("One root only        ", inst, frozenset({p["root1"]}))
    show(
        "Both wrong           ",
        inst,
        frozenset({sympy.Integer(99), sympy.Integer(100)}),
    )

    print()

    print("=== zero_product_extension ===")
    inst = engine.instantiate("zero_product_extension", seed=42)
    p = inst.params
    print(f"  Equation : x + {p['p']} + {p['q']}i = 0")
    canon = inst.verifier.canonicals[0]
    print(f"  Root     : {canon}")
    show("Correct              ", inst, canon)
    show("Wrong (forgot i term)", inst, sympy.Integer(-p["p"]))
