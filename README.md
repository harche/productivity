# Productivity Assistant

AI-powered productivity hub with Claude Code plugins for software engineering workflows — Jira, GitHub, Slack, Kubernetes/OpenShift docs, support cases, and more.

## Quick Start

### Prerequisites

Some plugins depend on external CLIs or API tokens being available on your system **before** you install them:

| Dependency | Needed by | Install |
|------------|-----------|---------|
| [`gh`](https://cli.github.com/) | `github` | `brew install gh` / `dnf install gh` / `apt install gh` |
| [`gog`](https://github.com/steipete/gogcli) | `google` | See repo README |
| API tokens (Jira, Red Hat, etc.) | `redhat-detective`, `cluster-installer` | See [Authentication & Secrets](#authentication--secrets) below |

### Install Plugins

In any project, add the marketplace and install plugins. Use `--local` to scope plugins to the current project — this way each repo gets only the plugins it needs:

```bash
# Add the marketplace (one-time)
claude plugin marketplace add harche/productivity

# Install plugins locally (scoped to the current project)
claude plugin install --local redhat-detective@productivity-tools
claude plugin install --local github@productivity-tools

# Browse all available plugins
claude plugin
```

## Available Plugins

### Workflow

| Plugin | Description |
|--------|-------------|
| `github` | GitHub repos, PRs, issues, and actions via `gh` CLI |
| `slack` | Read, search, and send Slack messages via browser session |
| `google` | Gmail, Google Calendar, Drive, and Docs via `gog` CLI |
| `redhat-detective` | Red Hat debugging/investigation toolkit: Jira, Knowledge Base, support cases, platform docs (k8s + OpenShift), and Prometheus metrics |
| `context-keeper` | Capture project state as structured markdown notes from Slack, Docs, Jira, and other sources |

### Infra

| Plugin | Description |
|--------|-------------|
| `cluster-installer` | Create, manage, and destroy clusters (kind, GKE, OpenShift on GCP) |
| `playwright-cli` | Browser automation: navigate, interact, screenshot, scrape |

### Misc

| Plugin | Description |
|--------|-------------|
| `ibkr` | Interactive Brokers Web API for trading, market data, and portfolio management |
| `twitter` | Read, search, and post on Twitter (X) via browser session |
| `youtube` | Fetch YouTube transcripts, metadata, comments, search, and browse channels/playlists |
| `polymarket` | Browse and analyze Polymarket prediction markets, events, prices, and leaderboards |

## Agent Plugins

Agent plugins are higher-level plugins that orchestrate other plugins to produce a complete deliverable. They don't provide tools themselves — instead, they define an agent with instructions, a model, and a list of plugin dependencies. When invoked, the agent runs autonomously, calling into its dependent plugins to gather data and synthesize a result.

| Agent | Description | Dependencies |
|-------|-------------|--------------|
| `dev-digest` | Generate a developer attention briefing from Jira issues, GitHub PRs, and GitHub issues — highlights what needs your action right now | `redhat-detective`, `github` |
| `market-news` | Generate a news briefing from Polymarket prediction markets, cross-referenced with Twitter for context | `polymarket`, `twitter` |

Install an agent plugin the same way as any other plugin — its dependencies must also be installed:

```bash
# Install dev-digest and its dependencies
claude plugin install --local dev-digest@productivity-tools
claude plugin install --local redhat-detective@productivity-tools
claude plugin install --local github@productivity-tools

# Install market-news and its dependencies
claude plugin install --local market-news@productivity-tools
claude plugin install --local polymarket@productivity-tools
claude plugin install --local twitter@productivity-tools
```

## Bulk Install by Category

To auto-install a group of plugins in a repo, add this to `.claude/settings.json`:

**Workflow plugins:**
```json
{
  "extraKnownMarketplaces": {
    "productivity-tools": {
      "source": { "source": "github", "repo": "harche/productivity" }
    }
  },
  "enabledPlugins": {
    "github@productivity-tools": true,
    "slack@productivity-tools": true,
    "google@productivity-tools": true,
    "redhat-detective@productivity-tools": true
  }
}
```

**All plugins:**
```json
{
  "extraKnownMarketplaces": {
    "productivity-tools": {
      "source": { "source": "github", "repo": "harche/productivity" }
    }
  },
  "enabledPlugins": {
    "github@productivity-tools": true,
    "slack@productivity-tools": true,
    "google@productivity-tools": true,
    "redhat-detective@productivity-tools": true,
    "twitter@productivity-tools": true,
    "youtube@productivity-tools": true,
    "polymarket@productivity-tools": true,
    "context-keeper@productivity-tools": true,
    "cluster-installer@productivity-tools": true,
    "playwright-cli@productivity-tools": true,
    "ibkr@productivity-tools": true
  }
}
```

Plugins are auto-installed when the repo folder is trusted in Claude Code.

## Authentication & Secrets

Some plugins require API tokens stored in the OS secret store. The table below lists every token, which plugin needs it, and how to store it on each platform.

### Prerequisites

| Platform | Secret store | Install |
|----------|-------------|---------|
| macOS | Keychain (built-in) | — |
| Linux | libsecret / GNOME Keyring | `sudo dnf install libsecret` (Fedora) or `sudo apt install libsecret-tools` (Ubuntu/Debian) |

### Required Tokens

| Token | Plugin | How to obtain |
|-------|--------|---------------|
| `JIRA_API_TOKEN` | `redhat-detective` | [Create a PAT](https://issues.redhat.com) → Profile → Personal Access Tokens |
| `RH_API_OFFLINE_TOKEN` | `redhat-detective` | [Generate an offline token](https://access.redhat.com/management/api) for the Customer Portal API |
| `OCP_PULL_SECRET` | `cluster-installer` | Download from [console.redhat.com/openshift/install/pull-secret](https://console.redhat.com/openshift/install/pull-secret) |

### Storing Tokens

**macOS (Keychain):**

```bash
# Jira PAT
security add-generic-password -a "$USER" -s "JIRA_API_TOKEN" -w "your-jira-token" -U

# Red Hat API offline token
security add-generic-password -a "$USER" -s "RH_API_OFFLINE_TOKEN" -w "your-offline-token" -U

# OpenShift pull secret (compact JSON)
security add-generic-password -a "$USER" -s "OCP_PULL_SECRET" \
  -w "$(cat pull-secret.json | python3 -c 'import sys,json; print(json.dumps(json.load(sys.stdin), separators=(",",":")))')" -U
```

**Linux (secret-tool / libsecret):**

```bash
# Jira PAT (enter token at the "Password:" prompt)
secret-tool store --label="JIRA_API_TOKEN" service jira key JIRA_API_TOKEN

# Red Hat API offline token
secret-tool store --label="RH_API_OFFLINE_TOKEN" service redhat key RH_API_OFFLINE_TOKEN

# OpenShift pull secret
cat pull-secret.json | python3 -c 'import sys,json; print(json.dumps(json.load(sys.stdin), separators=(",",":")))' | \
  secret-tool store --label="OCP Pull Secret" service ocp-install username "$USER" key OCP_PULL_SECRET
```

### Plugins That Don't Need Manual Tokens

| Plugin | Auth method |
|--------|-------------|
| `github` | `gh auth login` (GitHub CLI handles OAuth) |
| `google` | `gog` CLI (OAuth flow) |
| `slack` | Extracted automatically from Chrome session |
| `twitter` | Extracted automatically from Chrome cookies |
| `youtube` | No auth required (public API) |
| `polymarket` | No auth required (public API) |
| `ibkr` | Session-based via IBKR Client Portal Gateway |
| `playwright-cli` | No auth required |
| `context-keeper` | Uses other plugins' auth |

## Example Workflows

**Investigate a support case — Jira, KB, docs, and metrics in one plugin:**
```
claude plugin marketplace add harche/productivity
claude plugin install --local redhat-detective@productivity-tools
```

**Work on an OpenShift project with full investigation toolkit:**
```
claude plugin install --local redhat-detective@productivity-tools
claude plugin install --local github@productivity-tools
```

**Spin up a cluster and start working:**
```
claude plugin install --local cluster-installer@productivity-tools
claude plugin install --local redhat-detective@productivity-tools
```
