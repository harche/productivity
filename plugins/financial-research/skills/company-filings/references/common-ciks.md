# Common Company CIKs

CIKs must be 10-digit zero-padded with `CIK` prefix for the EDGAR API.

| Company | CIK | Ticker |
|---------|-----|--------|
| Apple | `0000320193` | AAPL |
| Microsoft | `0000789019` | MSFT |
| Tesla | `0001318605` | TSLA |
| Amazon | `0001018724` | AMZN |
| Google (Alphabet) | `0001652044` | GOOGL |
| Meta | `0001326801` | META |
| NVIDIA | `0001045810` | NVDA |

## Look up any company's CIK

```bash
curl -sf -A "claude-code your@email.com" \
  "https://www.sec.gov/cgi-bin/browse-edgar?company=COMPANY_NAME&CIK=&type=&owner=include&count=10&action=getcompany"
```

Replace `COMPANY_NAME` with the company name (URL-encoded).
