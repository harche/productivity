---
name: medical-research
description: "Find peer-reviewed medical evidence, clinical trials, and scientific papers across PubMed, Europe PMC, ClinicalTrials.gov, Semantic Scholar, and OpenAlex. Use when the user asks about treatments, drugs, conditions, or wants to find scientific literature."
allowed-tools: Bash(curl:*)
---

# Medical Research

Find peer-reviewed evidence, clinical trials, and scientific papers. No dependencies -- just `curl` and `jq`.

## Quick example

```bash
curl -sf "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=GLP-1%20receptor%20agonists&resultType=lite&format=json&pageSize=5" | jq '.resultList.result // [] | .[] | {title, authorString, journalTitle, pubYear, pmid, doi}'
```

## What you can do

### Research a medical topic

Start with **Europe PMC** -- indexes PubMed, PMC, bioRxiv/medRxiv, and patents in one API. Use `resultType=core` for abstracts. For AI paper summaries, add **Semantic Scholar** (requires API key in Keychain `semantic-scholar-api-key`). See [references/europe-pmc.md](references/europe-pmc.md) and [references/semantic-scholar.md](references/semantic-scholar.md).

```bash
curl -sf "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=semaglutide+obesity&resultType=core&format=json&pageSize=5" | jq '.resultList.result // [] | .[] | {title, pubYear, abstractText}'
```

### Find clinical trials

Search ClinicalTrials.gov by condition, intervention, sponsor, or location. See [references/clinical-trials.md](references/clinical-trials.md) for filters and field details.

```bash
curl -sf "https://clinicaltrials.gov/api/v2/studies?query.cond=obesity&query.intr=tirzepatide&filter.phase=PHASE3&pageSize=5&format=json" | jq '.studies // [] | .[] | {nctId: .protocolSection.identificationModule.nctId, title: .protocolSection.identificationModule.briefTitle, status: .protocolSection.statusModule.overallStatus}'
```

### Get paper details

Look up by PMID, DOI, or title. Use Europe PMC (no auth) or Semantic Scholar (includes TLDR):

```bash
curl -sf "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:12345678&resultType=core&format=json" | jq '.resultList.result[0] | {title, authorString, pubYear, abstractText, doi}'
```

### Search by author or institution

Use **OpenAlex** for author profiles, h-index, institution output, and funder analysis. See [references/openalex.md](references/openalex.md).

```bash
OA_KEY="${OPENALEX_API_KEY:-$(security find-generic-password -s "openalex-api-key" -w 2>/dev/null || true)}"
curl -sf "https://api.openalex.org/authors?search=Daniel+Drucker&per_page=5&api_key=${OA_KEY}" | jq '.results // [] | .[] | {name: .display_name, works_count, cited_by_count, h_index: .summary_stats.h_index}'
```

### Explore citation networks

Find what cites a paper (Europe PMC, no auth) or get influential citations (Semantic Scholar):

```bash
curl -sf "https://www.ebi.ac.uk/europepmc/webservices/rest/MED/12345678/citations?format=json&pageSize=10" | jq '.citationList.citation // [] | .[] | {title, authorString, pubYear}'
```

## References

- [references/europe-pmc.md](references/europe-pmc.md) -- article search, query fields, date filters, preprints
- [references/clinical-trials.md](references/clinical-trials.md) -- trial search, status/phase filters, study details
- [references/semantic-scholar.md](references/semantic-scholar.md) -- TLDRs, citation graphs, batch lookup
- [references/openalex.md](references/openalex.md) -- cross-discipline search, authors, institutions, bibliometrics

## API keys

| Source | Auth | Storage |
|---|---|---|
| Europe PMC | None | -- |
| ClinicalTrials.gov | None | -- |
| Semantic Scholar | API key (free) | Keychain: `semantic-scholar-api-key` |
| OpenAlex | API key (free) | Keychain: `openalex-api-key` |

## Important

- Start with **Europe PMC** for broad searches -- no auth, covers PubMed + preprints.
- When asked about a drug, search both literature and clinical trials for completeness.
- Always present results with titles, authors, year, and links where available.
