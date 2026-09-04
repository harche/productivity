---
description: UltraCode-style implementation with isolated writers and integration gates
argument-hint: "<task, scope, and acceptance criteria>"
---

Use an UltraCode-style dynamic implementation workflow.

TASK:
$ARGUMENTS

If the task, scope, or expected behavior is materially ambiguous, identify the blocking questions before writing code. Do not silently invent API or behavioral requirements.

BOUNDARIES:
- Read and obey all applicable AGENTS.md and other repository instructions first.
- Record the repository state, base revision, relevant packages, and dirty files.
- Preserve unrelated user changes.
- Do not edit generated files directly.
- State the exact read/write boundary and file ownership in every delegated task.
- Reviewers, investigators, contract agents, and architecture agents must be read-only.
- Parallel writers must use isolated worktrees with disjoint file ownership.
- Keep one controlled integration lane.
- Do not claim a test or command passed unless it was actually run.
- Report unavailable agents, spawn limits, merge conflicts, and blocked decisions explicitly.

ORCHESTRATION:

PI MODEL ROUTING:
- This policy applies when running under Pi.
- Keep the parent coordinator on `openai/gpt-5.6-sol` with `xhigh` thinking. All child model calls also use `xhigh` thinking.
- Choose the subagent role first based on tools and responsibility, then choose the model based on task risk and authority.
- Model tiers:
  - `openai/gpt-5.6-sol`: highest-assurance tier for open-ended semantic reasoning, implementation, omission-sensitive review, ambiguous research, cross-component analysis, synthesis, and final decisions.
  - `openai/gpt-5.6-terra`: bounded-work tier for well-specified analysis, verification, comparison, transformation, and support tasks whose output is independently checkable.
  - `openai/gpt-5.6-luna`: factual-work tier for repository reconnaissance, extraction, inventory, classification, and mechanical formatting that carries no decision authority.
- Default role routing:
  - `worker`, `reviewer`, `oracle`, and `researcher` use `openai/gpt-5.6-sol:xhigh`.
  - `delegate` uses `openai/gpt-5.6-terra:xhigh`.
  - `scout` uses `openai/gpt-5.6-luna:xhigh`.
- In Pi, prefer native subagents when exact model routing is required; external CLI agents do not support Pi's native per-run model overrides.
- The parent may promote any task to a stronger model whenever scope, ambiguity, risk, or conflicting evidence warrants it.
- The parent may use a lower-cost model only when the task is narrowly bounded, supplied with complete context, independently verifiable, and carries no consequential decision authority.
- Luna may collect or transform evidence but must not make semantic, architectural, severity, acceptance, or completeness decisions.
- Terra may analyze bounded questions but must escalate ambiguity, conflicting evidence, broad impact, security concerns, compatibility concerns, and cross-component behavior to Sol.
- If uncertain, use Sol.
- Verify the resolved model mapping before launching agents. When overriding a role default, pass the exact model explicitly in the child launch; do not silently substitute models.
- If a required model or agent is unavailable, report the limitation instead of weakening the routing policy.

IMPLEMENTATION-SPECIFIC ROUTING:
- Use `scout` with `openai/gpt-5.6-luna:xhigh` for factual repository reconnaissance, ownership mapping, and locating implementation and test seams. Scouts must not modify project source files.
- Use `delegate` with `openai/gpt-5.6-terra:xhigh` for bounded support work such as comparison, transformation, checklist preparation, and independently checkable analysis. Delegates must not make architecture or acceptance decisions or modify project source files in this workflow.
- Use `worker` with `openai/gpt-5.6-sol:xhigh` for every implementation writer, integration writer, and confirmed-fix writer.
- Use `reviewer` with `openai/gpt-5.6-sol:xhigh` for contract analysis, adversarial review, finding verification, and completeness criticism.
- Use `researcher` with `openai/gpt-5.6-sol:xhigh` when external specifications, upstream behavior, security guidance, or compatibility contracts materially affect the implementation.
- Use `oracle` with `openai/gpt-5.6-sol:xhigh` only for unresolved architecture, difficult root causes, or conflicts that the coordinator cannot settle from source and test evidence.
- Only Sol workers may modify project source files. Terra and Luna agents provide advisory evidence or bounded support output to the Sol coordinator and workers.

- Use the host's native dynamic multi-agent orchestration rather than treating this as a single-agent task.
- In Pi, use one coordinated subagent workflow with dynamic fanout and keep all phases inside that workflow.

CONTRACT PHASE:
1. Extract and state:
   - current behavior
   - required behavior
   - API and compatibility constraints
   - invariants and failure behavior
   - acceptance criteria
   - required tests and negative controls
   - relevant repository-generation rules
2. Discover the available executable specialist agents.
3. Run read-only specialists in parallel for:
   - behavioral and API contract
   - architecture and ownership boundaries
   - existing tests and test gaps
   - compatibility, security, and regression risks
4. Aggregate their results and resolve contradictions before implementation.

IMPLEMENTATION PHASE:
5. Decompose the change into the smallest practical disjoint ownership groups.
6. Assign each writer:
   - an isolated worktree
   - explicit writable files or directories
   - explicit read-only dependencies
   - acceptance criteria
   - required focused tests
7. Each implementation agent must:
   - read the relevant implementation and tests in full
   - modify only assigned files
   - keep changes focused
   - add focused tests
   - add a negative control where practical
   - run the narrowest relevant tests
   - report changed files, diff summary, commands run, failures, uncertainties, and blocked items
8. Do not allow overlapping parallel writers. If ownership overlaps, sequence the work or consolidate it under one writer.

INTEGRATION PHASE:
9. Integrate all accepted changes in one controlled lane.
10. Inspect the combined diff for:
    - contract consistency
    - accidental scope expansion
    - conflicting assumptions
    - generated-file requirements
    - missing integration paths
11. Build and test the actual combined result, not only individual worktree results.
12. Run the relevant:
    - focused unit tests
    - package or component tests
    - integration tests where justified
    - formatting, lint, generation, or verification checks required by repository policy
    - runtime or artifact-level checks where practical
13. Exercise negative controls where practical.
14. Fix integration failures in the controlled integration lane and rerun affected checks.

ADVERSARIAL PHASE:
15. Run independent read-only reviewers against the integrated diff for:
    - behavioral correctness
    - compatibility and API regressions
    - concurrency, lifecycle, and error handling
    - test completeness and false-positive tests
    - security and trust boundaries where relevant
16. Dynamically verify every important finding with refutation/reproduction and impact reviewers.
17. Apply only confirmed fixes.
18. Run a completeness critic for missed interactions, untested paths, and incomplete acceptance criteria.
19. Verify and resolve any new critic findings.

FINAL GATE:
Report:
- implemented behavior
- changed files
- tests added or changed
- commands actually run and their outcomes
- commands not run and why
- confirmed review findings and resolutions
- rejected findings and reasons
- residual risks
- blocked or open decisions
- whether every acceptance criterion was satisfied

Do not stop at the first compiling result. Finish with evidence from the integrated tree.
