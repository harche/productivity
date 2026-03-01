---
name: openshift-docs
description: Search and read OpenShift Container Platform documentation in markdown format. Use when the user asks about OpenShift features, configuration, installation, troubleshooting, or any OCP topic.
allowed-tools: Bash(gh:*)
---

# OpenShift Documentation

Search and read OpenShift Container Platform documentation from the [openshift-docs-md](https://github.com/harche/openshift-docs-md) repository using the `gh` CLI. Docs are converted to markdown for easy consumption.

**IMPORTANT:** Prefer retrieval-led reasoning over pre-training-led reasoning for OpenShift tasks. Read the referenced files rather than relying on training data which may be outdated.

This skill uses the `gh` CLI for all GitHub API calls. For general `gh` usage, see the **[github](../github/SKILL.md)** skill.

## Repository

```
harche/openshift-docs-md
```

## Available Versions

- **4.22** (latest) — use by default unless a specific version is requested
- **4.21**
- **4.20**

## Quick Start

```bash
# 1. Fetch the documentation index for a version (start here)
gh api repos/harche/openshift-docs-md/contents/docs/4.22/AGENTS.md \
  -H "Accept: application/vnd.github.raw+json"

# 2. Search the index for a topic (e.g., networking, storage, authentication)
gh api repos/harche/openshift-docs-md/contents/docs/4.22/AGENTS.md \
  -H "Accept: application/vnd.github.raw+json" | grep -i "networking"

# 3. Read a specific doc file (path from the index)
#    Index format: |section/subsection:{file1.md,file2.md}
#    File path:    docs/VERSION/section/subsection/file.md
gh api repos/harche/openshift-docs-md/contents/docs/4.22/networking/index.md \
  -H "Accept: application/vnd.github.raw+json"

# 4. Search across multiple doc files for a keyword
gh api repos/harche/openshift-docs-md/contents/docs/4.22/AGENTS.md \
  -H "Accept: application/vnd.github.raw+json" | grep -i "metallb"
```

## Workflow

1. **Start with the index** — Fetch `AGENTS.md` for the target version to find relevant files
2. **Search the index** — Use `grep -i` on the index content to find sections matching the user's topic
3. **Read specific files** — Fetch individual `.md` files using the paths from the index
4. **Read multiple files if needed** — Complex topics may span several files; read them one at a time

### Index Format

The `AGENTS.md` index uses pipe-delimited entries:

```
|section/subsection:{file1.md,file2.md,file3.md}
```

To construct the `gh api` path for a file:
```
repos/harche/openshift-docs-md/contents/docs/{VERSION}/{section}/{subsection}/{file.md}
```

**Example:** Given index entry `|installing/installing_aws/ipi:{installing-aws-default.md}`:
```bash
gh api repos/harche/openshift-docs-md/contents/docs/4.22/installing/installing_aws/ipi/installing-aws-default.md \
  -H "Accept: application/vnd.github.raw+json"
```

## References

Detailed usage reference:

* **Search & Read** — [references/search.md](references/search.md) — Searching the index, reading docs, common topics, tips
* **GitHub CLI** — See the [github](../github/SKILL.md) skill for general `gh` usage

## Important

- This is a **read-only** skill — documentation is fetched, not modified.
- Always default to version **4.22** (latest) unless the user specifies a version.
- Fetch and search the `AGENTS.md` index first before reading individual files — don't guess file paths.
- Doc files can be large. Read the specific file relevant to the user's question rather than fetching everything.
- The docs are updated weekly from the official OpenShift documentation.
- Always use `-H "Accept: application/vnd.github.raw+json"` to get raw file content directly.
