# Plugin Catalog

## Plugins

### Workflow

| Plugin | Install | Description |
|--------|---------|-------------|
| `github` | `claude plugin install --local github@productivity-tools` | GitHub repos, PRs, issues, and actions via `gh` CLI |
| `slack` | `claude plugin install --local slack@productivity-tools` | Read, search, and send Slack messages via browser session |
| `google` | `claude plugin install --local google@productivity-tools` | Gmail, Google Calendar, Drive, and Docs via `gog` CLI |
| `redhat-detective` | `claude plugin install --local redhat-detective@productivity-tools` | Red Hat debugging/investigation toolkit: Jira, Knowledge Base, support cases, platform docs (k8s + OpenShift), and Prometheus metrics |
| `context-keeper` | `claude plugin install --local context-keeper@productivity-tools` | Capture project state as structured markdown notes from Slack, Docs, Jira, and other sources |

### Infra

| Plugin | Install | Description |
|--------|---------|-------------|
| `cluster-installer` | `claude plugin install --local cluster-installer@productivity-tools` | Create, manage, and destroy clusters (kind, GKE, OpenShift on GCP) |
| `playwright-cli` | `claude plugin install --local playwright-cli@productivity-tools` | Browser automation: navigate, interact, screenshot, scrape |

### Misc

| Plugin | Install | Description |
|--------|---------|-------------|
| `ibkr` | `claude plugin install --local ibkr@productivity-tools` | Interactive Brokers Web API for trading, market data, and portfolio management |
| `twitter` | `claude plugin install --local twitter@productivity-tools` | Read, search, and post on Twitter (X) via browser session |
| `youtube` | `claude plugin install --local youtube@productivity-tools` | Fetch YouTube transcripts, metadata, comments, search, and browse channels/playlists |
| `polymarket` | `claude plugin install --local polymarket@productivity-tools` | Browse and analyze Polymarket prediction markets, events, prices, and leaderboards |

## Agent Plugins

Agent plugins orchestrate other plugins to produce a complete deliverable. They don't provide tools themselves — instead, they define an agent with instructions, a model, and a list of plugin dependencies. When invoked, the agent runs autonomously, calling into its dependent plugins to gather data and synthesize a result.

Install an agent plugin the same way as any other plugin — its dependencies must also be installed.

| Agent | Install | Description | Dependencies |
|-------|---------|-------------|--------------|
| `dev-digest` | `claude plugin install --local dev-digest@productivity-tools` | Developer attention briefing from Jira issues, GitHub PRs, and GitHub issues — highlights what needs your action right now | `redhat-detective`, `github` |
| `market-news` | `claude plugin install --local market-news@productivity-tools` | News briefing from Polymarket prediction markets, cross-referenced with Twitter for context | `polymarket`, `twitter` |
