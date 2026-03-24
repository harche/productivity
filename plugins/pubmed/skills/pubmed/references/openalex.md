# OpenAlex

Cross-discipline scholarly search covering 474M+ works (papers, datasets, preprints) across all academic fields. Knowledge graph linking works to authors, institutions, topics, and funders.

**Base URL:** `https://api.openalex.org`

**Auth:** API key via `api_key` param. Without key: severely rate-limited (testing only).

```bash
OA_KEY=$(security find-generic-password -s "openalex-api-key" -w 2>/dev/null)
```

## Search Works

```bash
# Full-text search
curl -sf "https://api.openalex.org/works?search=peptide+therapeutics&per_page=5&api_key=${OA_KEY}" | jq '.results // [] | .[] | {title, publication_year, cited_by_count, doi, type}'

# Filter by publication year
curl -sf "https://api.openalex.org/works?search=GLP-1&filter=publication_year:2024-2026&per_page=5&api_key=${OA_KEY}" | jq '.results // [] | .[] | {title, publication_year, cited_by_count}'

# Filter by open access
curl -sf "https://api.openalex.org/works?search=semaglutide&filter=open_access.is_oa:true&per_page=5&api_key=${OA_KEY}" | jq '.results // [] | .[] | {title, publication_year, open_access: .open_access}'

# Filter by type (journal-article, review, preprint, dataset)
curl -sf "https://api.openalex.org/works?search=peptide&filter=type:review&per_page=5&api_key=${OA_KEY}" | jq '.results // [] | .[] | {title, publication_year, cited_by_count}'

# Sort by citation count
curl -sf "https://api.openalex.org/works?search=neuropeptide&sort=cited_by_count:desc&per_page=5&api_key=${OA_KEY}" | jq '.results // [] | .[] | {title, publication_year, cited_by_count}'

# Pagination
curl -sf "https://api.openalex.org/works?search=peptide&per_page=25&page=2&api_key=${OA_KEY}" | jq '{count: .meta.count, page: .meta.page, results: [.results // [] | .[] | {title, publication_year}]}'
```

| Param | Type | Description |
|-------|------|-------------|
| `search` | string | Full-text search across title, abstract, full text |
| `filter` | string | Field filters (see below) |
| `sort` | string | `cited_by_count:desc`, `publication_date:desc`, `relevance_score:desc` |
| `per_page` | int | Results per page (max 200) |
| `page` | int | Page number |
| `api_key` | string | API key |

## Filter Syntax

Filters use `field:value` format, combined with commas (AND):

```bash
# Multiple filters: reviews from 2024+ about peptides in Nature
curl -sf "https://api.openalex.org/works?search=peptide&filter=type:review,publication_year:2024-,primary_location.source.display_name:Nature&per_page=5&api_key=${OA_KEY}" | jq '.results // [] | .[] | {title, publication_year, cited_by_count}'

# By institution
curl -sf "https://api.openalex.org/works?filter=authorships.institutions.display_name:Harvard,publication_year:2025&search=peptide&per_page=5&api_key=${OA_KEY}" | jq '.results // [] | .[] | {title, publication_year, cited_by_count}'

# By funder
curl -sf "https://api.openalex.org/works?filter=grants.funder:https://openalex.org/funders/F4320332161&search=peptide&per_page=5&api_key=${OA_KEY}" | jq '.results // [] | .[] | {title, publication_year}'
```

### Common Filters

| Filter | Example | Description |
|--------|---------|-------------|
| `publication_year` | `2024`, `2020-2024`, `2024-` | Year or range |
| `type` | `journal-article`, `review`, `preprint`, `dataset` | Work type |
| `open_access.is_oa` | `true` | Open access only |
| `cited_by_count` | `>100`, `10-50` | Citation count range |
| `primary_location.source.display_name` | `Nature` | Journal name |
| `authorships.institutions.display_name` | `MIT` | Institution name |
| `concepts.display_name` | `Machine Learning` | Topic/concept |

## Single Work

```bash
# By OpenAlex ID
curl -sf "https://api.openalex.org/works/W2741809807?api_key=${OA_KEY}" | jq '{title, publication_year, cited_by_count, doi, abstract: .abstract_inverted_index, authors: [.authorships // [] | .[] | {name: .author.display_name, institution: .institutions[0]?.display_name}]}'

# By DOI
curl -sf "https://api.openalex.org/works/doi:10.1038/s41586-021-03819-2?api_key=${OA_KEY}" | jq '{title, publication_year, cited_by_count}'

# By PMID
curl -sf "https://api.openalex.org/works/pmid:12345678?api_key=${OA_KEY}" | jq '{title, publication_year, cited_by_count}'
```

## Authors

```bash
# Search authors
curl -sf "https://api.openalex.org/authors?search=Daniel+Drucker&per_page=5&api_key=${OA_KEY}" | jq '.results // [] | .[] | {name: .display_name, works_count, cited_by_count, h_index: .summary_stats.h_index, institution: .last_known_institutions[0]?.display_name}'

# Author's works
curl -sf "https://api.openalex.org/works?filter=authorships.author.id:A1234567890&sort=publication_date:desc&per_page=10&api_key=${OA_KEY}" | jq '.results // [] | .[] | {title, publication_year, cited_by_count}'
```

## Institutions

```bash
# Search institutions
curl -sf "https://api.openalex.org/institutions?search=Mayo+Clinic&per_page=3&api_key=${OA_KEY}" | jq '.results // [] | .[] | {name: .display_name, works_count, cited_by_count, country: .country_code}'
```

## Topics & Concepts

```bash
# Search topics
curl -sf "https://api.openalex.org/topics?search=peptide+therapeutics&per_page=5&api_key=${OA_KEY}" | jq '.results // [] | .[] | {name: .display_name, works_count, domain: .domain.display_name}'

# Works by topic
curl -sf "https://api.openalex.org/works?filter=topics.id:T12345&sort=cited_by_count:desc&per_page=5&api_key=${OA_KEY}" | jq '.results // [] | .[] | {title, publication_year, cited_by_count}'
```

## Group-By (Aggregations)

Get counts grouped by a field — useful for understanding research landscapes:

```bash
# Publications per year for a topic
curl -sf "https://api.openalex.org/works?search=GLP-1&group_by=publication_year&api_key=${OA_KEY}" | jq '.group_by // [] | .[] | {year: .key, count}'

# Top journals for a topic
curl -sf "https://api.openalex.org/works?search=peptide+therapeutics&group_by=primary_location.source.id&api_key=${OA_KEY}" | jq '.group_by // [] | .[:10][] | {journal: .key_display_name, count}'

# Open access breakdown
curl -sf "https://api.openalex.org/works?search=semaglutide&group_by=open_access.oa_status&api_key=${OA_KEY}" | jq '.group_by // [] | .[] | {status: .key, count}'
```

## Important

- Rate limits (free tier): single lookups unlimited, list+filter 10K/day, full-text search 1K/day.
- Abstract is stored as `abstract_inverted_index` (inverted index format). Use `abstract` field in search results for the readable version when available.
- OpenAlex is CC0 licensed — the data is completely open.
- The `group_by` feature is powerful for bibliometric analysis (publication trends, top journals, institutional output).
- API key: get one free at https://openalex.org — store in Keychain as `openalex-api-key`.
