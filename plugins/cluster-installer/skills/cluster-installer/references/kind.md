# kind (Kubernetes in Docker)

Create local Kubernetes clusters using Docker containers as nodes. Fast, lightweight, and free.

## Prerequisites

- Docker running locally
- `kind` CLI installed (`brew install kind`)
- `kubectl` installed (`brew install kubectl`)

## Basic Usage

```bash
# Create default cluster (single control-plane node)
kind create cluster

# Create with a name
kind create cluster --name dev

# Create with specific Kubernetes version
kind create cluster --name dev --image kindest/node:v1.31.0

# List clusters
kind get clusters

# Get kubeconfig
kind get kubeconfig --name dev

# Delete cluster
kind delete cluster --name dev

# Delete all clusters
kind delete clusters --all
```

## Available Node Images

Find images at https://github.com/kubernetes-sigs/kind/releases. Common versions:

```bash
kind create cluster --image kindest/node:v1.31.0
kind create cluster --image kindest/node:v1.30.0
kind create cluster --image kindest/node:v1.29.0
```

## Custom Cluster Configurations

Create a config file and pass it with `--config`:

### Multi-node cluster

```yaml
# kind-config.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
- role: worker
- role: worker
```

```bash
kind create cluster --name multi --config kind-config.yaml
```

### HA control plane (3 control-plane + 3 workers)

```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
- role: control-plane
- role: control-plane
- role: worker
- role: worker
- role: worker
```

### Port mappings (expose services on host)

```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 30000
    hostPort: 30000
    protocol: TCP
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP
```

### Ingress-ready cluster

```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP
```

Then install an ingress controller:

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=90s
```

### Local registry

```bash
# Create a registry container
docker run -d --restart=always -p 5001:5000 --network bridge --name kind-registry registry:2

# Create cluster connected to it
kind create cluster --name dev --config - <<EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
containerdConfigPatches:
- |-
  [plugins."io.containerd.grpc.v1.cri".registry.mirrors."localhost:5001"]
    endpoint = ["http://kind-registry:5001"]
EOF

# Connect registry to kind network
docker network connect kind kind-registry

# Use it
docker tag my-app:latest localhost:5001/my-app:latest
docker push localhost:5001/my-app:latest
kubectl run my-app --image=localhost:5001/my-app:latest
```

## Loading Images

```bash
# Load a local Docker image into the cluster (avoids pulling from a registry)
kind load docker-image my-app:latest --name dev

# Load from a tar archive
kind load image-archive my-app.tar --name dev
```

## Working with the Cluster

```bash
# Set kubectl context
kubectl cluster-info --context kind-dev

# Get nodes
kubectl get nodes

# Access the control plane
docker exec -it dev-control-plane bash
```

## Tips

- kind clusters start in **seconds** — ideal for quick experiments.
- Default cluster name is `kind` if `--name` is not specified.
- Each cluster gets its own kubeconfig context (`kind-<name>`).
- Node images are Docker images — they download once and are cached.
- For persistent storage, use a local-path provisioner (installed by default as the default StorageClass).
