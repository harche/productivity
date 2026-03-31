---
name: deploy-debug-binary
description: Deploy a custom-built debug binary (CRI-O, crun, kubelet, etc.) to an OpenShift worker node running RHCOS. Use when the user wants to build, deploy, test, or replace a binary on a live OpenShift cluster for debugging or POC testing. Also trigger when the user mentions cross-compiling for RHCOS, replacing CRI-O on a node, bind-mounting binaries, testing a patched runtime on an OpenShift cluster, RHCOS layered images, or rolling out a custom OS image via MachineConfig.
allowed-tools: Bash(*), Read, Write, Edit, Glob, Grep
---

# Deploy Debug Binary to OpenShift Worker Node

Deploy a custom-built binary to an OpenShift cluster worker node running RHCOS (Red Hat Enterprise Linux CoreOS). RHCOS has an immutable `/usr` filesystem, so binaries are deployed via bind mounts that shadow the originals without modifying the rootfs.

## Prerequisites

- `oc` CLI authenticated to the target cluster
- `docker` or `podman` with cross-platform build support (`--platform linux/amd64`)
- SSH bastion deployed on the cluster — see [ssh-bastion.md](references/ssh-bastion.md)

## Workflow Overview

The deployment follows four phases. Read the relevant reference for detailed commands.

### Phase 1: Build

Cross-compile the binary for the target architecture (typically `linux/amd64`) using a Docker container that matches the target OS libraries. The binary must be dynamically linked against compatible library versions (same sonames as RHCOS).

Read [cross-compile.md](references/cross-compile.md) for the Docker-based build procedure.

### Phase 2: Access

Reach the worker node via the SSH bastion. RHCOS nodes are not directly accessible; the bastion pod provides a proxy. You need to discover which SSH key was used at cluster install time.

Read [ssh-bastion.md](references/ssh-bastion.md) for SSH setup and key discovery.

### Phase 3: Deploy

Transfer the binary, verify it works (`-h` and `ldd`), then cordon/drain the node, bind-mount, and restart the service. This phase has the most gotchas around SELinux, systemd, and service dependencies.

Read [deploy.md](references/deploy.md) for the full procedure.

For binary-specific details (build tags, library dependencies, systemd units, config drop-ins):
- CRI-O: read [crio.md](references/binaries/crio.md)

### Phase 4: Rollback

Unmount the bind mount, remove config drop-ins, restart the service. The original binary is untouched.

Read [rollback.md](references/rollback.md) for rollback steps.

### Alternative: Cluster-Wide via Layered Image

For deploying to **all nodes** in a pool (not just one), or when the binary must **survive reboots**, use RHCOS image layering instead of bind mounts. This builds a custom OS image with your binary baked in, and the MCO rolls it out across the cluster.

Read [layered-image.md](references/layered-image.md) for the full procedure.

This is also how customers would deploy a custom binary in production — layered image for the binary, then a MachineConfig to drop the configuration that enables the feature.

## Safety Rules

These are non-negotiable. Skipping any of these can take a node out of the cluster.

1. **Verify SSH bastion connectivity first.** Before building or deploying anything, confirm you can reach the target worker node via the bastion. Run a simple command like `uname -a` over SSH. If you can't reach the node, nothing else matters. See [ssh-bastion.md](references/ssh-bastion.md).

2. **Always preflight-test the binary** before deploying. SCP it to `/home/core/`, run `ldd` to verify libraries resolve, and run `<binary> -h` or `--version` to confirm it loads. If either fails, do not proceed.

3. **Always cordon and drain first.** Never restart a container runtime on a node with running workloads.

4. **Always test on ONE worker node.** Keep at least one healthy worker to maintain cluster capacity.

5. **Always set the SELinux context** before bind-mounting. Use `chcon --reference=<original> <new-binary>`. Without the correct context (`container_runtime_exec_t` for CRI-O), systemd will refuse to execute the binary with `Permission denied`.

6. **Know how to rollback** before you deploy. The rollback is: unmount, restart service. Read [rollback.md](references/rollback.md) before starting.

## Quick Reference

| Step | Command |
|------|---------|
| Check node OS | `oc get nodes -o wide` |
| Check current binary | SSH in, `<binary> --version` |
| Cordon node | `oc adm cordon <node>` |
| Drain node | `oc adm drain <node> --ignore-daemonsets --delete-emptydir-data` |
| Uncordon node | `oc adm uncordon <node>` |
| Verify node health | `oc get node <node>` (wait for Ready) |
