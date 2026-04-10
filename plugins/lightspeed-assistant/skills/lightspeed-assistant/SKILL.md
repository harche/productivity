---
name: lightspeed-assistant
description: Navigate and work with the LightspeedProposal system — the CRD-based automated remediation platform. Use when anyone asks about proposals, workflows, agents, LLM providers, adapters, deployment, or the proposal lifecycle. Covers both developing the platform and integrating with its API.
allowed-tools: Bash(oc:*) Bash(kubectl:*)
---

# LightspeedProposal Assistant

Help developers and integrators work with the LightspeedProposal system.

> **This is NOT the legacy OLSConfig/appserver system.**
> Ignore `appserver/`, `lightspeed-service/`. The proposal system is the new interface.

## How to Use

Read `AGENTS.md` in this skill directory to get the documentation index. It routes you to the right topic. Each topic folder has its own `AGENTS.md` with further routing.

**Progressive disclosure:** Read the topic AGENTS.md first, then only fetch the specific leaf doc you need. Do not read everything — fetch on demand.

## Write/Update Confirmation Rule

**Never perform write or update operations without explicit user confirmation.**
Before any `oc apply`, `oc patch`, `oc delete`, `oc scale`, `oc rollout restart`,
`kubectl apply`, or any command that creates, modifies, or deletes cluster resources,
you MUST ask the user for confirmation first. Show them exactly what you're about
to do and wait for approval. This applies to:

- Creating CRs (proposals, workflows, agents, providers)
- Patching or updating existing resources
- Deleting resources
- Scaling deployments
- Running deploy/redeploy scripts
- Any `oc` or `kubectl` write operation

Read-only operations (`oc get`, `oc describe`, `oc logs`) do not require confirmation.

## Audience

- **Developers** — building the proposal flow (operator, reconciler, CRDs, console)
- **Integrators** — using the API (creating workflows, adapters, proposals)

Both use the same documentation tree. Topic-level AGENTS.md files tag docs by audience.
