# SEC EDGAR API Endpoints

Free public access to SEC company filings, financial data, and insider transactions. No API key required -- just include a `User-Agent` header with your name and email.

**Rate limit:** 10 requests/second. All requests must include a descriptive `User-Agent`.

## Base URLs

| API | Base URL | Purpose |
|-----|----------|---------|
| Submissions | `https://data.sec.gov/submissions/` | Filing history by company |
| Company Facts | `https://data.sec.gov/api/xbrl/companyfacts/` | All XBRL financial data for a company |
| Company Concept | `https://data.sec.gov/api/xbrl/companyconcept/` | Single financial concept across filings |
| XBRL Frames | `https://data.sec.gov/api/xbrl/frames/` | Single concept across all companies |
| Full-Text Search | `https://efts.sec.gov/LATEST/search-index` | Search filing text content |

**CIK format:** 10-digit zero-padded, e.g., Apple = `CIK0000320193`. Find CIKs at `https://www.sec.gov/cgi-bin/browse-edgar?company=COMPANY&CIK=&type=&owner=include&count=10&action=getcompany`.

## Company Filing History

Returns all filings for a company -- 10-K, 10-Q, 8-K, proxy statements, insider trades, etc.

```bash
# Apple's recent filings
curl -sf -A "claude-code your@email.com" \
  "https://data.sec.gov/submissions/CIK0000320193.json" | jq '{name, cik, tickers, exchanges, filings: .filings.recent | {form: .form[:10], date: .filingDate[:10], description: .primaryDocDescription[:10]}}'

# Just recent filing types and dates
curl -sf -A "claude-code your@email.com" \
  "https://data.sec.gov/submissions/CIK0000320193.json" | jq '[.filings.recent | to_entries[] | select(.key == "form" or .key == "filingDate" or .key == "primaryDocDescription") | {(.key): .value[:5]}]'
```

Key response fields: `name`, `cik`, `tickers`, `exchanges`, `filings.recent.form[]`, `filings.recent.filingDate[]`, `filings.recent.primaryDocument[]`, `filings.recent.primaryDocDescription[]`.

## Company Financial Data (XBRL)

All financial facts from 10-K and 10-Q filings as structured data.

```bash
# All financial facts for Apple
curl -sf -A "claude-code your@email.com" \
  "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json" | jq '.facts["us-gaap"] | keys[:20]'

# Revenue history
curl -sf -A "claude-code your@email.com" \
  "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json" | jq '[.facts["us-gaap"].RevenueFromContractWithCustomerExcludingAssessedTax.units.USD[] | select(.form == "10-K") | {end, val}] | sort_by(.end) | .[-5:]'

# Net income history
curl -sf -A "claude-code your@email.com" \
  "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json" | jq '[.facts["us-gaap"].NetIncomeLoss.units.USD[] | select(.form == "10-K") | {end, val}] | sort_by(.end) | .[-5:]'

# EPS
curl -sf -A "claude-code your@email.com" \
  "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json" | jq '[.facts["us-gaap"].EarningsPerShareDiluted.units["USD/shares"][] | select(.form == "10-K") | {end, val}] | sort_by(.end) | .[-5:]'
```

## Single Concept Across All Companies

Compare a financial metric across the entire market for a specific period.

```bash
# All companies' revenue for CY2023
curl -sf -A "claude-code your@email.com" \
  "https://data.sec.gov/api/xbrl/frames/us-gaap/RevenueFromContractWithCustomerExcludingAssessedTax/USD/CY2023.json" | jq '.data[:5][] | {cik, entityName, val}'
```

Frame format: `us-gaap/CONCEPT/UNIT/CYYYYQnI.json`
- `CY2023` -- annual
- `CY2023Q1I` -- Q1 instant
- Units: `USD`, `USD-per-shares`, `shares`, `pure`

## Full-Text Search

Search the text content of all filings.

```bash
curl -sf -A "claude-code your@email.com" \
  "https://efts.sec.gov/LATEST/search-index?q=%22artificial%20intelligence%22&dateRange=custom&startdt=2024-01-01&enddt=2024-12-31&forms=10-K" | jq '.hits.hits[:5][] | {company: ._source.display_names[0], form: ._source.form_type, date: ._source.file_date, url: ._source.file_url}'
```

| Param | Description |
|-------|-------------|
| `q` | Search query (URL-encoded, phrases in `%22`) |
| `dateRange` | `custom` (requires `startdt`/`enddt`) |
| `startdt` / `enddt` | `YYYY-MM-DD` |
| `forms` | Comma-separated: `10-K`, `10-Q`, `8-K`, `4`, `SC 13D`, etc. |

## Important

- **User-Agent is required** -- requests without it are blocked. Use `"claude-code your@email.com"`.
- Rate limit: 10 req/sec.
- CIKs must be 10-digit zero-padded with `CIK` prefix.
- XBRL data only available from 10-K, 10-Q, 8-K, 20-F, 40-F, 6-K filings.
