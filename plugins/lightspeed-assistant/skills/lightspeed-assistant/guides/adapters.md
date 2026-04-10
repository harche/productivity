# Building a Webhook Adapter

An adapter receives external events and creates LightspeedProposal CRs.
The operator handles everything from there.

> **Confirm before applying.** Creating proposals and deploying adapters
> are write operations. Ask the user for confirmation before executing.

## What an Adapter Does

1. Receive webhook payload (AlertManager alert, ACS violation, custom event)
2. Extract relevant info (alert name, namespace, description)
3. Choose a workflow (remediation, advisory, gitops)
4. Create a LightspeedProposal CR
5. Handle dedup and cooldown

## Existing Adapters (use as reference)

All adapters are standalone Go programs in `examples/adapters/`:
- `examples/adapters/alertmanager/main.go` — AlertManager webhook (most complete reference)
- `examples/adapters/acs/main.go` — ACS violation webhook
- `examples/adapters/gitops/main.go` — GitOps-aware remediation
- `examples/adapters/upgrade/main.go` — Cluster upgrade trigger

Each adapter directory includes its own skills, Containerfile, deploy
script, and CLAUDE.md with a full walkthrough.

## Minimal Adapter: Create a Proposal

The minimum viable adapter creates a proposal from an event:

```go
proposal := &v1alpha1.LightspeedProposal{
    ObjectMeta: metav1.ObjectMeta{
        Name:      fmt.Sprintf("alert-%s", fingerprint),
        Namespace: "openshift-lightspeed",
        Labels: map[string]string{
            "ols.openshift.io/source": "my-adapter",
        },
    },
    Spec: v1alpha1.LightspeedProposalSpec{
        Request:          "Pod crashing in namespace production: OOMKilled",
        Workflow:         "remediation",
        TargetNamespaces: []string{"production"},
    },
}
```

## Dedup Pattern

Check if a proposal already exists for this event before creating:

```go
existing := &v1alpha1.LightspeedProposal{}
err := client.Get(ctx, types.NamespacedName{Name: name, Namespace: ns}, existing)
if err == nil {
    // already exists — skip
    return
}
// Create + handle AlreadyExists (create-only idempotency)
```

## Cooldown Pattern

Track last-created time per event fingerprint. Skip if within cooldown:

```go
if time.Since(lastCreated[fingerprint]) < cooldownDuration {
    return // too soon
}
```

## Workflow Selection

Choose workflow based on event context. AlertManager adapter example:

```go
// Check if namespace is ArgoCD-managed
annotations := namespace.GetAnnotations()
if _, ok := annotations["argocd.argoproj.io/managed-by"]; ok {
    workflow = "gitops-remediation"
} else {
    workflow = "remediation"
}
```

## Namespace Filtering

Restrict which namespaces your adapter creates proposals for:

```go
allowedNamespaces := map[string]bool{"production": true, "staging": true}
if !allowedNamespaces[targetNamespace] {
    return // not our responsibility
}
```

## Deployment

Each adapter deploys as a standalone Service in the cluster. See
the existing adapters' `deploy.sh` and `Containerfile` for the pattern.
Ensure NetworkPolicy allows traffic from the webhook source to your
adapter's port.

See also: examples/acs.md (ACS adapter walkthrough), api/proposal.md (spec fields)
