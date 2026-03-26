# Deploying the Binary

This is the critical phase. Follow the steps in order. Do not skip the preflight check.

## Step 1: Preflight Check

After SCPing the binary to `/home/core/`, verify it works before touching anything:

```bash
# Check libraries resolve
ssh core@${WORKER} "ldd /home/core/<binary>"

# Check it runs
ssh core@${WORKER} "/home/core/<binary> -h"
# or
ssh core@${WORKER} "/home/core/<binary> --version"
```

If `ldd` shows `not found` for any library, the binary was built against incompatible versions. Go back to the cross-compile step. If `-h` fails, check the error — it may be an architecture mismatch, missing library, or permissions issue.

## Step 2: Set SELinux Context

RHCOS runs SELinux in enforcing mode. Systemd checks the SELinux context of binaries before executing them. A binary in `/home/core/` has `user_home_t` context, which systemd will reject.

Copy the context from the original binary:

```bash
ssh core@${WORKER} "sudo chcon --reference=<original-path> /home/core/<binary>"
```

Verify:

```bash
ssh core@${WORKER} "ls -laZ /home/core/<binary> <original-path>"
```

Both should show the same context (e.g., `system_u:object_r:container_runtime_exec_t:s0` for CRI-O).

Without this step, systemd will fail with:
```
Failed to locate executable <path>: Permission denied
```

## Step 3: Cordon and Drain

Prevent new pods from being scheduled and evict existing workloads:

```bash
oc adm cordon <node>
oc adm drain <node> --ignore-daemonsets --delete-emptydir-data --timeout=120s
```

If drain times out on a stuck pod, check which pod and force-delete if appropriate:

```bash
oc get pods --all-namespaces --field-selector spec.nodeName=<node> | grep Terminating
oc delete pod <pod> -n <namespace> --force --grace-period=0
```

## Step 4: Stop, Mount, Start

```bash
# Stop the service
ssh core@${WORKER} "sudo systemctl stop <service>"

# Bind mount the new binary over the original
ssh core@${WORKER} "sudo mount --bind /home/core/<binary> <original-path>"

# Start the service
ssh core@${WORKER} "sudo systemctl start <service>"

# Verify it started
ssh core@${WORKER} "sudo systemctl is-active <service>"

# Verify the version
ssh core@${WORKER} "sudo <binary> --version"
```

The bind mount shadows the original binary without modifying it. The original remains intact underneath.

## Step 5: Restart Dependent Services

Some binaries have dependent services that lose their connection when the primary service restarts. Check the binary-specific reference for which services need restarting.

```bash
ssh core@${WORKER} "sudo systemctl restart <dependent-service>"
ssh core@${WORKER} "sudo systemctl is-active <dependent-service>"
```

## Step 6: Verify Node Health

```bash
# Wait for the node to become Ready
oc get node <node>
```

If the node stays `NotReady`, check the dependent services. A common issue is forgetting to restart a dependent service (e.g., kubelet after CRI-O restart).

## Step 7: Uncordon

```bash
oc adm uncordon <node>
```

## Step 8: Optional Config Drop-ins

To add configuration (e.g., feature flags), write a drop-in file and restart:

```bash
ssh core@${WORKER} "sudo tee <config-drop-in-path> <<'EOF'
<config-content>
EOF"

ssh core@${WORKER} "sudo systemctl restart <service>"
```

## Updating an Already-Deployed Binary

If you need to deploy a newer version and the bind mount is already in place:

1. SCP the new binary to a **different filename** (the mounted path is busy)
2. Stop the service
3. Unmount the old bind mount
4. Rename the new file to the expected name
5. Set SELinux context
6. Mount and start

```bash
scp <new-binary> core@${WORKER}:/home/core/<binary>-v2
ssh core@${WORKER} "sudo systemctl stop <service> && \
  sudo umount <original-path> && \
  mv /home/core/<binary>-v2 /home/core/<binary> && \
  chmod +x /home/core/<binary> && \
  sudo chcon --reference=<original-path> /home/core/<binary> && \
  sudo mount --bind /home/core/<binary> <original-path> && \
  sudo systemctl start <service>"
```
