---
description: UltraCode-style implementation with isolated writers and integration gates
argument-hint: "<task, scope, and acceptance criteria>"
---

Use an UltraCode-style dynamic implementation workflow.

TASK:
$ARGUMENTS

If the task, scope, or expected behavior is materially ambiguous, identify the blocking questions before writing code. Do not silently invent API or behavioral requirements.

BOUNDARIES:
- Read and obey all applicable AGENTS.md, CLAUDE.md, and repository instructions first.
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
- Use the host's native dynamic multi-agent orchestration rather than treating this as a single-agent task.
- In Pi, use one coordinated subagent workflow with dynamic fanout and keep all phases inside that workflow.
- In Claude Code, use parallel specialized agents and isolated worktrees for concurrent writers.

CONTRACT PHASE:
1. Extract and state:
   - current behavior
   - required behavior
   - API, compatibility, and sentinel/default semantics across backends
   - invariants, failure behavior, and mechanisms ensuring recovery progress
   - acceptance criteria, including behavior preserved during partial failure
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
   - test required behavior, including relevant sentinel and partial-failure cases
   - where practical, demonstrate failure on the base and success on the fix, or use an equivalent negative control; report unverified cases
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
16. Track material concerns, including proposed rejections. Dynamically verify important candidates with refutation/reproduction and impact reviewers. Independently challenge consequential dismissals based on intent, pre-existence, unreachability, sentinel semantics, or assumed retry progress.
17. Apply only confirmed fixes; rerun affected checks and review the fix diff.
18. Give a completeness critic the integrated diff and acceptance criteria before prior verdicts, then the concern ledger for reconciliation.
19. Verify new or reopened findings. The parent must audit final dispositions. Source proof is valid; blocked execution remains unverified, not disproven.

FINAL GATE:
Report:
- implemented behavior
- changed files
- tests added or changed
- commands actually run and their outcomes
- commands not run and why
- confirmed review findings and resolutions
- rejected findings with evidence, and unresolved concerns
- residual risks
- blocked or open decisions
- each acceptance criterion's status: satisfied, failed, or unverified

Do not stop at the first compiling result. Finish with evidence from the integrated tree.
