# Items & Comments Reference

## Fetch a single item (Firebase)

```bash
curl -sf "https://hacker-news.firebaseio.com/v0/item/ITEM_ID.json" | jq .
```

## Item fields

| Field | Type | Description |
|---|---|---|
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

## Reading comment threads

### Via Firebase (multiple requests)

Comments are items with `type: "comment"`. Follow `kids` arrays to traverse threads.

```bash
# Get top-level comments for a story
STORY_ID=12345
curl -sf "https://hacker-news.firebaseio.com/v0/item/${STORY_ID}.json" \
  | jq '.kids[0:5] | .[]' \
  | xargs -I{} curl -sf "https://hacker-news.firebaseio.com/v0/item/{}.json" \
  | jq '{id, by, text: (.text[:300]), score}'
```

### Via Algolia (single request, recommended)

The Algolia `/items/` endpoint returns the full comment tree in one request:

```bash
curl -sf "https://hn.algolia.com/api/v1/items/ITEM_ID" | jq '{title, url, points, author, children: [.children[:10][] | {author, text: (.text[:300]), points, children_count: (.children | length)}]}'
```

This is the preferred approach for reading discussions — it avoids the N+1 problem of Firebase.
