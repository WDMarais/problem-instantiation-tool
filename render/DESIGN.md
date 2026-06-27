# Graphics rendering — design

Scope: how the tool turns problems into figures (SVG). Covers two distinct visual
domains and the seam between them. Display-only is a hard rule: **the generator
bakes every answer; nothing is ever read off a rendered figure.** A figure is
orientation material, not a measurement instrument.

## The three-way split

The dividing question is not "geometry vs graphs" — it is **"is there a coordinate
frame?"** That cleaves the space into three, not two:

1. **Function plots** — Cartesian, metric, axes-bound. Position is *computed* and
   meaningful (the curve's shape encodes `f`). Parabola, hyperbola, exponential,
   trig, cubic, log.
2. **Analytic geometry** — *also* on axes, *also* metric, but the objects are
   points / lines / circles / polygons rather than function curves (distance,
   midpoint, gradient, equation of a circle). **Rides along with the Cartesian
   schema** — it just needs `Point`, `Segment`, and a `Circle` primitive on top of
   the function-plot vocabulary.
3. **Euclidean figures** — circle theorems, congruency, similar triangles,
   parallelogram angle-chases. **No coordinate frame.** Positions are authored for
   legibility and are deliberately *not to scale*. Separate schema.

```
            ┌─ CartesianScene ─┐         ┌─ GeometryFigure ─┐
            │ window + axes    │         │ labelled points  │
            │ curve/asymptote  │         │ segments / arcs  │
            │ point/segment/   │         │ angle+tick+R.A.  │
            │ region/circle    │         │ marks, parallels │
builders →  └────────┬─────────┘         └────────┬─────────┘
                     └──────────┬─────────────────┘
                       shared dumb SVG emitter
                  (line, polyline, arc, dot, text, style)
```

DRY lives at the **emitter**, not the **scene**. The two scenes share almost no
primitives (asymptotes/range-bands are meaningless in a triangle proof; angle-arcs
and congruence ticks are meaningless on a parabola), so merging their schemas would
produce a union type where half the fields are always null depending on mode —
which violates the project's *explicit-over-inferred* principle. Two honest
schemas, one shared emitter.

## Layering (applies to both scenes)

- **Scene / Figure** — pure data: a window (Cartesian) or layout box (Euclidean)
  plus a list of geometric primitives in *data* / *layout* coordinates.
- **Renderer** — `Scene → SVG`. Dumb: maps coordinates to pixels and draws. No
  `math` beyond the pixel transform. Trivially testable (assert on path strings).
- **Builders** — per family (`parabola_scene`, `hyperbola_scene`, `trig_scene`,
  `parallelogram_figure`, …). They hold the domain knowledge — sampling,
  discontinuity splitting, intercept/vertex computation, figure layout — and bake
  the answer-bearing marks. This is where math lives.

The existing `render/graph.py` currently *conflates* "evaluate sin/cos" with
"draw"; the eventual refactor is to lift its drawing into the shared emitter, lift
its sin/cos sampling into a `trig_scene` builder, and have it consume a
`CartesianScene`. Not yet done — trig still works standalone.

## CartesianScene — primitive vocabulary

The full NSC function-plot + analytic-geometry matrix collapses to ~7 primitives:

| Primitive | Covers | Status |
|---|---|---|
| `Axes` | range, tick step, label mode (numeric \| degrees), origin | partial in graph.py |
| `Polyline` | a sampled curve; **must support breaks** for discontinuities | partial |
| `ConstantLine` | dashed v/h/diagonal (asymptotes, `y=x`, `k`-line) | partial (`k_line`) |
| `Point` | dot + label + optional dashed drop-lines to axes | new |
| `Segment` | line between two points (PQ length, secants, tangents) | new |
| `Region` | fill between curves / inequality band | partial (axis-aligned bands only) |
| `Circle` | analytic-geometry circle `x²+y²=r²` | new |
| `Label` | free text at a coordinate | have (curve labels) |

Two notes:
- **Discontinuities** (hyperbola, tan) are the only genuinely new *plotting* logic.
  Handled builder-side: the builder splits the domain at the asymptote and emits
  two `Polyline`s; the renderer never sees the gap. A naïve single polyline would
  draw a false vertical streak across the asymptote.
- **True `Region` fill** (area between two curves for `f>g`) is the most expensive
  primitive. Deferred: most NSC graphical-inequality questions are adequately
  marked with a shaded vertical strip + boundary dots (which the `highlight_x`
  band nearly already is). Add true fill only when a problem genuinely needs it.

## GeometryFigure — primitive vocabulary

Layout coordinates (y-up, abstract units); the renderer fits the bounding box to
the viewBox. Not to scale by design.

| Primitive | Covers |
|---|---|
| `Point` | named vertex (A, B, O, …); auto label placement away from centroid |
| `Segment` | side / diagonal / transversal; optional dashed |
| ↳ `arrows=n` on a segment | parallel-mark chevrons (1 = single, 2 = double pair) |
| ↳ `ticks=n` on a segment | equal-length tick marks |
| `Angle` | arc at a vertex between two rays, with a text label (`x`, `70°`) |
| ↳ `arcs=n` on an angle | concentric arcs for equal-angle marks |
| ↳ `right=True` on an angle | right-angle square instead of an arc |

The mark primitives (angle-arc sweeps, equal ticks, right-angle squares, parallel
chevrons) are the real implementation cost here — the Euclidean equivalent of
"discontinuity handling is the real cost of function plots." Bounded but fiddly.

**Layout, not evaluation, is the hard part.** The answer (e.g. the value of angle
`x`) is baked by the generator via the theorem chain; the figure is pure display.
But placing a legible cyclic-quad-with-tangent is a layout problem. The NSC figure
set is bounded (triangle, circle+chords, cyclic quad, tangent+radius, two-triangle
similarity, midpoint/ladder), so the approach is **template-authored topologies
with parametric labels/values** — exactly how the algebra generators vary
coefficients, not structure — plus a small placement kernel when needed
(`point_on_circle`, `intersect`, `midpoint`, `foot_of_perpendicular`).

## Status

- `render/graph.py` — trig curves (standalone; pre-dates this design).
- `render/geometry.py` — `GeometryFigure` schema + emitter. **First consumer:
  parallelogram angle-chases** (`content/examples/parallelogram_angles.py`):
  co-interior, opposite, and alternate-angle ("Z-angle", diagonal as transversal)
  variants. Display-only; reason-chain in `worked_steps`.
- Shared SVG emitter extraction + porting trig onto `CartesianScene`: follow-up,
  not yet done.
- `GeometryFigure` placement kernel: add when the first circle-theorem figure
  needs it. Parallelograms only need authored coordinates.
