---
name: slack
description: Fetch Slack messages, channels, and threads from the user's browser session. Use when the user shares a Slack URL, asks about Slack content, or wants to interact with Slack (read messages, search, send messages).
allowed-tools: Bash(node:*)
---

# Slack Browser Tools

Read and interact with Slack via the user's authenticated browser session.

## Prerequisite

Slack must be open in Chrome, connected via Playwright CLI extension. If the browser is not connected, use the `playwright-cli` skill (invoke it with `/playwright-cli open --extension`) to connect first.

## Commands

All commands go through a single CLI tool bundled at `${CLAUDE_PLUGIN_ROOT}/slack-browser-tools/slack.mjs`. It handles init, auth, and rate limiting automatically.

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

## Error Handling

- If the browser is not connected, the tool prints an error asking to run `playwright-cli open --extension`
- If the token is stale, clear and re-init: run `init` command
- Rate limiting (429) is handled automatically with retry
- 1 second delay between API calls to avoid detection

## Important

- **Always confirm with the user before sending messages or reactions.**
- All actions happen as the logged-in user.
- Token is extracted from Slack's localStorage — workspace-aware, no Slack app needed.
