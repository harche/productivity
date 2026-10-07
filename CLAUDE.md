# Productivity Assistant

Personal AI-powered productivity hub focused on software engineering workflows.

## Directory Structure

- `plugins/` — Plugin marketplace: each plugin is at `plugins/<name>/` with `.claude-plugin/plugin.json`
- `.claude-plugin/marketplace.json` — Marketplace catalog listing all plugins

## Plugins

**workflow**
- `node-support` — OpenShift Node team assistant: kubelet/MCO/CRI-O/crun/conmonrs/Kueue development, debug-binary + CVO deployment, Jira (OCPNODE/OCPBUGS), Knowledge Base, support cases, platform docs (k8s + OpenShift), and Prometheus metrics
- `ultracode` — On-demand adversarial multi-agent review and isolated implementation workflows for Claude Code and Pi
- `treehouse` — Answer inline review comments left in VS Code (Treehouse Review extension), with a live watcher
- `kb` — Look up GitHub, OpenShift Node and Jira related knowledge, notes and tasks in pg_kb (PostgreSQL) with plain SQL
- `context-keeper` — Capture project state as structured markdown notes from Slack, Docs, Jira, and other sources

## Plugin Versioning

When bumping a plugin version, **always update both files**:
1. `plugins/<name>/.claude-plugin/plugin.json`
2. `.claude-plugin/marketplace.json`

## Conventions

- Keep responses concise and direct.
- Prefer reading existing code before suggesting changes.
- All skills, scripts, and commands must work on both macOS and Linux.
