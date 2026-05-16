We're doing a case-interviewer session for **problem-instantiation-tool** — a generic engine that sits between content definitions and downstream consumers (SRS, PDF, practice mode, Manim, etc.). This is a ground-up spec, not a description of existing code.

**The ecosystem context:**

- `srs-tool` — shared scheduling/state package (SRSState, SM-2 review, check_unlocks). Exists, stable.
- `problem-instantiation-tool` — the engine we're speccing today. Does not exist yet.
- `nsc_papers` — NSC math content: YAML concept definitions + some directly-scripted generators. Consumer of the engine.
- `cq` — Chinese vocabulary card pipeline. Second consumer of the engine. Use it as a cross-domain validation lens throughout — any engine behavior cq couldn't use without modification is a leaked nsc_papers assumption.

**The four core objects:**

- `Problem` — the spec (YAML declaration or registered generator function). Immutable content definition.
- `Verifier` — composed as `VerifierChain([StepVerifier, ...])`. Knows how to rate a SolutionAttempt. CA marking (Consistent Accuracy: if step N is wrong, step N+1 is re-evaluated against the student's derived value, not the canonical one) lives in the chain, not in individual step verifiers.
- `SolutionAttempt` — raw student input, one or multiple steps. Steps with multiple named outputs (e.g. `{x, y}`) are submitted as dicts; order within a step is irrelevant.
- `SolutionRating` — output of `verifier.rate(attempt_sequence)` where attempt_sequence can be partial (1 step, some steps, all steps). Pure function — no session state.

**StepVerifier types** (closed authored set for now): SymPy equivalence, MCQ, SelfGraded (human marks it). No others in v1.

**Scope boundaries — state these as explicit decisions, not open questions:**

- Not an ITS. Automated equivalence checking stays shallow; problems are authored for a specific solution path.
- Multi-step machine grading is out of scope for v1. SRS problems are 1-2 steps by convention, machine-gradeable. Complex worked examples produce a problem + worked solution(s) artifact; grading is human discretion. If a problem exceeds what SelfGradedVerifier handles gracefully, it belongs in the worked-example artifact type.
- CA marking applies only within the SRS (1-2 step) context.

**Interview the engine, not the content.** nsc_papers YAML and scripted generators are content; the engine is what dispatches to them. Cases should exercise the engine contract — `instantiate(spec)`, `verifier.rate(attempts)`, artifact shape, failure modes — not the mathematical content of specific NSC concepts.

**Schema probe is mandatory, not deferred.** Before closing any section, enumerate the fields of every object introduced in that section.

**Use cq as a cross-domain lens throughout.** After every significant case, ask: would this work for a Chinese vocabulary card with no changes? If not, why not?
