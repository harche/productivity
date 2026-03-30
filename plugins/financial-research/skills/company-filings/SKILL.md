---
name: company-filings
description: "Analyze company fundamentals, financial statements, and insider transactions from SEC filings. Use when the user wants to research a company's financials, check insider trading activity, or review regulatory filings."
allowed-tools: Bash(curl:*)
---

# Company Filings Research

Look up company financials, SEC filings, and insider transactions. All data comes from SEC EDGAR -- free, no API key, just needs a `User-Agent` header.

## Quick example

```bash
# Apple's revenue over the last 5 years
curl -sf -A "claude-code your@email.com" \
  "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json" | jq '[.facts["us-gaap"].RevenueFromContractWithCustomerExcludingAssessedTax.units.USD[] | select(.form == "10-K") | {end, val}] | sort_by(.end) | .[-5:]'
```

## What you can do

### Research a company's financials

Pull structured financial data (revenue, net income, EPS, assets, debt) from 10-K and 10-Q filings:

```bash
# Net income history (annual)
curl -sf -A "claude-code your@email.com" \
  "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json" | jq '[.facts["us-gaap"].NetIncomeLoss.units.USD[] | select(.form == "10-K") | {end, val}] | sort_by(.end) | .[-5:]'
```

Replace the CIK and XBRL concept as needed. See [references/xbrl-concepts.md](references/xbrl-concepts.md) for common financial concepts and [references/common-ciks.md](references/common-ciks.md) for major company CIKs.

To discover what data is available for a company:

```bash
curl -sf -A "claude-code your@email.com" \
  "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json" | jq '.facts["us-gaap"] | keys[:20]'
```

### Check insider trading

Look at Form 4 filings in a company's submission history:

```bash
curl -sf -A "claude-code your@email.com" \
  "https://data.sec.gov/submissions/CIK0000320193.json" | jq '[.filings.recent | to_entries | map(select(.key == "form" or .key == "filingDate" or .key == "primaryDocDescription")) | map(.value) | transpose[] | select(.[0] == "4") | {form: .[0], date: .[1], description: .[2]}] | .[:10]'
```

### Find recent filings

Get a company's filing history (10-K, 10-Q, 8-K, proxy statements, etc.):

```bash
curl -sf -A "claude-code your@email.com" \
  "https://data.sec.gov/submissions/CIK0000320193.json" | jq '{name, cik, tickers, filings: [.filings.recent | to_entries | map(select(.key == "form" or .key == "filingDate" or .key == "primaryDocDescription")) | map(.value[:10]) | transpose[] | {form: .[0], date: .[1], description: .[2]}]}'
```

### Compare financial metrics across companies

Use the XBRL frames endpoint to get a single metric across all filers for a given period:

```bash
# All companies' revenue for CY2023
curl -sf -A "claude-code your@email.com" \
  "https://data.sec.gov/api/xbrl/frames/us-gaap/RevenueFromContractWithCustomerExcludingAssessedTax/USD/CY2023.json" | jq '.data[:5][] | {cik, entityName, val}'
```

### Search filing text

Full-text search across all SEC filings:

```bash
curl -sf -A "claude-code your@email.com" \
  "https://efts.sec.gov/LATEST/search-index?q=%22artificial%20intelligence%22&dateRange=custom&startdt=2024-01-01&enddt=2024-12-31&forms=10-K" | jq '.hits.hits[:5][] | {company: ._source.display_names[0], form: ._source.form_type, date: ._source.file_date}'
```

## References

- [references/api-endpoints.md](references/api-endpoints.md) -- full endpoint docs, parameters, CIK format, and rate limits
- [references/xbrl-concepts.md](references/xbrl-concepts.md) -- common XBRL financial concepts (revenue, EPS, assets, etc.)
- [references/common-ciks.md](references/common-ciks.md) -- CIKs for major companies

## Important

- **User-Agent is required** -- requests without it are blocked. Use `"claude-code your@email.com"`.
- Rate limit: 10 requests/second.
- CIKs must be 10-digit zero-padded with `CIK` prefix (e.g., `CIK0000320193`).
- Find CIKs: `https://www.sec.gov/cgi-bin/browse-edgar?company=COMPANY&CIK=&type=&owner=include&count=10&action=getcompany`
