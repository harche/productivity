# Building CVO

## Build the Binary

CVO is a pure Go binary with no CGO dependencies. Cross-compile for linux/amd64:

```bash
CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o _output/linux/amd64/cluster-version-operator ./cmd/cluster-version-operator/
```

This must be run from the CVO source directory (the repo root with `go.mod`).

## Build the Container Image

CVO needs a minimal container image. Create a `Dockerfile.dev` if it doesn't exist:

```dockerfile
FROM registry.access.redhat.com/ubi9-minimal:latest
COPY _output/linux/amd64/cluster-version-operator /usr/bin/cluster-version-operator
COPY install /manifests
ENTRYPOINT ["/usr/bin/cluster-version-operator"]
```

Build with `--no-cache` to ensure the binary layer is fresh:

```bash
docker build --no-cache -f Dockerfile.dev -t localhost/cvo-dev:latest --platform linux/amd64 .
```

## Verify the Build

```bash
# Check binary exists and is linux/amd64
file _output/linux/amd64/cluster-version-operator
# Should show: ELF 64-bit LSB executable, x86-64

# Check image was built
docker images localhost/cvo-dev:latest
```

## Feature Gate Bypass (for testing)

If testing a feature gated behind `LightspeedProposals` on a non-TechPreview cluster, temporarily bypass the gate:

In `pkg/cvo/cvo.go`, find `shouldCreateLightspeedProposals()` and change it to:

```go
func (optr *Operator) shouldCreateLightspeedProposals() bool {
    // TODO: revert before committing — bypassing feature gate for testing
    return true
}
```

**Always revert this before committing.**
