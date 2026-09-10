# Handoff — hyperbola Q4: let `q` take either sign (mirror the inequality)

**Status:** designed, not built. Self-contained archetype extension. Not MVP-blocking.
**Written:** 2026-09-10, mid `september-push`.

## Why this exists

P1 Q4 is the hyperbola compound (`f(x) = a/(x+p) + q`). Reviewing rendered papers we
noticed the horizontal asymptote `y = q` is **positive on every seed**. That is not an
accident: the generator draws `q` only from the **positive** divisors of `a`, so the
asymptote never sits below the x-axis. This costs us a whole axis of visual variety.

The positive-`q` constraint is *currently* load-bearing (so it is NOT a cosmetic range
limit — see `[[feedback-no-cosmetic-range-limits]]`). Two real downstream consumers force it:

1. **Integer x-intercept.** `C = -a/q - p` is an integer iff `q | a`.
2. **A single clean interval for sub-part 4.4** ("values of `x` for which `f(x) ≤ 0`").
   With `a > 0`:
   - `q > 0`: `f ≤ 0` ⟺ `[C, -p)` — one bounded half-open interval. ✓
   - `q < 0`: `f ≤ 0` ⟺ `(-∞, -p) ∪ [C, ∞)` — a **union of two unbounded rays**. ✗
     (The memo `∴ C ≤ x < M_x` would be wrong.)

So today the archetype sidesteps the `q < 0` case by never generating it.

## The insight (feasible, elegant)

Flip the inequality direction with the sign of `q`. The two cases are **mirror images**
through `y = q`, each a single clean bounded half-open interval:

| sign(q) | ask            | answer set        | closed / open                     |
|---------|----------------|-------------------|-----------------------------------|
| `q > 0` | `f(x) ≤ 0`     | `[C, -p)`         | closed at intercept, open at asymptote |
| `q < 0` | `f(x) ≥ 0`     | `(-p, C]`         | open at asymptote, closed at intercept |

Rule in words: **closed at the x-intercept `C`, open at the vertical asymptote `-p`**;
only the side (which branch, hence which direction) swaps.

Worked check at `a = 9, p = 1`:
- `q = 1`  → `f ≤ 0` ⟺ `[-10, -1)` ✓
- `q = -1` → `f ≥ 0` ⟺ `(-1, 8]` ✓  (vs. the broken `f ≤ 0` = `(-∞,-1) ∪ [8,∞)`)

`C = -a/q - p` stays an integer for **negative** divisors of `a` too (−1, −3, −9 … all
divide 9), so `q` can range over *all nonzero divisors* and both properties survive.

### The other five sub-parts are sign-agnostic

Checked each — all are translates/reflections whose formulas don't care about `sign(q)`:
`M = (-p, q)` · `D = (0, a/p + q)` · axis of symmetry `t = p + q` · closest point
`A = (-p+√a, q+√a)` · reflection length `AA' = 2|x_A|`. **4.4 is the only part that
must branch.**

## Implementation (exact touch-points)

1. **`content/examples/hyperbola_properties.py`**
   - `~line 49`: draw `q` from *all nonzero* divisors of `a` (currently
     `range(1, a+1)`), e.g. `d for d in range(-a, a+1) if d != 0 and a % d == 0`.
   - `~line 60`: `solution_set` is built as `Interval(cx, mx, left_open=False,
     right_open=True)` = `[C, -p)`. When `q < 0`, build `Interval(mx, cx,
     left_open=True, right_open=False)` = `(-p, C]` instead. (Graded via
     `set_solution`, which already handles either orientation — no verifier change.)
   - Add an `ineq_dir`/`region_latex` param (`"\\le"` vs `"\\ge"`) for the template.
   - Update the module docstring (`~lines 11, 25`) to state the sign-mirrored contract.
   - `forbidden` set (`~line 52`, keeps `C` off the y-axis / distinct from `D`) is
     already sign-agnostic — re-verify it holds for `q < 0`.

2. **`worksheets/generate.py` — `template_hyperbola_properties`, SubPart "4" (~5005–5015)**
   - Instruction text: `f(x) \le 0` → use the sign-selected symbol.
   - Memo last line: `\therefore\; {C} \le x < {M_x}` → orient by sign
     (`-p < x \le C` for `q < 0`). `auto_marks=2` unchanged.

3. **`content/scope_predicates.py` — `hyperbola_properties_in_scope` (~1454, note ~1461)**
   - Relax `q > 0` to `q != 0 and q | a` (keep `a > 0`). Update the reason strings +
     the docstring bullet that currently asserts `q > 0`.

4. **Tests**
   - Add a `q < 0` seed end-to-end: interval orientation `(-p, C]`, correct openness,
     integer `C`, `set_solution` grades it, instruction shows `\ge`. Confirm the
     existing `q > 0` behaviour is unchanged.

The render side needs **nothing** — the window fix (`render/hyperbola.py`, commit
`18dcd76`) centres on `(-p, q)` and scales by `√|a|`, already sign-agnostic.

## Why prefer this over "regenerate on union"

An alternative is to keep asking `f ≤ 0` always and just re-roll `q`/allocations when the
numbers land in the union case. This mirror-the-inequality approach is strictly better:
it *keeps* the `q < 0` seeds (doubles the asymptote-position variety — the exact variety
we noticed missing) instead of discarding them, and it needs no reroll loop.

## Session state at handoff (for resume)

Branch `main`, tree clean. Full suite green (1741 passed, 52 skipped). Recent commits:
- `18dcd76` widen hyperbola window to curve scale for steep (large-a) seeds
- `d439b19` unify figure typography: serif labels, centred, larger, roomier
- `7c0a321` (earlier) Q6 hence-solve + static proof blocks — P2 already complete

**First P1/P2 pair is closed** (both fidelity audits done, both faithful; see
`[[project-p1-p2-loose-ends]]`). Remaining MVP pieces, unstarted: (a) worksheet
static-KaTeX pre-render (last stream-1 packaging TODO,
`[[project-september-delivery-week]]`); (b) second/third pair (needs another year's
skeleton ingested). This hyperbola enhancement sits below both in priority.
