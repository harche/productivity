# Examples

Annotated YAML examples for common use cases. Each explains
*why* the configuration is set that way.

## Workflow Patterns

|remediation.md — Standard auto-remediation: analyze → execute → verify (integrator)
|advisory.md — Analysis-only: diagnose without taking action (integrator)
|gitops.md — GitOps: analyze, user applies via git, agent verifies (integrator)
|acs.md — ACS violation triggers proposal pipeline (integrator)
|trust-mode.md — Full auto: skip analysis, execute immediately (integrator)
|upgrade.md — Cluster upgrade: risk assessment → upgrade → verify (integrator)

## Live Adapter Examples

Each adapter in `examples/adapters/` is self-contained with code, skills,
deploy script, and CLAUDE.md. Run any of them end-to-end:

| Adapter | Deploy Command | What It Demos |
|---------|---------------|---------------|
| `alertmanager/` | `bash examples/adapters/alertmanager/deploy.sh` | JVM OOMKill → alert → proposal → fix |
| `acs/` | `bash examples/adapters/acs/deploy.sh` | Image CVE → ACS violation → proposal |
| `gitops/` | `bash examples/adapters/gitops/deploy.sh` | ArgoCD-managed namespace remediation |
| `ossm/` | `bash examples/adapters/ossm/deploy.sh` | Service Mesh integration |
| `upgrade/` | `go run ./examples/adapters/upgrade/` | Cluster upgrade risk assessment + execution |

Each adapter's `CLAUDE.md` has the full walkthrough.
