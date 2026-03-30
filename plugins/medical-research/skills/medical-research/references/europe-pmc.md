# Europe PMC

Primary literature search API. Indexes PubMed (37M+ citations), PubMed Central (9M+ full-text), bioRxiv/medRxiv preprints, and European patents. No authentication required.

**Base URL:** `https://www.ebi.ac.uk/europepmc/webservices/rest`

## Search

```bash
# Basic keyword search
curl -sf "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=QUERY&resultType=lite&format=json&pageSize=10" | jq '.resultList.result // [] | .[] | {title, authorString, journalTitle, pubYear, pmid, doi, source}'

# With abstract (use resultType=core)
curl -sf "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=QUERY&resultType=core&format=json&pageSize=5" | jq '.resultList.result // [] | .[] | {title, authorString, pubYear, abstractText}'

# Pagination (cursorMark-based)
curl -sf "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=QUERY&resultType=lite&format=json&pageSize=25&cursorMark=*" | jq '{nextCursorMark, hitCount, results: [.resultList.result // [] | .[] | {title, pubYear, pmid}]}'
```

| Param | Type | Description |
|-------|------|-------------|
| `query` | string | Search query (supports field-specific syntax) |
| `resultType` | string | `idlist` (IDs only), `lite` (metadata), `core` (metadata + abstract) |
| `format` | string | `json` or `xml` |
| `pageSize` | int | Results per page (max 1000, default 25) |
| `cursorMark` | string | Pagination cursor (`*` for first page) |
| `sort` | string | Omit for relevance (default). Use `CITED desc`, `CITED asc`, `P_PDATE_D desc` (newest first), `P_PDATE_D asc` (oldest first). Format is `FIELD direction`. **Do NOT use `DATE_DESC` or other non-standard values — the API returns null results silently on invalid sort values.** |

## Query Syntax

Combine field-specific queries with boolean operators (`AND`, `OR`, `NOT`):

```bash
# By author
curl -sf "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=AUTH:%22Smith+J%22&resultType=lite&format=json&pageSize=5" | jq '.resultList.result // [] | .[] | {title, pubYear, journalTitle}'

# By journal
curl -sf "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=JOURNAL:%22Nature%22+AND+peptide+therapeutics&resultType=lite&format=json&pageSize=5" | jq '.resultList.result // [] | .[] | {title, pubYear, doi}'

# Date range
curl -sf "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=GLP-1+AND+(FIRST_PDATE:[2024-01-01+TO+2026-12-31])&resultType=lite&format=json&pageSize=10" | jq '.resultList.result // [] | .[] | {title, pubYear, pmid}'

# Preprints only (bioRxiv/medRxiv)
curl -sf "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=SRC:PPR+AND+peptide+delivery&resultType=lite&format=json&pageSize=5" | jq '.resultList.result // [] | .[] | {title, authorString, pubYear, source}'

# Open access only
curl -sf "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=OPEN_ACCESS:y+AND+semaglutide&resultType=lite&format=json&pageSize=5" | jq '.resultList.result // [] | .[] | {title, pubYear, isOpenAccess}'

# MeSH terms
curl -sf "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=MESH:%22Glucagon-Like+Peptide+1%22&resultType=lite&format=json&pageSize=5" | jq '.resultList.result // [] | .[] | {title, pubYear, pmid}'

# Sort by newest first (use P_PDATE_D desc, NOT DATE_DESC)
curl -sf "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=peptide+therapeutics&resultType=lite&format=json&pageSize=5&sort=P_PDATE_D+desc" | jq '.resultList.result // [] | .[] | {title, pubYear, pmid}'
```

### Query Field Reference

| Field | Example | Description |
|-------|---------|-------------|
| `AUTH` | `AUTH:"Smith J"` | Author name |
| `TITLE` | `TITLE:peptide` | Title words |
| `ABSTRACT` | `ABSTRACT:biomarker` | Abstract words |
| `JOURNAL` | `JOURNAL:"Nature"` | Journal name |
| `MESH` | `MESH:"Neoplasms"` | MeSH descriptor |
| `SRC` | `SRC:MED` / `SRC:PPR` | Source: `MED` (PubMed), `PMC`, `PPR` (preprints), `PAT` (patents) |
| `FIRST_PDATE` | `FIRST_PDATE:[2024-01-01 TO 2025-12-31]` | First publication date range |
| `OPEN_ACCESS` | `OPEN_ACCESS:y` | Open access filter |
| `HAS_FT` | `HAS_FT:y` | Has full text |
| `LANG` | `LANG:eng` | Language |

## Citations & References

```bash
# Articles that cite a paper (by PMID)
curl -sf "https://www.ebi.ac.uk/europepmc/webservices/rest/MED/PMID/citations?format=json&pageSize=10" | jq '.citationList.citation // [] | .[] | {title, authorString, pubYear, journalAbbreviation}'

# References from a paper
curl -sf "https://www.ebi.ac.uk/europepmc/webservices/rest/MED/PMID/references?format=json&pageSize=10" | jq '.referenceList.reference // [] | .[] | {title, authorString, pubYear, journalAbbreviation}'
```

Replace `MED` with the source (`PMC`, `PPR`, `PAT`) and `PMID` with the article ID.

## Full Text (Open Access)

```bash
# Full text XML for a PMC article
curl -sf "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12345/fullTextXML"
```

## Text-Mined Annotations

Europe PMC extracts entities (genes, diseases, chemicals) from articles:

```bash
curl -sf "https://www.ebi.ac.uk/europepmc/webservices/rest/MED/PMID/textMinedTerms?format=json&pageSize=20" | jq '.semanticTypeList.semanticType // [] | .[] | {name, total, terms: [.tmSummary[:3] // [] | .[] | {term, count}]}'
```

## Important

- Rate limit: ~10 requests/second (not formally documented).
- `resultType=core` includes abstracts but is slower — use `lite` for browsing, `core` when you need abstracts.
- Source codes: `MED` = PubMed, `PMC` = PubMed Central, `PPR` = preprints, `PAT` = patents, `AGR` = Agricola.
- Preprint content from bioRxiv/medRxiv often appears here before PubMed indexes it.
- The `cursorMark` pagination is more reliable than offset-based for large result sets.
