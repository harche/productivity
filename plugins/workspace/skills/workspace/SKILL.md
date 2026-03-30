---
name: workspace
description: "Manage email, calendar, and documents across Google Workspace. Use when the user wants to check calendar availability, search emails, read or edit Google Docs, or find files in Drive."
allowed-tools: Bash(gog:*)
---

# Google Workspace

Manage email, calendar, documents, and files through the `gog` CLI (OAuth-authenticated).

## Check calendar and schedule

```bash
gog calendar list --today                      # what's on today
gog calendar list --week                       # this week's events
gog calendar freebusy primary --from="..." --to="..."  # check availability
```

Create events, RSVP, manage focus time, and more -- see [references/calendar.md](references/calendar.md).

## Search and read emails

```bash
gog gmail search 'is:unread newer_than:1d'     # recent unread
gog gmail thread get <threadId> --full          # read full thread
```

Send, reply (always use `--quote`), manage labels and drafts -- see [references/gmail.md](references/gmail.md).

## Manage Google Docs

```bash
gog docs cat <docId>                            # read a doc
gog docs write <docId> --file=content.md --replace --markdown  # update a doc
```

Create, export, find-and-replace, comments -- see [references/docs.md](references/docs.md).

## Find files in Drive

```bash
gog drive search "quarterly report"             # full-text search
gog drive ls --parent=<folderId>                # browse a folder
```

Upload, download, share, manage permissions -- see [references/drive.md](references/drive.md).

## Output formats

All commands support these flags:

- `--json` (`-j`) -- JSON output (best for parsing)
- `--plain` (`-p`) -- TSV output (for piping)
- `--results-only` -- drop envelope fields like nextPageToken
- `--dry-run` (`-n`) -- preview without making changes
- `--account` (`-a`) -- specify account email for multi-account setups

## Rules

- **Always confirm with the user before sending emails, creating/modifying calendar events, deleting files, or sharing documents.**
- **When replying to emails, ALWAYS use `--quote` to preserve the email chain.**
- **When presenting dates to the user, verify the day of the week using `date -j -f '%Y-%m-%d' 'YYYY-MM-DD' '+%A'` instead of guessing it.**
- Use `--dry-run` (`-n`) to preview destructive actions.
- Use `--json` for reliable parsing of command output.
