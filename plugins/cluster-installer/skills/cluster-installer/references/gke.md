# GKE (Google Kubernetes Engine)

Create and manage production-grade Kubernetes clusters on Google Cloud.

## Prerequisites

- `gcloud` CLI installed and authenticated (`gcloud auth login`)
- A GCP project with Kubernetes Engine API enabled
- `kubectl` installed

## Default Environment

```
Project:  openshift-gce-devel
Region:   us-central1
```

## Basic Usage

```bash
# Create a standard cluster
gcloud container clusters create my-cluster \
  --project=openshift-gce-devel \
  --region=us-central1 \
  --num-nodes=3

# Get credentials (sets kubectl context)
gcloud container clusters get-credentials my-cluster \
  --project=openshift-gce-devel \
  --region=us-central1

# List clusters
gcloud container clusters list --project=openshift-gce-devel

# Describe a cluster
gcloud container clusters describe my-cluster \
  --project=openshift-gce-devel \
  --region=us-central1

# Delete a cluster
gcloud container clusters delete my-cluster \
  --project=openshift-gce-devel \
  --region=us-central1
```

## Cluster Configuration

### Machine types

```bash
# Small (dev/test)
gcloud container clusters create dev-cluster \
  --project=openshift-gce-devel \
  --region=us-central1 \
  --machine-type=e2-medium \
  --num-nodes=2

# Standard
gcloud container clusters create std-cluster \
  --project=openshift-gce-devel \
  --region=us-central1 \
  --machine-type=e2-standard-4 \
  --num-nodes=3

# High-memory
gcloud container clusters create mem-cluster \
  --project=openshift-gce-devel \
  --region=us-central1 \
  --machine-type=e2-highmem-4 \
  --num-nodes=3
```

### Specific Kubernetes version

```bash
# List available versions
gcloud container get-server-config \
  --project=openshift-gce-devel \
  --region=us-central1 \
  --format="yaml(validMasterVersions)"

# Create with specific version
gcloud container clusters create my-cluster \
  --project=openshift-gce-devel \
  --region=us-central1 \
  --cluster-version=1.31.1-gke.1678000
```

### Zonal vs regional

```bash
# Zonal cluster (single zone, cheaper)
gcloud container clusters create my-cluster \
  --project=openshift-gce-devel \
  --zone=us-central1-a \
  --num-nodes=3

# Regional cluster (HA across zones, default)
gcloud container clusters create my-cluster \
  --project=openshift-gce-devel \
  --region=us-central1 \
  --num-nodes=1  # 1 per zone = 3 total
```

## Node Pools

```bash
# Add a node pool
gcloud container node-pools create gpu-pool \
  --cluster=my-cluster \
  --project=openshift-gce-devel \
  --region=us-central1 \
  --machine-type=a2-highgpu-1g \
  --accelerator=type=nvidia-tesla-a100,count=1 \
  --num-nodes=1

# List node pools
gcloud container node-pools list \
  --cluster=my-cluster \
  --project=openshift-gce-devel \
  --region=us-central1

# Resize a node pool
gcloud container clusters resize my-cluster \
  --node-pool=default-pool \
  --num-nodes=5 \
  --project=openshift-gce-devel \
  --region=us-central1

# Delete a node pool
gcloud container node-pools delete gpu-pool \
  --cluster=my-cluster \
  --project=openshift-gce-devel \
  --region=us-central1
```

## Autoscaling

```bash
# Create with cluster autoscaler
gcloud container clusters create auto-cluster \
  --project=openshift-gce-devel \
  --region=us-central1 \
  --enable-autoscaling \
  --min-nodes=1 \
  --max-nodes=10

# Enable autoscaling on existing cluster
gcloud container clusters update my-cluster \
  --project=openshift-gce-devel \
  --region=us-central1 \
  --enable-autoscaling \
  --min-nodes=1 \
  --max-nodes=10
```

## GPU Nodes

```bash
# Create cluster with GPU node pool
gcloud container clusters create gpu-cluster \
  --project=openshift-gce-devel \
  --zone=us-central1-f \
  --num-nodes=1

gcloud container node-pools create gpu-pool \
  --cluster=gpu-cluster \
  --project=openshift-gce-devel \
  --zone=us-central1-f \
  --machine-type=a2-highgpu-1g \
  --accelerator=type=nvidia-tesla-a100,count=1 \
  --num-nodes=1

# Install NVIDIA GPU drivers
kubectl apply -f https://raw.githubusercontent.com/GoogleCloudPlatform/container-engine-accelerators/master/nvidia-driver-installer/cos/daemonset-preloaded-latest.yaml
```

## Private Clusters

```bash
# Create a private cluster (no public IPs on nodes)
gcloud container clusters create private-cluster \
  --project=openshift-gce-devel \
  --region=us-central1 \
  --enable-private-nodes \
  --enable-ip-alias \
  --master-ipv4-cidr=172.16.0.0/28
```

## Tips

- Regional clusters spread nodes across zones for HA — use `--num-nodes=1` to get 1 per zone (3 total).
- Zonal clusters are cheaper but have a single point of failure.
- GKE creates a `default-pool` automatically. Use `--node-pool` to manage additional pools.
- GPU nodes require the NVIDIA driver DaemonSet and are only available in specific zones.
- Cluster creation takes 5-10 minutes.
- Use `--quiet` to skip confirmation prompts in scripts.
