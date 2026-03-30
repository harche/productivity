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
| `google` | Gmail, Google Calendar, Drive, and Docs via `gog` CLI | — |
| `redhat-detective` | Red Hat debugging/investigation toolkit: Jira, Knowledge Base, support cases, platform docs (k8s + OpenShift), and Prometheus metrics | — |
| `context-keeper` | Capture project state as structured markdown notes from Slack, Docs, Jira, and other sources | `google`, `redhat-detective`, `github` (all optional) |

<details>
<summary><b>context-keeper</b> — full install</summary>

```sh
# Source plugins (install whichever you use)
claude plugin install --scope local google@productivity-tools
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
| `ibkr` | Interactive Brokers Web API for trading, market data, and portfolio management | `web-browser` |
| `youtube` | Fetch YouTube transcripts, metadata, comments, search, and browse channels/playlists | — |
| `polymarket` | Browse and analyze Polymarket prediction markets, events, prices, and leaderboards | — |
| `hackernews` | Browse, search, and read Hacker News stories, comments, and user profiles | — |
| `sec-edgar` | Search SEC EDGAR for company filings, financials, and insider transactions | — |
| `fred` | Federal Reserve economic data (GDP, CPI, interest rates, unemployment) | — |
| `pubmed` | Search biomedical literature, clinical trials, and scientific papers (Europe PMC, ClinicalTrials.gov, Semantic Scholar, OpenAlex) | — |

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
| [`gog`](https://github.com/steipete/gogcli) | `google` | See [repo README](https://github.com/steipete/gogcli) | See [repo README](https://github.com/steipete/gogcli) |
| [`playwright-cli`](https://github.com/nicolo-ribaudo/playwright-cli) | `web-browser` | `npm install -g @anthropic-ai/playwright-cli@latest` | `npm install -g @anthropic-ai/playwright-cli@latest` |

### API Tokens

| Token | Plugins | How to obtain |
|-------|---------|---------------|
| `JIRA_API_TOKEN` | `redhat-detective` | [Create a PAT](https://issues.redhat.com) — Profile → Personal Access Tokens |
| `RH_API_OFFLINE_TOKEN` | `redhat-detective` | [Generate an offline token](https://access.redhat.com/management/api) for the Customer Portal API |
| `OCP_PULL_SECRET` | `cluster-installer` | [Download from console.redhat.com](https://console.redhat.com/openshift/install/pull-secret) |
| `fred-api-key` | `fred` | [Get a free API key](https://fred.stlouisfed.org/docs/api/api_key.html) (instant approval) |
| `semantic-scholar-api-key` | `pubmed` | [Request a free API key](https://www.semanticscholar.org/product/api#api-key-form) (optional — plugin works without it) |
| `openalex-api-key` | `pubmed` | [Get a free API key](https://openalex.org/settings/api) (sign up, then copy from settings) |

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
| `google` | `gog` CLI (OAuth flow) |
| `youtube` | No auth required (public API) |
| `polymarket` | No auth required (public API) |
| `ibkr` | Auto-login via `web-browser` (headless); credentials from Keychain (`ibkr-paper-*`, `ibkr-live-*`) |
| `web-browser` | No auth required |
| `hackernews` | No auth required (public API) |
| `sec-edgar` | No auth required (User-Agent header only) |
| `fred` | API key from Keychain (`fred-api-key`) |
| `pubmed` | Europe PMC and ClinicalTrials.gov: no auth; Semantic Scholar and OpenAlex: API keys from Keychain (optional/free) |
| `context-keeper` | Uses other plugins' auth |
