---
name: video-research
description: "Extract insights from YouTube videos — transcripts, summaries, comments, and channel info. Use when the user wants to understand video content without watching, research a topic via video, or analyze a channel."
allowed-tools: Bash(node:*)
---

# Video Research

Understand YouTube video content without watching — get transcripts, metadata, comments, and channel info.

## Quick start

```bash
# Drop any YouTube URL to get metadata + transcript in one call
node ${CLAUDE_PLUGIN_ROOT}/youtube-tools/youtube.mjs url "<youtube-url>"
```

## Use cases

### Get a video transcript or summary

Extract the full transcript so you can summarize, search, or quote from a video.

```bash
# Metadata + transcript together (fastest for a single video)
node ${CLAUDE_PLUGIN_ROOT}/youtube-tools/youtube.mjs url "https://www.youtube.com/watch?v=VIDEO_ID"

# Transcript only
node ${CLAUDE_PLUGIN_ROOT}/youtube-tools/youtube.mjs transcript VIDEO_ID

# With timestamps (useful for "what did they say at minute X?")
node ${CLAUDE_PLUGIN_ROOT}/youtube-tools/youtube.mjs transcript VIDEO_ID --timestamps

# Non-English transcript
node ${CLAUDE_PLUGIN_ROOT}/youtube-tools/youtube.mjs transcript VIDEO_ID --lang es
```

See [references/commands.md](references/commands.md) for all transcript options and output format.

### Research a topic via videos

Search YouTube for videos on a topic, then pull transcripts from the most relevant ones.

```bash
# Search for videos
node ${CLAUDE_PLUGIN_ROOT}/youtube-tools/youtube.mjs search "QUERY" 10

# Then get the transcript of a promising result
node ${CLAUDE_PLUGIN_ROOT}/youtube-tools/youtube.mjs transcript VIDEO_ID
```

### Explore a channel

See what a channel is about and what they have been publishing recently.

```bash
# Channel info (description, subscriber count)
node ${CLAUDE_PLUGIN_ROOT}/youtube-tools/youtube.mjs channel HANDLE

# Recent uploads
node ${CLAUDE_PLUGIN_ROOT}/youtube-tools/youtube.mjs channel-videos HANDLE 10
```

### Read audience reactions

See what viewers are saying in the comments.

```bash
# Top comments (default 20)
node ${CLAUDE_PLUGIN_ROOT}/youtube-tools/youtube.mjs comments VIDEO_ID

# More comments
node ${CLAUDE_PLUGIN_ROOT}/youtube-tools/youtube.mjs comments VIDEO_ID 50
```

### Browse a playlist

```bash
node ${CLAUDE_PLUGIN_ROOT}/youtube-tools/youtube.mjs playlist PLAYLIST_ID
```

## Handling URLs

The `url` command auto-detects the content type from any YouTube URL:

| URL Pattern | What it returns |
|---|---|
| `youtube.com/watch?v=` / `youtu.be/` | Video metadata + transcript |
| `youtube.com/shorts/` / `youtube.com/live/` | Video metadata + transcript |
| `youtube.com/@handle` | Channel info + recent videos |
| `youtube.com/playlist?list=` | Playlist contents |
| `youtube.com/results?search_query=` | Search results |

## Important notes

- All commands output clean JSON.
- Transcripts show available languages and whether captions are auto-generated.
- If captions are unavailable, the error message suggests alternatives.
- Video metadata includes chapters extracted from the description when available.
- See [references/commands.md](references/commands.md) for the full command reference.
