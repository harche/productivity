---
name: youtube
description: Fetch YouTube video transcripts, metadata, comments, search videos, and browse channels/playlists. Use when the user shares a YouTube URL, asks about a video, wants to summarize or analyze video content, or search YouTube.
allowed-tools: Bash(node:*)
---

# YouTube CLI

Fetch transcripts, metadata, comments, and browse YouTube content. No API keys or authentication required.

## Prerequisites

- **Node.js** (v18+)

## Commands

All commands go through a single CLI tool at `${CLAUDE_PLUGIN_ROOT}/youtube-tools/youtube.mjs`.

```bash
# Auto-detect any YouTube URL (video, playlist, channel, search)
# Returns metadata + transcript for videos, info for channels, etc.
node ${CLAUDE_PLUGIN_ROOT}/youtube-tools/youtube.mjs url "<youtube-url>"

# Get video metadata (title, author, duration, views, description, chapters)
node ${CLAUDE_PLUGIN_ROOT}/youtube-tools/youtube.mjs video <videoId>

# Fetch transcript/subtitles as text
node ${CLAUDE_PLUGIN_ROOT}/youtube-tools/youtube.mjs transcript <videoId> [--lang en] [--timestamps]

# Get top comments
node ${CLAUDE_PLUGIN_ROOT}/youtube-tools/youtube.mjs comments <videoId> [count]

# Search YouTube (videos only)
node ${CLAUDE_PLUGIN_ROOT}/youtube-tools/youtube.mjs search "<query>" [count]

# Get channel info
node ${CLAUDE_PLUGIN_ROOT}/youtube-tools/youtube.mjs channel <handle>

# Get channel's recent videos
node ${CLAUDE_PLUGIN_ROOT}/youtube-tools/youtube.mjs channel-videos <handle> [count]

# Get playlist contents
node ${CLAUDE_PLUGIN_ROOT}/youtube-tools/youtube.mjs playlist <playlistId>
```

## URL Parsing

When the user shares a YouTube URL, use the `url` command — it auto-detects the content type:

```bash
node ${CLAUDE_PLUGIN_ROOT}/youtube-tools/youtube.mjs url "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

Supported URL patterns:
- `youtube.com/watch?v=` — video (returns metadata + transcript)
- `youtu.be/<id>` — short video URL
- `youtube.com/shorts/<id>` — YouTube Shorts
- `youtube.com/live/<id>` — livestream
- `youtube.com/@<handle>` — channel (returns info + recent videos)
- `youtube.com/playlist?list=` — playlist contents
- `youtube.com/results?search_query=` — search results

## Transcript Options

- `--lang <code>` — language code (default: `en`). Falls back to first available if not found.
- `--timestamps` — include per-segment timestamps (useful for finding specific moments)

The transcript command shows available languages, whether captions are auto-generated, and word/character counts.

## Output Format

All commands output **clean JSON** with:
- Video metadata (title, author, duration, views, publish date)
- Chapter markers extracted from descriptions
- Full transcript text or timestamped segments
- Comment text with author and like counts
- Search results with thumbnails and view counts

## Error Handling

- If captions are unavailable, the error message suggests alternatives
- Network errors and invalid URLs produce clear error messages
- All output is valid JSON (including errors)

## Tips

- Use `url` for the quickest way to get everything about a video (metadata + transcript in one call)
- Use `transcript --timestamps` when the user asks "what did they say at minute X?"
- Use `search` to find videos, then `transcript` to analyze specific ones
- Use `comments` to gauge audience reaction
