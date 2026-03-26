# SSH Bastion Access to RHCOS Nodes

RHCOS worker nodes are not directly accessible via SSH. The [ssh-bastion](https://github.com/eparis/ssh-bastion) project deploys a bastion pod that proxies SSH connections to cluster nodes.

## Setup

### 1. Deploy the Bastion

```bash
# Deploy the bastion pod and LoadBalancer service
oc apply -f https://raw.githubusercontent.com/eparis/ssh-bastion/master/deploy/deploy.yaml
oc wait --for=condition=available -n openshift-ssh-bastion deployment/ssh-bastion --timeout=120s
```

### 2. Discover the SSH Key

The cluster's `99-worker-ssh` MachineConfig contains the authorized public key. Match it against your local keys:

```bash
# Get the public key baked into the nodes
oc get machineconfig 99-worker-ssh -o jsonpath='{.spec.config.passwd.users[0].sshAuthorizedKeys[0]}'

# Compare against local keys
for f in ~/.ssh/*.pub; do echo "=== $f ===" && cat "$f"; done
```

The matching key is what you need. Common gotcha: GCP clusters often use `~/.ssh/google_compute_engine`, not `~/.ssh/id_rsa`.

### 3. Get the Bastion Host

```bash
BASTION_HOST=$(oc get service --all-namespaces -l run=ssh-bastion \
  -o go-template='{{ with (index (index .items 0).status.loadBalancer.ingress 0) }}{{ or .hostname .ip }}{{end}}')
echo "Bastion: $BASTION_HOST"
```

## Running Commands

Use raw SSH with the proxy command. The upstream `ssh-bastion.sh` script appends `sudo -i` which makes it unsuitable for non-interactive command execution.

```bash
SSH_KEY=~/.ssh/<matching-key>
BASTION_HOST=<from-above>
WORKER=<node-name>

ssh -i $SSH_KEY \
  -o StrictHostKeyChecking=no \
  -o ProxyCommand="ssh -i $SSH_KEY -A -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -W %h:%p core@${BASTION_HOST}" \
  core@${WORKER} "<command>"
```

## SCP (Transferring Files)

Use SCP with the same proxy command:

```bash
scp -i $SSH_KEY \
  -o StrictHostKeyChecking=no \
  -o ProxyCommand="ssh -i $SSH_KEY -A -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -W %h:%p core@${BASTION_HOST}" \
  ./local-file core@${WORKER}:/home/core/remote-file
```

The upstream [scp.sh](https://github.com/eparis/ssh-bastion/blob/master/scp.sh) script is also available but requires `SSH_KEY_PATH` to be set.

## Writable Paths on RHCOS

RHCOS has an immutable rootfs. You can only write to:
- `/home/core/` (user home)
- `/var/` (variable data)
- `/etc/` (configuration, overlayed)
- `/tmp/` (temporary)

Always SCP files to `/home/core/` first.

## Gotcha: SCP Fails on Bind-Mounted Files

If the target file is already bind-mounted (busy), SCP will fail with `Failure`. Copy to a new filename (e.g., `/home/core/binary-v2`), then swap after unmounting.
