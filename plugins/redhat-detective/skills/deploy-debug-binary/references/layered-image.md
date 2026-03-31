# Deploying via RHCOS Layered Image

For cluster-wide deployment that survives reboots, use RHCOS image layering instead of bind mounts. This creates a custom OS image with your binary baked in, and the MCO rolls it out to all nodes in a machine config pool.

**Use bind mounts** for quick single-node testing. **Use layered images** when you need the binary on all nodes, or need it to persist across reboots.

## Overview

1. Get the base RHCOS image digest from the cluster
2. Build a layered image that replaces the target binary
3. Push to a registry the cluster can pull from
4. Apply a `MachineConfig` with `osImageURL` pointing to the layered image
5. MCO drains, reboots each node with the new image

## Step 1: Get the Base RHCOS Image

```bash
BASE_IMAGE=$(oc adm release info --image-for rhel-coreos)
echo "$BASE_IMAGE"
# quay.io/openshift-release-dev/ocp-v4.0-art-dev@sha256:...
```

Always use the digest form (`@sha256:...`), not a tag.

## Step 2: Build the Layered Image

You can build either locally (cross-compile) or on a worker node (native). Building on a beefy worker node with `podman` is faster since it avoids QEMU emulation.

### Option A: Build on a Worker Node (Recommended)

The binary must already be on the worker (e.g., from a prior bind-mount deployment or SCP).

```bash
# Create Containerfile on the worker
ssh core@${WORKER} "cat > /home/core/Containerfile <<EOF
FROM ${BASE_IMAGE}
COPY <binary> /usr/bin/<binary>
RUN chmod 755 /usr/bin/<binary> && bootc container lint
EOF"

# Build using the node's pull secrets
ssh core@${WORKER} "sudo podman build \
  --authfile /var/lib/kubelet/config.json \
  -t <image-name>:latest \
  -f /home/core/Containerfile /home/core/"
```

The `--authfile /var/lib/kubelet/config.json` gives podman access to pull the base RHCOS image from the cluster's registry.

`bootc container lint` is required — it validates the image is a valid bootable container. The build will warn about sysusers entries; warnings are OK, errors are not.

### Option B: Build Locally with Docker

```bash
# Dockerfile.layered
FROM ${BASE_IMAGE}
COPY bin/<binary> /usr/bin/<binary>
RUN chmod 755 /usr/bin/<binary> && bootc container lint
```

```bash
docker build --platform linux/amd64 \
  -f Dockerfile.layered -t <image-name>:latest .
```

You'll need the cluster pull secret in `~/.docker/config.json` to pull the base image.

## Step 3: Push to a Registry

### Using the OpenShift Internal Registry

The internal registry is the simplest option — no external registry needed. However, there are important gotchas.

**Expose the registry route** (if not already exposed):

```bash
oc patch configs.imageregistry.operator.openshift.io/cluster \
  --patch '{"spec":{"defaultRoute":true}}' --type=merge

REGISTRY_ROUTE=$(oc get route -n openshift-image-registry default-route \
  -o jsonpath='{.spec.host}')
```

**Critical: Push to the `openshift-machine-config-operator` namespace.** The MCD uses `/etc/mco/internal-registry-pull-secret.json` to pull images. This secret only has access to `openshift-*` namespaces. If you push to a custom namespace (e.g., `crio-custom`), the MCD will fail with `authentication required`.

```bash
# Create a service account with push permissions IN the MCO namespace
oc create sa image-pusher -n openshift-machine-config-operator
oc policy add-role-to-user registry-editor \
  -z image-pusher -n openshift-machine-config-operator

# Get a push token
PUSH_TOKEN=$(oc create token image-pusher \
  -n openshift-machine-config-operator --duration=1h)

# Login and push (from the worker node or locally)
sudo podman login --tls-verify=false \
  -u image-pusher -p "${PUSH_TOKEN}" ${REGISTRY_ROUTE}

sudo podman tag localhost/<image-name>:latest \
  ${REGISTRY_ROUTE}/openshift-machine-config-operator/<image-name>:latest

sudo podman push --tls-verify=false \
  ${REGISTRY_ROUTE}/openshift-machine-config-operator/<image-name>:latest
```

**Get the digested image reference** (required for MachineConfig):

```bash
oc get istag -n openshift-machine-config-operator <image-name>:latest \
  -o jsonpath='{.image.dockerImageReference}'
# image-registry.openshift-image-registry.svc:5000/openshift-machine-config-operator/<image-name>@sha256:...
```

### Using an External Registry (quay.io, etc.)

Push to any registry the cluster can pull from. Make sure the cluster's global pull secret includes credentials for that registry.

```bash
podman push <image-name>:latest quay.io/<org>/<image-name>:latest
```

Get the digest:

```bash
podman inspect --format='{{.Digest}}' quay.io/<org>/<image-name>:latest
```

## Step 4: Apply the MachineConfig

```yaml
apiVersion: machineconfiguration.openshift.io/v1
kind: MachineConfig
metadata:
  labels:
    machineconfiguration.openshift.io/role: worker
  name: 99-worker-custom-os-image
spec:
  osImageURL: image-registry.openshift-image-registry.svc:5000/openshift-machine-config-operator/<image-name>@sha256:<digest>
```

```bash
oc apply -f machineconfig-layered.yaml
```

The MCO will:
1. Render a new machine config
2. Cordon and drain each node (one at a time)
3. Run `rpm-ostree rebase` to the new image
4. Reboot the node
5. Uncordon when healthy

Monitor progress:

```bash
oc get mcp worker -w
# UPDATED=False, UPDATING=True while rolling out
# UPDATED=True, UPDATING=False when complete

oc get nodes
# SchedulingDisabled = node being updated
# NotReady = node rebooting
```

## Step 5: Add Configuration via MachineConfig

After the layered image is rolled out, drop configuration files via a separate MachineConfig. This is how customers enable features — the binary is deployed first, then the config turns it on.

```yaml
apiVersion: machineconfiguration.openshift.io/v1
kind: MachineConfig
metadata:
  labels:
    machineconfiguration.openshift.io/role: worker
  name: 99-worker-<feature>-config
spec:
  config:
    ignition:
      version: 3.2.0
    storage:
      files:
      - contents:
          source: data:text/plain;charset=utf-8;base64,<base64-encoded-config>
        mode: 0644
        overwrite: true
        path: <config-drop-in-path>
```

Generate base64 content:

```bash
echo -n '[crio.runtime]
inject_gomaxprocs = 4
' | base64
```

This triggers another MCO rollout (drain + reboot per node).

## Rollback

Delete the MachineConfig to revert all nodes to the base RHCOS image:

```bash
oc delete mc 99-worker-custom-os-image
```

The MCO will drain and reboot each node back to the stock OS image.

## Troubleshooting

### MCD fails with "authentication required"

The image is in a namespace the MCD can't pull from. Push to `openshift-machine-config-operator` namespace instead. See Step 3.

### MCP stuck in Degraded after fixing the image

The MCD caches the old rendered config and keeps retrying the failed image URL. Fix:

1. Delete the old MachineConfig
2. Wait for a new rendered config to appear: `oc get mc --sort-by=.metadata.creationTimestamp`
3. Apply the corrected MachineConfig
4. If the MCD is still stuck, force-annotate the node to the new rendered config:

```bash
oc annotate node <node> \
  machineconfiguration.openshift.io/desiredConfig=<new-rendered-mc> \
  --overwrite
```

5. If still stuck, delete the MCD pod to force a restart:

```bash
oc delete pod -n openshift-machine-config-operator \
  -l k8s-app=machine-config-daemon \
  --field-selector spec.nodeName=<node> --force --grace-period=0
```

### bootc container lint fails

The layered image must be a valid bootable container. Common issues:
- Missing `/usr/lib/os-release`
- Broken symlinks in `/usr`
- Package conflicts with base image RPMs

### Node stays NotReady after reboot

Check kubelet and CRI-O status via SSH:

```bash
ssh core@${WORKER} "sudo systemctl is-active crio kubelet"
ssh core@${WORKER} "sudo journalctl -u crio --no-pager -n 20"
```

## Example: CRI-O Layered Image

Full example replacing CRI-O with a custom build:

```bash
# Get base image
BASE_IMAGE=$(oc adm release info --image-for rhel-coreos)

# Containerfile
cat > Containerfile <<EOF
FROM ${BASE_IMAGE}
COPY crio /usr/bin/crio
RUN chmod 755 /usr/bin/crio && bootc container lint
EOF

# Build on worker (binary already at /home/core/crio)
ssh core@${WORKER} "sudo podman build \
  --authfile /var/lib/kubelet/config.json \
  -t crio-custom:latest -f /home/core/Containerfile /home/core/"

# Push to internal registry (MCO namespace)
PUSH_TOKEN=$(oc create token image-pusher -n openshift-machine-config-operator --duration=1h)
ssh core@${WORKER} "sudo podman login --tls-verify=false \
  -u image-pusher -p '${PUSH_TOKEN}' ${REGISTRY_ROUTE} && \
  sudo podman tag localhost/crio-custom:latest \
    ${REGISTRY_ROUTE}/openshift-machine-config-operator/crio-custom:latest && \
  sudo podman push --tls-verify=false \
    ${REGISTRY_ROUTE}/openshift-machine-config-operator/crio-custom:latest"

# Get digest and apply MachineConfig
IMAGE=$(oc get istag -n openshift-machine-config-operator crio-custom:latest \
  -o jsonpath='{.image.dockerImageReference}')

cat <<EOF | oc apply -f -
apiVersion: machineconfiguration.openshift.io/v1
kind: MachineConfig
metadata:
  labels:
    machineconfiguration.openshift.io/role: worker
  name: 99-worker-crio-custom
spec:
  osImageURL: ${IMAGE}
EOF

# Monitor: oc get mcp worker -w
```
