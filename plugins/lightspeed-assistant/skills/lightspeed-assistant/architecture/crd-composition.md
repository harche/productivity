# CRD Composition Model

The platform uses 4 CRDs that compose from leaf to root:

```
OlsLlmProvider        (cluster-scoped)
  └─► OlsAgent        (cluster-scoped, references a provider)
       └─► OlsWorkflow (cluster-scoped, references agents per step)
            └─► LightspeedProposal (namespaced, references a workflow)
```

## OlsLlmProvider

Defines an LLM backend. Provider type, model name, credentials secret.
Created once per model tier (e.g., "smart" for Opus, "fast" for Haiku).

## OlsAgent

Bundles three things: which LLM to use (`spec.llm`), which skills
OCI image to mount (`spec.skills.image`), and an optional system prompt
ConfigMap (`spec.systemPromptRef`). Different agents for different roles
(analyzer, executor, verifier).

## OlsWorkflow

Wires agents to 3 steps: analysis, execution, verification. Each step
has an `agent` name and a `skip` flag. Skipping a step changes the
phase flow (see phases.md).

Workflows are reusable templates. One workflow can serve many proposals.

## LightspeedProposal

The actual unit of work. References a workflow by name, carries the
request text and target namespaces. Status tracks the full lifecycle
with per-step results.

Supports `workflowOverride` to tweak a workflow for one proposal
without creating a new workflow CR.

## Composition Example

```
OlsLlmProvider "smart"  ──► OlsAgent "analyzer"  ──┐
OlsLlmProvider "fast"   ──► OlsAgent "executor"  ──┼──► OlsWorkflow "remediation"
OlsLlmProvider "smart"  ──► OlsAgent "verifier"  ──┘         │
                                                              ▼
                                                   LightspeedProposal
                                                   (spec.workflow: "remediation")
```

An agent can reuse the same LLM provider. A workflow can reuse the
same agent for multiple steps. This is intentional composability.

See also: api/provider.md, api/agent.md, api/workflow.md, api/proposal.md
