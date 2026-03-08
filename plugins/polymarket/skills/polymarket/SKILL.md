---
name: polymarket
description: Browse and analyze Polymarket prediction markets, events, prices, and leaderboards. Use when the user asks about prediction markets, shares a Polymarket URL, wants to check market odds/probabilities, view trending events, look up trader positions, or see price history.
allowed-tools: Bash(curl:*)
---

# Polymarket

Browse prediction markets on Polymarket using their public REST APIs. No API keys, authentication, or dependencies required — just `curl` and `jq`.

Full API reference: https://docs.polymarket.com/api-reference/introduction
- Gamma API docs: https://docs.polymarket.com/api-reference/gamma-api
- Data API docs: https://docs.polymarket.com/api-reference/data-api
- OpenAPI specs: https://docs.polymarket.com/api-spec/gamma-openapi.yaml and https://docs.polymarket.com/api-spec/data-openapi.yaml

## APIs

| API | Base URL | Purpose |
|-----|----------|---------|
| Gamma | `https://gamma-api.polymarket.com` | Events, markets, search, tags, comments, profiles |
| Data | `https://data-api.polymarket.com` | Positions, trades, leaderboard, holders, open interest |
| CLOB | `https://clob.polymarket.com` | Price history |

## Key Concepts

- **Event**: A topic containing one or more markets (e.g., "Fed decision in March?").
- **Market**: A specific question with Yes/No outcomes (e.g., "Will the Fed cut rates by 25bps?"). Identified by numeric `id` (Gamma) or `conditionId` (on-chain hex).
- **Outcome prices**: JSON string like `'["0.65","0.35"]'` — these are probabilities (0.65 = 65% Yes).
- **CLOB Token ID**: Long numeric string found in `market.clobTokenIds`. Needed for price history. The array has two entries: `[yes_token, no_token]`.
- **Condition ID**: Hex string (`0x...`) identifying a market on-chain. Used for trades, holders, positions, and open interest.

---

## Search

Search across events, tags, and profiles.

```bash
curl -sf "https://gamma-api.polymarket.com/public-search?q=QUERY&limit_per_type=5" | jq .
```

| Param | Type | Description |
|-------|------|-------------|
| `q` | string, **required** | Search query (URL-encode spaces as `%20`) |
| `limit_per_type` | int | Max results per category (events, tags, profiles) |

Response: `{ events: [...], tags: [...], profiles: [...] }`

---

## Events

List or filter events. Each event contains nested `markets` with current prices.

```bash
# Trending active events by 24h volume
curl -sf "https://gamma-api.polymarket.com/events?active=true&closed=false&order=volume24hr&ascending=false&limit=10" | jq .

# Featured events
curl -sf "https://gamma-api.polymarket.com/events?featured=true&limit=5" | jq .

# Events by tag
curl -sf "https://gamma-api.polymarket.com/events?tag_slug=politics&active=true&closed=false&order=volume24hr&ascending=false&limit=10" | jq .

# Paginate
curl -sf "https://gamma-api.polymarket.com/events?active=true&closed=false&limit=10&offset=10" | jq .
```

| Param | Type | Description |
|-------|------|-------------|
| `limit` | int | Results per page |
| `offset` | int | Skip N results |
| `order` | string | Sort field: `volume24hr`, `volume`, `liquidity`, `startDate`, `endDate`, `competitive` |
| `ascending` | bool | Sort direction (default: unspecified; use `false` for descending) |
| `active` | bool | Filter to active events |
| `closed` | bool | Filter to closed events |
| `featured` | bool | Filter to featured events |
| `tag_slug` | string | Filter by tag slug (e.g., `politics`, `crypto`, `sports`) |
| `tag_id` | int | Filter by tag ID |

Response: array of Event objects, each with nested `markets` array.

---

## Event Detail

```bash
# By ID
curl -sf "https://gamma-api.polymarket.com/events/EVENT_ID" | jq .

# By slug
curl -sf "https://gamma-api.polymarket.com/events/slug/EVENT_SLUG" | jq .
```

---

## Market Detail

```bash
# By ID
curl -sf "https://gamma-api.polymarket.com/markets/MARKET_ID" | jq .

# By slug
curl -sf "https://gamma-api.polymarket.com/markets/slug/MARKET_SLUG" | jq .
```

Key response fields: `question`, `outcomePrices`, `bestBid`, `bestAsk`, `lastTradePrice`, `oneDayPriceChange`, `volume`, `conditionId`, `clobTokenIds`.

---

## Price History

Get historical prices for a market token. The `market` param is a **CLOB Token ID** (long numeric string), not a condition ID.

```bash
curl -sf "https://clob.polymarket.com/prices-history?market=CLOB_TOKEN_ID&interval=1d" | jq .
```

| Param | Type | Description |
|-------|------|-------------|
| `market` | string, **required** | CLOB token ID (from `market.clobTokenIds`) |
| `interval` | string | `1h`, `6h`, `1d`, `1w`, `1m`, `all` |
| `fidelity` | int | Granularity in minutes (default: 1) |
| `startTs` | int | Unix timestamp start |
| `endTs` | int | Unix timestamp end |

Response: `{ history: [{ t: <unix_timestamp>, p: <price> }, ...] }`

---

## Tags

```bash
curl -sf "https://gamma-api.polymarket.com/tags?limit=20" | jq .
```

Response: array of `{ id, label, slug }`. Use `slug` with `events?tag_slug=`.

---

## Leaderboard

```bash
# Top traders today by PnL
curl -sf "https://data-api.polymarket.com/v1/leaderboard?category=OVERALL&timePeriod=DAY&limit=10" | jq .

# Politics traders this week
curl -sf "https://data-api.polymarket.com/v1/leaderboard?category=POLITICS&timePeriod=WEEK&limit=10" | jq .

# All-time top by volume
curl -sf "https://data-api.polymarket.com/v1/leaderboard?category=OVERALL&timePeriod=ALL&orderBy=VOL&limit=10" | jq .
```

| Param | Type | Description |
|-------|------|-------------|
| `category` | string | `OVERALL`, `POLITICS`, `SPORTS`, `CRYPTO`, `CULTURE`, `WEATHER`, `ECONOMICS`, `TECH`, `FINANCE` |
| `timePeriod` | string | `DAY`, `WEEK`, `MONTH`, `ALL` |
| `orderBy` | string | `PNL` (default), `VOL` |
| `limit` | int | Max 50 |
| `offset` | int | For pagination |

Response: array of `{ rank, userName, pnl, vol, proxyWallet, profileImage, xUsername }`.

---

## Positions

Get a user's open or closed positions.

```bash
# Open positions
curl -sf "https://data-api.polymarket.com/positions?user=WALLET_ADDRESS&limit=20&sortBy=CASHPNL" | jq .

# Closed positions
curl -sf "https://data-api.polymarket.com/closed-positions?user=WALLET_ADDRESS&limit=20" | jq .
```

| Param | Type | Description |
|-------|------|-------------|
| `user` | address, **required** | Wallet address (`0x...`) |
| `limit` | int | Max results (default: 100, max: 500) |
| `offset` | int | Pagination offset |
| `sortBy` | string | `TOKENS`, `CURRENT`, `INITIAL`, `CASHPNL`, `PERCENTPNL`, `TITLE`, `PRICE`, `AVGPRICE` |
| `sortDirection` | string | `ASC`, `DESC` (default) |
| `market` | string | Filter by condition ID |
| `eventId` | int | Filter by event ID |

Response: array of `{ title, outcome, size, avgPrice, currentValue, cashPnl, percentPnl, ... }`.

---

## Profile

```bash
curl -sf "https://gamma-api.polymarket.com/public-profile?address=WALLET_ADDRESS" | jq .
```

Response: `{ name, pseudonym, proxyWallet, bio, xUsername, profileImage, verifiedBadge, ... }`.

---

## Trades

```bash
# Trades for a specific market
curl -sf "https://data-api.polymarket.com/trades?market=CONDITION_ID&limit=20" | jq .

# Trades by a user
curl -sf "https://data-api.polymarket.com/trades?user=WALLET_ADDRESS&limit=20" | jq .
```

| Param | Type | Description |
|-------|------|-------------|
| `market` | string | Condition ID (hex `0x...`) |
| `user` | string | Wallet address |
| `limit` | int | Max 10000 (default: 100) |
| `offset` | int | Pagination offset |
| `side` | string | `BUY` or `SELL` |

Response: array of `{ title, side, size, price, outcome, timestamp, transactionHash, ... }`.

---

## Holders

Top holders for a market.

```bash
curl -sf "https://data-api.polymarket.com/holders?market=CONDITION_ID&limit=5" | jq .
```

| Param | Type | Description |
|-------|------|-------------|
| `market` | string, **required** | Condition ID (hex `0x...`) |
| `limit` | int | Max holders per token (max: 20) |

Response: array of `{ token, holders: [{ name, pseudonym, amount, outcomeIndex, ... }] }` — one entry per outcome token.

---

## Open Interest

```bash
curl -sf "https://data-api.polymarket.com/oi?market=CONDITION_ID" | jq .
```

Response: `[{ market, value }]` — value is total open interest in USD.

---

## Comments

```bash
curl -sf "https://gamma-api.polymarket.com/comments?parent_entity_type=Event&parent_entity_id=EVENT_ID&limit=10" | jq .
```

| Param | Type | Description |
|-------|------|-------------|
| `parent_entity_type` | string, **required** | `Event`, `Series`, or `market` |
| `parent_entity_id` | int, **required** | The entity's numeric ID |
| `limit` | int | Max results |
| `offset` | int | Pagination offset |

---

## URL Parsing

When the user shares a Polymarket URL, extract the slug and use the appropriate endpoint:

| URL Pattern | Action |
|-------------|--------|
| `polymarket.com/event/<slug>` | `GET /events/slug/<slug>` |
| `polymarket.com/event/<slug>/<market-slug>` | `GET /markets/slug/<market-slug>` |

---

## Interpreting Results

- `outcomePrices`: Multiply by 100 for percentage probability.
- `volume` / `volume24hr`: Total traded in USD.
- `bestBid` / `bestAsk`: Current order book prices.
- `lastTradePrice`: Most recent trade price.
- `oneDayPriceChange`: 24h price change (can be null if no change).
- Price history `p` values: 0-1 scale, same as outcome prices.
