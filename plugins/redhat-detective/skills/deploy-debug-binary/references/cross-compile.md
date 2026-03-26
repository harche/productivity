# Cross-Compiling for RHCOS

RHCOS worker nodes run `linux/amd64`. If you are building from an arm64 Mac (Apple Silicon), you need to cross-compile using Docker with QEMU emulation.

## Why Not Build on the Node?

RHCOS is an immutable OS. It has no package manager (`dnf`/`yum` are not available), no development headers, and no Go toolchain. Building must happen off-cluster.

## Why Not Build a Static Binary?

RHCOS ships dynamically-linked binaries. The target binary must link against the same shared libraries (same sonames) as the RPM-installed version on RHCOS. A statically-linked binary might work but diverges from the production configuration and may miss features gated behind dynamic library detection (e.g., SELinux, seccomp, gpgme).

## Build Procedure

### 1. Create a Dockerfile

Use a base image with matching libraries. Debian Bookworm and Fedora both produce binaries with compatible sonames for RHCOS 9.x.

The binary-specific reference (e.g., `binaries/crio.md`) lists the exact `apt-get` or `dnf` packages and build tags needed.

```dockerfile
FROM --platform=linux/amd64 golang:<version>-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    <packages from binary-specific reference> \
    pkg-config make git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build/<project>
COPY . .

RUN make <target> && ldd <output-binary>
```

### 2. Build

```bash
docker build --platform linux/amd64 -f Dockerfile.cross -t <name>-cross .
```

This uses QEMU emulation on arm64 Mac. Expect builds to take 2-5x longer than native.

### 3. Extract the Binary

```bash
docker create --platform linux/amd64 --name extract <name>-cross
mkdir -p bin
docker cp extract:/build/<project>/<binary-path> ./bin/<binary-name>
docker rm extract
```

### 4. Verify

```bash
file ./bin/<binary-name>
# Should show: ELF 64-bit LSB executable, x86-64
```

## Determining the Go Version

Check `go.mod` in the source directory for the required Go version:

```bash
head -3 go.mod
```

Use the matching `golang:<version>-bookworm` Docker image.

## Determining Library Dependencies

SSH into the target node and check what the existing binary links against:

```bash
ldd $(which <binary>)
```

The cross-compiled binary must link against the same sonames. The `ldd` output from the Docker build (the `RUN ldd` step in the Dockerfile) should show matching library names.
