# Plugin Catalog

Install any plugin with:

```sh
claude plugin install --scope local <name>@productivity-tools
```

## Plugins

### Workflow

| Plugin | Description | Requires |
|--------|-------------|----------|
| `github` | GitHub repos, PRs, issues, and actions via `gh` CLI | — |
| `slack` | Read, search, and send Slack messages via browser session | — |
| `google` | Gmail, Google Calendar, Drive, and Docs via `gog` CLI | — |
| `redhat-detective` | Red Hat debugging/investigation toolkit: Jira, Knowledge Base, support cases, platform docs (k8s + OpenShift), and Prometheus metrics | — |
| `context-keeper` | Capture project state as structured markdown notes from Slack, Docs, Jira, and other sources | `slack`, `google`, `redhat-detective`, `github` * |

\* `context-keeper` uses these plugins to fetch data from different sources. Install whichever sources you need — if a plugin isn't installed, it will ask you to paste the content directly.

<details>
<summary><b>context-keeper</b> — full install</summary>

```sh
# Source plugins (install whichever you use)
claude plugin install --scope local slack@productivity-tools
claude plugin install --scope local google@productivity-tools
claude plugin install --scope local redhat-detective@productivity-tools
claude plugin install --scope local github@productivity-tools

# The plugin itself
claude plugin install --scope local context-keeper@productivity-tools
```

</details>

### Infra

| Plugin | Description | Requires |
|--------|-------------|----------|
| `cluster-installer` | Create, manage, and destroy clusters (kind, GKE, OpenShift on GCP) | — |
| `playwright-cli` | Browser automation: navigate, interact, screenshot, scrape | — |

### Misc

| Plugin | Description | Requires |
|--------|-------------|----------|
| `ibkr` | Interactive Brokers Web API for trading, market data, and portfolio management | — |
| `twitter` | Read, search, and post on Twitter (X) via browser session | — |
| `youtube` | Fetch YouTube transcripts, metadata, comments, search, and browse channels/playlists | — |
| `polymarket` | Browse and analyze Polymarket prediction markets, events, prices, and leaderboards | — |

## Agent Plugins

Agent plugins orchestrate other plugins to produce a complete deliverable. They don't provide tools themselves — instead, they define an agent with instructions, a model, and a list of plugin dependencies. When invoked, the agent runs autonomously, calling into its dependent plugins to gather data and synthesize a result.

| Agent | Description | Requires |
|-------|-------------|----------|
| `dev-digest` | Developer attention briefing from Jira issues, GitHub PRs, and GitHub issues — highlights what needs your action right now | `redhat-detective`, `github` |
| `market-news` | News briefing from Polymarket prediction markets, cross-referenced with Twitter for context | `polymarket`, `twitter` |

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

<details>
<summary><b>market-news</b> — full install</summary>

```sh
# Dependencies
claude plugin install --scope local polymarket@productivity-tools
claude plugin install --scope local twitter@productivity-tools

# The agent
claude plugin install --scope local market-news@productivity-tools
```

</details>
