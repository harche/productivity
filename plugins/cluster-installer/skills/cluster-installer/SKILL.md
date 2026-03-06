---
name: cluster-installer
description: Create, destroy, and manage Kubernetes and OpenShift clusters. Supports kind (local), GKE (Google Kubernetes Engine), and OpenShift on GCP. Use when the user wants to install, create, destroy, or list clusters of any type.
allowed-tools: Bash(kind:*) Bash(gcloud:*) Bash(kubectl:*) Bash(oc:*) Bash(${CLAUDE_PLUGIN_ROOT}/ocp-install.sh:*) Bash(curl:*) Bash(export:*)
---

# Cluster Installer

Create, manage, and destroy Kubernetes and OpenShift clusters.

## Cluster Types

| Type | Tool | Where | Use Case |
|------|------|-------|----------|
| **kind** | `kind` | Local (Docker) | Fast local dev/test, CI, quick experiments |
| **GKE** | `gcloud` | Google Cloud | Production-grade Kubernetes on GCP |
| **OpenShift** | `ocp-install.sh` | Google Cloud | OpenShift Container Platform on GCP |

## Quick Start

### kind (local cluster)

```bash
# Create a single-node cluster
kind create cluster --name my-cluster

# Create with specific k8s version
kind create cluster --name my-cluster --image kindest/node:v1.31.0

# List clusters
kind get clusters

# Set kubeconfig
kubectl cluster-info --context kind-my-cluster

# Delete
kind delete cluster --name my-cluster
```

### GKE (Google Kubernetes Engine)

```bash
# Create a cluster
gcloud container clusters create my-cluster \
  --project=openshift-gce-devel \
  --region=us-central1 \
  --num-nodes=3

# Get credentials
gcloud container clusters get-credentials my-cluster \
  --project=openshift-gce-devel \
  --region=us-central1

# List clusters
gcloud container clusters list --project=openshift-gce-devel

# Delete
gcloud container clusters delete my-cluster \
  --project=openshift-gce-devel \
  --region=us-central1
```

### OpenShift on GCP

```bash
# Download installer
${CLAUDE_PLUGIN_ROOT}/ocp-install.sh download 4.21.3

# Create a cluster (types: regular, sno, gpu, sno-cpu)
${CLAUDE_PLUGIN_ROOT}/ocp-install.sh create 4.21.3 regular

# List clusters
${CLAUDE_PLUGIN_ROOT}/ocp-install.sh list

# Set kubeconfig
eval $(${CLAUDE_PLUGIN_ROOT}/ocp-install.sh kubeconfig 4.21.3 cluster1)

# Destroy
${CLAUDE_PLUGIN_ROOT}/ocp-install.sh destroy 4.21.3 cluster1
```

## Choosing a Cluster Type

- Need a cluster in **seconds** for local testing? → **kind**
- Need **upstream Kubernetes** on real infrastructure? → **GKE**
- Need **OpenShift** features (operators, routes, machine sets, GPU nodes)? → **OpenShift**

## References

Detailed setup and configuration for each cluster type:

* **kind** — [references/kind.md](references/kind.md) — Multi-node, custom configs, ingress, registry, port mappings
* **GKE** — [references/gke.md](references/gke.md) — Machine types, node pools, autoscaling, GPU nodes, private clusters
* **OpenShift** — [references/openshift.md](references/openshift.md) — Cluster types (regular, SNO, GPU), debug, download, full lifecycle

## Important

- **Always confirm with the user before creating or destroying clusters.**
- kind clusters are local and free. GKE and OpenShift clusters incur cloud costs.
- GPU instances (GKE and OpenShift) are expensive — remind the user to destroy when done.
- OpenShift cluster creation takes 30-45 minutes. kind takes seconds. GKE takes 5-10 minutes.
