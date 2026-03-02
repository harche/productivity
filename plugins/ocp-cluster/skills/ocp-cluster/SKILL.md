---
name: ocp-cluster
description: Create, destroy, and manage OpenShift clusters on GCP. Supports regular, SNO, GPU, and SNO-CPU cluster types across OCP versions. Use when the user wants to install, create, destroy, or list OpenShift clusters.
allowed-tools: Bash(ocp-install:*) Bash(openshift-install:*) Bash(oc:*) Bash(curl:*) Bash(export:*)
---

# OpenShift Cluster Manager

Manage OpenShift clusters using the `ocp-install.sh` script.

## Script location

When installed as a plugin, use `${CLAUDE_PLUGIN_ROOT}`:

```bash
${CLAUDE_PLUGIN_ROOT}/ocp-install.sh <command>
```

## Commands

### Download installer for a version

```bash
${CLAUDE_PLUGIN_ROOT}/ocp-install.sh download <version>
```

Downloads `openshift-install` from `https://amd64.ocp.releases.ci.openshift.org/` artifacts.
Binary is saved to `~/clusters/<major.minor>/<version>/openshift-install`.

### Create a cluster

```bash
${CLAUDE_PLUGIN_ROOT}/ocp-install.sh create <version> <type> [cluster-name]
```

Types:
- `regular` — 3 control-plane + 3 workers (standard GCP instances)
- `sno` — Single Node OpenShift with GPU (a2-highgpu-2g, zone us-central1-f)
- `gpu` — 3 control-plane + 3 GPU workers (a2-highgpu-1g, zone us-central1-f)
- `sno-cpu` — Single Node OpenShift, CPU only (cpuPartitioningMode: AllNodes)

If cluster-name is omitted, one is auto-generated as `$USER<type><random>`.

The script:
1. Reads pull secret from macOS Keychain (`OCP_PULL_SECRET`)
2. Generates `install-config.yaml` from built-in templates
3. Shows a summary and asks for confirmation
4. Runs `openshift-install create cluster`
5. Prints the KUBECONFIG path on success

### Debug a failed installation

```bash
${CLAUDE_PLUGIN_ROOT}/ocp-install.sh debug <version> <cluster-dir>
```

Runs a full diagnostic:
1. **Local log analysis** — parses `.openshift_install.log` for errors, fatals, and failure patterns (bootstrap failure, timeouts, quota issues, SSH auth, resource conflicts)
2. **Log bundle inventory** — lists available `log-bundle-*.tar.gz` files with extract instructions
3. **GCP diagnostics** (requires `gcloud`) — lists compute instances, serial console output from bootstrap and master nodes, Cloud Logging errors, firewall rules, and orphaned disks

### Destroy a cluster

```bash
${CLAUDE_PLUGIN_ROOT}/ocp-install.sh destroy <version> <cluster-dir>
```

Asks for confirmation before destroying.

### List clusters

```bash
${CLAUDE_PLUGIN_ROOT}/ocp-install.sh list [version]
```

Shows all clusters with their version, status (ACTIVE/DESTROYED/CONFIG/EMPTY), and path.

### Get kubeconfig

```bash
eval $(${CLAUDE_PLUGIN_ROOT}/ocp-install.sh kubeconfig <version> <cluster-dir>)
```

## Workflow example

```bash
# 1. Download the installer
${CLAUDE_PLUGIN_ROOT}/ocp-install.sh download 4.21.3

# 2. Create an SNO cluster
${CLAUDE_PLUGIN_ROOT}/ocp-install.sh create 4.21.3 sno

# 3. List clusters
${CLAUDE_PLUGIN_ROOT}/ocp-install.sh list

# 4. Set kubeconfig
eval $(${CLAUDE_PLUGIN_ROOT}/ocp-install.sh kubeconfig 4.21.3 cluster1)

# 5. Verify
oc get nodes
oc get co

# 6. Destroy when done
${CLAUDE_PLUGIN_ROOT}/ocp-install.sh destroy 4.21.3 cluster1
```

## Environment

- Platform: GCP (`openshift-gce-devel` project, `us-central1` region)
- Base domain: `gcp.devcluster.openshift.com`
- Pull secret: macOS Keychain (`OCP_PULL_SECRET`), falls back to `~/clusters/pull-secret-gcp.txt`
- SSH key: `~/.ssh/id_rsa.pub`
- Data directory: `~/clusters/<major.minor>/<full-version>/cluster<N>/`

## Important notes

- **Always confirm with the user** before creating or destroying clusters (the script also prompts)
- Cluster creation takes 30-45 minutes
- The `install-config.yaml` is consumed during install; a `.backup` copy is saved
- The download source is the CI release artifacts, not the official mirror
- GPU instances (a2-highgpu) are expensive — remind the user to destroy when done
