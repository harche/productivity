# User Profiles Reference

## Fetch a user profile (Firebase)

```bash
curl -sf "https://hacker-news.firebaseio.com/v0/user/USERNAME.json" | jq '{id, karma, created, about}'
```

## User fields

| Field | Type | Description |
|---|---|---|
| `id` | string | Username (case-sensitive) |
| `karma` | int | Karma score |
| `created` | int | Unix timestamp of account creation |
| `about` | string | Bio (HTML) |
| `submitted` | array | Item IDs authored by this user |

## Fetch a user's recent submissions

The `submitted` array contains all item IDs by this user (stories, comments, etc). Fetch individual items for details:

```bash
# Get a user's 5 most recent submissions
curl -sf "https://hacker-news.firebaseio.com/v0/user/USERNAME.json" \
  | jq '.submitted[0:5] | .[]' \
  | xargs -I{} curl -sf "https://hacker-news.firebaseio.com/v0/item/{}.json" \
  | jq '{id, type, title, text: (.text[:200]), score, time}'
```

## Search a user's activity (Algolia, faster)

```bash
# All stories by a user
curl -sf "https://hn.algolia.com/api/v1/search_by_date?tags=story,author_USERNAME&hitsPerPage=10" | jq '.hits[] | {title, points, num_comments, created_at}'

# All comments by a user
curl -sf "https://hn.algolia.com/api/v1/search_by_date?tags=comment,author_USERNAME&hitsPerPage=10" | jq '.hits[] | {story_title, comment_text, points, created_at}'
```
