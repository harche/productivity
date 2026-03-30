---
name: tech-news
description: "Discover trending tech news and developer discussions on Hacker News. Use when the user wants to find what developers are talking about, read tech discussions, or research community opinions on tools and technologies."
allowed-tools: Bash(curl:*)
---

# Tech News

Find out what developers are talking about, research community opinions, and read tech discussions — all via Hacker News.

## Quick start

```bash
# What's trending right now?
curl -sf "https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=20" | jq '.hits[] | {title, url, points, num_comments, author}'
```

## Use cases

### Discover trending stories

See what's on the front page or browse top/new/best feeds.

```bash
# Front page stories right now (fastest single-request approach)
curl -sf "https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=30" | jq '.hits[] | {title, url, points, num_comments, author}'

# Ask HN / Show HN / Jobs — see references/feeds.md for all feed types
curl -sf "https://hn.algolia.com/api/v1/search_by_date?tags=show_hn&hitsPerPage=10" | jq '.hits[] | {title, url, points, num_comments}'
```

### Research a topic

Search stories and comments for any technology, tool, or concept.

```bash
# Stories about a topic, sorted by relevance
curl -sf "https://hn.algolia.com/api/v1/search?query=QUERY&tags=story&hitsPerPage=10" | jq '.hits[] | {title, points, num_comments, url}'

# High-signal results only (100+ points)
curl -sf "https://hn.algolia.com/api/v1/search?query=QUERY&tags=story&numericFilters=points%3E100&hitsPerPage=10" | jq '.hits[] | {title, points, num_comments, url}'

# Most recent results first
curl -sf "https://hn.algolia.com/api/v1/search_by_date?query=QUERY&tags=story&hitsPerPage=10" | jq '.hits[] | {title, points, num_comments, created_at}'
```

See [references/search.md](references/search.md) for all search parameters, filters, and advanced queries.

### Read discussions

Dive into comment threads on a story.

```bash
# Full comment thread in one request (use Algolia items endpoint)
curl -sf "https://hn.algolia.com/api/v1/items/ITEM_ID" | jq '{title, url, points, author, children: [.children[:10][] | {author, text: (.text[:300]), points, children_count: (.children | length)}]}'
```

See [references/items.md](references/items.md) for item fields, comment traversal, and the Firebase single-item endpoint.

### Find expert takes

Search comments by a specific user or find highly-upvoted comments on a topic.

```bash
# Comments by a specific user
curl -sf "https://hn.algolia.com/api/v1/search_by_date?tags=comment,author_USERNAME&hitsPerPage=10" | jq '.hits[] | {story_title, comment_text, points, created_at}'

# Comments on a topic (useful for "what do developers think about X?")
curl -sf "https://hn.algolia.com/api/v1/search?query=QUERY&tags=comment&numericFilters=points%3E10&hitsPerPage=10" | jq '.hits[] | {story_title, comment_text, author, points}'
```

### Track a user's activity

Look up a user's profile and recent submissions.

```bash
# User profile (karma, bio, account age)
curl -sf "https://hacker-news.firebaseio.com/v0/user/USERNAME.json" | jq '{id, karma, created, about}'
```

See [references/users.md](references/users.md) for user fields and how to fetch their submissions.

## Handling URLs

When the user shares a Hacker News URL, extract the relevant ID:

| URL Pattern | What to do |
|---|---|
| `news.ycombinator.com/item?id=ID` | Fetch item via Algolia: `/items/ID` |
| `news.ycombinator.com/user?id=USER` | Fetch user profile |
| `news.ycombinator.com` or `/news` | Show front page stories |
| `news.ycombinator.com/newest` | Show newest stories |
| `news.ycombinator.com/ask` | Show Ask HN |
| `news.ycombinator.com/show` | Show Show HN |

## Important notes

- Algolia API allows ~10,000 requests/hour per IP. Firebase has no official limit.
- Item `text` and user `about` fields contain HTML.
- Use Algolia for rich search results; use Firebase for individual items or live feeds.
