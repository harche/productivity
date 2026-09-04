---
description: Adversarial UltraCode-style review with dynamic verification
argument-hint: "[target, base, scope, or PR]"
---

Use an UltraCode-style adversarial code-review workflow.

REVIEW TARGET:
$ARGUMENTS

If no target was supplied, review the current working tree against the appropriate merge base. Determine and state the base before reviewing.

BOUNDARIES:
- Read and obey all applicable AGENTS.md, CLAUDE.md, and repository instructions first.
- Establish the exact target, base revision, included paths, exclusions, and repository state.
- State the exact read boundary in every delegated task.
- All review, investigation, and verification agents must be read-only.
- Do not modify source files.
- Do not claim a command or test passed unless it was actually run.
- Report unavailable agents, spawn limits, or other orchestration constraints instead of silently weakening the workflow.
- Avoid style-only comments, vague risks, duplicate findings, and pre-existing issues outside the review scope.

ORCHESTRATION:
1. Discover the available executable specialist agents.
2. Use the host's native dynamic multi-agent orchestration rather than treating this as a single-agent review or launching a fixed handful of generic agents.
   - In Pi, use one coordinated subagent workflow with dynamic fanout and keep all waves inside that workflow.
   - In Claude Code, use parallel specialized agents and preserve the same read-only boundaries and structured contracts.
3. Select 6–10 independent review lenses appropriate to the change, such as:
   - behavioral correctness
   - concurrency and lifecycle
   - API and compatibility
   - security and trust boundaries
   - error handling and recovery
   - state persistence and migration
   - tests and negative controls
   - performance and resource use
   - repository-specific conventions
4. Run the first-wave reviewers in parallel.
5. Require every candidate finding to contain:
   - stable finding ID
   - concise title
   - exact file and line evidence
   - triggering scenario
   - concrete impact
   - suggested correction
   - commands or tests actually run
   - uncertainty or blocked evidence
6. Aggregate and deduplicate the candidates.
7. For every nontrivial candidate, dynamically launch:
   - a refutation or reproduction reviewer
   - an impact, severity, or compatibility reviewer
   - an additional verifier when the claim is high-risk, disputed, or cross-component
8. Reject findings that are unsupported, unreproducible, pre-existing, intentional, or outside scope.
9. Run a completeness critic over:
   - the reviewed diff
   - confirmed findings
   - rejected findings
   - interactions and untested paths that the first wave may have missed
10. Independently verify any new finding produced by the completeness critic.

FINAL RESPONSE:
- Confirmed findings first, ordered by severity.
- For each confirmed finding include file:line, trigger, impact, evidence, and suggested fix.
- Then list rejected findings with concise rejection reasons.
- State review coverage, commands/tests run, commands/tests not run, residual risks, and blocked questions.
- If there are no confirmed findings, say so directly.

Prefer fewer evidence-backed conclusions over speculative coverage. Do not stop at the first plausible answer.
