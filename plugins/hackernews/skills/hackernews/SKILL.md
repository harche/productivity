---
name: hackernews
description: Browse, search, and read Hacker News stories, comments, and user profiles. Use when the user asks about Hacker News, shares an HN URL, wants to see top/new/best stories, search HN, or read HN discussions.
allowed-tools: Bash(curl:*)
---

# Hacker News

Browse and search Hacker News using the official Firebase API and Algolia Search API. No authentication, API keys, or dependencies required — just `curl` and `jq`.

## APIs

| API | Base URL | Purpose |
|-----|----------|---------|
| Firebase | `https://hacker-news.firebaseio.com/v0` | Stories, items, users, live feeds |
| Algolia | `https://hn.algolia.com/api/v1` | Full-text search, threaded comments |

---

## Story Feeds

Each feed returns an array of up to 500 item IDs. Fetch individual items for details.

```bash
# Top stories (ranked by score)
curl -sf "https://hacker-news.firebaseio.com/v0/topstories.json" | jq '.[0:10]'

# New stories (most recent)
curl -sf "https://hacker-news.firebaseio.com/v0/newstories.json" | jq '.[0:10]'

# Best stories
curl -sf "https://hacker-news.firebaseio.com/v0/beststories.json" | jq '.[0:10]'

# Ask HN
curl -sf "https://hacker-news.firebaseio.com/v0/askstories.json" | jq '.[0:10]'

# Show HN
curl -sf "https://hacker-news.firebaseio.com/v0/showstories.json" | jq '.[0:10]'

# Jobs
curl -sf "https://hacker-news.firebaseio.com/v0/jobstories.json" | jq '.[0:10]'
```

### Fetch top N stories with details

To get full details for a feed, fetch each item by ID. Use `xargs` for parallel fetching:

```bash
# Top 10 stories with titles, scores, and comment counts
curl -sf "https://hacker-news.firebaseio.com/v0/topstories.json" | jq '.[0:10] | .[]' | xargs -I{} curl -sf "https://hacker-news.firebaseio.com/v0/item/{}.json" | jq '{id, title, by, score, descendants, url, time}'
```

---

## Item (Story / Comment / Job / Poll)

```bash
curl -sf "https://hacker-news.firebaseio.com/v0/item/ITEM_ID.json" | jq .
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Unique identifier |
| `type` | string | `story`, `comment`, `job`, `poll`, `pollopt` |
| `by` | string | Author username |
| `time` | int | Unix timestamp |
| `title` | string | Title (stories, jobs, polls) |
| `url` | string | External link (stories) |
| `text` | string | HTML body (comments, self-posts, jobs) |
| `score` | int | Upvote count |
| `descendants` | int | Total comment count |
| `kids` | array | Child comment IDs (ranked order) |
| `parent` | int | Parent item ID (comments) |
| `dead` | bool | Whether item is dead |
| `deleted` | bool | Whether item is deleted |

---

## Comments

Comments are items with `type: "comment"`. To read a comment thread, follow `kids` arrays. For full threads in a single request, use the Algolia API instead.

```bash
# Get a single comment
curl -sf "https://hacker-news.firebaseio.com/v0/item/COMMENT_ID.json" | jq '{id, by, text, score, time, kids}'

# Get top-level comments for a story (fetch the story, then each kid)
STORY_ID=12345
curl -sf "https://hacker-news.firebaseio.com/v0/item/${STORY_ID}.json" | jq '.kids[0:5] | .[]' | xargs -I{} curl -sf "https://hacker-news.firebaseio.com/v0/item/{}.json" | jq '{id, by, text: (.text[:300]), score}'
```

---

## User Profile

```bash
curl -sf "https://hacker-news.firebaseio.com/v0/user/USERNAME.json" | jq '{id, karma, created, about}'
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Username (case-sensitive) |
| `karma` | int | Karma score |
| `created` | int | Unix timestamp |
| `about` | string | Bio (HTML) |
| `submitted` | array | Item IDs authored by user |

---

## Search (Algolia)

The Algolia API provides full-text search with much richer results than the Firebase API.

```bash
# Search by relevance
curl -sf "https://hn.algolia.com/api/v1/search?query=QUERY&hitsPerPage=10" | jq '.hits[] | {title, url, author, points, num_comments, objectID}'

# Search by date (most recent first)
curl -sf "https://hn.algolia.com/api/v1/search_by_date?query=QUERY&hitsPerPage=10" | jq '.hits[] | {title, url, author, points, num_comments, created_at}'
```

| Param | Type | Description |
|-------|------|-------------|
| `query` | string | Full-text search |
| `tags` | string | Filter: `story`, `comment`, `ask_hn`, `show_hn`, `job`, `front_page`, `author_USERNAME`, `story_ID` |
| `numericFilters` | string | Filter: `points>100`, `num_comments>50`, `created_at_i>UNIX_TS` |
| `hitsPerPage` | int | Results per page (max 1000, default 20) |
| `page` | int | Page number (0-indexed) |

### Search examples

```bash
# Stories about Rust with 100+ points
curl -sf "https://hn.algolia.com/api/v1/search?query=rust&tags=story&numericFilters=points%3E100&hitsPerPage=10" | jq '.hits[] | {title, points, num_comments, url}'

# Recent Ask HN posts
curl -sf "https://hn.algolia.com/api/v1/search_by_date?tags=ask_hn&hitsPerPage=10" | jq '.hits[] | {title, points, num_comments, created_at}'

# Comments by a specific user
curl -sf "https://hn.algolia.com/api/v1/search_by_date?tags=comment,author_dang&hitsPerPage=5" | jq '.hits[] | {story_title, comment_text, points, created_at}'

# Show HN posts from the last week
curl -sf "https://hn.algolia.com/api/v1/search_by_date?tags=show_hn&hitsPerPage=10" | jq '.hits[] | {title, url, points, num_comments}'

# Front page stories right now
curl -sf "https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=30" | jq '.hits[] | {title, url, points, num_comments, author}'
```

### Full thread (single request)

The Algolia items endpoint returns the full comment tree in one request:

```bash
curl -sf "https://hn.algolia.com/api/v1/items/ITEM_ID" | jq '{title, url, points, author, children: [.children[:10][] | {author, text: (.text[:300]), points, children_count: (.children | length)}]}'
```

---

## URL Parsing

When the user shares a Hacker News URL, extract the item ID and fetch it:

| URL Pattern | Action |
|-------------|--------|
| `news.ycombinator.com/item?id=ID` | Fetch item (story or comment) |
| `news.ycombinator.com/user?id=USER` | Fetch user profile |
| `news.ycombinator.com` or `/news` | Top stories feed |
| `news.ycombinator.com/newest` | New stories feed |
| `news.ycombinator.com/ask` | Ask HN feed |
| `news.ycombinator.com/show` | Show HN feed |
| `news.ycombinator.com/jobs` | Jobs feed |

---

## Important

- The Firebase API has no official rate limit but be responsible.
- The Algolia API allows ~10,000 requests/hour per IP.
- Firebase feeds return only IDs — use Algolia for richer results.
- Use the Algolia `/items/ID` endpoint for full comment threads in a single request.
- Item `text` and user `about` fields contain HTML.
