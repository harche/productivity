# Events & Markets API Reference

## APIs

| API | Base URL | Purpose |
|---|---|---|
| Gamma | `https://gamma-api.polymarket.com` | Events, markets, search, tags, comments, profiles |
| Data | `https://data-api.polymarket.com` | Positions, trades, leaderboard, holders, open interest |
| CLOB | `https://clob.polymarket.com` | Price history |

Full docs: https://docs.polymarket.com/api-reference/introduction

---

## Search

```bash
curl -sf "https://gamma-api.polymarket.com/public-search?q=QUERY&limit_per_type=5" | jq .
```

| Param | Type | Description |
|---|---|---|
| `q` | string, **required** | Search query (URL-encode spaces as `%20`) |
| `limit_per_type` | int | Max results per category (events, tags, profiles) |

Response: `{ events: [...], tags: [...], profiles: [...] }`

---

## List events

```bash
curl -sf "https://gamma-api.polymarket.com/events?active=true&closed=false&order=volume24hr&ascending=false&limit=10" | jq .
```

| Param | Type | Description |
|---|---|---|
| `limit` | int | Results per page |
| `offset` | int | Skip N results |
| `order` | string | Sort: `volume24hr`, `volume`, `liquidity`, `startDate`, `endDate`, `competitive` |
| `ascending` | bool | Sort direction (use `false` for descending) |
| `active` | bool | Filter to active events |
| `closed` | bool | Filter to closed events |
| `featured` | bool | Filter to featured events |
| `tag_slug` | string | Filter by tag slug (e.g., `politics`, `crypto`, `sports`) |
| `tag_id` | int | Filter by tag ID |

Response: array of Event objects, each with nested `markets` array.

---

## Event detail

```bash
# By ID
curl -sf "https://gamma-api.polymarket.com/events/EVENT_ID" | jq .

# By slug
curl -sf "https://gamma-api.polymarket.com/events/slug/EVENT_SLUG" | jq .
```

---

## Market detail

```bash
# By ID
curl -sf "https://gamma-api.polymarket.com/markets/MARKET_ID" | jq .

# By slug
curl -sf "https://gamma-api.polymarket.com/markets/slug/MARKET_SLUG" | jq .
```

Key fields: `question`, `outcomePrices`, `bestBid`, `bestAsk`, `lastTradePrice`, `oneDayPriceChange`, `volume`, `conditionId`, `clobTokenIds`.

---

## Tags

```bash
curl -sf "https://gamma-api.polymarket.com/tags?limit=20" | jq .
```

Response: array of `{ id, label, slug }`. Use `slug` with `events?tag_slug=`.

---

## Comments

```bash
curl -sf "https://gamma-api.polymarket.com/comments?parent_entity_type=Event&parent_entity_id=EVENT_ID&limit=10" | jq .
```

| Param | Type | Description |
|---|---|---|
| `parent_entity_type` | string, **required** | `Event`, `Series`, or `market` |
| `parent_entity_id` | int, **required** | The entity's numeric ID |
| `limit` | int | Max results |
| `offset` | int | Pagination offset |

---

## Open interest

```bash
curl -sf "https://data-api.polymarket.com/oi?market=CONDITION_ID" | jq .
```

Response: `[{ market, value }]` — value is total open interest in USD.
