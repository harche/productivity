---
name: fred
description: Query Federal Reserve Economic Data (FRED) for economic indicators like GDP, CPI, interest rates, unemployment, inflation, and 800k+ time series. Use when the user asks about economic data, macro indicators, interest rates, inflation, employment statistics, or economic trends.
allowed-tools: Bash(curl:*)
---

# FRED API

Access 800,000+ economic time series from the Federal Reserve Bank of St. Louis. Free API key required (instant approval).

**Base URL:** `https://api.stlouisfed.org/fred`

## Series Observations (Time Series Data)

The primary endpoint — fetch data points for any economic indicator.

```bash
# GDP (quarterly)
FRED_KEY="${FRED_API_KEY:-$(security find-generic-password -s "fred-api-key" -w 2>/dev/null)}" && curl -sf "https://api.stlouisfed.org/fred/series/observations?series_id=GDP&api_key=${FRED_KEY}&file_type=json" | jq '.observations[-5:][] | {date, value}'

# Unemployment rate (monthly)
FRED_KEY="${FRED_API_KEY:-$(security find-generic-password -s "fred-api-key" -w 2>/dev/null)}" && curl -sf "https://api.stlouisfed.org/fred/series/observations?series_id=UNRATE&api_key=${FRED_KEY}&file_type=json" | jq '.observations[-12:][] | {date, value}'

# CPI - Consumer Price Index (monthly, percent change from year ago)
FRED_KEY="${FRED_API_KEY:-$(security find-generic-password -s "fred-api-key" -w 2>/dev/null)}" && curl -sf "https://api.stlouisfed.org/fred/series/observations?series_id=CPIAUCSL&units=pc1&api_key=${FRED_KEY}&file_type=json" | jq '.observations[-12:][] | {date, value}'

# Federal funds rate
FRED_KEY="${FRED_API_KEY:-$(security find-generic-password -s "fred-api-key" -w 2>/dev/null)}" && curl -sf "https://api.stlouisfed.org/fred/series/observations?series_id=FEDFUNDS&api_key=${FRED_KEY}&file_type=json" | jq '.observations[-12:][] | {date, value}'

# 10-Year Treasury yield
FRED_KEY="${FRED_API_KEY:-$(security find-generic-password -s "fred-api-key" -w 2>/dev/null)}" && curl -sf "https://api.stlouisfed.org/fred/series/observations?series_id=DGS10&api_key=${FRED_KEY}&file_type=json" | jq '.observations[-20:][] | {date, value}'

# S&P 500 index
FRED_KEY="${FRED_API_KEY:-$(security find-generic-password -s "fred-api-key" -w 2>/dev/null)}" && curl -sf "https://api.stlouisfed.org/fred/series/observations?series_id=SP500&api_key=${FRED_KEY}&file_type=json" | jq '.observations[-20:][] | {date, value}'

# With date range
FRED_KEY="${FRED_API_KEY:-$(security find-generic-password -s "fred-api-key" -w 2>/dev/null)}" && curl -sf "https://api.stlouisfed.org/fred/series/observations?series_id=GDP&observation_start=2023-01-01&observation_end=2025-12-31&api_key=${FRED_KEY}&file_type=json" | jq '.observations[] | {date, value}'
```

| Param | Type | Description |
|-------|------|-------------|
| `series_id` | string | **Required.** FRED series ID (e.g., `GDP`, `UNRATE`) |
| `api_key` | string | **Required.** Your API key |
| `file_type` | string | `json` or `xml` |
| `observation_start` | string | Start date `YYYY-MM-DD` |
| `observation_end` | string | End date `YYYY-MM-DD` |
| `frequency` | string | `d`, `w`, `bw`, `m`, `q`, `sa`, `a` (aggregate to frequency) |
| `units` | string | `lin` (levels), `chg` (change), `ch1` (change from year ago), `pch` (% change), `pc1` (% change from year ago), `pca` (compounded annual rate of change), `log` (natural log) |
| `sort_order` | string | `asc` (default) or `desc` |
| `limit` | int | Max observations (default 100000) |

---

## Series Info

Get metadata about a series.

```bash
FRED_KEY="${FRED_API_KEY:-$(security find-generic-password -s "fred-api-key" -w 2>/dev/null)}" && curl -sf "https://api.stlouisfed.org/fred/series?series_id=GDP&api_key=${FRED_KEY}&file_type=json" | jq '.seriess[0] | {id, title, frequency_short, units_short, seasonal_adjustment_short, last_updated}'
```

---

## Search Series

Find series by keyword.

```bash
# Search for inflation-related series
FRED_KEY="${FRED_API_KEY:-$(security find-generic-password -s "fred-api-key" -w 2>/dev/null)}" && curl -sf "https://api.stlouisfed.org/fred/series/search?search_text=inflation&api_key=${FRED_KEY}&file_type=json&limit=10" | jq '.seriess[] | {id, title, frequency_short, popularity}'

# Search with ordering by popularity
FRED_KEY="${FRED_API_KEY:-$(security find-generic-password -s "fred-api-key" -w 2>/dev/null)}" && curl -sf "https://api.stlouisfed.org/fred/series/search?search_text=housing%20starts&order_by=popularity&sort_order=desc&api_key=${FRED_KEY}&file_type=json&limit=5" | jq '.seriess[] | {id, title, popularity}'
```

| Param | Type | Description |
|-------|------|-------------|
| `search_text` | string | Keywords to search |
| `order_by` | string | `search_rank` (default), `series_id`, `title`, `popularity`, `last_updated` |
| `sort_order` | string | `asc` or `desc` |
| `limit` | int | Max results (default 1000) |
| `filter_variable` | string | `frequency`, `units`, `seasonal_adjustment` |
| `filter_value` | string | Value for the filter |

---

## Key Series IDs

### Headline indicators

| Series ID | Description | Frequency |
|-----------|-------------|-----------|
| `GDP` | Gross Domestic Product | Quarterly |
| `GDPC1` | Real GDP | Quarterly |
| `UNRATE` | Unemployment Rate | Monthly |
| `CPIAUCSL` | Consumer Price Index (All Urban) | Monthly |
| `CPILFESL` | Core CPI (ex food & energy) | Monthly |
| `PCEPI` | PCE Price Index (Fed's preferred inflation gauge) | Monthly |
| `FEDFUNDS` | Federal Funds Effective Rate | Monthly |
| `DFEDTARU` | Fed Funds Target Rate (Upper) | Daily |

### Rates & yields

| Series ID | Description | Frequency |
|-----------|-------------|-----------|
| `DGS2` | 2-Year Treasury Yield | Daily |
| `DGS10` | 10-Year Treasury Yield | Daily |
| `DGS30` | 30-Year Treasury Yield | Daily |
| `T10Y2Y` | 10Y-2Y Spread (yield curve) | Daily |
| `T10YFF` | 10Y Treasury minus Fed Funds | Daily |
| `MORTGAGE30US` | 30-Year Fixed Mortgage Rate | Weekly |
| `BAMLH0A0HYM2` | High Yield Bond Spread | Daily |

### Labor market

| Series ID | Description | Frequency |
|-----------|-------------|-----------|
| `PAYEMS` | Total Nonfarm Payrolls | Monthly |
| `ICSA` | Initial Jobless Claims | Weekly |
| `CCSA` | Continued Jobless Claims | Weekly |
| `AHETPI` | Average Hourly Earnings | Monthly |
| `JTSJOL` | Job Openings (JOLTS) | Monthly |

### Markets & money

| Series ID | Description | Frequency |
|-----------|-------------|-----------|
| `SP500` | S&P 500 Index | Daily |
| `VIXCLS` | VIX Volatility Index | Daily |
| `DTWEXBGS` | Trade-Weighted Dollar Index | Daily |
| `M2SL` | M2 Money Supply | Monthly |
| `WALCL` | Fed Total Assets (balance sheet) | Weekly |

### Housing & consumer

| Series ID | Description | Frequency |
|-----------|-------------|-----------|
| `HOUST` | Housing Starts | Monthly |
| `CSUSHPISA` | Case-Shiller Home Price Index | Monthly |
| `UMCSENT` | Consumer Sentiment (UMich) | Monthly |
| `RSAFS` | Retail Sales | Monthly |

---

## Important

- API key is in macOS Keychain (service: `fred-api-key`).
- Rate limit: 120 requests/minute.
- Always include `file_type=json` for JSON responses (default is XML).
- Use `units=pc1` for year-over-year percent change (useful for CPI/inflation).
- Series with `.` values mean data not available for that date.
