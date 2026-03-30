# Search API Reference (Algolia)

Base URL: `https://hn.algolia.com/api/v1`

## Endpoints

| Endpoint | Sort order |
|---|---|
| `/search` | By relevance |
| `/search_by_date` | By date (newest first) |

## Parameters

| Param | Type | Description |
|---|---|---|
| `query` | string | Full-text search query |
| `tags` | string | Filter by type (see below). Combine with comma for AND. |
| `numericFilters` | string | Filter by numeric fields (see below) |
| `hitsPerPage` | int | Results per page (max 1000, default 20) |
| `page` | int | Page number (0-indexed) |

## Tag filters

Use with the `tags` parameter. Comma-separated tags are AND-ed together.

| Tag | Description |
|---|---|
| `story` | Stories only |
| `comment` | Comments only |
| `ask_hn` | Ask HN posts |
| `show_hn` | Show HN posts |
| `job` | Job posts |
| `front_page` | Currently on front page |
| `author_USERNAME` | Posts by a specific user |
| `story_ID` | Comments on a specific story |

## Numeric filters

URL-encode the operators (`%3E` for `>`, `%3C` for `<`).

| Filter | Example |
|---|---|
| `points>N` | `numericFilters=points%3E100` |
| `num_comments>N` | `numericFilters=num_comments%3E50` |
| `created_at_i>UNIX` | `numericFilters=created_at_i%3E1700000000` |

Combine multiple filters with comma: `numericFilters=points%3E100,num_comments%3E50`

## Response fields (each hit)

| Field | Description |
|---|---|
| `title` | Story title |
| `url` | External link |
| `author` | Username |
| `points` | Upvote count |
| `num_comments` | Comment count |
| `created_at` | ISO timestamp |
| `objectID` | HN item ID |
| `story_title` | Parent story title (for comments) |
| `comment_text` | Comment body (for comments) |

## Examples

```bash
# Stories about Rust with 100+ points
curl -sf "https://hn.algolia.com/api/v1/search?query=rust&tags=story&numericFilters=points%3E100&hitsPerPage=10" | jq '.hits[] | {title, points, num_comments, url}'

# Recent Ask HN posts
curl -sf "https://hn.algolia.com/api/v1/search_by_date?tags=ask_hn&hitsPerPage=10" | jq '.hits[] | {title, points, num_comments, created_at}'

# Comments by a specific user
curl -sf "https://hn.algolia.com/api/v1/search_by_date?tags=comment,author_dang&hitsPerPage=5" | jq '.hits[] | {story_title, comment_text, points, created_at}'

# Front page stories right now
curl -sf "https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=30" | jq '.hits[] | {title, url, points, num_comments, author}'
```
