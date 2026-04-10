# LightspeedProposal Documentation

> This documents the LightspeedProposal system — the CRD-based
> automated remediation platform for OpenShift. This is NOT the
> legacy OLSConfig appserver. Ignore appserver/ and lightspeed-service/.

## The System in Brief

4 CRDs compose the platform. Each builds on the previous:

- **OlsLlmProvider** — LLM backend config (provider type, model, credentials)
- **OlsAgent** — bundles an LLM provider + skills OCI image + system prompt
- **OlsWorkflow** — wires agents to 3 steps: analysis, execution, verification (any skippable)
- **LightspeedProposal** — the actual request; references a workflow, tracks full lifecycle

External adapters (AlertManager, ACS, custom) create proposals. The operator
reconciles them through phases: Pending → Analyzing → Proposed → Approved →
Executing → Verifying → Completed. Failed proposals retry with enriched context;
after max attempts, they escalate to a child proposal.

## Documentation Map

### How it works
|architecture:{crd-composition.md,phases.md,rbac.md}

### CRD field reference
|api:{proposal.md,workflow.md,agent.md,provider.md}

### Step-by-step guides
|guides:{quickstart.md,custom-workflow.md,adapters.md,system-prompts.md,skills.md}

### Building the platform
|developing:{codebase.md,reconciler.md,deploying.md,worktrees.md}
|developing/references:{clusters.md,components.md}

### Annotated YAML examples
|examples:{remediation.md,advisory.md,gitops.md,acs.md,trust-mode.md}
