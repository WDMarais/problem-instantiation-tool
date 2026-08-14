# Finance / Annuities — detailed family build-spec (2026-08-07)

Deep per-archetype spec for **Family 2** of `family-build-specs.md` (the summary table there is
the index; this is the build sheet the generators are authored against — same role Family 1's
detail played for `geometric_sequence.py` / `series.py`).

**Template:** `content/examples/finance.py` (Gr10 annual simple/compound/reverse). Same
numeric-answer shape; the Gr12 work is (a) **compounding frequency**, (b) the **annuity
formulae**, and (c) — the real payload — **NSC rounding & payment-timing conventions**.

**Corpus anchors (every P1 has exactly one finance question, ~14 marks):**

| paper | Q | marks | parts (verbatim skills) |
|---|---|---|---|
| 2023 Nov | Q6 | 16 | solve-rate-from-growth; effective rate; straight-line depreciation→years; FV-annuity solve deposit; PV-annuity solve #withdrawals |
| 2024 Nov | Q7 | 14 | compound quarterly (16 yr); straight-line depreciation→rate; loan total interest; PV-annuity extra-payment "months earlier" |
| 2025 M/J | Q7 | 13 | nominal→effective; PV-annuity solve #withdrawals; lump-sum + deferred monthly deposits timeline |
| 2025 Nov | Q7 | 15 | inflation (appreciation); FV-annuity due quarterly; PV-annuity loan with missed first payments solve n |

Total in-corpus = **58 marks / 4 papers**. Guaranteed block; formula-driven; zero renderer dependency.

---

## Conventions (the F-payload — get these into the memo faithfully)

These are assessed distinctions, not incidental. Every generator must **state its convention in
the stem** and **honour it in the canonical + memo**.

- **Period rate & count.** Nominal rate `r%` p.a. compounded `m` times/yr → per-period rate
  `i = r/(100·m)`, periods `= m·n` over `n` years. `m ∈ {1 (annual), 4 (quarterly), 12 (monthly)}`.
  All three appear in the corpus (annual/inflation, quarterly ×2, monthly ×4).
- **Rounding — currency.** Final money answer to **2 dp (cents)**. Canonical is the *unrounded*
  exact value; verifier tolerance absorbs the student's 2dp rounding (see engine note below).
- **Rounding — n (count of payments/withdrawals).** Two opposite conventions, both assessed:
  - *"How many full withdrawals of Rx can be made"* → **floor** (the last drop is a smaller
    partial withdrawal; the question asks for whole ones). — 2023 Q6.3, 2025 M/J Q7.2.
  - *"How many months/payments to repay the loan"* → **ceil** (a final smaller payment still
    counts as a payment that clears the debt). — 2025 Nov Q7.3.1.
  - The generator must know which it is; the memo shows the exact `n` before rounding **and** the
    rounding direction with a one-line reason.
- **Payment timing — ordinary vs due.** Ordinary annuity = payments at the **end** of each period
  (the default; PV/FV formulae below). Annuity **due** = payments at the **start** → multiply the
  ordinary result by `(1+i)`. Corpus has both; 2025 Nov Q7.2 and 2025 M/J Q7.3 are **due**.
- **Deferred / missed first payment.** When the first payment is not one period after the anchor
  (missed months, deposit "on day born" then first withdrawal years later), grow the balance over
  the gap with plain compound first, then apply the annuity. This is the classic trap and lives in
  archetype #6, deferred to build-last.
- **First-payment placement in the stem.** Always state the date/period of the first and last
  payment explicitly — the number of payments is a mark, and off-by-one on the endpoints is the
  most common real error the memo must pin down.

### Engine note — tolerance must go relative (one small change)

`numeric_equality` today is **absolute-only**: `abs(student − canonical) <= tolerance`
(`verifier.py:225`), and `finance.py` uses `tolerance = 0.01`. That is correct for Gr10 principals
(≤ R20k) but **breaks at Gr12 scale**: on a R900 000 loan a student who rounds `i = 0.068/12` to
5 dp drifts by several rand over 60+ periods — an answer any NSC marker accepts, but ±R0.01 rejects.

**Decision:** extend `numeric_equality` with an optional **relative** tolerance, accept if *either*
absolute or relative passes: `abs(s−c) <= abs_tol or abs(s−c) <= rel_tol*abs(c)`. Finance specs use
`rel_tol ≈ 1e-4` (0.01%), keeping `abs_tol = 0.01` for the small-money cases. This is the **one
engine touch** the family needs — do it in its own commit *before* the annuity archetypes, keep it
backward-compatible (default `rel_tol = 0`, existing specs unchanged), add a verifier test at
R900k scale. All Gr10 `finance.py` specs keep working untouched.

---

## Archetypes

Marks are DBE-calibrated (≈ one mark per method/accuracy step a marker ticks), matching the
corpus part-marks. `verifier_spec` = `numeric_equality` with `tolerance` (abs) + `rel_tol`
(new field) unless noted; multi-part uses the `param_key` list shape.

### 1 · `compound_periodic` — non-annual compound growth  ·  2–3 marks
The Gr10 `compound_growth`/`compound_reverse` lifted to `m > 1`, plus **inflation/appreciation**
(same formula, "will cost" framing) and **solve-for-rate** (2023 Q6.1).
- **Formula:** `A = P·(1 + i/m)^(m·n)`, `i = r/100`.
- **Modes:** solve `A` (given P,r,m,n) · solve `P` (reverse) · solve `r` (given A,P,m,n →
  `r = 100·m·((A/P)^(1/(m·n)) − 1)`) · appreciation variant (same as solve-A, cost framing).
- **Params (corpus-grounded):** `P ∈ {5 000 … 1 600 000}`; `r ∈ {5.8, 6, 6.8, 7.8, 8.7, 9.5, 11.2, 13.5, 15}`;
  `m ∈ {4, 12}` (annual is the Gr10 case); `n` yrs `∈ {2…16}`.
- **Verifier:** numeric, `abs 0.01 / rel 1e-4`. Rate-mode answer is a % → 2 dp.
- **Marks:** solve-A/appreciation **2**; solve-P **2**; solve-r **3** (extra root/log step).
- **Anchor:** 2024 Q7.1 (quarterly, 16 yr), 2025 Nov Q7.1 (inflation).

### 2 · `nominal_effective_rate` — rate conversion  ·  2 marks
Smallest build; pure formula, no principal.
- **Formula:** `1 + i_eff = (1 + i_nom/m)^m` → `i_eff = (1 + i_nom/m)^m − 1`; reverse solves `i_nom`.
- **Modes:** nominal→effective (dominant) · effective→nominal.
- **Params:** `i_nom ∈ {6 … 15}%`, `m ∈ {4, 12}`.
- **Verifier:** numeric on the **percentage**, `abs 0.01` (answer is small, e.g. 9.06); `rel_tol`
  irrelevant here. Answer to 2 dp %.
- **Marks:** **2** both directions.
- **Anchor:** 2023 Q6.1.2 (→9.06%), 2025 M/J Q7.1.

### 3 · `depreciation` — straight-line & reducing-balance  ·  2–3 marks
Two sub-models; the stem **must name which** ("straight-line" vs "reducing balance / on a reducing
balance").
- **Formulae:** straight-line (simple) `A = P·(1 − i·n)`; reducing-balance `A = P·(1 − i)^n`
  (`i = r/100`).
- **Modes:** solve `A` · solve `r` (2024 Q7.2: "determine the rate", straight-line) · solve `n`
  (2023 Q6.2.1: "after how many years will value = R0" — straight-line only, `n = 1/i` → integer/ceil).
- **Params:** `P ∈ {5 000 … 200 000}`; `r ∈ {10, 15, 20, 25}%`; `n ∈ {3…8}`.
- **Verifier:** numeric `abs 0.01 / rel 1e-4`; rate-mode 2 dp %; `n`-to-zero mode is exact integer.
- **Marks:** solve-A **2**; solve-r **2**; straight-line-to-zero **2**.
- **Anchor:** 2023 Q6.2.1, 2024 Q7.2.

### 4 · `future_value_annuity` — regular deposits  ·  3–4 marks  **[flagship]**
- **Formula (ordinary):** `F = x·[(1+i)^N − 1] / i`, `i = r/(100m)`, `N = m·n`.
  **Due:** `F_due = F·(1+i)`.
- **Modes:** solve `F` (given deposit x) · solve `x` (deposit needed to reach a target F —
  2023 Q6.2.2) · solve `N` (number of deposits, logs; floor/ceil per framing).
- **Timing:** ordinary vs due is a **param**, stated in the stem; corpus has due (2025 Nov Q7.2).
- **Params:** `x ∈ {500, 2 300, …}`; `r ∈ {5.8, 6.8, 8.7}%`; `m ∈ {4, 12}`; `N` derived from dates.
- **Verifier:** numeric `abs 0.01 / rel 1e-4`; solve-N → count.
- **Guards:** `i > 0`; for solve-N ensure the target is reachable (`F·i/x + 1 > 1`, always true for
  positive inputs — no degenerate case here, unlike PV).
- **Marks:** solve-F **3**; solve-x **4**; solve-N **4**.
- **Anchor:** 2023 Q6.2.2 (solve deposit), 2025 Nov Q7.2 (due, quarterly), 2025 M/J Q7.3 (part).

### 5 · `present_value_annuity` — loans & withdrawals  ·  3–5 marks  **[flagship]**
The highest-recurrence family (all 4 papers). **Solve-for-n is the load-bearing hard part.**
- **Formula (ordinary):** `P = x·[1 − (1+i)^(−N)] / i`. **Due:** `P_due = P·(1+i)`.
- **Modes:** solve `P` (loan amount affordable) · solve `x` (instalment/withdrawal) · **solve `N`**
  (number of payments/withdrawals):
  `N = −ln(1 − P·i/x) / ln(1+i)`, then **floor** (withdrawals) or **ceil** (loan repayment).
- **Guard (assessed concept):** `x > P·i` — the payment must exceed the interest accruing, else
  `1 − P·i/x ≤ 0`, the log is undefined, and the loan/fund **never clears**. Generators must keep
  `x` comfortably above `P·i`; a "why can he never repay" variant is class-c (defer).
- **Loan total interest** (2024 Q7.3.1) is a trivial rider: `total = x·N − P`, **2 marks** — expose
  as a mode here rather than its own archetype.
- **Params:** `P ∈ {100 000 … 1 600 000}`; `x ∈ {10 000, 11 250, 20 000, 2 300.98}`;
  `r ∈ {6, 6.8, 11.2, 13.5}%`; `m ∈ {4, 12}`.
- **Verifier:** numeric `abs 0.01 / rel 1e-4` — **this is the archetype that needs rel_tol most**
  (large P). solve-N → count.
- **Marks:** solve-P **3**; solve-x **4**; solve-N **5**; total-interest rider **2**.
- **Anchor:** 2023 Q6.3, 2024 Q7.3.1, 2025 M/J Q7.2, 2025 Nov Q7.3.1.

### 6 · `annuity_timeline` — deferred / missed / extra-payment  ·  5–7 marks  **[BUILD LAST or v2]**
Class-b-but-hard: composes #1 + #4/#5 across a multi-phase timeline. High per-mark, gnarly.
- **Shapes in corpus:**
  - *lump sum then deferred deposits* (2025 M/J Q7.3, [6]): compound the lump over the whole term;
    FV-annuity the deposits over their (shorter, offset) window; sum at the valuation date.
  - *missed first k payments* (2025 Nov Q7.3.1, [5]): grow loan by plain compound over the k missed
    periods → new principal → PV-annuity solve-N from there.
  - *extra lump payment mid-loan* (2024 Q7.3.2, [7]): PV of remaining balance at the extra-payment
    date, subtract extra, re-solve N for the shortened tail; "how many months earlier" = original
    N − new N.
- **Marks:** 5–7 (multi-step; each phase is a method mark).
- **Decision:** **defer to a Level-2 pass** alongside the per-line method-marks item. Land #1–#5
  clean first — they cover ~9 of the ~14 marks/paper without the timeline machinery.

---

## Gr10 → Gr12 upgrade of `finance.py`

Minimal, backward-compatible:
- Add a `compounding` (`m`) param to `compound_growth` / `compound_reverse` → `i/m`, `m·n`.
  `simple_interest` stays annual Gr10 filler (untouched).
- Set `rel_tol = 1e-4` on the compound specs once the engine field lands (keep `abs 0.01`).
- **Recalibrate marks** (currently all `1`) to the DBE part-marks above — same pass done for
  `arithmetic_sequence.py`. Rough map: `compound_growth`→2, `compound_reverse`→2.
- Keep the demo `__main__` block (rounding-boundary showcase) — extend it with an `m=12` case.

---

## Build order (own commits, in sequence)

1. **engine:** `numeric_equality` relative-tolerance field (+ R900k test). *(the one engine touch)*
2. `compound_periodic` — + upgrade `finance.py` compound specs (they share the frequency change).
3. `nominal_effective_rate` — smallest, warms the % conventions.
4. `future_value_annuity` — flagship A.
5. `present_value_annuity` (incl. solve-N + loan-interest rider) — flagship B, highest recurrence.
6. `depreciation` — two sub-models.
7. **marks recalibration** across the family + `--bundle finance` demo (mirror `--bundle sequences`).
8. *(deferred)* `annuity_timeline` — Level-2, with the per-line method-marks work.

**Coverage:** #1–#7 address ≈ 9–11 of the ~14 marks/paper (the class-b clean parts); the timeline
tail (#8) is the remaining ~3–5, deferred with eyes open.
