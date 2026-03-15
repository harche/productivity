---
name: gdelt
description: Search and analyze global news, events, and television coverage using GDELT APIs. Use when the user asks about global news trends, media coverage, geopolitical events, news sentiment, TV news mentions, or wants to search worldwide news articles.
allowed-tools: Bash(curl:*)
---

# GDELT

Search and analyze global news coverage across 65+ languages using the GDELT Project APIs. No authentication, API keys, or dependencies required — just `curl` and `jq`.

GDELT monitors news media worldwide in near real-time, covering online news, print, and 163 television stations.

## APIs

| API | Base URL | Coverage |
|-----|----------|----------|
| DOC 2.0 | `https://api.gdeltproject.org/api/v2/doc/doc` | Online news articles (3-month rolling window) |
| GEO 2.0 | `https://api.gdeltproject.org/api/v2/geo/geo` | Geographic mentions (last 7 days) |
| TV 2.0 | `https://api.gdeltproject.org/api/v2/tv/tv` | TV news transcripts (2009-present, 163 stations) |
| Context 2.0 | `https://api.gdeltproject.org/api/v2/context/context` | Sentence-level search (last 72 hours) |

---

## DOC API — Article Search

Search online news articles from around the world.

```bash
# Search recent articles (last 7 days, top 25)
curl -sf "https://api.gdeltproject.org/api/v2/doc/doc?query=QUERY&mode=artlist&format=json&maxrecords=25&timespan=7d" | jq '.articles[] | {title, url, source: .domain, language: .language, seendate, tone}'

# Articles from a specific source
curl -sf "https://api.gdeltproject.org/api/v2/doc/doc?query=QUERY%20domain:reuters.com&mode=artlist&format=json&maxrecords=25" | jq '.articles[] | {title, url, seendate}'

# Articles in a specific language
curl -sf "https://api.gdeltproject.org/api/v2/doc/doc?query=QUERY%20sourcelang:spanish&mode=artlist&format=json&maxrecords=25" | jq .

# Articles from a specific country
curl -sf "https://api.gdeltproject.org/api/v2/doc/doc?query=QUERY%20sourcecountry:france&mode=artlist&format=json&maxrecords=25" | jq .

# Negative-tone articles
curl -sf "https://api.gdeltproject.org/api/v2/doc/doc?query=QUERY%20tone<-5&mode=artlist&format=json&maxrecords=25" | jq .

# Coverage volume over time
curl -sf "https://api.gdeltproject.org/api/v2/doc/doc?query=QUERY&mode=timelinevol&format=json&timespan=3m" | jq .
```

| Param | Type | Description |
|-------|------|-------------|
| `query` | string | Search terms with operators (URL-encode spaces as `%20`) |
| `mode` | string | `artlist` (articles), `timelinevol` (timeline), `timelinetone` (sentiment), `tonechart` |
| `format` | string | `json`, `csv`, `rss`, `html` |
| `timespan` | string | `15m`, `1h`, `2d`, `1w`, `3m` |
| `maxrecords` | int | 1-250 (default 75) |

### Query operators

| Operator | Description | Example |
|----------|-------------|---------|
| `"phrase"` | Exact phrase | `"climate change"` |
| `OR` | Boolean OR | `trump OR biden` |
| `-term` | Exclude | `-sports` |
| `domain:` | Source domain | `domain:bbc.com` |
| `domainis:` | Exact domain | `domainis:un.org` |
| `sourcelang:` | Language | `sourcelang:french` |
| `sourcecountry:` | Country | `sourcecountry:india` |
| `theme:` | GDELT theme | `theme:TERROR`, `theme:PROTEST`, `theme:ECON_BANKRUPTCY` |
| `tone<N` / `tone>N` | Sentiment filter | `tone<-5` (negative), `tone>5` (positive) |
| `near20:"a b"` | Proximity search | `near10:"trump putin"` |

---

## GEO API — Geographic Search

See where in the world a topic is being mentioned. Returns GeoJSON for mapping.

```bash
# Country-level map of mentions
curl -sf "https://api.gdeltproject.org/api/v2/geo/geo?query=QUERY&mode=country&format=geojson&timespan=7d" | jq .

# Point data (specific locations mentioned)
curl -sf "https://api.gdeltproject.org/api/v2/geo/geo?query=QUERY&mode=pointdata&format=geojson&timespan=7d&maxpoints=100" | jq '.features[:10][] | {name: .properties.name, count: .properties.count, lat: .geometry.coordinates[1], lon: .geometry.coordinates[0]}'

# Source country (where articles originate)
curl -sf "https://api.gdeltproject.org/api/v2/geo/geo?query=QUERY&mode=sourcecountry&format=geojson&timespan=7d" | jq .
```

| Param | Type | Description |
|-------|------|-------------|
| `query` | string | Search terms with operators |
| `mode` | string | `pointdata`, `country`, `sourcecountry`, `adm1` |
| `format` | string | `geojson`, `csv`, `html` |
| `timespan` | string | `15m` to `7d` |
| `maxpoints` | int | 1-1000 for pointdata |

---

## TV API — Television News Search

Search transcripts from 163 TV stations (CNN, MSNBC, BBC, Bloomberg, etc.) going back to 2009.

```bash
# Recent TV clips mentioning a topic
curl -sf "https://api.gdeltproject.org/api/v2/tv/tv?query=QUERY&mode=clipgallery&format=json&timespan=7d" | jq '.clips[:10][] | {station, show, date, snippet: .snippet}'

# TV coverage volume over time
curl -sf "https://api.gdeltproject.org/api/v2/tv/tv?query=QUERY&mode=timelinevol&format=json&timespan=30d&datanorm=perc" | jq .

# Coverage by station
curl -sf "https://api.gdeltproject.org/api/v2/tv/tv?query=QUERY&mode=stationchart&format=json&timespan=7d" | jq .

# Currently trending topics on TV
curl -sf "https://api.gdeltproject.org/api/v2/tv/tv?query=&mode=trendingtopics&format=json" | jq .

# Filter by network
curl -sf "https://api.gdeltproject.org/api/v2/tv/tv?query=QUERY&network=CNN&mode=clipgallery&format=json&timespan=7d" | jq .

# Filter by market
curl -sf "https://api.gdeltproject.org/api/v2/tv/tv?query=QUERY&market=National&mode=clipgallery&format=json&timespan=7d" | jq .
```

| Param | Type | Description |
|-------|------|-------------|
| `query` | string | Search terms (must appear within a 15-second clip) |
| `mode` | string | `clipgallery`, `timelinevol`, `stationchart`, `wordcloud`, `trendingtopics` |
| `format` | string | `json`, `csv`, `html` |
| `timespan` | string | `24h`, `7d`, `30d`, `1y` |
| `datanorm` | string | `raw` (counts) or `perc` (normalized percentage) |
| `network` | string | `CNN`, `MSNBC`, `FOXNEWS`, `BLOOMBERG`, `BBCNEWS`, etc. |
| `market` | string | `National`, `NYDma`, etc. |
| `startdatetime` | string | Start time `YYYYMMDDHHMMSS` |
| `enddatetime` | string | End time `YYYYMMDDHHMMSS` |

---

## Context API — Sentence-Level Search

Search at the sentence level — all terms must appear in the same sentence. Returns text snippets with context. Limited to last 72 hours.

```bash
curl -sf "https://api.gdeltproject.org/api/v2/context/context?query=QUERY&mode=artlist&format=json&timespan=24H&maxrecords=25" | jq '.articles[] | {title, url, context: .context, seendate}'
```

| Param | Type | Description |
|-------|------|-------------|
| `query` | string | All terms must appear in same sentence |
| `mode` | string | `artlist` |
| `format` | string | `json`, `csv`, `html` |
| `timespan` | string | Max `72H` or `3d` |
| `maxrecords` | int | 1-200 (default 75) |
| `sortby` | string | `relevance`, `DateDesc`, `DateAsc` |

---

## Common Patterns

```bash
# Breaking news on a topic (last hour)
curl -sf "https://api.gdeltproject.org/api/v2/doc/doc?query=QUERY&mode=artlist&format=json&maxrecords=25&timespan=1h" | jq '.articles[] | {title, url, source: .domain, seendate}'

# Sentiment analysis over time
curl -sf "https://api.gdeltproject.org/api/v2/doc/doc?query=QUERY&mode=timelinetone&format=json&timespan=1w" | jq .

# Compare TV coverage across networks
curl -sf "https://api.gdeltproject.org/api/v2/tv/tv?query=QUERY&mode=stationchart&format=json&timespan=7d" | jq .

# Global spread of a story
curl -sf "https://api.gdeltproject.org/api/v2/geo/geo?query=QUERY&mode=sourcecountry&format=geojson&timespan=7d" | jq '.features[] | {country: .properties.name, count: .properties.count}' | head -20
```

---

## Important

- All APIs are public and free — no auth required.
- Rate limits are enforced but not published. Be responsible with request volume.
- DOC API covers a 3-month rolling window. GEO covers 7 days. Context covers 72 hours.
- TV API covers 163 stations from 2009 to present (~2 million hours, 5.7 billion words).
- URL-encode query parameters (spaces as `%20`, quotes as `%22`).
- Tone values: negative < 0, neutral ~ 0, positive > 0.
- GDELT themes list: `TERROR`, `PROTEST`, `ECON_BANKRUPTCY`, `ENV_CLIMATECHANGE`, `HEALTH_PANDEMIC`, etc.
