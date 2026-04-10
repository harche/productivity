# Productivity Assistant

Personal AI-powered productivity hub focused on software engineering workflows.

## Directory Structure

- `plugins/` — Plugin marketplace: each plugin is at `plugins/<name>/` with `.claude-plugin/plugin.json`
- `.claude-plugin/marketplace.json` — Marketplace catalog listing all plugins

## Plugins

**workflow**
- `github` — GitHub repos, PRs, issues, and actions via `gh` CLI
- `workspace` — Manage email, calendar, and documents across Google Workspace
- `redhat-detective` — Red Hat debugging/investigation toolkit: Jira issues, Knowledge Base, support cases, platform docs (k8s + OpenShift), and Prometheus metrics
- `context-keeper` — Capture project state as structured markdown notes from Slack, Docs, Jira, and other sources

**infra**
- `cluster-installer` — Create, manage, and destroy clusters (kind, GKE, OpenShift on GCP)
- `web-browser` — Browse the web: look up information, extract data, fill forms, take screenshots

**misc**
- `trading` — Monitor portfolio, place trades, and analyze account performance on Interactive Brokers (depends on `web-browser`)
- `video-research` — Extract insights from YouTube videos: transcripts, summaries, comments, and channel info
- `predictions` — Research prediction markets and event probabilities on Polymarket
- `tech-news` — Discover trending tech news and developer discussions on Hacker News
- `financial-research` — Research company fundamentals (SEC filings) and economic trends (Federal Reserve data)
- `medical-research` — Find peer-reviewed medical evidence, clinical trials, and scientific papers

**platform**
- `lightspeed-assistant` — Navigate the LightspeedProposal system: architecture, CRD fields, integration, deployment, skills authoring

**agents** (orchestrate other plugins, no tools of their own)
- `dev-digest` — Developer attention briefing from Jira + GitHub (depends on `redhat-detective`, `github`)

## Plugin Versioning

When bumping a plugin version, **always update both files**:
1. `plugins/<name>/.claude-plugin/plugin.json`
2. `.claude-plugin/marketplace.json`

## Conventions

- Keep responses concise and direct.
- Prefer reading existing code before suggesting changes.
- All skills, scripts, and commands must work on both macOS and Linux.
