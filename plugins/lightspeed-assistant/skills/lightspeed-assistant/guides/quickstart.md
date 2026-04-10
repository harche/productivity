# Quickstart: First Proposal in 5 Minutes

Get a working LightspeedProposal on your cluster. Assumes the
lightspeed-operator is already deployed.

> **Confirm before applying.** Each step below creates cluster resources.
> Ask the user for confirmation before running any `oc apply` command.

## Step 1: Create an LLM Provider

```yaml
apiVersion: ols.openshift.io/v1alpha1
kind: OlsLlmProvider
metadata:
  name: smart
spec:
  type: vertex
  model: claude-opus-4-6
  credentialsSecretRef:
    name: llm-credentials  # must exist in openshift-lightspeed namespace
```

## Step 2: Create an Agent

```yaml
apiVersion: ols.openshift.io/v1alpha1
kind: OlsAgent
metadata:
  name: analyzer
spec:
  llm: smart
  skills:
    image: image-registry.openshift-image-registry.svc:5000/openshift-lightspeed/my-adapter-skills:latest
  systemPromptRef:
    name: analysis-prompt  # ConfigMap with key "prompt"
```

## Step 3: Create a Workflow

```yaml
apiVersion: ols.openshift.io/v1alpha1
kind: OlsWorkflow
metadata:
  name: advisory-only
spec:
  analysis:
    agent: analyzer
  execution:
    skip: true
  verification:
    skip: true
```

Start with advisory-only. It runs analysis but takes no action —
safe for testing.

## Step 4: Create a Proposal

```yaml
apiVersion: ols.openshift.io/v1alpha1
kind: LightspeedProposal
metadata:
  name: test-proposal
  namespace: openshift-lightspeed
spec:
  request: "Investigate high CPU usage in namespace default"
  workflow: advisory-only
  targetNamespaces:
    - default
```

## Step 5: Watch it

```bash
oc get lightspeedproposal test-proposal -n openshift-lightspeed -w
```

The proposal will move through Pending → Analyzing → Proposed.
Since execution is skipped, it stays at Proposed with the analysis results.

## What's Next

- **Add execution:** See guides/custom-workflow.md to build a full remediation workflow
- **Automate creation:** See guides/adapters.md to create proposals from alerts
- **Tune the agent:** See guides/system-prompts.md to customize analysis behavior

See also: architecture/phases.md
