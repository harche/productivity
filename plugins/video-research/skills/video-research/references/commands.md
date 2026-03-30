# YouTube CLI Command Reference

All commands go through: `node ${CLAUDE_PLUGIN_ROOT}/youtube-tools/youtube.mjs <command> [args]`

## Commands

### url — Auto-detect any YouTube URL

```bash
node ${CLAUDE_PLUGIN_ROOT}/youtube-tools/youtube.mjs url "<youtube-url>"
```

Parses the URL and returns the appropriate data:
- Video URLs: metadata + transcript
- Channel URLs: info + recent videos
- Playlist URLs: playlist contents
- Search URLs: search results

### video — Get video metadata

```bash
node ${CLAUDE_PLUGIN_ROOT}/youtube-tools/youtube.mjs video <videoId>
```

Returns: title, author, duration, views, likes, publish date, description, chapters, keywords, thumbnail.

### transcript — Fetch transcript/subtitles

```bash
node ${CLAUDE_PLUGIN_ROOT}/youtube-tools/youtube.mjs transcript <videoId> [--lang <code>] [--timestamps]
```

| Option | Default | Description |
|---|---|---|
| `--lang <code>` | `en` | Language code. Falls back to first available if not found. |
| `--timestamps` | off | Include per-segment timestamps |

Returns: full transcript text, language info, whether captions are auto-generated, word/character counts.

### comments — Get top comments

```bash
node ${CLAUDE_PLUGIN_ROOT}/youtube-tools/youtube.mjs comments <videoId> [count]
```

| Param | Default | Description |
|---|---|---|
| `count` | 20 | Number of comments to fetch |

Returns: array of `{ author, text, likes, publishedTime, replyCount }`.

### search — Search YouTube

```bash
node ${CLAUDE_PLUGIN_ROOT}/youtube-tools/youtube.mjs search "<query>" [count]
```

| Param | Default | Description |
|---|---|---|
| `count` | 10 | Number of results |

Returns videos only. Each result: `{ id, title, author, duration, views, publishedTime, description, thumbnail }`.

### channel — Get channel info

```bash
node ${CLAUDE_PLUGIN_ROOT}/youtube-tools/youtube.mjs channel <handle>
```

Handle can be with or without `@`. Returns: name, handle, channelId, description, subscriberCount, thumbnail, url.

### channel-videos — Get channel's recent videos

```bash
node ${CLAUDE_PLUGIN_ROOT}/youtube-tools/youtube.mjs channel-videos <handle> [count]
```

| Param | Default | Description |
|---|---|---|
| `count` | 10 | Number of videos |

Returns: array of `{ id, title, duration, views, publishedTime, thumbnail }`.

### playlist — Get playlist contents

```bash
node ${CLAUDE_PLUGIN_ROOT}/youtube-tools/youtube.mjs playlist <playlistId>
```

Returns: playlistId, title, videoCount, author, and array of videos with `{ id, title, author, duration, index }`.

## Supported URL formats

- `youtube.com/watch?v=ID`
- `youtu.be/ID`
- `youtube.com/shorts/ID`
- `youtube.com/live/ID`
- `youtube.com/embed/ID`
- `youtube.com/@handle`
- `youtube.com/playlist?list=ID`
- `youtube.com/results?search_query=QUERY`

## Error handling

- All output is valid JSON, including errors.
- If captions are unavailable, the error message suggests alternatives.
- Network errors and invalid URLs produce clear error messages.
