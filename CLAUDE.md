# Productivity Assistant

Personal AI-powered productivity hub focused on software engineering workflows.

## Directory Structure

- `plugins/` — Plugin marketplace: each plugin is at `plugins/<name>/` with `.claude-plugin/plugin.json`
- `.claude-plugin/marketplace.json` — Marketplace catalog listing all plugins

## Plugins

**workflow**
- `workspace` — Manage email, calendar, and documents across Google Workspace
- `node-support` — OpenShift Node team assistant: kubelet/MCO/CRI-O/crun/conmonrs/Kueue development, debug-binary + CVO deployment, Jira (OCPNODE/OCPBUGS), Knowledge Base, support cases, platform docs (k8s + OpenShift), and Prometheus metrics
- `ultracode` — On-demand adversarial multi-agent review and isolated implementation workflows for Claude Code and Pi
- `hunk-review` — Interactive Hunk reviews, inline answers, and automatic comment watching in one slash command
- `context-keeper` — Capture project state as structured markdown notes from Slack, Docs, Jira, and other sources

**infra**
- `web-browser` — Browse the web: look up information, extract data, fill forms, take screenshots

**misc**
- `trading` — Monitor portfolio, place trades, and analyze account performance on Interactive Brokers (depends on `web-browser`)
- `video-research` — Extract insights from YouTube videos: transcripts, summaries, comments, and channel info
- `predictions` — Research prediction markets and event probabilities on Polymarket
- `financial-research` — Research company fundamentals (SEC filings) and economic trends (Federal Reserve data)
- `medical-research` — Find peer-reviewed medical evidence, clinical trials, and scientific papers

## Plugin Versioning

When bumping a plugin version, **always update both files**:
1. `plugins/<name>/.claude-plugin/plugin.json`
2. `.claude-plugin/marketplace.json`

## Conventions

- Keep responses concise and direct.
- Prefer reading existing code before suggesting changes.
- All skills, scripts, and commands must work on both macOS and Linux.
