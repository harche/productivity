---
description: Adversarial UltraCode-style review with dynamic verification
argument-hint: "[target, base, scope, or PR]"
---

Use an UltraCode-style adversarial code-review workflow.

REVIEW TARGET:
$ARGUMENTS

If no target was supplied, review the current working tree against the appropriate merge base. Determine and state the base before reviewing.

BOUNDARIES:
- Read and obey all applicable AGENTS.md and other repository instructions first.
- Establish the exact target, base revision, included paths, exclusions, and repository state.
- State the exact read boundary in every delegated task.
- All review, investigation, and verification agents must be read-only.
- Do not modify source files.
- Do not claim a command or test passed unless it was actually run.
- Report unavailable agents, spawn limits, or other orchestration constraints instead of silently weakening the workflow.
- Avoid style-only comments, vague risks, duplicate findings, and pre-existing issues outside the review scope.

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

REVIEW-SPECIFIC ROUTING:
- Do not launch `worker` or any writer agent in this read-only workflow.
- Use `reviewer` with `openai/gpt-5.6-luna:xhigh` only for factual mapping of changed files, symbols, callers, tests, and repository instructions.
- Use `reviewer` with `openai/gpt-5.6-terra:xhigh` only for bounded reproduction, reachability, contradiction, or impact analysis when given a complete candidate packet.
- Use `reviewer` with `openai/gpt-5.6-sol:xhigh` for first-wave semantic review, consequential or disputed findings, high-risk or cross-component verification, completeness criticism, and independent final verification.
- Use `researcher` with `openai/gpt-5.6-sol:xhigh` only when external specifications, upstream behavior, security advisories, or compatibility contracts materially affect the review.
- Use `oracle` with `openai/gpt-5.6-sol:xhigh` only for unresolved architectural invariants, difficult root causes, or conflicts between reviewers.
- Terra and Luna outputs are advisory evidence. The Sol coordinator owns finding validity, severity, rejection, completeness, and final acceptance.

1. Discover the available executable specialist agents.
2. Use the host's native dynamic multi-agent orchestration rather than treating this as a single-agent review or launching a fixed handful of generic agents.
   - In Pi, use one coordinated subagent workflow with dynamic fanout and keep all waves inside that workflow.
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
