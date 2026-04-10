# API Reference

CRD field reference for the 4 proposal-system CRDs.
Listed from leaf (simplest) to root (most complex):

## CRDs

|provider.md — OlsLlmProvider: LLM type, model, credentials secret
|agent.md — OlsAgent: bundles provider + skills image + system prompt
|workflow.md — OlsWorkflow: 3 steps (analysis/execution/verification), skip flags
|proposal.md — LightspeedProposal: request, workflow ref, full lifecycle status

All CRDs are `v1alpha1` in group `ols.openshift.io`.
Provider, Agent, and Workflow are cluster-scoped. Proposal is namespaced.
