---
name: gdelt
description: Search and analyze global news, events, and television coverage using GDELT APIs. Use when the user asks about global news trends, media coverage, geopolitical events, news sentiment, TV news mentions, or wants to search worldwide news articles.
allowed-tools: Bash(curl:*)
---

# GDELT

Search and analyze global news coverage across 65+ languages using the GDELT Project APIs. No authentication or API keys required — just `curl` and `jq`.

GDELT monitors news media worldwide in near real-time, covering online news, print, and 163 television stations.

**Rate limit: minimum 5 seconds between requests.** Batch your jq processing — never make multiple curl calls in quick succession.

## APIs

| API | Base URL | Coverage |
|-----|----------|----------|
| DOC 2.0 | `https://api.gdeltproject.org/api/v2/doc/doc` | Online news articles (3-month rolling window) |
| GEO 2.0 | `https://api.gdeltproject.org/api/v2/geo/geo` | Geographic mentions (last 7 days) |
| TV 2.0 | `https://api.gdeltproject.org/api/v2/tv/tv` | TV news transcripts (2009-present, 163 stations) |
| Context 2.0 | `https://api.gdeltproject.org/api/v2/context/context` | Sentence-level search (last 72 hours) |

---

## Query Syntax (shared across all APIs)

**Critical rules:**
- OR terms **must** be wrapped in parentheses: `(kubernetes OR openshift)`
- Phrases use double quotes URL-encoded as `%22`: `%22climate%20change%22`
- Spaces in query are `%20`
- Operators are part of the query value, space-separated
- Boolean OR cannot be nested — only single-level OR blocks

| Operator | Syntax | Example (raw) | Example (URL-encoded) |
|----------|--------|---------------|----------------------|
| Exact phrase | `"phrase"` | `"climate change"` | `%22climate%20change%22` |
| Boolean OR | `(a OR b)` | `(kubernetes OR openshift)` | `(kubernetes%20OR%20openshift)` |
| Exclude | `-term` | `-sports` | `-sports` |
| Domain | `domain:X` | `domain:bbc.com` | `domain:bbc.com` |
| Exact domain | `domainis:X` | `domainis:un.org` | `domainis:un.org` |
| Language | `sourcelang:X` | `sourcelang:spanish` | `sourcelang:spanish` |
| Country | `sourcecountry:X` | `sourcecountry:india` | `sourcecountry:india` |
| Theme | `theme:X` | `theme:TERROR` | `theme:TERROR` |
| Tone | `tone>N` / `tone<N` | `tone<-5` | `tone%3C-5` |
| Proximity | `nearN:"a b"` | `near10:"trump putin"` | `near10:%22trump%20putin%22` |
| Repetition | `repeatN:"word"` | `repeat2:"trump"` | `repeat2:%22trump%22` |

### Timespan syntax

Format: number + unit. Examples: `15min`, `1h`, `2hours`, `7d`, `2days`, `1w`, `3weeks`, `1m`, `3months`

### Date range (alternative to timespan)

`STARTDATETIME` and `ENDDATETIME` in `YYYYMMDDHHMMSS` format (UTC).

---

## DOC API — Article Search

3-month rolling window of online news articles.

```bash
# Recent articles (last 7 days)
curl -sf "https://api.gdeltproject.org/api/v2/doc/doc?query=kubernetes&mode=artlist&format=json&maxrecords=25&timespan=7d" | jq '.articles[] | {title, url, domain, seendate, tone}'

# Multiple terms (OR must use parentheses)
curl -sf "https://api.gdeltproject.org/api/v2/doc/doc?query=(kubernetes%20OR%20openshift)&mode=artlist&format=json&maxrecords=10&timespan=7d" | jq '.articles[] | {title, url, domain, seendate}'

# From a specific source
curl -sf "https://api.gdeltproject.org/api/v2/doc/doc?query=kubernetes%20domain:reuters.com&mode=artlist&format=json&maxrecords=25" | jq '.articles[] | {title, url, seendate}'

# Negative-tone coverage
curl -sf "https://api.gdeltproject.org/api/v2/doc/doc?query=kubernetes%20tone%3C-5&mode=artlist&format=json&maxrecords=25" | jq .

# Coverage volume over time
curl -sf "https://api.gdeltproject.org/api/v2/doc/doc?query=kubernetes&mode=timelinevol&format=json&timespan=3months" | jq .

# Sentiment trend over time
curl -sf "https://api.gdeltproject.org/api/v2/doc/doc?query=kubernetes&mode=timelinetone&format=json&timespan=1w" | jq .
```

| Param | Type | Description |
|-------|------|-------------|
| `query` | string | **Required.** Search terms with operators |
| `mode` | string | `artlist`, `timelinevol`, `timelinevolraw`, `timelinetone`, `timelinelang`, `timelinesourcecountry`, `tonechart` |
| `format` | string | `json`, `csv`, `rss`, `jsonfeed`, `html` |
| `timespan` | string | e.g., `15min`, `1h`, `7d`, `1w`, `3months` |
| `maxrecords` | int | 1-250 (default 75, artlist mode only) |
| `sort` | string | `hybridrel` (default), `datedesc`, `dateasc`, `tonedesc`, `toneasc` |
| `startdatetime` | string | `YYYYMMDDHHMMSS` (within last 3 months) |
| `enddatetime` | string | `YYYYMMDDHHMMSS` |
| `timelinesmooth` | int | 1-30 moving average smoothing (timeline modes) |

---

## GEO API — Geographic Search

Where in the world a topic is being mentioned. Last 7 days.

```bash
# Country-level mentions
curl -sf "https://api.gdeltproject.org/api/v2/geo/geo?query=kubernetes&mode=country&format=geojson&timespan=7d" | jq '.features[] | {country: .properties.name, count: .properties.count}'

# Specific locations mentioned
curl -sf "https://api.gdeltproject.org/api/v2/geo/geo?query=kubernetes&mode=pointdata&format=geojson&timespan=7d&maxpoints=50" | jq '.features[:10][] | {name: .properties.name, count: .properties.count, lat: .geometry.coordinates[1], lon: .geometry.coordinates[0]}'

# Where articles originate from
curl -sf "https://api.gdeltproject.org/api/v2/geo/geo?query=kubernetes&mode=sourcecountry&format=geojson&timespan=7d" | jq '.features[] | {country: .properties.name, count: .properties.count}'

# Near a location (100 mile radius from Paris)
curl -sf "https://api.gdeltproject.org/api/v2/geo/geo?query=kubernetes%20near:48.8566,2.3522,100&mode=pointdata&format=geojson" | jq .
```

| Param | Type | Description |
|-------|------|-------------|
| `query` | string | Search terms. Supports `location:`, `locationcc:`, `locationadm1:`, `near:lat,lon,radius` |
| `mode` | string | `pointdata`, `country`, `sourcecountry`, `adm1` |
| `format` | string | `geojson`, `csv`, `rss`, `html` |
| `timespan` | string | `15min` to `7d` (default 7 days) |
| `maxpoints` | int | 1-1000 (pointdata), 1-25000 (heatmap) |
| `geores` | int | `0` all, `1` exclude countries, `2` cities only |
| `sortby` | string | `Date`, `ToneDesc`, `ToneAsc` |

---

## TV API — Television News Search

Search transcripts from 163 TV stations (CNN, MSNBC, BBC, Bloomberg, Fox News, etc.) going back to July 2009. Keywords must appear within 15-second broadcast intervals.

```bash
# Recent TV clips
curl -sf "https://api.gdeltproject.org/api/v2/tv/tv?query=kubernetes&mode=clipgallery&format=json&timespan=7d&maxrecords=10" | jq '.clips[:10][] | {station, show, date, snippet}'

# Coverage volume over time (normalized %)
curl -sf "https://api.gdeltproject.org/api/v2/tv/tv?query=kubernetes&mode=timelinevol&format=json&timespan=30d&datanorm=perc" | jq .

# Coverage by station
curl -sf "https://api.gdeltproject.org/api/v2/tv/tv?query=kubernetes&mode=stationchart&format=json&timespan=7d" | jq .

# Trending topics on TV right now
curl -sf "https://api.gdeltproject.org/api/v2/tv/tv?query=&mode=trendingtopics&format=json" | jq .

# Filter by network
curl -sf "https://api.gdeltproject.org/api/v2/tv/tv?query=kubernetes%20network:CNN&mode=clipgallery&format=json&timespan=7d" | jq .

# Filter by national market
curl -sf "https://api.gdeltproject.org/api/v2/tv/tv?query=kubernetes%20market:%22National%22&mode=clipgallery&format=json&timespan=7d" | jq .
```

| Param | Type | Description |
|-------|------|-------------|
| `query` | string | Search terms. Supports `network:CNN`, `market:"National"`, `show:"Show Name"`, `context:"term"` (extends to adjacent 15s clips) |
| `mode` | string | `clipgallery`, `timelinevol`, `stationchart`, `showchart`, `wordcloud`, `trendingtopics` |
| `format` | string | `json`, `csv`, `rss`, `jsonfeed`, `html` |
| `timespan` | string | e.g., `24h`, `7d`, `30d`, `1y` |
| `datanorm` | string | `raw` (counts) or `perc` (normalized %) |
| `datacomb` | string | `combined` (collapse all stations into single series) |
| `datares` | string | `Hour`, `Day`, `Week`, `Month`, `Year` |
| `maxrecords` | int | Up to 3000 (clipgallery only) |
| `sort` | string | `DateDesc`, `DateAsc`, or relevance (default) |
| `startdatetime` | string | `YYYYMMDDHHMMSS` |
| `enddatetime` | string | `YYYYMMDDHHMMSS` |
| `timelinesmooth` | int | 0-30 moving average |
| `last24` | string | `yes` to include incomplete last-24h data |

---

## Context API — Sentence-Level Search

All query terms must appear in the **same sentence**. Returns text snippets with context. Last 72 hours only.

```bash
curl -sf "https://api.gdeltproject.org/api/v2/context/context?query=kubernetes%20security&mode=artlist&format=json&timespan=24h&maxrecords=25" | jq '.articles[] | {title, url, context, seendate}'
```

| Param | Type | Description |
|-------|------|-------------|
| `query` | string | All terms must co-occur in same sentence. Supports `near`, `repeat`, `domain`, `domainis` |
| `mode` | string | `artlist` (only option) |
| `format` | string | `json`, `csv`, `rss`, `jsonfeed` |
| `timespan` | string | Max `72h` or `3d` |
| `maxrecords` | int | 1-200 (default 75) |
| `sort` | string | `DateDesc`, `DateAsc` (default: relevance) |
| `isquote` | int | `1` to return only quoted sentences |

---

## Important

- **Rate limit: 1 request per 5 seconds minimum.** You will be blocked otherwise.
- All APIs are public and free — no auth required.
- DOC: 3-month window. GEO: 7 days. Context: 72 hours. TV: 2009-present.
- URL-encode all query parameters (spaces `%20`, quotes `%22`, `<` as `%3C`, `>` as `%3E`).
- OR terms **must** be in parentheses: `(a OR b)` — bare `a OR b` will error.
- Tone values: negative < 0, neutral ~ 0, positive > 0.
- Common themes: `TERROR`, `PROTEST`, `ECON_BANKRUPTCY`, `ENV_CLIMATECHANGE`, `HEALTH_PANDEMIC`, `CYBER_ATTACK`, `AI`.
