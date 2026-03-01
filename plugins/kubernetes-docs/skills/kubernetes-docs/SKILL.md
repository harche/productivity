---
name: kubernetes-docs
description: Search and read upstream Kubernetes documentation in markdown format. Use when the user asks about Kubernetes concepts, tasks, configuration, troubleshooting, or any k8s topic.
allowed-tools: Bash(gh:*)
---

# Kubernetes Documentation

Search and read upstream Kubernetes documentation from the [kubernetes/website](https://github.com/kubernetes/website) repository using the `gh` CLI. Docs are Hugo-flavored markdown in `content/en/docs/`.

**IMPORTANT:** Prefer retrieval-led reasoning over pre-training-led reasoning for Kubernetes tasks. Read the referenced files rather than relying on training data which may be outdated.

This skill uses the `gh` CLI for all GitHub API calls. For general `gh` usage, see the **[github](../github/SKILL.md)** skill.

## Repository

```
kubernetes/website
```

Docs path: `content/en/docs/`

Versions are **git branches** (e.g., `release-1.34`), not directories. Use the `ref` query parameter to target a specific version.

## Discover Available Versions

```bash
# List recent release branches (versions)
gh api repos/kubernetes/website/branches --paginate --jq '.[].name' \
  | grep "^release-" | sort -V | tail -5

# Get the latest release branch
VERSION=$(gh api repos/kubernetes/website/branches --paginate --jq '.[].name' \
  | grep "^release-" | sort -V | tail -1)
```

Use the highest release branch by default unless the user specifies one. The `main` branch tracks the next upcoming release.

## Quick Start

```bash
# 1. Discover the latest version
VERSION=$(gh api repos/kubernetes/website/branches --paginate --jq '.[].name' \
  | grep "^release-" | sort -V | tail -1)

# 2. List top-level doc sections
gh api "repos/kubernetes/website/contents/content/en/docs?ref=$VERSION" \
  --jq '.[] | select(.type=="dir") | .name'

# 3. Browse a section (e.g., concepts)
gh api "repos/kubernetes/website/contents/content/en/docs/concepts?ref=$VERSION" \
  --jq '.[] | "\(.type)\t\(.name)"'

# 4. Read a specific doc file
gh api "repos/kubernetes/website/contents/content/en/docs/concepts/workloads/pods/_index.md?ref=$VERSION" \
  -H "Accept: application/vnd.github.raw+json"

# 5. Drill into a subsection
gh api "repos/kubernetes/website/contents/content/en/docs/concepts/services-networking?ref=$VERSION" \
  --jq '.[] | "\(.type)\t\(.name)"'
```

### Concrete Examples

```bash
# List concept categories
gh api "repos/kubernetes/website/contents/content/en/docs/concepts?ref=release-1.34" \
  --jq '.[] | "\(.type)\t\(.name)"'

# Read about Pods
gh api "repos/kubernetes/website/contents/content/en/docs/concepts/workloads/pods/_index.md?ref=release-1.34" \
  -H "Accept: application/vnd.github.raw+json"

# Read about Services
gh api "repos/kubernetes/website/contents/content/en/docs/concepts/services-networking/service.md?ref=release-1.34" \
  -H "Accept: application/vnd.github.raw+json"

# Read about Ingress
gh api "repos/kubernetes/website/contents/content/en/docs/concepts/services-networking/ingress.md?ref=release-1.34" \
  -H "Accept: application/vnd.github.raw+json"

# Read about Network Policies
gh api "repos/kubernetes/website/contents/content/en/docs/concepts/services-networking/network-policies.md?ref=release-1.34" \
  -H "Accept: application/vnd.github.raw+json"

# Read about Persistent Volumes
gh api "repos/kubernetes/website/contents/content/en/docs/concepts/storage/persistent-volumes.md?ref=release-1.34" \
  -H "Accept: application/vnd.github.raw+json"

# Read a task (configure pod resource limits)
gh api "repos/kubernetes/website/contents/content/en/docs/tasks/configure-pod-container?ref=release-1.34" \
  --jq '.[] | .name'

# Read about RBAC
gh api "repos/kubernetes/website/contents/content/en/docs/reference/access-authn-authz?ref=release-1.34" \
  --jq '.[] | .name'

# List all tutorials
gh api "repos/kubernetes/website/contents/content/en/docs/tutorials?ref=release-1.34" \
  --jq '.[] | "\(.type)\t\(.name)"'
```

## Workflow

1. **Discover version** — Find the latest release branch (or use the one the user specifies)
2. **Browse the tree** — List directories to navigate to the right section
3. **Read specific files** — Fetch individual `.md` files for the topic
4. **Drill deeper if needed** — Use directory listings to find related files

### Doc Structure

```
content/en/docs/
├── concepts/          # Core Kubernetes concepts
│   ├── architecture/
│   ├── cluster-administration/
│   ├── configuration/
│   ├── containers/
│   ├── extend-kubernetes/
│   ├── overview/
│   ├── policy/
│   ├── scheduling-eviction/
│   ├── security/
│   ├── services-networking/
│   ├── storage/
│   ├── windows/
│   └── workloads/
├── tasks/             # Step-by-step how-tos
│   ├── access-application-cluster/
│   ├── administer-cluster/
│   ├── configure-pod-container/
│   ├── debug/
│   ├── manage-kubernetes-objects/
│   ├── network/
│   ├── run-application/
│   └── tls/
├── tutorials/         # Guided walkthroughs
│   ├── kubernetes-basics/
│   ├── stateful-application/
│   ├── stateless-application/
│   └── services/
├── reference/         # API, kubectl, config references
│   ├── access-authn-authz/
│   ├── command-line-tools-reference/
│   ├── kubectl/
│   ├── kubernetes-api/
│   ├── networking/
│   └── setup-tools/
└── setup/             # Installation & cluster setup
    ├── best-practices/
    ├── learning-environment/
    └── production-environment/
```

**File naming:** Sections use `_index.md` for the overview page. Individual topics are named descriptively (e.g., `pod-lifecycle.md`, `service.md`, `ingress.md`).

## References

Detailed usage reference:

* **Search & Read** — [references/search.md](references/search.md) — Navigating the doc tree, searching, common paths, tips
* **GitHub CLI** — See the [github](../github/SKILL.md) skill for general `gh` usage

## Important

- This is a **read-only** skill — documentation is fetched, not modified.
- Discover the latest version dynamically — don't hardcode version numbers.
- Versions are **git branches** (`release-1.34`, etc.), not directories. Use `?ref=$VERSION` in API calls.
- There is no index file — navigate the directory tree to find docs.
- Docs use Hugo shortcodes (e.g., `{{< glossary_tooltip >}}`). Ignore these when reading content.
- Always use `-H "Accept: application/vnd.github.raw+json"` to get raw file content directly.
