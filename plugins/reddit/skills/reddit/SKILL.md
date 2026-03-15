---
name: reddit
description: Browse and search Reddit using the user's Chrome session. Use when the user shares a Reddit URL, asks about subreddits, posts, comments, wants to search Reddit, or check their feed.
allowed-tools: Bash(node:*),Bash(curl:*)
---

# Reddit

Browse and search Reddit using the user's Chrome session. Auth tokens are extracted directly from Chrome's cookie store — no API keys, OAuth apps, or registration required.

## Prerequisite

The user must be logged into Reddit (reddit.com) in Google Chrome. The tool reads the `token_v2` cookie directly from Chrome's storage files on disk.

The token is a JWT valid for ~24 hours. Chrome refreshes it automatically when you browse Reddit. If the token expires, just visit reddit.com in Chrome.

## Authentication

Get a bearer token from Chrome (extracts and decrypts `token_v2` from Chrome's cookie store):

```bash
TOKEN=$(node ${CLAUDE_PLUGIN_ROOT}/reddit-tools/get-token.mjs)
```

Verify auth and check token expiry:

```bash
node ${CLAUDE_PLUGIN_ROOT}/reddit-tools/get-token.mjs --check
```

**All curl commands below assume TOKEN is set.** Use this header pattern:

```bash
curl -sf -H "Authorization: Bearer $TOKEN" -A "claude-code-reddit/0.1" \
  "https://oauth.reddit.com/ENDPOINT?raw_json=1" | jq .
```

---

## Browse Subreddit

```bash
# Hot posts (default)
curl -sf -H "Authorization: Bearer $TOKEN" -A "claude-code-reddit/0.1" \
  "https://oauth.reddit.com/r/SUBREDDIT/hot?limit=10&raw_json=1" | jq '.data.children[] | .data | {id, title, author, score, num_comments, url, selftext: .selftext[:200]}'

# New posts
curl -sf -H "Authorization: Bearer $TOKEN" -A "claude-code-reddit/0.1" \
  "https://oauth.reddit.com/r/SUBREDDIT/new?limit=10&raw_json=1" | jq .

# Top posts (time filter: hour, day, week, month, year, all)
curl -sf -H "Authorization: Bearer $TOKEN" -A "claude-code-reddit/0.1" \
  "https://oauth.reddit.com/r/SUBREDDIT/top?t=week&limit=10&raw_json=1" | jq .

# Rising posts
curl -sf -H "Authorization: Bearer $TOKEN" -A "claude-code-reddit/0.1" \
  "https://oauth.reddit.com/r/SUBREDDIT/rising?limit=10&raw_json=1" | jq .
```

| Param | Type | Description |
|-------|------|-------------|
| `limit` | int | 1-100 (default 25) |
| `t` | string | Time filter for `top`: `hour`, `day`, `week`, `month`, `year`, `all` |
| `after` | string | Fullname of last item for pagination (e.g., `t3_abc123`) |
| `raw_json` | int | Set to `1` to get unescaped unicode/HTML |

---

## Subreddit Info

```bash
curl -sf -H "Authorization: Bearer $TOKEN" -A "claude-code-reddit/0.1" \
  "https://oauth.reddit.com/r/SUBREDDIT/about?raw_json=1" | jq '.data | {display_name, title, public_description, subscribers, accounts_active, created_utc, over18}'
```

---

## Read Post + Comments

```bash
# Get post and comments (POST_ID without t3_ prefix)
curl -sf -H "Authorization: Bearer $TOKEN" -A "claude-code-reddit/0.1" \
  "https://oauth.reddit.com/comments/POST_ID?limit=25&depth=5&raw_json=1" | jq .
```

The response is a 2-element array:
- `[0]` — the post (listing with one child)
- `[1]` — the comments tree

```bash
# Extract post details
curl -sf -H "Authorization: Bearer $TOKEN" -A "claude-code-reddit/0.1" \
  "https://oauth.reddit.com/comments/POST_ID?limit=25&depth=5&raw_json=1" | jq '.[0].data.children[0].data | {id, title, author, score, selftext, url, num_comments, upvote_ratio}'

# Extract top-level comments
curl -sf -H "Authorization: Bearer $TOKEN" -A "claude-code-reddit/0.1" \
  "https://oauth.reddit.com/comments/POST_ID?limit=25&depth=5&raw_json=1" | jq '[.[1].data.children[] | select(.kind=="t1") | .data | {id, author, score, body: .body[:300]}]'
```

| Param | Type | Description |
|-------|------|-------------|
| `limit` | int | Max comments to return |
| `depth` | int | Max comment tree depth |
| `sort` | string | `confidence`, `top`, `new`, `controversial`, `old`, `qa` |
| `comment` | string | Focus on a specific comment ID |

---

## Search

```bash
# Search all of Reddit
curl -sf -H "Authorization: Bearer $TOKEN" -A "claude-code-reddit/0.1" \
  "https://oauth.reddit.com/search?q=QUERY&limit=10&raw_json=1" | jq '.data.children[] | .data | {id, subreddit, title, author, score, num_comments, url}'

# Search within a subreddit
curl -sf -H "Authorization: Bearer $TOKEN" -A "claude-code-reddit/0.1" \
  "https://oauth.reddit.com/r/SUBREDDIT/search?q=QUERY&restrict_sr=true&limit=10&raw_json=1" | jq .
```

| Param | Type | Description |
|-------|------|-------------|
| `q` | string | Search query (URL-encode spaces as `%20`) |
| `restrict_sr` | bool | `true` to limit to the subreddit in the URL path |
| `sort` | string | `relevance`, `hot`, `top`, `new`, `comments` |
| `t` | string | Time filter: `hour`, `day`, `week`, `month`, `year`, `all` |
| `limit` | int | 1-100 |
| `after` | string | Pagination cursor |

---

## User Profile

```bash
curl -sf -H "Authorization: Bearer $TOKEN" -A "claude-code-reddit/0.1" \
  "https://oauth.reddit.com/user/USERNAME/about?raw_json=1" | jq '.data | {name, total_karma, link_karma, comment_karma, created_utc, is_gold}'
```

## User Posts

```bash
curl -sf -H "Authorization: Bearer $TOKEN" -A "claude-code-reddit/0.1" \
  "https://oauth.reddit.com/user/USERNAME/submitted?sort=new&limit=10&raw_json=1" | jq '.data.children[] | .data | {id, subreddit, title, score, num_comments, url}'
```

## User Comments

```bash
curl -sf -H "Authorization: Bearer $TOKEN" -A "claude-code-reddit/0.1" \
  "https://oauth.reddit.com/user/USERNAME/comments?sort=new&limit=10&raw_json=1" | jq '.data.children[] | .data | {id, subreddit, link_title, body: .body[:200], score}'
```

---

## Home Feed

```bash
# Best (algorithmic)
curl -sf -H "Authorization: Bearer $TOKEN" -A "claude-code-reddit/0.1" \
  "https://oauth.reddit.com/best?limit=10&raw_json=1" | jq '.data.children[] | .data | {id, subreddit, title, author, score, num_comments}'

# Hot from subscriptions
curl -sf -H "Authorization: Bearer $TOKEN" -A "claude-code-reddit/0.1" \
  "https://oauth.reddit.com/hot?limit=10&raw_json=1" | jq .
```

---

## Saved Items

```bash
curl -sf -H "Authorization: Bearer $TOKEN" -A "claude-code-reddit/0.1" \
  "https://oauth.reddit.com/user/USERNAME/saved?limit=10&raw_json=1" | jq '.data.children[] | .data | {kind: .name[:2], title: (.title // .link_title), subreddit, score, body: (.body // .selftext)[:200]}'
```

---

## My Subscriptions

```bash
curl -sf -H "Authorization: Bearer $TOKEN" -A "claude-code-reddit/0.1" \
  "https://oauth.reddit.com/subreddits/mine/subscriber?limit=100&raw_json=1" | jq '[.data.children[] | .data | {name: .display_name, subscribers, description: .public_description[:100]}]'
```

---

## URL Parsing

When the user shares a Reddit URL, extract the relevant parts and call the appropriate endpoint:

| URL Pattern | Action |
|-------------|--------|
| `reddit.com/r/<sub>` | Browse subreddit (hot) |
| `reddit.com/r/<sub>/comments/<id>/...` | Read post + comments |
| `reddit.com/r/<sub>/top`, `/new`, `/rising` | Browse subreddit with sort |
| `reddit.com/r/<sub>/search?q=...` | Search within subreddit |
| `reddit.com/u/<user>` or `/user/<user>` | User profile |
| `reddit.com/search?q=...` | Global search |

---

## Response Structure

All listing endpoints return:

```json
{
  "kind": "Listing",
  "data": {
    "after": "t3_abc123",
    "children": [
      { "kind": "t3", "data": { ... } }
    ]
  }
}
```

- `kind`: `t1` = comment, `t3` = post, `t5` = subreddit
- `data.after`: pagination cursor — pass as `?after=` for next page
- `data.children[].data`: the actual post/comment/subreddit object

---

## Important

- Add `raw_json=1` to GET requests to get unescaped content.
- All actions happen as the logged-in Chrome user.
- Reddit rate limits to ~60 requests/minute for authenticated sessions.
- URL-encode query parameters (spaces as `%20`, etc.).
- If the token expires, visit reddit.com in Chrome to refresh it.
