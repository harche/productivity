---
name: economic-data
description: "Research economic trends and indicators — GDP, inflation, employment, interest rates, and 800k+ time series from the Federal Reserve. Use when the user asks about economic conditions, wants historical data, or needs to compare economic metrics."
allowed-tools: Bash(curl:*)
---

# Economic Data Research

Look up economic indicators, track trends over time, and compare metrics using 800,000+ time series from the Federal Reserve (FRED).

## Quick example

```bash
# Get the latest unemployment rate
FRED_KEY="${FRED_API_KEY:-$(security find-generic-password -s "fred-api-key" -w 2>/dev/null)}" && curl -sf "https://api.stlouisfed.org/fred/series/observations?series_id=UNRATE&api_key=${FRED_KEY}&file_type=json" | jq '.observations[-1] | {date, value}'
```

## What you can do

### Check current economic conditions

Pull the latest reading for any major indicator. Common ones:

- `GDP` / `GDPC1` -- nominal / real GDP (quarterly)
- `UNRATE` -- unemployment rate (monthly)
- `CPIAUCSL` -- CPI inflation; add `&units=pc1` for year-over-year % change
- `FEDFUNDS` -- federal funds rate (monthly)
- `DGS10` -- 10-year Treasury yield (daily)
- `SP500` -- S&P 500 index (daily)

See [references/series-ids.md](references/series-ids.md) for the full list of common series.

### Get historical data on an indicator

Add `observation_start` and `observation_end` to scope a date range:

```bash
FRED_KEY="${FRED_API_KEY:-$(security find-generic-password -s "fred-api-key" -w 2>/dev/null)}" && curl -sf "https://api.stlouisfed.org/fred/series/observations?series_id=GDP&observation_start=2020-01-01&observation_end=2025-12-31&api_key=${FRED_KEY}&file_type=json" | jq '.observations[] | {date, value}'
```

Use `units=pch` (% change), `pc1` (% change from year ago), or `chg` (level change) to transform the data. Use `frequency=a` to aggregate to annual, `q` for quarterly, etc.

### Compare metrics across time

Fetch multiple series and align by date. Example -- unemployment vs. inflation:

```bash
FRED_KEY="${FRED_API_KEY:-$(security find-generic-password -s "fred-api-key" -w 2>/dev/null)}"
curl -sf "https://api.stlouisfed.org/fred/series/observations?series_id=UNRATE&observation_start=2020-01-01&api_key=${FRED_KEY}&file_type=json" | jq '.observations[-12:][] | {date, unemployment: .value}'
curl -sf "https://api.stlouisfed.org/fred/series/observations?series_id=CPIAUCSL&units=pc1&observation_start=2020-01-01&api_key=${FRED_KEY}&file_type=json" | jq '.observations[-12:][] | {date, cpi_yoy: .value}'
```

### Explore available series

Search by keyword when you don't know the series ID:

```bash
FRED_KEY="${FRED_API_KEY:-$(security find-generic-password -s "fred-api-key" -w 2>/dev/null)}" && curl -sf "https://api.stlouisfed.org/fred/series/search?search_text=housing%20starts&order_by=popularity&sort_order=desc&api_key=${FRED_KEY}&file_type=json&limit=5" | jq '.seriess[] | {id, title, frequency_short, popularity}'
```

Get metadata about a series (units, frequency, last update):

```bash
FRED_KEY="${FRED_API_KEY:-$(security find-generic-password -s "fred-api-key" -w 2>/dev/null)}" && curl -sf "https://api.stlouisfed.org/fred/series?series_id=GDP&api_key=${FRED_KEY}&file_type=json" | jq '.seriess[0] | {id, title, frequency_short, units_short, seasonal_adjustment_short, last_updated}'
```

## References

- [references/api-endpoints.md](references/api-endpoints.md) -- full endpoint docs, parameters, and query options
- [references/series-ids.md](references/series-ids.md) -- common series IDs by category (rates, labor, housing, markets)

## Important

- API key is in macOS Keychain (service: `fred-api-key`).
- Rate limit: 120 requests/minute.
- Always include `file_type=json` (default is XML).
- Series with `.` values mean data not available for that date.
