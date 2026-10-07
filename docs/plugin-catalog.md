# Plugin Catalog

Install any plugin with:

```sh
claude plugin install --scope local <name>@productivity-tools
```

## Plugins

### Workflow

| Plugin | Description | Dependencies |
|--------|-------------|--------------|
| `node-support` | OpenShift Node team assistant: kubelet/MCO/CRI-O/crun/conmonrs/Kueue development, debug-binary + CVO deployment, Jira (OCPNODE/OCPBUGS), Knowledge Base, support cases, platform docs (k8s + OpenShift), and Prometheus metrics | — |
| `ultracode` | On-demand adversarial multi-agent review and isolated implementation workflows for Claude Code and Pi | — |
| `kb` | Look up GitHub, OpenShift Node and Jira related knowledge, notes and tasks in [pg_kb](https://github.com/harche/pg_kb) with plain SQL ([usage](../plugins/kb/README.md)) | — |

## Prerequisites

External CLI tools and API tokens required by specific plugins. Only install what you need. Plugins not listed here have no external prerequisites.

### CLI Tools

| Tool | Plugins | macOS | Linux |
|------|---------|-------|-------|
| `psql` + a running [pg_kb](https://github.com/harche/pg_kb) | `kb` | `brew install postgresql@18`, then follow the pg_kb README | Same |

### API Tokens

| Token | Plugins | How to obtain |
|-------|---------|---------------|
| `JIRA_API_TOKEN` | `node-support` | [Create a PAT](https://issues.redhat.com) — Profile → Personal Access Tokens |
| `RH_API_OFFLINE_TOKEN` | `node-support` | [Generate an offline token](https://access.redhat.com/management/api) for the Customer Portal API |

### Storing Tokens

**macOS (Keychain):**

```bash
security add-generic-password -a "$USER" -s "<TOKEN_NAME>" -w "<token-value>" -U
```

**Linux (secret-tool / libsecret):**

```bash
# Enter token at the "Password:" prompt
secret-tool store --label="<TOKEN_NAME>" service <service> key <TOKEN_NAME>
```

See the full examples in the [README](../README.md#authentication--secrets).

### Plugins That Don't Need Manual Tokens

| Plugin | Auth method |
|--------|-------------|
| `ultracode` | No auth required |
