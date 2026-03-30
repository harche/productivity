# Traders API Reference

## Leaderboard

```bash
curl -sf "https://data-api.polymarket.com/v1/leaderboard?category=OVERALL&timePeriod=DAY&limit=10" | jq .
```

| Param | Type | Description |
|---|---|---|
| `category` | string | `OVERALL`, `POLITICS`, `SPORTS`, `CRYPTO`, `CULTURE`, `WEATHER`, `ECONOMICS`, `TECH`, `FINANCE` |
| `timePeriod` | string | `DAY`, `WEEK`, `MONTH`, `ALL` |
| `orderBy` | string | `PNL` (default), `VOL` |
| `limit` | int | Max 50 |
| `offset` | int | For pagination |

Response: array of `{ rank, userName, pnl, vol, proxyWallet, profileImage, xUsername }`.

### Examples

```bash
# Top traders today by PnL
curl -sf "https://data-api.polymarket.com/v1/leaderboard?category=OVERALL&timePeriod=DAY&limit=10" | jq .

# Politics traders this week
curl -sf "https://data-api.polymarket.com/v1/leaderboard?category=POLITICS&timePeriod=WEEK&limit=10" | jq .

# All-time top by volume
curl -sf "https://data-api.polymarket.com/v1/leaderboard?category=OVERALL&timePeriod=ALL&orderBy=VOL&limit=10" | jq .
```

---

## Profile

```bash
curl -sf "https://gamma-api.polymarket.com/public-profile?address=WALLET_ADDRESS" | jq .
```

Response: `{ name, pseudonym, proxyWallet, bio, xUsername, profileImage, verifiedBadge, ... }`.

---

## Positions

### Open positions

```bash
curl -sf "https://data-api.polymarket.com/positions?user=WALLET_ADDRESS&limit=20&sortBy=CASHPNL" | jq .
```

### Closed positions

```bash
curl -sf "https://data-api.polymarket.com/closed-positions?user=WALLET_ADDRESS&limit=20" | jq .
```

| Param | Type | Description |
|---|---|---|
| `user` | address, **required** | Wallet address (`0x...`) |
| `limit` | int | Max results (default: 100, max: 500) |
| `offset` | int | Pagination offset |
| `sortBy` | string | `TOKENS`, `CURRENT`, `INITIAL`, `CASHPNL`, `PERCENTPNL`, `TITLE`, `PRICE`, `AVGPRICE` |
| `sortDirection` | string | `ASC`, `DESC` (default) |
| `market` | string | Filter by condition ID |
| `eventId` | int | Filter by event ID |

Response: array of `{ title, outcome, size, avgPrice, currentValue, cashPnl, percentPnl, ... }`.

---

## Trades

```bash
# Trades for a specific market
curl -sf "https://data-api.polymarket.com/trades?market=CONDITION_ID&limit=20" | jq .

# Trades by a user
curl -sf "https://data-api.polymarket.com/trades?user=WALLET_ADDRESS&limit=20" | jq .
```

| Param | Type | Description |
|---|---|---|
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
|---|---|---|
| `market` | string, **required** | Condition ID (hex `0x...`) |
| `limit` | int | Max holders per token (max: 20) |

Response: array of `{ token, holders: [{ name, pseudonym, amount, outcomeIndex, ... }] }` — one entry per outcome token.
