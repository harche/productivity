---
name: slack
description: Fetch Slack messages, channels, and threads from the user's browser session. Use when the user shares a Slack URL, asks about Slack content, or wants to interact with Slack (read messages, search channels, read threads, check DMs, send messages).
allowed-tools: Bash(node:*),Bash(playwright-cli:*)
---

# Slack CLI

Read and interact with Slack using the user's Chrome session via the Playwright Chrome extension.

## Prerequisite

The user must be logged into Slack in Google Chrome, and the browser must be connected via the Playwright extension.

**Before any Slack command, always ensure the Chrome extension is connected:**

```bash
playwright-cli open --extension
```

This connects to the user's running Chrome and allows the tool to interact with Slack using the active session.

## Commands

All commands go through a single CLI tool bundled at `${CLAUDE_PLUGIN_ROOT}/slack-browser-tools/slack.mjs`.

```bash
# Fetch content from a Slack URL (channels, threads, messages)
node ${CLAUDE_PLUGIN_ROOT}/slack-browser-tools/slack.mjs url "<slack-url>"

# Read channel history
node ${CLAUDE_PLUGIN_ROOT}/slack-browser-tools/slack.mjs history <channelId> [limit]

# Read a thread
node ${CLAUDE_PLUGIN_ROOT}/slack-browser-tools/slack.mjs thread <channelId> <threadTs>

# Search messages
node ${CLAUDE_PLUGIN_ROOT}/slack-browser-tools/slack.mjs search "<query>" [count]

# List channels
node ${CLAUDE_PLUGIN_ROOT}/slack-browser-tools/slack.mjs channels

# Channel details
node ${CLAUDE_PLUGIN_ROOT}/slack-browser-tools/slack.mjs channel-info <channelId>

# List users
node ${CLAUDE_PLUGIN_ROOT}/slack-browser-tools/slack.mjs users [limit]

# User details
node ${CLAUDE_PLUGIN_ROOT}/slack-browser-tools/slack.mjs user-info <userId>

# Send a message (ALWAYS confirm with user first)
node ${CLAUDE_PLUGIN_ROOT}/slack-browser-tools/slack.mjs send <channelId> "<text>" [threadTs]

# Add a reaction (ALWAYS confirm with user first)
node ${CLAUDE_PLUGIN_ROOT}/slack-browser-tools/slack.mjs react <channelId> <messageTs> <emoji>

# Call any Slack API method directly
node ${CLAUDE_PLUGIN_ROOT}/slack-browser-tools/slack.mjs api <method> '<json-params>'
```

## URL Parsing

When the user shares a Slack URL, use the `url` command — it automatically parses the channel ID, message timestamp, and thread info:

```bash
node ${CLAUDE_PLUGIN_ROOT}/slack-browser-tools/slack.mjs url "https://redhat-internal.slack.com/archives/C0A8HU4VCG0/p1771943379438339"
```

Supported URL patterns:
- `*/archives/<channelId>` → channel history
- `*/archives/<channelId>/p<timestamp>` → thread
- `*/archives/<channelId>/p<ts>?thread_ts=<ts>` → thread
- `*/client/<teamId>/<channelId>` → channel history

## Output Format

All commands output **clean JSON** with Slack markup already converted:
- `<@U123>` → `@U123`
- `<#C123|channel-name>` → `#channel-name`
- `<https://url|text>` → `[text](https://url)`
- `&amp;` `&lt;` `&gt;` → `&` `<` `>`

## Enterprise Grid Restrictions

This workspace runs on Slack Enterprise Grid, which restricts certain API methods for browser session tokens. **Avoid these API calls** — they will fail with `enterprise_is_restricted`:
- `conversations.list` (especially with `types: "im"`)
- Other admin/discovery endpoints

**Use `search` instead.** For example, to check recent DMs or mentions:
- `search "to:me"` — messages sent to you
- `search "from:@username"` — messages from a specific person
- `search "in:#channel"` — messages in a specific channel

## Error Handling

- If the Chrome extension is not connected, run `playwright-cli open --extension` first
- Rate limiting (429) is handled automatically with retry
- 800-1500ms random delay between API calls
- `enterprise_is_restricted` — see Enterprise Grid Restrictions above

## Important

- **Always confirm with the user before sending messages or reactions.**
- All actions happen as the logged-in Chrome user via the Playwright extension.
