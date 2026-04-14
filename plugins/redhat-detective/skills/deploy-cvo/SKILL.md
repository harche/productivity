---
name: deploy-cvo
description: Build and deploy a custom Cluster Version Operator (CVO) to an OpenShift test cluster. Use when the user wants to test CVO changes, deploy a development CVO image, build a release payload with a custom CVO binary, or set up the CVO lightspeed integration (proposals, readiness checks, skills image, workflows). Also trigger when the user mentions CVO image, release payload, oc adm release new, or testing CVO on a cluster.
allowed-tools: Bash(*), Read, Write, Edit, Glob, Grep
---

# Deploy Custom CVO to OpenShift Test Cluster

Build a custom CVO binary, package it into a release payload image, and deploy it to an OpenShift cluster for testing. Optionally deploy the Lightspeed integration (skills image, workflows, agents, system prompts).

## Prerequisites

- `oc` CLI authenticated to a **disposable test cluster** (never production)
- `docker` available and running (for image builds)
- `skopeo` available (for pushing to registries)
- Logged in to quay.io via `docker login quay.io`
- CVO source code checked out (current working directory)

## Information to Gather

Before starting, ask the user for:

1. **KUBECONFIG path** — path to the cluster's kubeconfig
2. **Quay.io repo** — e.g., `quay.io/username/cvo-dev` (needs two repos: one for the release payload, one for skills image)
3. **Whether to deploy Lightspeed integration** — workflows, agents, skills image

## Workflow Overview

### Phase 1: Build

Cross-compile the CVO binary and build the container image. Read [build.md](references/build.md) for details.

### Phase 2: Push and Create Release Payload

Push the CVO image to quay.io, then use `oc adm release new` to create a release payload that combines the existing cluster's release manifests with the custom CVO binary. Read [release-payload.md](references/release-payload.md) for details.

### Phase 3: Deploy to Cluster

Patch the CVO deployment to use the custom release payload. Read [deploy.md](references/deploy.md) for details.

### Phase 4: Deploy Lightspeed Integration (Optional)

Apply the Lightspeed manifests (system prompts, agents, workflows) and push the skills image. Read [lightspeed.md](references/lightspeed.md) for details.

### Phase 5: Verify

Confirm CVO is running with the correct binary and check for proposal creation. Read [verify.md](references/verify.md) for details.

## Safety Rules

1. **Never deploy to production clusters.** Only use disposable test clusters.
2. **Always verify the binary matches** after deployment. Compare file sizes between local build and pod.
3. **Use unique image tags** for each build (e.g., append timestamp). Tag reuse causes caching issues.
4. **Save the original CVO image** before patching so you can restore it.
5. **The CVO will reconcile manifests** from the release payload. If your custom manifests cause failures, the cluster may degrade.
6. **Feature-gated manifests** (LightspeedProposals) are excluded on Default feature set clusters. Bypass the gate in code for testing, but revert before committing.

## Quick Reference

| Step | Command |
|------|---------|
| Build binary | `CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o _output/linux/amd64/cluster-version-operator ./cmd/cluster-version-operator/` |
| Build image | `docker build --no-cache -f Dockerfile.dev -t localhost/cvo-dev:latest --platform linux/amd64 .` |
| Push to quay | `docker tag localhost/cvo-dev:latest quay.io/USER/cvo-dev:TAG && docker push quay.io/USER/cvo-dev:TAG` |
| Build release payload | `oc adm release new --from-release=CURRENT --to-image-base=quay.io/USER/cvo-dev:TAG --to-image=quay.io/USER/cvo-dev:release-TAG -a PULL_SECRET` |
| Deploy | `oc patch -n openshift-cluster-version deployment cluster-version-operator --type json --patch='[IMAGE_PATCH, ARG_PATCH]'` |
| Check pod | `oc get pods -n openshift-cluster-version -l k8s-app=cluster-version-operator` |
| Check binary | `oc exec -n openshift-cluster-version deployment/cluster-version-operator -- ls -la /usr/bin/cluster-version-operator` |
| Check proposals | `oc get lightspeedproposals -n openshift-lightspeed` |
| View proposal output | `oc get lightspeedproposal NAME -n openshift-lightspeed -o jsonpath='{.status}' \| python3 -m json.tool` |
| CVO logs | `oc logs -n openshift-cluster-version -l k8s-app=cluster-version-operator --tail=200` |
| Restore original | `oc patch -n openshift-cluster-version deployment cluster-version-operator --type json --patch='[ORIGINAL_IMAGE_PATCH, ORIGINAL_ARG_PATCH]'` |
