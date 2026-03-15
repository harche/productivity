# Productivity Assistant

Personal AI-powered productivity hub focused on software engineering workflows.

## Directory Structure

- `plugins/` — Plugin marketplace: each plugin is at `plugins/<name>/` with `.claude-plugin/plugin.json`
- `.claude-plugin/marketplace.json` — Marketplace catalog listing all plugins

## Plugins

**workflow**
- `github` — GitHub repos, PRs, issues, and actions via `gh` CLI
- `slack` — Read/search/send Slack messages via browser session
- `google` — Gmail, Google Calendar, Drive, and Docs via `gog` CLI
- `redhat-detective` — Red Hat debugging/investigation toolkit: Jira issues, Knowledge Base, support cases, platform docs (k8s + OpenShift), and Prometheus metrics
- `context-keeper` — Capture project state as structured markdown notes from Slack, Docs, Jira, and other sources

**infra**
- `cluster-installer` — Create, manage, and destroy clusters (kind, GKE, OpenShift on GCP)
- `playwright-cli` — Browser automation: navigate, interact, screenshot, scrape

**misc**
- `ibkr` — Interactive Brokers Web API for trading, market data, and portfolio management (depends on `playwright-cli`)
- `twitter` — Read, search, and post on Twitter (X) via browser session
- `youtube` — Fetch YouTube transcripts, metadata, comments, search, and browse channels/playlists
- `polymarket` — Browse and analyze Polymarket prediction markets, events, prices, and leaderboards
- `reddit` — Browse and search Reddit via Chrome session
- `hackernews` — Browse, search, and read Hacker News stories, comments, and user profiles

**agents** (orchestrate other plugins, no tools of their own)
- `dev-digest` — Developer attention briefing from Jira + GitHub (depends on `redhat-detective`, `github`)
- `market-news` — News briefing from Polymarket + Twitter (depends on `polymarket`, `twitter`)

## Plugin Versioning

When bumping a plugin version, **always update both files**:
1. `plugins/<name>/.claude-plugin/plugin.json`
2. `.claude-plugin/marketplace.json`

## Conventions

- Keep responses concise and direct.
- Prefer reading existing code before suggesting changes.
- All skills, scripts, and commands must work on both macOS and Linux.
