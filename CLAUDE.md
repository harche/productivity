# Productivity Assistant

Personal AI-powered productivity hub focused on software engineering workflows.

## Directory Structure

- `plugins/` — Plugin marketplace: each plugin is at `plugins/<name>/` with `.claude-plugin/plugin.json`
- `.claude-plugin/marketplace.json` — Marketplace catalog listing all plugins
- `.claude/skills/` — Local standalone skill copies (flat, auto-discovered by Claude Code)

## Skills

- `/playwright-cli` — Browser automation: navigate, interact, screenshot, scrape
- `/slack` — Read/search/send Slack messages via browser session
- `/gmail` — Gmail, Google Calendar, Drive, and Docs via `gog` CLI
- `/jira` — View, search, create, and update Jira issues via REST API
- `/github` — GitHub repos, PRs, issues, and actions via `gh` CLI
- `/support-cases` — View, search, and manage Red Hat support cases via Customer Portal API
- `/knowledge-base` — Search Red Hat Knowledge Base articles, solutions, and documentation
- `/openshift-docs` — Search and read OpenShift Container Platform docs via `gh` CLI
- `/kubernetes-docs` — Search and read upstream Kubernetes docs via `gh` CLI
- `/ocp-cluster` — Create, destroy, and list OpenShift clusters on GCP

## Authentication

API tokens are stored in macOS Keychain and loaded as environment variables via `~/.zshrc`. Skills that need tokens (Jira, support cases, GitHub, etc.) read them from env vars — check `~/.zshrc` for the variable names. To update a token:

```bash
security add-generic-password -a "$USER" -s "TOKEN_NAME" -w "new-value" -U
```

## Distributing Plugins to Other Repos

In the target repo, use Claude Code's native plugin system:
```bash
/plugin marketplace add harche/productivity
/plugin install jira@productivity-tools
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
