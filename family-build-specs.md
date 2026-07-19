# Family build-specs — the four September P1 archetype families (2026-07-19)

Detailed build-list for the four highest-ROI families identified in `corpus-crosswalk.md`.
These convert P1 class-b marks (parameterizable-but-unbuilt) into coverage. Order is by
yield × engine-proximity. Each family is a set of **archetypes** (sub-generators) built on the
existing engine (`content/generators/base.py`, `problem_instantiation_tool/verifier.py`,
`content/sheet.py`, `content/scope_predicates.py`) — no new engine work.

**Scope discipline (from crosswalk §6f):** each archetype covers the *class-b* (mechanical,
auto-markable) parts of its questions. The **class-c siblings** — "show that…", "prove…",
"sketch…", "interpret the graph…" — are listed under each family as **DEFER (resistant)** so the
boundary is explicit and we don't silently claim them.

**Coverage prize:** the four families ≈ **92 marks of a 150-mark P1 (~61%)**; with the ~9% P1
class-a already covered, that's **~70% of a P1 addressable** once built. (P2 deferred — 31%
Euclidean-proof wall; see crosswalk.)

**Verifier vocabulary already in the engine:** `symbolic_equality`, `set_equality`,
`numeric_equality` (tolerance), `exact_equality`, multi-step `param_key`. All four families reuse
these; only Finance leans on `numeric_equality` (rounding), the rest are `symbolic_equality`/
`set_equality`. **Zero renderer dependency across all four** (the diagram/sketch parts are the
deferred class-c siblings).

---

## Family 1 — Sequences & Series  ·  ~23 marks/P1  ·  engine-proximity HIGHEST
**Template:** `content/examples/arithmetic_sequence.py` already exists (AP nth-term/find-term/
find-n). Every archetype below is structurally identical: param ranges → sympy closed-form
expr → expected value. **This is the warm-up family — start here.**
**Anchors:** 2023 P1 Q2–3, 2024 P1 Q2–3, 2025 M/J P1 Q2–3, 2025 Nov P1 Q2–3.

| # | archetype_id | parameterizes | answer shape | verifier | fidelity-critical note |
|---|---|---|---|---|---|
| 1 | `arithmetic_series_sum` | a, d, n → Sₙ=n/2(2a+(n−1)d); also **solve n** given Sₙ (quadratic in n) | integer / n-value | symbolic_equality + param_key | when solving n, reject non-positive-integer root |
| 2 | `geometric_sequence` | a, r, n → Tₙ=ar^(n−1); find term / **find n** (logs) / find r or a from two terms | integer / expr | symbolic_equality | integer-r vs fractional-r param split; guard r≠1, r≠0 |
| 3 | `geometric_series_finite` | a, r, n → Sₙ=a(rⁿ−1)/(r−1); Σ-notation form; solve n or r | value / n | symbolic_equality | present both Σ and expanded forms in stem |
| 4 | `geometric_series_infinite` | a, r (\|r\|<1) → S∞=a/(1−r); find S∞, or r or a given S∞; convergence condition | Rational / interval | symbolic_equality | **guard \|r\|<1** — convergence is an assessed concept; a "for which x does it converge" variant is class-b |
| 5 | `sigma_notation` | translate Σ ↔ closed form; evaluate Σ; write a given series in Σ form | value / expression | symbolic_equality | index bounds + first/last term are the marks |
| 6 | `quadratic_pattern` | 2nd-difference-constant seq → **find** Tₙ=an²+bn+c from terms; find a term; **find n** for a value; find max/min (vertex) | expr / integer | symbolic_equality + param_key | 2nd-difference = 2a is the method mark |

**DEFER (resistant, class-c):** "show that Tₙ = …", "show that the sequence is increasing",
"prove Sₙ = …". These recur in Q2–3 but are proof-shaped — out of scope.
**Build size:** 6 archetypes, template exists → **~1.5 active days.**

---

## Family 2 — Finance / Annuities  ·  ~15 marks/P1  ·  engine-proximity HIGH
**Template:** `content/examples/finance.py` (Gr10 annual simple/compound) — same numeric-answer
shape; these are more formulae of the same kind. **The real work is not the maths — it's the
NSC rounding/timing conventions** (round to cents, when the first payment falls, deferred
periods). That convention-fidelity is the F3 payload and where memo care goes.
**Anchors:** 2023 P1 Q6, 2024 P1 Q7, 2025 M/J P1 Q7, 2025 Nov P1 Q7.

| # | archetype_id | parameterizes | answer shape | verifier | fidelity-critical note |
|---|---|---|---|---|---|
| 1 | `compound_periodic` | P, i, m (comp/yr), n → A=P(1+i/m)^(mn); solve A/P/n/i | currency | numeric_equality tol 0.01 | monthly/quarterly — the step beyond finance.py's annual |
| 2 | `nominal_effective_rate` | i_nom, m → i_eff=(1+i_nom/m)^m−1; convert either direction | rate (%) | numeric_equality | tiny build; pure formula |
| 3 | `depreciation` | P, i, n → straight-line A=P(1−in) **and** reducing-balance A=P(1−i)ⁿ; solve any var | currency / n | numeric_equality | two sub-modes; state which model |
| 4 | `future_value_annuity` | x, i, n → F=x[(1+i)ⁿ−1]/i; find F, **find x** (deposit), find n | currency / n | numeric_equality | **payment-timing convention** (ordinary vs due) is an assessed distinction |
| 5 | `present_value_annuity` | x, i, n → P=x[1−(1+i)^−n]/i; loan repayment; find P, x, or **n** (logs) | currency / n | numeric_equality | rounding of n **up** to whole payments |
| 6 | `loan_outstanding_balance` | balance after k payments = PV of remaining; extra-payment "months saved" | currency / count | numeric_equality | deferred-first-payment offset is the classic trap |

**DEFER (resistant):** the rare "explain why the balance…" interpretive parts. The multi-phase
`annuity_timeline` (lump sum + deferred deposits, e.g. 2025 M/J P1 Q7.3) is **class-b but hard** —
build it LAST in this family, or defer to v2; it composes #1/#4/#5.
**Build size:** 6 archetypes (+1 optional hard one) → **~2 active days**, most of it on rounding/
timing fidelity, not algebra.

---

## Family 3 — Q1 Algebra Extensions  ·  ~17 marks/P1  ·  engine-proximity HIGH
**Template:** reuse `quadratic_roots`, `zero_product_rule`, `exponent_laws` machinery — these
extend them with a wrapper skill. The **assessed skill is usually the guard**, not the algebra
(extraneous-root rejection, reject-negative-substitution, denominator restriction). Getting the
guard into the memo faithfully is the point.
**Anchors:** Q1 of every P1 (1.1.x, 1.2, 1.3).

| # | archetype_id | parameterizes | answer shape | verifier | fidelity-critical note |
|---|---|---|---|---|---|
| 1 | `quadratic_inequality` | ax²+bx+c ≥/≤/>/< 0 → critical values + sign analysis | interval / union | set_equality | reuses quadratic_roots; the sign-line reasoning is the memo skill |
| 2 | `surd_equation` | √(linear)=linear → isolate-square-**check** | valid root set | set_equality | **extraneous-root rejection is the assessed skill** — memo must show the check |
| 3 | `exponential_equation` | a·k^(2x)+b·k^x+c=0 via u=k^x → quadratic → back-sub; or common-base equate | root set | symbolic/set_equality | **reject non-positive u** before back-substituting |
| 4 | `nonlinear_simultaneous` | one linear + one quadratic/rational → substitute → quadratic → two (x,y) pairs | pair set | set_equality | present BOTH solution pairs; word-problem wrapper variant |
| 5 | `discriminant_nature` | quadratic (param k) → Δ=b²−4ac; classify roots / **find k** for a nature | classification / k-range | symbolic_equality + param_key | "for which k are roots real/equal/non-real" |

**DEFER (resistant):** "show that … is divisible by 2" / integer-reasoning proofs (2025 M/J P1 1.3,
2024 P1 1.3). Rational-equation-with-restrictions is partly covered by the existing
`linear_equations` SPEC — extend only if a real question needs it.
**Build size:** 5 archetypes, all extending existing verifiers → **~1.5–2 active days.**

---

## Family 4 — Calculus  ·  ~37 marks/P1 (biggest block)  ·  engine-proximity MED, math-risk LOW
**No existing archetype — but sympy does the heavy lifting: the answer key for a derivative is
literally `sympy.diff`, for optimisation `sympy.solve(diff(...))`.** So the verifier is nearly
free; the build cost is stems + faithful memo working (esp. first-principles limit notation, where
the *working* carries the marks, not just the answer).
**Anchors:** every P1 Q7–Q10 (first principles, rules, tangents, cubic analysis, optimisation, motion).

| # | archetype_id | parameterizes | answer shape | verifier | fidelity-critical note |
|---|---|---|---|---|---|
| 1 | `derivative_first_principles` | quadratic/simple-cubic coeffs → f′(x)=lim_{h→0}[f(x+h)−f(x)]/h | f′(x) expr | symbolic_equality | **memo must render the full limit-notation derivation** — the marks are in the steps |
| 2 | `derivative_rules` | polynomial incl. **neg/fractional exponents needing rewrite** (√x→x^½, a/x→ax⁻¹) | f′(x) | symbolic_equality (sympy.diff) | the **rewrite-before-differentiate** step is the assessed skill |
| 3 | `tangent_line` | point x₀ → gradient f′(x₀), line y−y₀=m(x−x₀) | line equation | symbolic_equality | composes #2 |
| 4 | `cubic_stationary_points` | cubic coeffs → f′(x)=0 → TP coords; classify via f″ | coordinate pairs | symbolic_equality + param_key | y-coords of TPs feed the "k for 3 real roots" variant (class-b) |
| 5 | `optimisation_solve` | given the quantity function → differentiate, =0, solve, verify max/min | optimal value | symbolic_equality | the **"show that Q(x)=…" setup is DEFER**; the minimise/maximise step is class-b |
| 6 | `motion_calculus` | s(t) → v=s′ (max speed at a=0), a=s″; distance | value | symbolic_equality | 2024 P1 Q10; light integration (antiderivative + bounds) |
| 7 | `concavity_inflection` | cubic → f″(x) sign, point of inflection | interval / point | symbolic_equality | one-word "concave up/down" + inflection x |

**DEFER (resistant, and there's a lot of it here):** "sketch the cubic", "use the graph to
determine k for 3 real roots" (graph-interpretation form — but the *algebraic* TP-value form is #4,
class-b), all "interpret f′ from the graph" items (2024 P1 Q9 is 8 marks of these), "show that
V(x)=…" optimisation setups. Build the algebra, defer the graph.
**Build size:** 7 archetypes, new verifier patterns but sympy-backed → **~2.5–3 active days.**

---

## Roll-up & schedule

| family | archetypes | ~marks/P1 | est. active-days | engine proximity |
|---|---|---|---|---|
| 1. Sequences & Series | 6 | 23 | 1.5 | highest (template exists) |
| 2. Finance / Annuities | 6 | 15 | 2.0 | high (rounding/timing is the work) |
| 3. Q1 Algebra Extensions | 5 | 17 | 1.5–2 | high (extends existing verifiers) |
| 4. Calculus | 7 | 37 | 2.5–3 | med build / low math-risk (sympy) |
| **total** | **~24** | **~92 (61% of a P1)** | **~7.5–8.5 active days** | on the existing engine |

**Velocity anchor (receipts):** the initial May burst built the **engine + 32 archetypes in ~8
un-prioritized active days** (~4.5 archetype-specs/day for 4 days, then 9 full generators in 2).
These 24 archetypes sit on the finished engine, so per-archetype should be ≥ that rate. **~8
focused active days ≈ all four families.** For calibration, p-i-t got only **14 active days across
the whole May–July window** while owm consumed **38 active days / 477 commits** — i.e. p-i-t has
*never once been the priority*. If it gets even a fraction of owm's attention, the four families
are a **~2–3 week calendar** build; even at p-i-t's historic un-prioritized drip it's ~one focused
month. The math is not the risk — attention allocation is.

**Sequencing:** build in table order. Family 1 is the warm-up (template exists, pure symbolic, zero
guards-heavy) — it re-warms the codebase and ships the first standalone topic-bundle ("Sequences &
Series — variable practice + DBE-faithful memo") fastest. Family 4 is last (biggest, newest
verifier patterns) but also the biggest single coverage jump. After all four, P1 topic-bundles
compose into a near-complete variable P1 (~70% with existing class-a) — the September deliverable.
