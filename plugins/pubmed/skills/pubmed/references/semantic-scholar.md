# Semantic Scholar

AI-powered academic search with TLDRs (auto-generated paper summaries), citation graphs, and influential citation detection. 214M+ papers.

**Base URL:** `https://api.semanticscholar.org/graph/v1`

**Auth:** API key in `x-api-key` header. Without key: shared rate pool (unreliable during peak). With key: dedicated 1 req/sec.

**Before using Semantic Scholar, check if the API key is available.** If not, skip Semantic Scholar and use Europe PMC instead — it covers the same literature without auth.

```bash
S2_KEY=$(security find-generic-password -s "semantic-scholar-api-key" -w 2>/dev/null)
if [ -z "$S2_KEY" ]; then
  echo "Semantic Scholar API key not found — skipping. Use Europe PMC instead."
  # To set up: security add-generic-password -s "semantic-scholar-api-key" -a "$USER" -w "YOUR_KEY"
  return 2>/dev/null || exit 0
fi
```

## Search Papers

```bash
# Basic search with TLDRs
curl -sf -H "x-api-key: ${S2_KEY}" "https://api.semanticscholar.org/graph/v1/paper/search?query=peptide+drug+delivery&fields=title,tldr,year,citationCount,url&limit=5" | jq '.data[] | {title, tldr: .tldr.text, year, citations: .citationCount, url}'

# Search with abstracts and authors
curl -sf -H "x-api-key: ${S2_KEY}" "https://api.semanticscholar.org/graph/v1/paper/search?query=GLP-1+receptor+agonist&fields=title,abstract,authors,year,citationCount,openAccessPdf&limit=5" | jq '.data[] | {title, year, citations: .citationCount, authors: [.authors[]?.name], pdf: .openAccessPdf.url}'

# Filter by year range
curl -sf -H "x-api-key: ${S2_KEY}" "https://api.semanticscholar.org/graph/v1/paper/search?query=semaglutide&fields=title,year,citationCount,tldr&year=2023-2026&limit=10" | jq '.data[] | {title, year, citations: .citationCount, tldr: .tldr.text}'

# Filter by open access
curl -sf -H "x-api-key: ${S2_KEY}" "https://api.semanticscholar.org/graph/v1/paper/search?query=BPC-157&fields=title,year,openAccessPdf,citationCount&openAccessPdf&limit=5" | jq '.data[] | {title, year, citations: .citationCount, pdf: .openAccessPdf.url}'

# Pagination
curl -sf -H "x-api-key: ${S2_KEY}" "https://api.semanticscholar.org/graph/v1/paper/search?query=peptides&fields=title,year&limit=100&offset=100" | jq '{total, offset, next, data: [.data[] | {title, year}]}'
```

| Param | Type | Description |
|-------|------|-------------|
| `query` | string | Search terms |
| `fields` | string | Comma-separated fields to return |
| `limit` | int | Results per page (max 100) |
| `offset` | int | Pagination offset |
| `year` | string | Year or range: `2024`, `2020-2024`, `2020-` |
| `openAccessPdf` | flag | Only papers with open-access PDFs |
| `fieldsOfStudy` | string | e.g., `Medicine`, `Biology`, `Chemistry` |
| `publicationTypes` | string | `Review`, `JournalArticle`, `CaseReport`, `ClinicalTrial` |

## Paper Details

Look up a paper by various ID types:

```bash
# By Semantic Scholar ID
curl -sf -H "x-api-key: ${S2_KEY}" "https://api.semanticscholar.org/graph/v1/paper/PAPER_ID?fields=title,abstract,tldr,authors,year,citationCount,referenceCount,influentialCitationCount,openAccessPdf" | jq '{title, tldr: .tldr.text, year, citations: .citationCount, influential: .influentialCitationCount, authors: [.authors[]?.name], pdf: .openAccessPdf.url}'

# By DOI
curl -sf -H "x-api-key: ${S2_KEY}" "https://api.semanticscholar.org/graph/v1/paper/DOI:10.1038/s41586-021-03819-2?fields=title,tldr,citationCount,year" | jq .

# By PubMed ID
curl -sf -H "x-api-key: ${S2_KEY}" "https://api.semanticscholar.org/graph/v1/paper/PMID:12345678?fields=title,tldr,citationCount,year" | jq .

# By ArXiv ID
curl -sf -H "x-api-key: ${S2_KEY}" "https://api.semanticscholar.org/graph/v1/paper/ARXIV:2301.00001?fields=title,tldr,citationCount,year" | jq .
```

Supported ID prefixes: `DOI:`, `PMID:`, `ARXIV:`, `CorpusId:`, `MAG:`, `ACL:`.

## Citations & References

```bash
# Papers that cite this paper
curl -sf -H "x-api-key: ${S2_KEY}" "https://api.semanticscholar.org/graph/v1/paper/PAPER_ID/citations?fields=title,year,citationCount,isInfluential&limit=10" | jq '.data[] | {title: .citingPaper.title, year: .citingPaper.year, citations: .citingPaper.citationCount, influential: .isInfluential}'

# Papers this paper references
curl -sf -H "x-api-key: ${S2_KEY}" "https://api.semanticscholar.org/graph/v1/paper/PAPER_ID/references?fields=title,year,citationCount,isInfluential&limit=10" | jq '.data[] | {title: .citedPaper.title, year: .citedPaper.year, citations: .citedPaper.citationCount, influential: .isInfluential}'
```

The `isInfluential` flag indicates whether the citation significantly impacted the citing paper — useful for finding the most important connections.

## Batch Lookup

Look up multiple papers at once (up to 500):

```bash
curl -sf -X POST -H "x-api-key: ${S2_KEY}" -H "Content-Type: application/json" \
  "https://api.semanticscholar.org/graph/v1/paper/batch?fields=title,tldr,year,citationCount" \
  -d '{"ids": ["DOI:10.1038/s41586-021-03819-2", "PMID:12345678"]}' | jq '.[] | {title, tldr: .tldr.text, year, citations: .citationCount}'
```

## Author Search

```bash
# Search authors
curl -sf -H "x-api-key: ${S2_KEY}" "https://api.semanticscholar.org/graph/v1/author/search?query=Daniel+Drucker&fields=name,hIndex,citationCount,paperCount&limit=5" | jq '.data[] | {name, hIndex, citations: .citationCount, papers: .paperCount}'

# Author's papers
curl -sf -H "x-api-key: ${S2_KEY}" "https://api.semanticscholar.org/graph/v1/author/AUTHOR_ID/papers?fields=title,year,citationCount&limit=10" | jq '.data[] | {title, year, citations: .citationCount}'
```

## Autocomplete

```bash
curl -sf -H "x-api-key: ${S2_KEY}" "https://api.semanticscholar.org/graph/v1/paper/autocomplete?query=semaglu" | jq '.completions[] | {text, id}'
```

## Available Fields

| Field | Description |
|-------|-------------|
| `title` | Paper title |
| `abstract` | Full abstract |
| `tldr` | AI-generated one-sentence summary |
| `year` | Publication year |
| `authors` | Author list (name, authorId) |
| `citationCount` | Total citations |
| `influentialCitationCount` | Citations that significantly build on this work |
| `referenceCount` | Number of references |
| `fieldsOfStudy` | Academic disciplines |
| `publicationTypes` | Review, JournalArticle, etc. |
| `journal` | Journal name and volume |
| `openAccessPdf` | URL to open-access PDF |
| `url` | Semantic Scholar page URL |
| `externalIds` | DOI, PMID, ArXiv ID, etc. |

## Important

- Rate limit: 1 req/sec with API key.
- The `tldr` field is Semantic Scholar's unique feature — use it for quick paper summaries.
- `influentialCitationCount` helps distinguish high-impact papers from merely well-cited ones.
- Always request only the fields you need — smaller payloads and faster responses.
- API key: get one free at https://www.semanticscholar.org/product/api — store in Keychain as `semantic-scholar-api-key`.
