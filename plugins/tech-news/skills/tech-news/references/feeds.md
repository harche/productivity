# Story Feeds Reference (Firebase API)

Base URL: `https://hacker-news.firebaseio.com/v0`

Each feed endpoint returns an array of up to 500 item IDs. Fetch individual items for details.

## Feed endpoints

| Feed | Endpoint | Description |
|---|---|---|
| Top | `/topstories.json` | Ranked by score |
| New | `/newstories.json` | Most recent |
| Best | `/beststories.json` | All-time best |
| Ask HN | `/askstories.json` | Ask HN posts |
| Show HN | `/showstories.json` | Show HN posts |
| Jobs | `/jobstories.json` | Job listings |

## Basic usage

```bash
# Get top 10 story IDs
curl -sf "https://hacker-news.firebaseio.com/v0/topstories.json" | jq '.[0:10]'
```

## Fetch stories with details

Feed endpoints return only IDs. To get full details, fetch each item:

```bash
# Top 10 stories with titles, scores, and comment counts
curl -sf "https://hacker-news.firebaseio.com/v0/topstories.json" \
  | jq '.[0:10] | .[]' \
  | xargs -I{} curl -sf "https://hacker-news.firebaseio.com/v0/item/{}.json" \
  | jq '{id, title, by, score, descendants, url, time}'
```

> **Tip**: For faster results, use the Algolia `front_page` tag instead:
> ```bash
> curl -sf "https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=30" | jq '.hits[] | {title, url, points, num_comments}'
> ```
> This returns full details in a single request.
