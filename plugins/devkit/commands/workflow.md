---
description: Author and run a dynamic workflow to explore the task from all angles
argument-hint: "<task> [--solo-ok]"
---

# Dynamic workflow

REQUEST: $ARGUMENTS

Author and run a dynamic workflow for the given task to explore from all
angles. The goal is the most exhaustive, correct answer you can produce —
token cost is not a constraint.

Use the host's native delegation mechanism (Pi: `subagent` with
`workflowScript` + `runs.run` / `runs.all` / `runs.lanes`; Claude Code:
subagents via the Task tool). Never shell out to a foreign CLI agent as a
workflow fallback.

## 1. Solo or orchestrate

- Solo only on conversational turns or trivial mechanical edits, or when the
  work is already verified. Everything else leans toward orchestrating with
  workflows and adversarially verifying the findings.
- For multi-phase work (understand → design → implement → review), run
  several workflows in sequence — one per phase — so the user stays in the
  loop between them. End each phase with a short checkpoint, wait for
  feedback, then launch the next.

## 2. Author the workflow

- Give every worker a bounded handoff: objective, repo/cwd/ref,
  authority/edit boundary, relevant files and constraints, acceptance
  criteria, expected output/report, stop/ask conditions.
- Keep one writer per cwd/worktree. Use an isolated worktree lane when
  isolation, overlap, or concurrent juggling matters (see
  `/devkit:worktree`).
- Fan out with distinct prompts per seam, evidence source, or decision —
  never clones with only item numbers swapped. No duplicate scouts, no
  overlapping writers, no vague prompts without a concrete deliverable.

## 3. Quality patterns — pick what fits

- **Adversarial verify:** a fresh-context reviewer tries to break the
  finding (counterexamples, missed cases, wrong assumptions). Synthesize
  and fix in the parent. Default for non-trivial findings.
- **Multi-modal sweep:** parallel lanes attack from different angles
  (docs vs. code vs. history vs. runtime) then merge.
- **Completeness critic:** one pass asks only "what is missing?" and
  returns gaps, not praise.
- **Loop-until-dry:** repeat a check until a full pass returns nothing new,
  then stop. State the stop condition up front.

## 4. Execute and report

- Launch async by default; yield and let completion wake you. Block only
  when a same-turn artifact is required.
- Treat workflow/launch/prompt failures as lane infrastructure blockers:
  stop, report the exact failure plus run/worktree state, capture partial
  diffs, retry same-protocol or ask the owner before any fallback.
- End with: what was run (phases, lanes), key findings with evidence,
  residual risks, and what needs the user's eye.
