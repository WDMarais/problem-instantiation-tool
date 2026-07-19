# Corpus crosswalk — NSC Gr-12 Maths vs p-i-t archetype coverage (2026-07-19)

Every question in the 8 transcribed DBE papers (`nsc_papers/transcriptions/maths/`),
classified against the fixed p-i-t archetype vocabulary (32 archetypes: 11 BUILT
worksheet generators + 21 SPEC examples). Method: one canonical-inventory pass to fix the
vocabulary, then one classifier per paper against it. Feeds `mvp-scope.md` §6.

**Class key:**
- **a** = cleanly parameterizable *and an existing archetype covers it* — swap numbers, memo follows mechanically.
- **b** = parameterizable-with-effort — symbolic and generatable, but **no archetype exists yet** (or multi-part / renderer / awkward guards).
- **c** = resistant — proof / "show that" / "explain" / "interpret graph" / open modelling. Out of scope by §6f.

---

## Headline: existing archetypes cover ~10% of real exam marks

| paper | total | a (covered) | b (gap, buildable) | c (resistant) | a % |
|---|---|---|---|---|---|
| 2023 Nov P1 | 150 | 17 | 110 | 23 | 11.3% |
| 2023 Nov P2 | 150 | 13 | 102 | 35 | 8.7% |
| 2024 Nov P1 | 150 | 8 | 123 | 19 | 5.3% |
| 2024 Nov P2 | 150 | 9 | 75 | 66 | 6.0% |
| 2025 M/J P1 | 150 | 16 | 119 | 15 | 10.7% |
| 2025 M/J P2 | 150 | 17 | 85 | 48 | 11.3% |
| 2025 Nov P1 | 150 | 11 | 116 | 23 | 7.3% |
| 2025 Nov P2 | 150 | 26 | 85 | 39 | 17.3% |
| **TOTAL** | **1200** | **117** | **815** | **268** | **9.75%** |

**Split by paper type (the load-bearing distinction):**

| | marks | a (covered) | a+b (addressable ceiling) | c (resistant floor) |
|---|---|---|---|---|
| **P1** (4 papers) | 600 | 52 (8.7%) | **520 (86.7%)** | 80 (13.3%) |
| **P2** (4 papers) | 600 | 65 (10.8%) | 412 (68.7%) | **188 (31.3%)** |

### What this overturns
The prior read (mvp-scope §6 pre-6i, and the 2026-07-19 memory note) held that the ~15–20
archetypes were **largely already built** and the only 0%-done piece was the corpus↔generator
*bridge*. **The receipts falsify that.** The existing 32 archetypes are concentrated in
**foundational / Grade-10 algebra** (linear-equation solving, monic factorise, single-var stats,
AP *terms*) that Grade-12 NSC finals **barely test directly**. Only ~10% of real marks land on
them. The September gap is not the crosswalk — **it is building the missing Grade-12 archetype
families**, which is where 68–87% of the marks actually live (class-b). The good news inside the
bad: class-b is *parameterizable* (symbolic, sympy-verifiable) — it's buildable, just not built.

---

## The real backlog — GAP families ranked by yield

Class-b marks cluster into ~10 families with **no current archetype**. Approx marks/paper:

### P1 families (P1 is the high-yield, low-resistance surface)
| family | ~marks/P1 | existing engine proximity | notes |
|---|---|---|---|
| **Calculus** (first-principles, derivative rules, tangent-via-derivative, cubic-graph analysis, optimisation, motion/integration) | ~35 | none | biggest single block; mechanically sympy-clean (diff/solve). Cubic-graph *interpretation* parts are class-c. |
| **Function-graph analysis** (hyperbola/parabola/exp/log: intercepts, asymptote, range, transformation, inverse) | ~26 | `func_eval`/`func_inverse` are linear-only | many parts diagram-stem → renderer dependency; numeric parts clean |
| **Sequences & series** (geometric seq, arithmetic/geometric **series** sum-to-n & S∞, quadratic patterns) | ~23 | extends `arithmetic_sequence` (AP terms only) | closest cousin to existing; pure symbolic — **high ROI** |
| **Q1 algebra extensions** (quadratic inequality, surd equation, exponential equation, nonlinear simultaneous) | ~16 | reuses quadratic/exponent verifiers | close cousins of existing quadratic archetypes — **high ROI** |
| **Finance: annuities/loans/timelines/effective-rate** | ~14 | `finance` is Gr10 annual only | formula-driven, small build, clean — **high ROI** |
| **Probability & counting** (counting principle, independence, tree, total-probability, contingency) | ~9 | `probability_venn` is P(A∪B) only | mostly clean; tree/Venn have render parts |

### P2 families (lower ceiling — Euclidean geometry is a ~40-mark resistant wall/paper)
| family | ~marks/P2 | notes |
|---|---|---|
| **Analytic geometry: circles + full straight-line** (equation-of-line, inclination angle, perpendicular, circle eqns/tangents) | ~28 | `analytic_geometry_triangle` only does midpoint/gradient/distance/area. Big clean block, diagram-stem. |
| **Extended trig identities** (compound-angle, double-angle, reduction, sum-to-product) + solving | ~18 | `trig` archetype is CAST + special-angle only. Identity *proofs* are class-c; simplify/solve are class-b. |
| **Statistics** (regression/correlation, ogive, box-plot, grouped-mean, std-dev) | ~12 | `statistics_*` only do positional/modal measures. Ogive/box-plot need a renderer. |
| **3D/2D sine & cosine rule trig** | ~10 | no archetype; sine/cosine-rule triangle solving. Clean symbolic. |
| **Euclidean geometry** (circle theorems, similarity, proportionality proofs) | ~40 | **~class-c / out of scope** — proofs + reason-graded. Deliberately deferred per §6f. |

---

## Recommendation — P1 topic-bundles, not "variable whole papers"

Three findings force a sharper MVP cut than "NSC Papers (variable)":

1. **Target P1, not the full paper set.** P1 is 86.7% addressable; P2 is 68.7% with a hard
   31% Euclidean-proof floor you cannot auto-generate or auto-mark. A "variable paper" product
   on P2 would ship visibly incomplete.
2. **Ship topic-bundles, then compose to papers.** A whole variable paper needs *every* one of
   its families built. A topic-bundle ("Calculus — variable practice + DBE-faithful memo",
   "Sequences & Series — …") needs only *one* family and maps that archetype across all years of
   real questions — the §6a "one archetype fans to many real questions" model, shippable
   incrementally. Compose bundles into whole papers once enough families exist.
3. **Build order by yield × engine-proximity:** **Sequences & Series** (extends the one existing
   sequence generator) → **Finance/Annuities** (small, formula-driven, clean) → **Q1 algebra
   extensions** (reuse quadratic verifiers) → **Calculus** (zero existing but ~35 marks/P1 and
   sympy-clean). Those four ≈ 88 marks of a 150-mark P1 (~58% — the archetype-level re-estimate in
   `family-build-specs.md` puts it at 92 / ~61%), almost all non-diagram, all
   high-parameterizability. **Function-graphs** and the P2 families come after (renderer
   dependency raises their cost).

Note the flagship worked example (Nov-2025 P2 Q5) is only *partially* class-a: the CAST-ratio and
special-angle sub-parts (5.1.1, 5.1.3) map to `trig`, but the double-angle/compound/reduction
manipulation is class-b (no identity archetype) and the "prove/deduce" parts are class-c. Even the
poster question needs the extended-trig-identity family built.

---

## Appendix — full per-question tables

### 2023 Nov P1 — a 17 / b 110 / c 23 · archetypes hit: quadratic_roots, arithmetic_sequence, func_eval, finance, probability_venn

| q_id | topic | marks | archetype | class | note |
|---|---|---|---|---|---|
| 1.1.1 | quadratic (factorise) | 3 | quadratic_roots | a | monic factorise |
| 1.1.2 | quadratic (formula) | 4 | quadratic_roots | a | non-monic, 2-dp |
| 1.1.3 | surd equation | 4 | GAP:surd-equation | b | extraneous-root check |
| 1.1.4 | quadratic inequality | 4 | GAP:quadratic-inequality | b | sign/critical-value |
| 1.2 | simultaneous (linear+rational) | 5 | GAP:nonlinear-simultaneous | b | reduces to quadratic |
| 1.3 | exponential equation | 4 | GAP:exponential-equation | b | equate integer exponents |
| 2.1.1 | AP nth-term | 3 | arithmetic_sequence | a | find-term |
| 2.1.2 | AP series sum | 2 | GAP:series-sum | b | S_n |
| 2.1.3 | AP find-n | 3 | arithmetic_sequence | a | find-n |
| 2.2.1–3 | quadratic pattern | 8 | RESISTANT | c | "show that" ×3 |
| 3.1.1 | geometric nth-term | 1 | GAP:geometric-sequence | b | write-down |
| 3.1.2 | geometric sigma-sum | 4 | GAP:series-sum | b | Σ, solve k |
| 3.2 | geo S∞ + arith sum | 5 | GAP:geometric-series | b | |
| 4.1–4.2 | exp graph asymptote/x-int | 3 | GAP:exponential-function | b | |
| 4.3 | line through 2 pts | 3 | GAP:straight-line | b | |
| 4.4 | vertical distance k−f | 3 | func_eval | b | depends on 4.3 |
| 4.5 | exp transformation | 1 | GAP:function-transformation | b | |
| 4.6–4.7 | inverse (log/domain) | 4 | GAP:inverse-function | b | func_inverse is linear-only |
| 5.1 | parabola TP | 2 | GAP:parabola | b | |
| 5.2 | parabola y-intercept | 2 | func_eval | a | f(0) |
| 5.3–5.4 | hyperbola const/range | 2 | GAP:hyperbola | b | |
| 5.5 | sign of f·g | 3 | RESISTANT | c | graph-read |
| 5.6 | line–hyperbola non-intersect | 5 | GAP:hyperbola-line | b | discriminant<0 |
| 5.7 | tangent to hyperbola | 4 | GAP:calculus-tangent | b | |
| 6.1.1 | compound, solve rate | 3 | finance | b | monthly reverse-compound |
| 6.1.2 | effective rate | 2 | GAP:effective-rate | b | |
| 6.2.1 | straight-line depreciation | 2 | finance | b | |
| 6.2.2–6.3 | annuities (FV/PV) | 9 | GAP:annuity | b | |
| 7.1 | first principles | 5 | GAP:differentiation-first-principles | b | |
| 7.2.1–7.2.2 | derivative rules | 5 | GAP:differentiation-rules | b | |
| 7.3 | derivative sign | 3 | GAP:derivative-application | b | |
| 8.1 | cubic turning points | 4 | GAP:cubic-graph | b | |
| 8.2–8.3 | sketch / k for 3 roots | 6 | RESISTANT | c | draw / graph-interpret |
| 8.4 | tangent at inflection | 6 | GAP:calculus-tangent | b | |
| 8.5 | inclination angle | 2 | GAP:inclination-angle | b | |
| 9.1 | optimisation setup | 3 | RESISTANT | c | "show that A(x)=…" |
| 9.2 | optimisation minimise | 3 | GAP:optimisation | b | |
| 10.1.1 | independent P(A∩B) | 2 | GAP:independent-events | b | |
| 10.1.2 | P(at least one) | 2 | probability_venn | a | |
| 10.2.1 | tree diagram | 3 | RESISTANT | c | diagram-producing |
| 10.2.2 | tree/total probability | 3 | GAP:tree-probability | b | |
| 10.3.1–2 | arrangements | 5 | GAP:counting-arrangements | b | |

### 2023 Nov P2 — a 13 / b 102 / c 35 · archetypes hit: analytic_geometry_triangle, trig, trig_graph_properties, statistics_grouped

| q_id | topic | marks | archetype | class | note |
|---|---|---|---|---|---|
| 1.1–1.3 | regression/correlation | 6 | GAP:regression | b | |
| 1.4 | interpret r | 1 | RESISTANT | c | |
| 1.5.1–3 | mean / std-dev / threshold | 5 | GAP:mean, GAP:std_dev | b | positional-only archetype |
| 2.1 | cumulative frequency | 2 | statistics_grouped | b | |
| 2.2–2.3 | total / count | 2 | statistics_grouped | a | |
| 2.4 | find k from est. mean | 4 | GAP:grouped_mean | b | |
| 3.1–3.2 | length / gradient | 4 | analytic_geometry_triangle | a | |
| 3.3 | inclination θ | 2 | GAP:inclination | b | |
| 3.4 | angle between lines | 3 | GAP:line_angle | b | |
| 3.5 | line ∥ SN | 3 | GAP:line_equation | b | |
| 3.6 | area ΔLSN | 3 | analytic_geometry_triangle | a | |
| 3.7 | equidistant point | 3 | GAP:circumcentre | b | |
| 3.8 | angle LP̂S | 2 | GAP:line_angle | b | |
| 4.1 | show p=4 | 2 | RESISTANT | c | |
| 4.2–4.6 | circle: F/tangent/t/eqn/tangency | 18 | GAP:analytic_circles | b | 20-mark clean block |
| 5.1.1 | cos β from sin β | 3 | trig | a | |
| 5.1.2 | sin 2β | 3 | GAP:double_angle | b | |
| 5.1.3 | cos(450°−β) | 3 | trig | b | |
| 5.2.1 | prove identity | 4 | RESISTANT | c | |
| 5.2.2–5.2.3 | undefined / minimum | 4 | trig, trig_graph_properties | b | |
| 5.3.1 | deduce sin(A−B) | 3 | RESISTANT | c | |
| 5.3.2 | general solution | 5 | trig | b | |
| 5.4 | simplify single ratio | 6 | GAP:sum_to_product | b | |
| 6.1 | period of f | 1 | trig_graph_properties | a | |
| 6.2–6.5 | range/interval/solve/transform | 11 | trig_graph_properties | b | |
| 7.1 | SK in terms of p,q,α | 2 | GAP:trig_3d | b | |
| 7.2 | show RS=… | 2 | RESISTANT | c | |
| 7.3 | calculate α | 3 | GAP:trig_3d | b | |
| 8.1 | prove ∠centre=2∠circ | 5 | RESISTANT | c | |
| 8.2–8.3 | circle angle-chase w/ reasons | 11 | GAP:circle_geometry | b | reason-graded |
| 9.1 | FB w/ reasons | 3 | GAP:proportionality | b | |
| 9.2 | prove similar | 3 | RESISTANT | c | |
| 9.3 | FC w/ reasons | 3 | GAP:proportionality | b | |
| 10.1–10.3 | circle-geom proofs | 15 | RESISTANT | c | |

### 2024 Nov P1 — a 8 / b 123 / c 19 · archetypes hit: zero_product_rule, quadratic_roots, exponent_laws, finance, probability_venn

| q_id | topic | marks | archetype | class | note |
|---|---|---|---|---|---|
| 1.1.1 | quadratic (zero product) | 2 | zero_product_rule | a | |
| 1.1.2 | quadratic (formula) | 4 | quadratic_roots | a | |
| 1.1.3 | quadratic inequality | 4 | GAP:quadratic-inequality | b | |
| 1.1.4 | exponential quadratic | 5 | exponent_laws | b | k=2^x substitution |
| 1.1.5 | surd equation | 4 | GAP:surd-equation | b | |
| 1.2 | nonlinear simultaneous | 5 | GAP:nonlinear-simultaneous | b | |
| 1.3 | telescoping/integer reasoning | 3 | RESISTANT | c | |
| 2.1.1–2.1.2 | AP series sum / sigma | 6 | GAP:series-sum, GAP:series-sigma | b | |
| 2.2.1–2.2.2 | quadratic pattern | 8 | GAP:quadratic-pattern | b | |
| 3.1–3.3 | geometric seq/series | 10 | GAP:geometric-sequence, GAP:geometric-series | b | |
| 4.1–4.2 | exp function param/range | 3 | GAP:exp-function, GAP:function-range | b | |
| 4.3 | exp graph sketch | 3 | RESISTANT | c | renderer |
| 4.4 | reflection about y=x | 3 | GAP:reflection-inverse | b | |
| 5.1–5.4 | hyperbola params/inequality | 8 | GAP:hyperbola, GAP:hyperbola-inequality | b | |
| 5.5 | describe transformation | 2 | RESISTANT | c | |
| 6.1 | parabola turning point | 3 | GAP:parabola-vertex | b | |
| 6.2 | show line equation | 3 | RESISTANT | c | |
| 6.3 | max vertical distance | 4 | GAP:optimisation | b | |
| 6.4 | tangent condition | 5 | GAP:tangent-discriminant | b | |
| 7.1 | compound (quarterly) | 3 | finance | b | |
| 7.2 | straight-line depreciation | 2 | GAP:depreciation | b | |
| 7.3.1–7.3.2 | loan/annuity | 9 | GAP:annuity-loan | b | |
| 8.1.1–8.1.2 | derivative rules | 6 | GAP:calculus-derivative | b | |
| 8.2 | tangent via derivative | 3 | GAP:calculus-tangent | b | |
| 8.3.1 | first principles | 5 | GAP:first-principles | b | |
| 8.3.2–8.3.3 | inverse of quadratic | 4 | GAP:inverse-domain, GAP:inverse-function | b | |
| 9.1–9.4 | cubic graph interpretation | 8 | RESISTANT | c | interpret-graph ×4 |
| 10.1 | motion max speed | 3 | GAP:calculus-motion | b | |
| 10.2 | motion distance (integrate) | 5 | GAP:calculus-integration | b | |
| 11.1 | draw Venn | 3 | probability_venn | b | render |
| 11.2 | P(at least two) | 2 | probability_venn | a | |
| 11.3 | independence test | 4 | probability_venn | b | |
| 12.1–12.3 | counting principle | 8 | GAP:counting-principle | b | |

### 2024 Nov P2 — a 9 / b 75 / c 66 · archetypes hit: statistics_one_var, analytic_geometry_triangle, trig, trig_graph_properties

| q_id | topic | marks | archetype | class | note |
|---|---|---|---|---|---|
| 1.1–1.3 | regression/correlation/predict | 6 | GAP:regression | b | |
| 1.4 | mean | 1 | statistics_one_var | a | |
| 1.5 | effect on sd | 1 | RESISTANT | c | |
| 1.6 | max increase to target | 2 | GAP:regression | b | |
| 2.1–2.3, 2.5–2.6 | ogive read-offs / IQR / rules | 8 | GAP:ogive | b | |
| 2.4 | draw box-and-whisker | 2 | GAP:boxplot | b | render |
| 3.1 | gradient DC | 2 | analytic_geometry_triangle | a | |
| 3.2 | equation of line DC | 2 | GAP:line | b | |
| 3.3 | show k=−6 | 1 | RESISTANT | c | |
| 3.4 | length DC | 2 | analytic_geometry_triangle | a | |
| 3.5 | ratio DB/DC | 2 | analytic_geometry_triangle | b | |
| 3.6 | area ratio via ∥ | 4 | GAP:area-ratio | b | |
| 3.7 | coords of A | 6 | GAP:line | b | |
| 4.1–4.5 | circle: L/tangent/eqn/angle | 17 | GAP:circle-geom, RESISTANT | b/c | 4.3/4.4 show-that=c |
| 4.6 | prove PT⊥RT | 3 | RESISTANT | c | |
| 5.1.1 | cos A from P(−3,−4) | 2 | trig | a | |
| 5.1.2–5.1.3, 5.2 | double/compound-angle | 10 | GAP:compound-angle | b | |
| 6.1.1–6.1.2 | derive/prove identity | 8 | RESISTANT | c | |
| 6.2 | solve f(x)=2 | 6 | trig | b | |
| 6.3.1–6.3.2 | max / smallest-x | 4 | trig_graph_properties | b | |
| 7.1 | asymptote of tan | 1 | trig_graph_properties | a | |
| 7.2 | f(x)≤0 interval | 2 | trig_graph_properties | c | graph-interpret |
| 7.3.1 | period of g | 1 | trig_graph_properties | a | |
| 7.3.2 | draw g | 3 | trig_graph_properties | b | render |
| 7.4 | general soln via graphs | 4 | trig_graph_properties | c | graph-dependent |
| 8.1–8.2 | 3D trig (distance) | 9 | GAP:trig-3d | b | |
| 9.1–11.4 | Euclidean geometry proofs | 41 | RESISTANT | c | 100% resistant |

### 2025 May/June P1 — a 16 / b 119 / c 15 · archetypes hit: quadratic_roots, exponent_laws, arithmetic_sequence, func_eval, func_inverse, probability_venn

| q_id | topic | marks | archetype | class | note |
|---|---|---|---|---|---|
| 1.1.1–1.1.2 | quadratic factorise/formula | 6 | quadratic_roots | a | |
| 1.1.3 | exponential equation | 3 | exponent_laws | b | |
| 1.1.4 | quadratic inequality | 3 | GAP:quadratic-inequality | b | |
| 1.1.5 | surd equation | 4 | GAP:surd-equation | b | |
| 1.2 | nonlinear simultaneous (word) | 6 | GAP:nonlinear-simultaneous | b | |
| 1.3 | exponent algebra proof | 3 | RESISTANT | c | |
| 2.1.1–2.1.2 | AP general term / find-n | 4 | arithmetic_sequence | a | |
| 2.1.3 | arithmetic series sum | 3 | GAP:arithmetic-series-sum | b | |
| 2.2.1–2.2.4 | geometric seq/series | 11 | GAP:geometric-sequence, GAP:geometric-series | b | |
| 3.1 | quadratic seq gen term | 3 | RESISTANT | c | "show that" |
| 3.2–3.3 | quadratic sequence | 6 | GAP:quadratic-sequence | b | |
| 4.1, 4.3, 4.4 | hyperbola graph | 8 | GAP:hyperbola-graph | b | |
| 4.2 | hyperbola y-intercept | 2 | func_eval | a | |
| 4.5 | closest-point optimisation | 3 | GAP:optimisation | b | |
| 4.6 | function transformation | 2 | GAP:function-transformation | b | |
| 5.1 | parabola from TP+pt | 3 | RESISTANT | c | "show that" |
| 5.2 | discriminant (no roots) | 2 | GAP:discriminant-nature-of-roots | b | |
| 5.3 | sketch g from g′ | 4 | RESISTANT | c | |
| 6.1–6.2 | exponential graph | 5 | GAP:exponential-graph | b | |
| 6.3 | line via inverse property | 4 | func_inverse | b | |
| 6.4 | linear inverse | 2 | func_inverse | a | |
| 7.1 | effective interest rate | 2 | GAP:effective-rate | b | |
| 7.2–7.3 | annuities / timeline | 11 | GAP:annuity, GAP:annuity-timeline | b | |
| 8.1 | first principles | 5 | GAP:first-principles | b | |
| 8.2.1–8.2.2 | derivative rules | 6 | GAP:derivative-rules | b | |
| 8.3 | common tangent | 6 | GAP:tangent-line | b | |
| 9.1 | cubic factor form | 2 | RESISTANT | c | "show that" |
| 9.2–9.5 | cubic TP/concavity/sketch/max | 16 | GAP:cubic-*, GAP:optimisation | b | 9.4 sketch=render |
| 10.1 | probability addition rule | 2 | probability_venn | a | |
| 10.2 | compound probability (word) | 6 | GAP:compound-probability | b | |
| 11.1–11.2 | counting principle | 7 | GAP:counting-principle | b | |

### 2025 May/June P2 — a 17 / b 85 / c 48 · archetypes hit: statistics_one_var, analytic_geometry_triangle, trig, trig_graph_properties

| q_id | topic | marks | archetype | class | note |
|---|---|---|---|---|---|
| 1.1–1.3 | stats mean/sd/count | 5 | statistics_one_var | a | |
| 1.4 | piecewise % increase, solve k | 4 | statistics_one_var | b | |
| 2.1–2.4 | regression / scatter / predict | 9 | GAP:regression | b | |
| 2.5 | explain y-intercept | 1 | RESISTANT | c | |
| 3.1 | R = x-intercept of line | 2 | GAP:line | b | |
| 3.2–3.3 | length RT / solve m | 7 | analytic_geometry_triangle | b | |
| 3.4 | eqn VR ⊥ ST | 5 | GAP:line | b | |
| 3.5 | show V=(−8;4) | 2 | RESISTANT | c | |
| 3.6 | area RVTR′ | 5 | analytic_geometry_triangle | b | |
| 4.1–4.7 | circle geometry (analytic) | 20 | GAP:circle, RESISTANT | b/c | 4.4 show-that=c; 4.1=c |
<!-- OPEN (2026-07-20): this paper's four unsplit b/c ranges (4.1–4.7=20, 8.1–8.3=8, 9.1.1–9.1.4=7,
     10.1–10.2.4=20; 55 marks) are arithmetically consistent with the 85/48 heading, which needs
     them to supply 29b/26c. But splitting per-sub-question on this file's own show-that/prove
     criteria gives 32b/23c → the paper would be a 17 / b 88 / c 45. Resolve when the ranges are
     split for real. -->

| 5.1.1–5.1.3 | trig ratios | 9 | trig | a | |
| 5.2–5.3 | simplify / product trick | 10 | trig | b | |
| 6.1–6.2.1 | prove identity ×2 | 6 | RESISTANT | c | |
| 6.2.2–6.2.3 | hence simplify / solve | 7 | trig | b | |
| 7.1–7.3 | trig-graph range/period/increasing | 3 | trig_graph_properties | a | |
| 7.4.1–7.5 | derivative-sign / solve / shift | 7 | trig_graph_properties | b | |
| 8.1–8.3 | 2D/3D trig | 8 | GAP:3d-trig, RESISTANT | b/c | 8.2 show-that=c |
| 9.1.1–9.1.4 | similarity (BPT) | 7 | GAP:similarity | b/c | |
| 9.2.1–9.2.3 | circle proofs | 13 | RESISTANT | c | |
| 10.1–10.2.4 | similarity/circle proofs | 20 | RESISTANT, GAP:circle | c/b | |

### 2025 Nov P1 — a 11 / b 116 / c 23 · archetypes hit: zero_product_rule, quadratic_roots, arithmetic_sequence, func_eval, finance

| q_id | topic | marks | archetype | class | note |
|---|---|---|---|---|---|
| 1.1.1 | quadratic (zero product) | 2 | zero_product_rule | a | |
| 1.1.2 | quadratic (formula) | 4 | quadratic_roots | a | |
| 1.1.3 | quadratic inequality | 4 | GAP:quadratic-inequality | b | |
| 1.1.4 | exponential eqn → quadratic | 4 | GAP:exponential-equation | b | |
| 1.1.5 | surd/radical equation | 5 | GAP:surd-equation | b | |
| 1.2 | nonlinear simultaneous (word) | 6 | GAP:simultaneous-nonlinear | b | |
| 2.1.1 | geometric series (show) | 3 | RESISTANT | c | |
| 2.1.2–2.1.3 | geometric nth/S∞ | 5 | GAP:geometric-sequence, GAP:geometric-series-infinite | b | |
| 2.2.1 | AP term difference | 2 | arithmetic_sequence | a | |
| 2.2.2 | series sum-to-n, solve k | 5 | GAP:series-sum-to-n | b | |
| 3.1, 3.3, 3.4 | quadratic pattern | 7 | GAP:quadratic-pattern | b | |
| 3.2 | quadratic pattern (show) | 3 | RESISTANT | c | |
| 4.1 | log eval | 1 | func_eval | a | |
| 4.2–4.6 | log/exp graph, inverse, transform | 9 | GAP:log-function, GAP:inverse-log-exp, GAP:exp-transformation | b | 4.5 sketch=render |
| 5.1–5.2 | hyperbola/parabola write-down | 2 | GAP:hyperbola-graph, GAP:parabola-graph | b | |
| 5.3.1 | g≤f from graph | 2 | RESISTANT | c | |
| 5.3.2, 5.5 | parabola algebraic | 8 | GAP:parabola-graph | b | |
| 5.4 | show parabola eqn | 3 | RESISTANT | c | |
| 5.6, 6.4 | tangent (derivative) | 5 | GAP:calculus-tangent | b | |
| 6.1–6.2 | hyperbola params | 4 | GAP:hyperbola-graph | b | |
| 6.3 | describe transformation | 2 | RESISTANT | c | |
| 7.1 | compound growth FV | 2 | finance | a | |
| 7.2 | future-value annuity | 4 | GAP:annuity-fv | b | |
| 7.3.1–7.3.2 | loan repayment | 9 | GAP:loan-repayment | b | |
| 8.1 | first principles | 4 | GAP:first-principles | b | |
| 8.2.1–8.2.2 | derivative rules | 6 | GAP:derivative-rules | b | |
| 9.1–9.2, 9.4 | cubic graph | 13 | GAP:cubic-graph | b | |
| 9.3 | f·f′<0 from graph | 4 | RESISTANT | c | |
| 10.1 | show volume eqn | 3 | RESISTANT | c | |
| 10.2 | optimise volume | 3 | GAP:optimisation | b | |
| 11.1.1 | independence (show) | 3 | RESISTANT | c | |
| 11.1.2 | two-way table probability | 3 | GAP:contingency-table | b | |
| 11.2 | total probability (word) | 4 | GAP:total-probability | b | |
| 11.3.1–11.3.2 | counting | 6 | GAP:counting-principle | b | |

### 2025 Nov P2 — a 26 / b 85 / c 39 · archetypes hit: analytic_geometry_triangle, trig, trig_graph_properties, statistics_grouped

> **OPEN — Q5 classification unresolved (flagged 2026-07-20).** The rows below class 5.1.1/5.1.2/
> 5.1.3/5.2 as class-a (`trig`). The transcription's memo does not support this: 5.1.2 is a
> double-angle manipulation, 5.1.3 a compound-angle expansion (`sin(60°−50°)`), 5.2 a reduction —
> all in the *extended trig identities* GAP family (see the family table above), not the CAST +
> special-angle scope of the built `trig` archetype. Only **5.1.1 (2)** is defensible as class-a.
> The §"flagship worked example" prose is also wrong in its own way: it names 5.1.1 **and 5.1.3**
> as the `trig` pair, and refers to Q5 "prove/deduce parts" — Q5 has none (the proof is 6.1).
> Reclassifying 5.1.2/5.1.3/5.2 (12 marks) a→b would make this paper **a 14 / b 97 / c 39** and
> the corpus total **105/1200 ≈ 8.75%**. Settle before citing Q5 as a coverage example.

| q_id | topic | marks | archetype | class | note |
|---|---|---|---|---|---|
| 1.1–1.3, 1.5 | least-squares line / predict / r / gradient-rate | 7 | GAP:regression | b | |
| 1.4 | interpret r | 1 | RESISTANT | c | |
| 2.1, 2.4 | frequency table from ogive / outside-1sd count | 8 | statistics_grouped | b | |
| 2.2 | draw histogram | 2 | statistics_grouped | b | render |
| 2.3 | describe + explain skewness | 2 | RESISTANT | c | |
| 3.1–3.2 | distance / gradient QR | 4 | analytic_geometry_triangle | a | |
| 3.3–3.4, 3.6 | inclination / line eqn / perp-foot | 7 | GAP:straight_line | b | |
| 3.5 | parallelogram 4th vertex | 3 | analytic_geometry_triangle | b | |
| 3.7 | triangle area | 4 | analytic_geometry_triangle | a | |
| 4.1, 4.3–4.8 | circle geometry (analytic) | 17 | GAP:analytic_circle | b | 21-mark block |
| 4.2 | show q=4 | 4 | RESISTANT | c | |
| 5.1.1 | co-ratio in terms of k | 2 | trig | a | |
| 5.1.2 | double-angle in terms of k | 4 | trig | a | |
| 5.1.3 | compound-angle in terms of k | 4 | trig | a | |
| 5.2 | simplify (reduction) | 4 | trig | a | |
| 5.3 | where undefined (domain) | 3 | trig | b | |
| 6.1 | prove identity | 6 | RESISTANT | c | |
| 6.2 | AP condition → gen. solution | 7 | trig | b | |
| 7.1, 7.3, 7.4 | trig-graph period/eqn/range | 4 | trig_graph_properties | a | |
| 7.2 | draw tan 2x−1 | 3 | trig_graph_properties | b | render |
| 7.5 | solve inequality | 3 | trig_graph_properties | b | |
| 8.1 | show AB=18 | 3 | RESISTANT | c | |
| 8.2–8.4 | 2D/3D trig lengths/angle | 7 | GAP:trig_2d3d | b | |
| 9.1 | prove ∠centre=2∠circ | 5 | RESISTANT | c | |
| 9.2.1–9.2.2, 10.1 | circle angle-chase | 8 | GAP:circle_geometry | b | reason-graded |
| 10.2–10.3 | circle proofs | 5 | RESISTANT | c | |
| 11.1.1–11.1.3 | similarity ratios | 10 | GAP:similarity | b | |
| 11.2.1–11.2.5 | similarity proofs | 13 | RESISTANT | c | |
