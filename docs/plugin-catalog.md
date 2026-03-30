# Plugin Catalog

Install any plugin with:

```sh
claude plugin install --scope local <name>@productivity-tools
```

## Plugins

### Workflow

| Plugin | Description | Dependencies |
|--------|-------------|--------------|
| `github` | GitHub repos, PRs, issues, and actions via `gh` CLI | — |
| `workspace` | Manage email, calendar, and documents across Google Workspace | — |
| `redhat-detective` | Red Hat debugging/investigation toolkit: Jira, Knowledge Base, support cases, platform docs (k8s + OpenShift), and Prometheus metrics | — |
| `context-keeper` | Capture project state as structured markdown notes from Slack, Docs, Jira, and other sources | `workspace`, `redhat-detective`, `github` (all optional) |

<details>
<summary><b>context-keeper</b> — full install</summary>

```sh
# Source plugins (install whichever you use)
claude plugin install --scope local workspace@productivity-tools
claude plugin install --scope local redhat-detective@productivity-tools
claude plugin install --scope local github@productivity-tools

# The plugin itself
claude plugin install --scope local context-keeper@productivity-tools
```

</details>

### Infra

| Plugin | Description | Dependencies |
|--------|-------------|--------------|
| `cluster-installer` | Create, manage, and destroy clusters (kind, GKE, OpenShift on GCP) | — |
| `web-browser` | Browse the web: look up information, extract data, fill forms, take screenshots | — |

### Misc

| Plugin | Description | Dependencies |
|--------|-------------|--------------|
| `trading` | Monitor portfolio, place trades, and analyze account performance on Interactive Brokers | `web-browser` |
| `video-research` | Extract insights from YouTube videos: transcripts, summaries, comments, and channel info | — |
| `predictions` | Research prediction markets and event probabilities on Polymarket | — |
| `tech-news` | Discover trending tech news and developer discussions on Hacker News | — |
| `financial-research` | Research company fundamentals (SEC filings) and economic trends (Federal Reserve data) | — |
| `medical-research` | Find peer-reviewed medical evidence, clinical trials, and scientific papers | — |

## Agent Plugins

Agent plugins orchestrate other plugins to produce a complete deliverable. They don't provide tools themselves — instead, they define an agent with instructions, a model, and a list of plugin dependencies. When invoked, the agent runs autonomously, calling into its dependent plugins to gather data and synthesize a result.

| Agent | Description | Dependencies |
|-------|-------------|--------------|
| `dev-digest` | Developer attention briefing from Jira issues, GitHub PRs, and GitHub issues — highlights what needs your action right now | `redhat-detective`, `github` |
<details>
<summary><b>dev-digest</b> — full install</summary>

```sh
# Dependencies
claude plugin install --scope local redhat-detective@productivity-tools
claude plugin install --scope local github@productivity-tools

# The agent
claude plugin install --scope local dev-digest@productivity-tools
```

</details>

## Prerequisites

External CLI tools and API tokens required by specific plugins. Only install what you need. Plugins not listed here have no external prerequisites.

### CLI Tools

| Tool | Plugins | macOS | Linux |
|------|---------|-------|-------|
| [`gh`](https://cli.github.com/) | `github` | `brew install gh` | `dnf install gh` / `apt install gh` |
| [`gog`](https://github.com/steipete/gogcli) | `workspace` | See [repo README](https://github.com/steipete/gogcli) | See [repo README](https://github.com/steipete/gogcli) |
| [`playwright-cli`](https://github.com/nicolo-ribaudo/playwright-cli) | `web-browser` | `npm install -g @anthropic-ai/playwright-cli@latest` | `npm install -g @anthropic-ai/playwright-cli@latest` |

### API Tokens

| Token | Plugins | How to obtain |
|-------|---------|---------------|
| `JIRA_API_TOKEN` | `redhat-detective` | [Create a PAT](https://issues.redhat.com) — Profile → Personal Access Tokens |
| `RH_API_OFFLINE_TOKEN` | `redhat-detective` | [Generate an offline token](https://access.redhat.com/management/api) for the Customer Portal API |
| `OCP_PULL_SECRET` | `cluster-installer` | [Download from console.redhat.com](https://console.redhat.com/openshift/install/pull-secret) |
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
| `github` | `gh auth login` (GitHub CLI handles OAuth) |
| `workspace` | `gog` CLI (OAuth flow) |
| `video-research` | No auth required (public API) |
| `predictions` | No auth required (public API) |
| `trading` | Auto-login via `web-browser` (headless); credentials from Keychain (`ibkr-paper-*`, `ibkr-live-*`) |
| `web-browser` | No auth required |
| `tech-news` | No auth required (public API) |
| `financial-research` | SEC EDGAR: no auth; FRED: API key from Keychain (`fred-api-key`) |
| `medical-research` | Europe PMC and ClinicalTrials.gov: no auth; Semantic Scholar and OpenAlex: API keys from Keychain (optional/free) |
| `context-keeper` | Uses other plugins' auth |
