# Example: Cluster Upgrade

Risk assessment and execution for OpenShift cluster upgrades.
The upgrade-specific agents check deprecated APIs, operator compatibility,
node capacity, and workload disruption before proceeding.

## Setup

> **Confirm before applying.** Ask the user for confirmation before
> creating any resources on the cluster.

Assumes providers from `examples/setup/01-llm-providers.yaml` are applied.
The upgrade workflow requires its own system prompts, agents, and workflow
from `examples/setup/00-system-prompts.yaml`, `02-agents.yaml`, and
`03-workflows.yaml`.

## System Prompts

```yaml
# Risk assessment prompt — read-only cluster inspection
apiVersion: v1
kind: ConfigMap
metadata:
  name: upgrade-analysis-prompt
  namespace: openshift-lightspeed
data:
  prompt: |
    You are an expert OpenShift upgrade advisor. You are running inside
    a read-only sandbox with access to the cluster.

    ## Your Task
    1. Assess the risk of upgrading to the requested version
    2. Check for deprecated API usage across all workloads
    3. Verify operator compatibility with the target version
    4. Check node capacity and resource headroom
    5. Identify any workloads that may be disrupted

    ## Rules
    - Use `oc` to inspect ClusterVersion, nodes, operators, and workloads
    - Check deprecated APIs with `oc get apirequestcounts`
    - Verify operator health with `oc get clusteroperators`
    - Check node resources with `oc adm top nodes`
    - Be conservative in risk assessment — flag anything uncertain
---
# Execution prompt — write access to trigger and monitor the upgrade
apiVersion: v1
kind: ConfigMap
metadata:
  name: upgrade-execution-prompt
  namespace: openshift-lightspeed
data:
  prompt: |
    You are an expert OpenShift upgrade executor. You are running inside
    an execution sandbox with write access to the cluster.

    ## Your Task
    1. Apply the approved upgrade to the target version
    2. Monitor the upgrade progress
    3. Verify nodes are updating correctly

    ## Rules
    - Use `oc adm upgrade` to trigger the upgrade
    - Monitor with `oc get clusterversion` and `oc get nodes`
    - Do NOT force the upgrade — use standard channels
    - Report progress at each stage
```

Two separate prompts because the concerns are different. Analysis needs
deep inspection of APIs and operators. Execution needs the minimal set
of `oc adm upgrade` commands to apply the change safely.

## Agents

```yaml
# Upgrade analyzer — smart model, upgrade-specific skills image
apiVersion: ols.openshift.io/v1alpha1
kind: OlsAgent
metadata:
  name: upgrade-analyzer
spec:
  llm: smart                # Opus — deep reasoning for risk assessment
  skills:
    image: quay.io/openshift-lightspeed/skills-upgrade:latest
  systemPromptRef:
    name: upgrade-analysis-prompt
---
# Upgrade executor — fast model, same skills image
apiVersion: ols.openshift.io/v1alpha1
kind: OlsAgent
metadata:
  name: upgrade-executor
spec:
  llm: fast                 # Haiku — follows approved upgrade plan
  skills:
    image: quay.io/openshift-lightspeed/skills-upgrade:latest
  systemPromptRef:
    name: upgrade-execution-prompt
```

Both agents share the `skills-upgrade` image but use different
system prompts and LLM tiers. The analyzer benefits from a capable
model for risk assessment; the executor follows a pre-approved plan.

## Workflow

```yaml
apiVersion: ols.openshift.io/v1alpha1
kind: OlsWorkflow
metadata:
  name: upgrade
spec:
  analysis:
    agent: upgrade-analyzer    # checks deprecated APIs, operator health, node capacity
  execution:
    agent: upgrade-executor    # runs `oc adm upgrade` and monitors progress
  verification:
    agent: verifier            # reuses the standard verifier agent
```

The verification step reuses the standard `verifier` agent from
`examples/setup/02-agents.yaml`. It independently confirms the
cluster version updated and all nodes are healthy.

## Proposal

```yaml
apiVersion: ols.openshift.io/v1alpha1
kind: LightspeedProposal
metadata:
  name: upgrade-4-22
  namespace: openshift-lightspeed
spec:
  workflow: upgrade
  request: "Upgrade cluster from OCP 4.21.5 to 4.22.0"
  maxAttempts: 2               # retry once if first attempt fails
```

No `targetNamespaces` — upgrades are cluster-scoped operations.
`maxAttempts: 2` gives the system one retry in case a transient
issue blocks the upgrade (e.g., a degraded operator that recovers).

## What Happens

1. **Pending -> Analyzing:** Upgrade analyzer inspects the cluster:
   deprecated API usage (`oc get apirequestcounts`), operator health
   (`oc get clusteroperators`), node resources (`oc adm top nodes`),
   and workload compatibility. Returns a risk assessment + upgrade plan.

2. **Analyzing -> Proposed:** User sees the risk report in the console.
   Can approve if risk is acceptable, deny, or refine the plan.

3. **Proposed -> Approved -> Executing:** Upgrade executor runs
   `oc adm upgrade --to=4.22.0` and monitors ClusterVersion status.

4. **Executing -> Verifying:** Standard verifier checks that
   ClusterVersion reports the target version, all nodes are Ready,
   and all ClusterOperators are Available.

5. **Verifying -> Completed:** Upgrade confirmed.

## Upgrade Adapter

The upgrade adapter in `examples/adapters/upgrade/` automates proposal
creation. It polls `ClusterVersion` for available updates and creates
a proposal when a new version is detected.

```
ClusterVersion (availableUpdates) -> Upgrade Adapter -> LightspeedProposal
                                     polls every 1h          |
                                                       Operator reconciles
```

Key behaviors:
- **Deduplication:** Won't create a proposal if one already exists for
  the same source-to-target version pair
- **Naming convention:** `upgrade-<current>-to-<target>` (sanitized)
- **Labels:** `ols.openshift.io/source: upgrade-watcher`,
  `ols.openshift.io/current-version`, `ols.openshift.io/target-version`

Run the adapter:

```bash
go run ./examples/adapters/upgrade/ \
  --namespace=openshift-lightspeed \
  --workflow=upgrade \
  --poll-interval=1h
```

## Advisory Variant

To assess upgrade risk without executing, use a `workflowOverride`:

```yaml
spec:
  workflow: upgrade
  workflowOverride:
    execution:
      skip: true
    verification:
      skip: true
```

This runs the upgrade analyzer for risk assessment only. Useful for
planning upgrade windows or getting a pre-flight check before the
maintenance window.

See also: examples/remediation.md (standard remediation pattern), examples/advisory.md (advisory-only pattern)
