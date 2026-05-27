# News

## Available News Providers

```python
providers = ib.reqNewsProviders()
for p in providers:
    print(f'{p.code}: {p.name}')
```

Typical providers (depends on subscription):

| Code | Provider |
|------|----------|
| `BRFG` | Briefing.com General Market Columns |
| `BRFUPDN` | Briefing.com Analyst Actions |
| `DJ-N` | Dow Jones Global Equity Trader |
| `DJ-RT` | Dow Jones Trader News |
| `DJ-RTA` | Dow Jones Top Stories Asia Pacific |
| `DJ-RTE` | Dow Jones Top Stories Europe |
| `DJ-RTG` | Dow Jones Top Stories Global |
| `DJNL` | Dow Jones Newsletters |

## Historical News for a Stock

```python
from ib_async import Stock

aapl = ib.qualifyContracts(Stock('AAPL', 'SMART', 'USD'))[0]

# Join provider codes with '+'
provider_codes = '+'.join(p.code for p in ib.reqNewsProviders())

news = ib.reqHistoricalNews(
    conId=aapl.conId,
    providerCodes=provider_codes,
    startDateTime='',      # empty = oldest available
    endDateTime='',        # empty = now
    totalResults=10,
)
for article in news:
    print(f'{article.time}: {article.headline}')
    print(f'  Provider: {article.providerCode}, ID: {article.articleId}')
```

### Headline format

Headlines include metadata tags like `{A:800015:L:en}` at the start — strip these for display:

```python
import re
clean = re.sub(r'\{[^}]+\}', '', article.headline).strip()
```

## Reading a Full Article

```python
article = ib.reqNewsArticle(providerCode='DJ-N', articleId='DJ-N$1e8dc8a8')
print(f'Type: {article.articleType}')  # 0 = text, 1 = binary/PDF
print(f'Body: {article.articleText}')
```

## News Ticks (Real-Time)

News ticks arrive on the ticker when subscribed to market data with the news generic tick:

```python
ticker = ib.reqMktData(contract, genericTickList='mdoff,292')
ib.sleep(5)
for tick in ib.newsTicks():
    print(f'{tick.timeStamp}: {tick.headline}')
```

## Gotchas

- News requires an IBKR news subscription. Without one, `reqHistoricalNews` returns results but `reqNewsArticle` may fail.
- `reqHistoricalNews` returns a list of `HistoricalNews` objects, not a special container.
- Article IDs are provider-specific (e.g., `DJ-N$1e8dc8a8`). Pass the full ID including provider prefix to `reqNewsArticle`.
- Rate-limited — don't request articles in a tight loop.
- Dow Jones content is the most comprehensive for US stocks.
