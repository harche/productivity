# OpenShift Docs — Search & Read Reference

All commands use the `gh` CLI. See the [github](../../tools/github/SKILL.md) skill for general `gh` usage.

## Fetching the Documentation Index

Each version has an `AGENTS.md` file that maps topics to documentation files.

```bash
# Fetch the full index for version 4.22
gh api repos/harche/openshift-docs-md/contents/docs/4.22/AGENTS.md \
  -H "Accept: application/vnd.github.raw+json"

# Fetch for a different version
gh api repos/harche/openshift-docs-md/contents/docs/4.21/AGENTS.md \
  -H "Accept: application/vnd.github.raw+json"
```

## Searching the Index

Search the index to find which files cover a topic:

```bash
# Search for a topic (case-insensitive)
gh api repos/harche/openshift-docs-md/contents/docs/4.22/AGENTS.md \
  -H "Accept: application/vnd.github.raw+json" | grep -i "topic"

# Examples
gh api repos/harche/openshift-docs-md/contents/docs/4.22/AGENTS.md \
  -H "Accept: application/vnd.github.raw+json" | grep -i "network"

gh api repos/harche/openshift-docs-md/contents/docs/4.22/AGENTS.md \
  -H "Accept: application/vnd.github.raw+json" | grep -i "storage"

gh api repos/harche/openshift-docs-md/contents/docs/4.22/AGENTS.md \
  -H "Accept: application/vnd.github.raw+json" | grep -i "authentication"

gh api repos/harche/openshift-docs-md/contents/docs/4.22/AGENTS.md \
  -H "Accept: application/vnd.github.raw+json" | grep -i "install"

gh api repos/harche/openshift-docs-md/contents/docs/4.22/AGENTS.md \
  -H "Accept: application/vnd.github.raw+json" | grep -i "monitor"
```

## Reading Documentation Files

### Constructing File Paths

Index entries follow this format:
```
|section/subsection:{file1.md,file2.md}
```

Construct the `gh api` path:
```
repos/harche/openshift-docs-md/contents/docs/{VERSION}/{section}/{subsection}/{file.md}
```

Always include the raw content header:
```
-H "Accept: application/vnd.github.raw+json"
```

### Examples

```bash
# Read the networking overview
gh api repos/harche/openshift-docs-md/contents/docs/4.22/networking/index.md \
  -H "Accept: application/vnd.github.raw+json"

# Read about installing on AWS (IPI)
gh api repos/harche/openshift-docs-md/contents/docs/4.22/installing/installing_aws/ipi/installing-aws-default.md \
  -H "Accept: application/vnd.github.raw+json"

# Read about persistent storage with CSI
gh api repos/harche/openshift-docs-md/contents/docs/4.22/storage/container_storage_interface/persistent-storage-csi.md \
  -H "Accept: application/vnd.github.raw+json"

# Read about RBAC
gh api repos/harche/openshift-docs-md/contents/docs/4.22/authentication/using-rbac.md \
  -H "Accept: application/vnd.github.raw+json"

# Read the release notes
gh api repos/harche/openshift-docs-md/contents/docs/4.22/release_notes/ocp-4-22-release-notes.md \
  -H "Accept: application/vnd.github.raw+json"
```

## Listing Directory Contents

```bash
# List files in a directory
gh api repos/harche/openshift-docs-md/contents/docs/4.22/networking \
  --jq '.[].name'

# List with type info (file vs dir)
gh api repos/harche/openshift-docs-md/contents/docs/4.22/networking \
  --jq '.[] | "\(.type)\t\(.name)"'
```

## Common Documentation Sections

| Section | Description |
|---------|-------------|
| `welcome` | Overview, glossary |
| `release_notes` | Version-specific release information |
| `architecture` | System design and components |
| `installing` | Installation guides (AWS, GCP, Azure, bare metal, vSphere, etc.) |
| `post_installation_configuration` | Post-install cluster setup |
| `updating` | Cluster upgrade processes |
| `networking` | Network configuration, DNS, ingress, routes, network policies |
| `storage` | Persistent storage, CSI, ephemeral storage |
| `security` | Certificates, audit logs, compliance |
| `authentication` | Identity providers, RBAC, service accounts |
| `nodes` | Node management, pods, scheduling, taints/tolerations |
| `machine_management` | Machine sets, autoscaling, machine health checks |
| `observability` | Monitoring, logging, distributed tracing |
| `applications` | Deployments, operators, Helm, quotas |
| `cicd` | Builds, pipelines, GitOps |
| `virt` | OpenShift Virtualization |
| `edge_computing` | Remote worker nodes, single-node OpenShift |
| `windows_containers` | Windows container support |

## Tips

- **Start broad, then narrow**: Search the index first with a general term, then read the specific file that matches.
- **Large files**: Some doc files are long. Focus on the sections relevant to the user's question.
- **Cross-reference**: Complex topics (e.g., "install on AWS with custom networking") may require reading from multiple sections.
- **Version differences**: If the user is on an older version, use that version's index — docs differ between versions.
- **Rate limits**: `gh` uses your authenticated GitHub token, so you get higher API rate limits than unauthenticated `curl`.
