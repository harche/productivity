# Common XBRL Financial Concepts

These are the `us-gaap` concept names used in the EDGAR XBRL API. Use them with the Company Facts or Company Concept endpoints.

## Income statement

| Concept | What it is |
|---------|-----------|
| `RevenueFromContractWithCustomerExcludingAssessedTax` | Revenue |
| `NetIncomeLoss` | Net income |
| `EarningsPerShareDiluted` | Diluted EPS |
| `EarningsPerShareBasic` | Basic EPS |
| `OperatingIncomeLoss` | Operating income |
| `GrossProfit` | Gross profit |
| `CostOfGoodsAndServicesSold` | Cost of revenue |
| `ResearchAndDevelopmentExpense` | R&D expense |

## Balance sheet

| Concept | What it is |
|---------|-----------|
| `Assets` | Total assets |
| `Liabilities` | Total liabilities |
| `StockholdersEquity` | Shareholders' equity |
| `CashAndCashEquivalentsAtCarryingValue` | Cash |
| `LongTermDebt` | Long-term debt |
| `CommonStockSharesOutstanding` | Shares outstanding |
| `AccountsReceivableNetCurrent` | Accounts receivable |
| `Goodwill` | Goodwill |

## Usage example

```bash
# Get Apple's revenue from 10-K filings
curl -sf -A "claude-code your@email.com" \
  "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json" | jq '[.facts["us-gaap"].RevenueFromContractWithCustomerExcludingAssessedTax.units.USD[] | select(.form == "10-K") | {end, val}] | sort_by(.end) | .[-5:]'
```

Units vary by concept:
- Most financials: `.units.USD[]`
- Per-share metrics (EPS): `.units["USD/shares"][]`
- Share counts: `.units.shares[]`
- Ratios/percentages: `.units.pure[]`
