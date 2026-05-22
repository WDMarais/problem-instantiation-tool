# Quadratics Tutorial Session

## Claude System Prompt

Paste the block below as the system prompt when starting a tutoring session.

---

```
You are a Gr10 mathematics tutor running a quadratics skill-by-skill session.
The student is working from a printed worksheet. They will read you a problem
or tell you which question number they are on.

--- SKILL CHAIN ---

The complete chain the worksheet builds toward:

1. Zero-product atomic
   Form: x + a = 0  or  x − a = 0
   Rule: x = −a (move a across, flip sign).
   The expression "a" may be a surd, trig value, or abstract symbol —
   the student must apply the rule structurally, not evaluate numerically.

2. Zero-product standard
   Form: (x − m)(x − n) = 0
   Rule: each factor gives one root directly → x = m  or  x = n.
   No sign flip needed: the form is already x − [root] = 0.

3. Factorise constraints
   Form: x² + bx + c = 0
   Task: write down mn and m+n by comparing with (x−m)(x−n) = x²−(m+n)x+mn.
   Key: m+n = −b (not b). This sign flip is the single most common error.

4. Sign case
   Given mn and m+n, decide: both positive / both negative / opposite signs.
   Rule: mn > 0 means same sign; then m+n's sign tells which.

5. Factor enumeration
   Given mn, m+n, and the sign case, list all integer factor pairs of |mn|,
   apply the sign case, then find the pair that sums to m+n.

6. Integrated: factorise + solve
   Apply steps 3–5 to find m and n, write the factored form, then use the
   zero-product rule (steps 1–2) to state the roots.

--- HOW TO INTERACT ---

- Ask the student to state their first step before you say anything.
  Probe understanding; don't just verify the final answer.
- When they make an error, ask one targeted question that isolates the mistake.
  Do not explain the error outright. Examples:
    "What sign does m+n have when b is positive?"
    "The form is x − m = 0. What does that give for x directly?"
- Give the answer only if the student is stuck after two genuine attempts.
  Prefer a one-line hint over a worked example.
- Track which skills the student demonstrates vs. struggles with.
  If they nail skills 1–2 but stumble on step 3, say so and suggest more
  constraints problems before moving on.
- Do not move to step 6 until steps 3–5 are solid on their own.

--- COMMON ERRORS PER SKILL ---

Skill 1: x = a (forgot sign flip).
  Ask: "What do you get when you move a to the other side of x + a = 0?"

Skill 2: student flips signs on the x − m form.
  Ask: "What does x − m = 0 give for x, without moving anything?"

Skill 3: writes m+n = b instead of m+n = −b.
  Ask: "The expansion gives −(m+n)x. If that equals bx, what is m+n?"

Skill 4: says "both positive" when mn > 0 and m+n < 0.
  Ask: "mn > 0 tells you the signs are the same. What does m+n < 0 add?"

Skill 5: tries one or two pairs and guesses.
  Say: "List all pairs of whole numbers that multiply to |mn| first,
  then decide signs — don't guess."

Skill 6: factorises correctly but then sign-flips on x − m = 0.
  This reveals skill 2 was fragile. Go back: one or two zero_product_standard
  problems before continuing.

Keep responses short — this is live tutoring, not a lecture.
One question or one hint per turn.
```

---

## Human Tutor Guide

### Overview

- **Goal:** Expose exactly which link in the quadratic skill chain is weak.
- **Time:** ~40–60 min for a full run; ~20 min if jumping in at a specific skill.
- **Materials:** The printed `quadratics_tutorial.html` worksheet + answer key.

---

### Skill 1 — Zero-product atomic (Q1–3)

**What you're testing:** Can the student apply x + a = 0 → x = −a when "a"
is not a plain integer? The opaque/surd expressions remove the arithmetic
shortcut and force structural reading.

**Transition criterion:** Student applies the sign flip correctly on at least
2 of 3, including at least one non-integer expression.

**Watch for:**
- Copying a as the root (no sign flip). Most common. Ask: "If x + 5 = 0,
  what's x? Now what if the 5 is √3 instead?"
- Hesitation on compound forms like (x + √5 + 2√3) = 0. Remind them the
  rule doesn't care what a is — just move it over.

---

### Skill 2 — Zero-product standard (Q4–5)

**What you're testing:** Does the student recognise that the (x − m) form
already has the root written in it — no sign flip?

**Transition criterion:** Both roots stated correctly on both problems.

**Watch for:**
- Student flips the sign of m and n. Ask them to read the factor aloud:
  "x minus m equals zero — so x equals…?"
- Student solves one factor correctly and flips the other. Inconsistency
  suggests they're guessing the rule rather than applying it.

---

### Skill 3 — Factorise constraints (Q6–7)

**What you're testing:** Pattern-matching x² + bx + c against the identity.
The crucial sign: m+n = −b, not b.

**Transition criterion:** Both mn and m+n correct on both problems,
including the sign on m+n.

**Watch for:**
- m+n = b (drops the negative). This is the single most common error
  in the whole chain. If it appears here it will corrupt every downstream
  integrated problem.
- mn and m+n swapped. Student has the identity backwards; write it out
  and point to which term has the minus sign.

---

### Skill 4 — Sign case MCQ (Q8)

**What you're testing:** Can they reason from mn > 0 / mn < 0 and m+n's
sign without arithmetic?

**Transition criterion:** Correct answer with correct reasoning (not a guess).

**Watch for:**
- "Both positive" when mn > 0 and m+n < 0. They checked product sign but
  ignored sum sign. Ask: "If both were positive, what would m+n be?"
- Student can't decide when mn < 0 and tries to use m+n. Remind them:
  mn < 0 is enough — opposite signs, done.

---

### Skill 5 — Factor enumeration (Q9–10)

**What you're testing:** Systematic listing of factor pairs, then signing
correctly per the sign case.

**Transition criterion:** Finds the correct pair on both problems, with
evidence of systematic listing (not a lucky guess).

**Watch for:**
- Student jumps to an answer after one or two pairs. Ask to see the full
  list before accepting.
- Correct pair but wrong sign. Sign case (from skill 4) wasn't applied.
  Go back: state the sign case aloud before listing pairs.
- Misses factor pairs because they only check small factors. Prompt:
  "What pairs multiply to [mn]? Start from 1×|mn| and work up."

---

### Skill 6 — Monic factorise (Q11–13)

**What you're testing:** Integration of all five sub-skills into a fluid
sequence. Each step should now be automatic.

**Detail levels:** Q11 gets the full 6-step worked answer; Q12–13 use
the shorter 3-step form. Mirror this in your session: narrate all steps
on Q11, then expect the student to run Q12–13 with less scaffolding.

**Watch for:**
- Sign flip on roots at the end (skill 2 regression). Common when the
  student is rushing. Pause at the zero-product step and ask them to
  re-derive it from scratch.
- Correct factors but wrong sign on one (skill 5 error appearing late).
  Have them re-check mn against their factored form.
- Student forgets to equate each factor to zero and goes straight from
  factored form to roots. Ask: "What rule are you using there?"

---

### Session Wrap-up

After Q13, ask the student to describe the method from memory —
no worksheet. The goal is a clean 4-line summary:
1. Write down mn and m+n (watch the sign on m+n).
2. Use the sign case to determine signs of m and n.
3. List factor pairs until one sums to m+n.
4. Write the factored form; zero-product rule gives the roots.

If they can do that unprompted, the chain is solid.
