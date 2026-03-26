# CRI-O Binary Reference

## Binary Details

| Property | Value |
|----------|-------|
| Binary path | `/usr/bin/crio` |
| Systemd unit | `crio.service` |
| Dependent service | `kubelet.service` (must restart after CRI-O restart) |
| RPM package | `cri-o` |
| SELinux context | `system_u:object_r:container_runtime_exec_t:s0` |
| Config drop-in dir | `/etc/crio/crio.conf.d/` |
| Linkmode | dynamic |

## Build Dependencies (Debian/Bookworm)

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    libseccomp-dev \
    libgpgme-dev \
    libassuan-dev \
    libgpg-error-dev \
    libselinux1-dev \
    pkg-config \
    make \
    git \
    && rm -rf /var/lib/apt/lists/*
```

## Dynamic Libraries

CRI-O links against these shared libraries. The cross-compiled binary must show the same sonames in `ldd` output:

```
libseccomp.so.2
libgpgme.so.11
libassuan.so.0
libgpg-error.so.0
libc.so.6
```

## Build Command

```bash
make bin/crio
```

The Makefile auto-detects build tags based on available libraries. Expected tags on RHCOS-compatible builds:

```
containers_image_ostree_stub
exclude_graphdriver_btrfs
btrfs_noversion
seccomp
selinux
```

## Go Version

Check `go.mod` for the required Go version. Use the matching `golang:<version>-bookworm` Docker image.

## Example Dockerfile

```dockerfile
FROM --platform=linux/amd64 golang:1.26-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    libseccomp-dev libgpgme-dev libassuan-dev \
    libgpg-error-dev libselinux1-dev \
    pkg-config make git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build/cri-o
COPY . .

RUN make bin/crio && ldd bin/crio
```

## CRI-O Restart Behavior

Restarting CRI-O terminates all running containers on the node and disconnects kubelet from the container runtime. Kubelet will go inactive and the node will become `NotReady`.

After starting CRI-O, always restart kubelet:

```bash
sudo systemctl restart kubelet
```

Wait ~15 seconds, then verify the node returns to `Ready`.

## Config Drop-ins

CRI-O reads additional configuration from `/etc/crio/crio.conf.d/`. Files are processed in lexicographic order, later files override earlier ones.

Example (enabling GOMAXPROCS injection):

```bash
sudo tee /etc/crio/crio.conf.d/01-gomaxprocs.conf <<'EOF'
[crio.runtime]
inject_gomaxprocs = 4
EOF
sudo systemctl restart crio
```

## Verifying the Deployment

```bash
# Check version and build info
sudo crio --version

# Check it's running
sudo systemctl is-active crio

# Check kubelet is connected
sudo systemctl is-active kubelet

# Check node status (from your workstation)
oc get node <node-name>

# Check CRI-O logs for errors
sudo journalctl -u crio --no-pager -n 20
```
