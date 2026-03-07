# Productivity Assistant

AI-powered productivity hub with Claude Code plugins for software engineering workflows — Jira, GitHub, Slack, Kubernetes/OpenShift docs, support cases, and more.

## Quick Start

In any project, add the marketplace and install plugins:

```bash
# Add the marketplace (one-time)
/plugin marketplace add harche/productivity

# Install individual plugins
/plugin install redhat-support@productivity-tools
/plugin install github@productivity-tools

# Browse all available plugins
/plugin
```

## Available Plugins

### Workflow

| Plugin | Description |
|--------|-------------|
| `github` | GitHub repos, PRs, issues, and actions via `gh` CLI |
| `slack` | Read, search, and send Slack messages via browser session |
| `google` | Gmail, Google Calendar, Drive, and Docs via `gog` CLI |
| `redhat-support` | Red Hat Jira, Knowledge Base, and support cases |
| `context-keeper` | Capture project state as structured markdown notes from Slack, Docs, Jira, and other sources |

### Reference

| Plugin | Description |
|--------|-------------|
| `platform-docs` | Search and read Kubernetes and OpenShift documentation |

### Infra

| Plugin | Description |
|--------|-------------|
| `cluster-installer` | Create, manage, and destroy clusters (kind, GKE, OpenShift on GCP) |
| `playwright-cli` | Browser automation: navigate, interact, screenshot, scrape |
| `prometheus` | Query and analyze Prometheus metrics on Kubernetes/OpenShift clusters |

### Misc

| Plugin | Description |
|--------|-------------|
| `ibkr` | Interactive Brokers Web API for trading, market data, and portfolio management |
| `twitter` | Read, search, and post on Twitter (X) via browser session |
| `youtube` | Fetch YouTube transcripts, metadata, comments, search, and browse channels/playlists |

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
    "redhat-support@productivity-tools": true
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
    "redhat-support@productivity-tools": true,
    "twitter@productivity-tools": true,
    "youtube@productivity-tools": true,
    "context-keeper@productivity-tools": true,
    "platform-docs@productivity-tools": true,
    "cluster-installer@productivity-tools": true,
    "playwright-cli@productivity-tools": true,
    "prometheus@productivity-tools": true,
    "ibkr@productivity-tools": true
  }
}
```

Plugins are auto-installed when the repo folder is trusted in Claude Code.

## Example Workflows

**Investigate a support case and check related Jira bugs:**
```
/plugin marketplace add harche/productivity
/plugin install redhat-support@productivity-tools
```

**Work on an OpenShift project with docs at hand:**
```
/plugin install platform-docs@productivity-tools
/plugin install github@productivity-tools
/plugin install redhat-support@productivity-tools
```

**Spin up a cluster and start working:**
```
/plugin install cluster-installer@productivity-tools
/plugin install platform-docs@productivity-tools
```
