# Productivity Assistant

Personal AI-powered productivity hub focused on software engineering workflows.

## Directory Structure

- `workspace/` — Coding repos and projects (gitignored, local-only)
- `docs/` — Important documents and references (gitignored, local-only)
- `bookmarks/` — Saved links and resources (gitignored, local-only)
- `slack-browser-tools/` — Slack API integration via browser session injection
- `.claude/skills/` — Skill definitions (playwright-cli, slack, gmail/workspace, jira, github, support-cases)

## Skills

- `/playwright-cli` — Browser automation: navigate, interact, screenshot, scrape
- `/slack` — Read/search/send Slack messages via browser session
- `/gmail` — Gmail, Google Calendar, Drive, and Docs via `gog` CLI
- `/jira` — View, search, create, and update Jira issues via REST API
- `/github` — GitHub repos, PRs, issues, and actions via `gh` CLI
- `/support-cases` — View, search, and manage Red Hat support cases via Customer Portal API

## Authentication

API tokens are stored in macOS Keychain and loaded as environment variables via `~/.zshrc`. Skills that need tokens (Jira, support cases, GitHub, etc.) read them from env vars — check `~/.zshrc` for the variable names. To update a token:

```bash
security add-generic-password -a "$USER" -s "TOKEN_NAME" -w "new-value" -U
```

## Guardrails

- **Always confirm with the user** before sending emails, Slack messages, creating calendar events, creating/updating Jira issues, pushing code, or any action visible to others.
- Never auto-commit or push without explicit request.
- Never delete files, branches, or data without confirmation.
- When working in `workspace/` repos, respect each repo's own CLAUDE.md if present.

## Conventions

- Keep responses concise and direct.
- When working on code in `workspace/`, cd into the specific project — don't operate from the productivity root unless managing the assistant itself.
- Prefer reading existing code before suggesting changes.
