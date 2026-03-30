# FRED API Endpoints

**Base URL:** `https://api.stlouisfed.org/fred`

All requests require `api_key` and should include `file_type=json`.

```bash
FRED_KEY="${FRED_API_KEY:-$(security find-generic-password -s "fred-api-key" -w 2>/dev/null)}"
```

## Series Observations (Time Series Data)

The primary endpoint -- fetch data points for any economic indicator.

```bash
# GDP (quarterly)
curl -sf "https://api.stlouisfed.org/fred/series/observations?series_id=GDP&api_key=${FRED_KEY}&file_type=json" | jq '.observations[-5:][] | {date, value}'

# Unemployment rate (monthly)
curl -sf "https://api.stlouisfed.org/fred/series/observations?series_id=UNRATE&api_key=${FRED_KEY}&file_type=json" | jq '.observations[-12:][] | {date, value}'

# CPI - year-over-year percent change
curl -sf "https://api.stlouisfed.org/fred/series/observations?series_id=CPIAUCSL&units=pc1&api_key=${FRED_KEY}&file_type=json" | jq '.observations[-12:][] | {date, value}'

# Federal funds rate
curl -sf "https://api.stlouisfed.org/fred/series/observations?series_id=FEDFUNDS&api_key=${FRED_KEY}&file_type=json" | jq '.observations[-12:][] | {date, value}'

# 10-Year Treasury yield
curl -sf "https://api.stlouisfed.org/fred/series/observations?series_id=DGS10&api_key=${FRED_KEY}&file_type=json" | jq '.observations[-20:][] | {date, value}'

# S&P 500 index
curl -sf "https://api.stlouisfed.org/fred/series/observations?series_id=SP500&api_key=${FRED_KEY}&file_type=json" | jq '.observations[-20:][] | {date, value}'

# With date range
curl -sf "https://api.stlouisfed.org/fred/series/observations?series_id=GDP&observation_start=2023-01-01&observation_end=2025-12-31&api_key=${FRED_KEY}&file_type=json" | jq '.observations[] | {date, value}'
```

### Parameters

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

## Series Info

Get metadata about a series.

```bash
curl -sf "https://api.stlouisfed.org/fred/series?series_id=GDP&api_key=${FRED_KEY}&file_type=json" | jq '.seriess[0] | {id, title, frequency_short, units_short, seasonal_adjustment_short, last_updated}'
```

## Search Series

Find series by keyword.

```bash
# Search for inflation-related series
curl -sf "https://api.stlouisfed.org/fred/series/search?search_text=inflation&api_key=${FRED_KEY}&file_type=json&limit=10" | jq '.seriess[] | {id, title, frequency_short, popularity}'

# Search with ordering by popularity
curl -sf "https://api.stlouisfed.org/fred/series/search?search_text=housing%20starts&order_by=popularity&sort_order=desc&api_key=${FRED_KEY}&file_type=json&limit=5" | jq '.seriess[] | {id, title, popularity}'
```

### Parameters

| Param | Type | Description |
|-------|------|-------------|
| `search_text` | string | Keywords to search |
| `order_by` | string | `search_rank` (default), `series_id`, `title`, `popularity`, `last_updated` |
| `sort_order` | string | `asc` or `desc` |
| `limit` | int | Max results (default 1000) |
| `filter_variable` | string | `frequency`, `units`, `seasonal_adjustment` |
| `filter_value` | string | Value for the filter |
