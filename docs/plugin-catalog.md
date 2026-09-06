# Plugin Catalog

Install any plugin with:

```sh
claude plugin install --scope local <name>@productivity-tools
```

## Plugins

### Workflow

| Plugin | Description | Dependencies |
|--------|-------------|--------------|
| `workspace` | Manage email, calendar, and documents across Google Workspace | — |
| `node-support` | OpenShift Node team assistant: kubelet/MCO/CRI-O/crun/conmonrs/Kueue development, debug-binary + CVO deployment, Jira (OCPNODE/OCPBUGS), Knowledge Base, support cases, platform docs (k8s + OpenShift), and Prometheus metrics | — |
| `ultracode` | On-demand adversarial multi-agent review and isolated implementation workflows for Claude Code and Pi | — |
| `hunk-review` | Watch a live Hunk session for user comments and answer them inline (loads Hunk's own skill via `hunk skill path`) ([usage](../plugins/hunk-review/README.md)) | — |
| `knowledge-base` | Build and maintain knowledge bases: ingest sources (conversations, articles, URLs), compile structured wikis, and lint for consistency. Obsidian-compatible. | — |

### Infra

| Plugin | Description | Dependencies |
|--------|-------------|--------------|
| `web-browser` | Browse the web: look up information, extract data, fill forms, take screenshots | — |

### Misc

| Plugin | Description | Dependencies |
|--------|-------------|--------------|
| `trading` | Monitor portfolio, place trades, and analyze account performance on Interactive Brokers | `web-browser` |
| `video-research` | Extract insights from YouTube videos: transcripts, summaries, comments, and channel info | — |
| `predictions` | Research prediction markets and event probabilities on Polymarket | — |
| `financial-research` | Research company fundamentals (SEC filings) and economic trends (Federal Reserve data) | — |
| `medical-research` | Find peer-reviewed medical evidence, clinical trials, and scientific papers | — |

## Prerequisites

External CLI tools and API tokens required by specific plugins. Only install what you need. Plugins not listed here have no external prerequisites.

### CLI Tools

| Tool | Plugins | macOS | Linux |
|------|---------|-------|-------|
| [`gog`](https://github.com/steipete/gogcli) | `workspace` | See [repo README](https://github.com/steipete/gogcli) | See [repo README](https://github.com/steipete/gogcli) |
| [`playwright-cli`](https://github.com/nicolo-ribaudo/playwright-cli) | `web-browser` | `npm install -g @anthropic-ai/playwright-cli@latest` | `npm install -g @anthropic-ai/playwright-cli@latest` |
| `hunk` | `hunk-review` | Install Hunk 0.20.1+ (`hunk skill path` and `session comment list --type user --json`) | Same CLI required |
| `python3` | `hunk-review` | `brew install python` | Install Python 3 with your package manager |

### API Tokens

| Token | Plugins | How to obtain |
|-------|---------|---------------|
| `JIRA_API_TOKEN` | `node-support` | [Create a PAT](https://issues.redhat.com) — Profile → Personal Access Tokens |
| `RH_API_OFFLINE_TOKEN` | `node-support` | [Generate an offline token](https://access.redhat.com/management/api) for the Customer Portal API |
| `fred-api-key` | `financial-research` | [Get a free API key](https://fred.stlouisfed.org/docs/api/api_key.html) (instant approval) |
| `semantic-scholar-api-key` | `medical-research` | [Request a free API key](https://www.semanticscholar.org/product/api#api-key-form) (optional — plugin works without it) |
| `openalex-api-key` | `medical-research` | [Get a free API key](https://openalex.org/settings/api) (sign up, then copy from settings) |

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
| `workspace` | `gog` CLI (OAuth flow) |
| `video-research` | No auth required (public API) |
| `predictions` | No auth required (public API) |
| `trading` | Auto-login via `web-browser` (headless); credentials from Keychain (`ibkr-paper-*`, `ibkr-live-*`) |
| `web-browser` | No auth required |
| `financial-research` | SEC EDGAR: no auth; FRED: API key from Keychain (`fred-api-key`) |
| `medical-research` | Europe PMC and ClinicalTrials.gov: no auth; Semantic Scholar and OpenAlex: API keys from Keychain (optional/free) |
| `knowledge-base` | No auth required |
| `ultracode` | No auth required |
| `hunk-review` | No auth required; uses the local Hunk daemon |
