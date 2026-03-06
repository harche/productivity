---
name: google
description: Manage Gmail, Google Calendar, Google Drive, and Google Docs using the gog CLI. Use when the user asks about email, calendar events, drive files, or Google Docs.
allowed-tools: Bash(gog:*)
---

# Google Workspace via gog CLI

Manage Gmail, Calendar, Drive, and Docs using the `gog` CLI tool (authenticated via OAuth).

## Quick Start

```bash
# Gmail: search recent emails
gog gmail search 'newer_than:1d'

# Calendar: list upcoming events
gog calendar list --max=5

# Drive: list files
gog drive ls --max=5

# Docs: read a Google Doc
gog docs cat <docId>
```

## Global Flags

All commands support these flags:

- `--json` (`-j`): JSON output (best for scripting/parsing)
- `--plain` (`-p`): TSV output (for piping)
- `--results-only`: In JSON mode, drops envelope fields like nextPageToken
- `--dry-run` (`-n`): Preview without making changes
- `--account` (`-a`): Specify account email for multi-account setups

## Services

Detailed command references for each service:

* **Gmail** — [references/gmail.md](references/gmail.md)
* **Calendar** — [references/calendar.md](references/calendar.md)
* **Drive** — [references/drive.md](references/drive.md)
* **Docs** — [references/docs.md](references/docs.md)

## Important

- **Always confirm with the user before sending emails, creating/modifying calendar events, deleting files, or sharing documents.**
- **When presenting dates to the user, always verify the day of the week using `date -j -f '%Y-%m-%d' 'YYYY-MM-DD' '+%A'` instead of guessing it.**
- Use `--dry-run` (`-n`) to preview destructive actions.
- Use `--json` for reliable parsing of command output.
- All actions happen as the authenticated OAuth user.
