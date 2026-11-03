# Product Roadmap

This document lists delivery steps in build order. `docs/features.md` owns the user-facing feature catalog and functional groupings, `docs/concepts/` owns domain models and cross-feature macro-flows (`C-nn`), and `docs/tech-stack.md` records technology context; this roadmap synthesizes them (along with existing AST symbols when `.codegraph/` is present) into dependency-driven delivery sequencing, architectural rationale, technical guardrails, and verification checkpoints.

---

## How to Use This Roadmap

* **Step IDs (`R-pp.ss`):** Each delivery step uses the `R-pp.ss` scheme, where `pp` is the two-digit Delivery Phase (`00`–`99`) in build order, and `ss` is the sequential Step (`01`–`99`) within that phase. IDs are assigned once and never renumbered; list order determines delivery order.
* **Target Linking:** Each step completes one or more Use Cases, written as `[UC-gg.nn.uu](features/f-gg.nn/uc-gg.nn.uu-short-slug.md)`. When a foundational or setup feature has no separate use cases, the step falls back to linking the feature directly as `[F-gg.nn](features/f-gg.nn/feature.md)`.
* **Planning vs. Implementation Boundary:** Unlike feature guides and use cases (which must remain in non-technical, user-focused language), roadmap steps and `Verify:` checkpoints may include concrete technical delivery decisions, technology selections, symbol anchors, and verification commands. However, roadmap steps must **not** contain source code snippets, function definitions, file-by-file edit tasks, class/call trees, or database DDL schemas—those belong in downstream implementation planning (`/plan` or `ce-plan`).
* **Enriched Step Schema (Field Guide):** Every step captures high-signal sub-bullets under its statement line:
  1. **Statement:** One human-readable statement line: `- [ ] R-pp.ss: Imperative statement — [UC-gg.nn.uu](features/f-gg.nn/uc-gg.nn.uu-short-slug.md)`, with `— after: ...` appended only when the step declares dependencies.
  2. **Rationale (`- Rationale:`):** Causal reason why this step is positioned here and what upstream state or prerequisite capability it relies upon.
  3. **Concepts (`- Concepts:`):** Linked domain models (`[C-nn](concepts/c-nn-short-slug.md)`) and tech-stack capabilities informing this delivery slice.
  4. **Anchors (`- Anchors:`):** *(Conditional: included only when `.codegraph/` is present at the repo root)* Names prerequisite AST symbols consumed and target symbols/interfaces established so `ce-plan` can query them directly via `codegraph_explore`. Omit cleanly when CodeGraph is not active.
  5. **Gotchas (`- Gotchas:`):** Critical architectural constraints, edge cases, or concurrency/idempotency pitfalls to account for without prescribing implementation code.
  6. **Verify (`- Verify:`):** A user-verifiable stopping point describing what the user runs or clicks, what observable outcome confirms success, and demo data when needed. A step with no direct user-observable outcome may defer with `Verify: with R-pp.ss`, naming a later step whose checkpoint demonstrates it (never more than two consecutive open steps defer).
* **Dependencies (`after:`):** An optional `after:` list names prior step IDs (`R-pp.ss`) or feature IDs (`F-gg.nn`) this step must follow. A step must not name its own parent feature or use case.
* **Status:** Check a step only when its work is implemented and verified. Completed steps are immutable history.
* **Coverage:** Every incomplete feature in `docs/features.md` needs step coverage here.
* **Engineering Handoff (`ce-plan`):** Each `R-pp.ss` step is structured as a briefing note for `/plan` or `ce-plan` to initiate technical implementation planning.

---

## Steps

### Phase 01: Foundation & Core Flows

- [ ] R-01.01: Example foundational step — [F-00.01](features/f-00.01/feature.md)
    - Rationale: Establishes foundational storage and configuration prerequisites required by downstream feature workflows.
    - Concepts: Informed by `[C-01: Example Domain Model](concepts/c-01-example-domain-model.md)` invariants and core runtime stack in `docs/tech-stack.md`.
    - Anchors: Establishes `ConfigStore` and `WorkspacePaths` interfaces (include `Anchors:` only when `.codegraph/` is active).
    - Gotchas: Ensure configuration initialization is idempotent and preserves existing user-customized files on re-run.
    - Verify: run the named command or open the named screen with the listed demo data, and confirm the described outcome.
- [ ] R-01.02: Example dependent step — [UC-01.01.01](features/f-01.01/uc-01.01.01-slug.md) — after: R-01.01
    - Rationale: Requires persisted foundational state from R-01.01 before actor workflow transitions can be recorded.
    - Concepts: Enforces stage transitions defined in `[C-01: Example Domain Model](concepts/c-01-example-domain-model.md)`.
    - Anchors: Consumes `ConfigStore` (from R-01.01); establishes `WorkflowDispatcher` interface (include `Anchors:` only when `.codegraph/` is active).
    - Gotchas: Concurrent or retried requests must be handled idempotently without duplicating state transitions.
    - Verify: describe the user-runnable check and demo data for this step, or defer with `with R-pp.ss` to a later checkpoint.
