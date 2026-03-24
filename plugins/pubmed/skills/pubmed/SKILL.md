---
name: pubmed
description: Search biomedical literature, clinical trials, and scientific papers. Use when the user asks about medical research, drugs, peptides, clinical studies, scientific papers, PubMed, biomedical topics, or wants to find peer-reviewed articles.
allowed-tools: Bash(curl:*)
---

# Biomedical Literature Search

Search peer-reviewed articles, clinical trials, and scientific papers across multiple open databases. No dependencies — just `curl` and `jq`.

## Quick Start

```bash
# Search articles (Europe PMC — covers PubMed, PMC, preprints, patents)
curl -sf "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=GLP-1%20receptor%20agonists&resultType=lite&format=json&pageSize=5" | jq '.resultList.result // [] | .[] | {title, authorString, journalTitle, pubYear, pmid, doi}'

# Search clinical trials
curl -sf "https://clinicaltrials.gov/api/v2/studies?query.cond=obesity&query.intr=semaglutide&pageSize=5&format=json" | jq '.studies // [] | .[] | {nctId: .protocolSection.identificationModule.nctId, title: .protocolSection.identificationModule.briefTitle, status: .protocolSection.statusModule.overallStatus, phase: .protocolSection.designModule.phases}'

# Paper details with AI summary (Semantic Scholar — requires API key)
S2_KEY=$(security find-generic-password -s "semantic-scholar-api-key" -w 2>/dev/null)
if [ -n "$S2_KEY" ]; then
  curl -sf -H "x-api-key: ${S2_KEY}" "https://api.semanticscholar.org/graph/v1/paper/search?query=peptide+drug+delivery&fields=title,tldr,citationCount,year&limit=5" | jq '.data // [] | .[] | {title, tldr: .tldr.text, citations: .citationCount, year}'
fi
```

## Sources

Read the reference that matches the user's intent:

| User intent | Read |
|---|---|
| Search articles, papers, preprints, patents | [references/europe-pmc.md](references/europe-pmc.md) |
| Find clinical trials for a drug or condition | [references/clinical-trials.md](references/clinical-trials.md) |
| Paper summaries (TLDRs), citation analysis, related papers | [references/semantic-scholar.md](references/semantic-scholar.md) |
| Cross-discipline search, author/institution/funder analysis | [references/openalex.md](references/openalex.md) |

For broad literature searches, start with **Europe PMC** — it indexes PubMed, PubMed Central, bioRxiv, medRxiv, and European patents in one API. Use **Semantic Scholar** to enrich results with AI-generated summaries and citation graphs. Use **ClinicalTrials.gov** specifically for clinical trial data. Use **OpenAlex** for cross-discipline or bibliometric queries.

## API Keys

| Source | Auth | Storage |
|---|---|---|
| Europe PMC | None required | — |
| ClinicalTrials.gov | None required | — |
| Semantic Scholar | API key (free, required) | macOS Keychain: `semantic-scholar-api-key` — check availability before use; if missing, skip and use Europe PMC |
| OpenAlex | API key (free) | macOS Keychain: `openalex-api-key` |

## Important

- All APIs return JSON. Use `jq` to filter results.
- Europe PMC and ClinicalTrials.gov need zero authentication.
- For Semantic Scholar and OpenAlex, get free API keys at their respective sites.
- Always present results with titles, authors, year, and links where available.
- When the user asks about a drug or compound, search both literature (Europe PMC) and trials (ClinicalTrials.gov) for a complete picture.
