---
name: predictions
description: "Research prediction markets and event probabilities on Polymarket. Use when the user wants to check market odds, track how predictions are moving, or explore what crowds expect about upcoming events."
allowed-tools: Bash(curl:*)
---

# Predictions

Check what crowds expect about upcoming events, track how odds are shifting, and explore prediction markets on Polymarket.

## Quick start

```bash
# What's trending? Top events by 24h volume
curl -sf "https://gamma-api.polymarket.com/events?active=true&closed=false&order=volume24hr&ascending=false&limit=10" | jq '.[].title'
```

## Use cases

### Check odds on an event

Look up the current probability for any prediction market.

```bash
# Search for an event
curl -sf "https://gamma-api.polymarket.com/public-search?q=QUERY&limit_per_type=5" | jq '.events[] | {id, title, slug}'

# Get event details with market odds
curl -sf "https://gamma-api.polymarket.com/events/EVENT_ID" | jq '{title, markets: [.markets[] | {question, outcomePrices, volume, lastTradePrice}]}'

# Get a specific market by slug (from a URL)
curl -sf "https://gamma-api.polymarket.com/markets/slug/MARKET_SLUG" | jq '{question, outcomePrices, bestBid, bestAsk, lastTradePrice, volume}'
```

`outcomePrices` is a JSON string like `["0.65","0.35"]` — multiply by 100 for percentage (65% Yes, 35% No).

See [references/events-and-markets.md](references/events-and-markets.md) for all event/market fields and filtering options.

### Track how a market is moving

View price history to see how odds have shifted over time.

```bash
# First, get the CLOB token ID from the market
curl -sf "https://gamma-api.polymarket.com/markets/MARKET_ID" | jq '{question, clobTokenIds, outcomePrices}'

# Then fetch price history (use the first CLOB token ID = Yes token)
curl -sf "https://clob.polymarket.com/prices-history?market=CLOB_TOKEN_ID&interval=1w" | jq '.history | [.[-10:][] | {t: .t, price: .p}]'
```

Intervals: `1h`, `6h`, `1d`, `1w`, `1m`, `all`. See [references/price-history.md](references/price-history.md) for full options.

### Explore trending markets

Browse what is active, featured, or popular in a category.

```bash
# Trending events by volume
curl -sf "https://gamma-api.polymarket.com/events?active=true&closed=false&order=volume24hr&ascending=false&limit=10" | jq '.[] | {title, slug, markets: [.markets[] | {question, outcomePrices: .outcomePrices}]}'

# Featured events
curl -sf "https://gamma-api.polymarket.com/events?featured=true&limit=5" | jq '.[] | {title, slug}'

# Filter by category (politics, crypto, sports, etc.)
curl -sf "https://gamma-api.polymarket.com/events?tag_slug=politics&active=true&closed=false&order=volume24hr&ascending=false&limit=10" | jq '.[] | {title, slug}'

# Browse all available tags/categories
curl -sf "https://gamma-api.polymarket.com/tags?limit=20" | jq '.[] | {label, slug}'
```

See [references/events-and-markets.md](references/events-and-markets.md) for all sorting and filtering parameters.

### Analyze top traders

See who is making the best calls and what positions they hold.

```bash
# Top traders today by PnL
curl -sf "https://data-api.polymarket.com/v1/leaderboard?category=OVERALL&timePeriod=DAY&limit=10" | jq '.[] | {rank, userName, pnl, vol}'

# A trader's open positions
curl -sf "https://data-api.polymarket.com/positions?user=WALLET_ADDRESS&limit=20&sortBy=CASHPNL" | jq '.[] | {title, outcome, size, avgPrice, cashPnl}'

# Top holders for a specific market
curl -sf "https://data-api.polymarket.com/holders?market=CONDITION_ID&limit=5" | jq .
```

See [references/traders.md](references/traders.md) for leaderboard categories, position filters, and trade history.

## Handling URLs

When the user shares a Polymarket URL, extract the slug:

| URL Pattern | What to do |
|---|---|
| `polymarket.com/event/<slug>` | `GET /events/slug/<slug>` |
| `polymarket.com/event/<slug>/<market-slug>` | `GET /markets/slug/<market-slug>` |

## Key concepts

- **Event**: A topic with one or more markets (e.g., "Fed decision in March?")
- **Market**: A specific Yes/No question with outcome prices
- **CLOB Token ID**: Long numeric string needed for price history (found in `market.clobTokenIds`, array of `[yes_token, no_token]`)
- **Condition ID**: Hex string (`0x...`) identifying a market on-chain, used for trades/holders/positions

## Important notes

- `outcomePrices`: Multiply by 100 for percentage probability.
- `volume` / `volume24hr`: Total traded in USD.
- `oneDayPriceChange`: 24h price change (can be null).
- Price history `p` values: 0-1 scale, same as outcome prices.
