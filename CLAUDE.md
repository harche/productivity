# Productivity Assistant

Personal AI-powered productivity hub focused on software engineering workflows.

## Directory Structure

- `plugins/` — Plugin marketplace: each plugin is at `plugins/<name>/` with `.claude-plugin/plugin.json`
- `.claude-plugin/marketplace.json` — Marketplace catalog listing all plugins
- `.claude/skills/` — Local standalone skill copies (flat, auto-discovered by Claude Code)

## Plugins

**workflow**
- `github` — GitHub repos, PRs, issues, and actions via `gh` CLI
- `slack` — Read/search/send Slack messages via browser session
- `google` — Gmail, Google Calendar, Drive, and Docs via `gog` CLI
- `redhat-support` — Red Hat Jira, Knowledge Base, and support cases
- `context-keeper` — Capture project state as structured markdown notes from Slack, Docs, Jira, and other sources

**reference**
- `platform-docs` — Search and read Kubernetes and OpenShift documentation

**infra**
- `cluster-installer` — Create, manage, and destroy clusters (kind, GKE, OpenShift on GCP)
- `playwright-cli` — Browser automation: navigate, interact, screenshot, scrape
- `prometheus` — Query and analyze Prometheus metrics on Kubernetes/OpenShift clusters

**misc**
- `ibkr` — Interactive Brokers Web API for trading, market data, and portfolio management
- `twitter` — Read, search, and post on Twitter (X) via browser session
- `polymarket` — Browse and analyze Polymarket prediction markets, events, prices, and leaderboards
- `market-news` — Generate news briefings from Polymarket, cross-referenced with Twitter (agent plugin; depends on `polymarket` + `twitter`)

## Authentication

API tokens are stored in macOS Keychain and loaded as environment variables via `~/.zshrc`. Skills that need tokens (Jira, support cases, GitHub, etc.) read them from env vars — check `~/.zshrc` for the variable names. To update a token:

```bash
security add-generic-password -a "$USER" -s "TOKEN_NAME" -w "new-value" -U
```

## Distributing Plugins to Other Repos

In the target repo, use Claude Code's native plugin system:
```bash
/plugin marketplace add harche/productivity
/plugin install redhat-support@productivity-tools
```

## Guardrails

- **Always confirm with the user** before sending emails, Slack messages, creating calendar events, creating/updating Jira issues, pushing code, or any action visible to others.
- Never auto-commit or push without explicit request.
- Never delete files, branches, or data without confirmation.
## Plugin Versioning

When bumping a plugin version, **always update both files**:
1. `plugins/<name>/.claude-plugin/plugin.json`
2. `.claude-plugin/marketplace.json`

## Conventions

- Keep responses concise and direct.
- Prefer reading existing code before suggesting changes.
