# ClinicalTrials.gov

Search 500K+ registered clinical studies worldwide. Clean JSON API, no authentication required.

**Base URL:** `https://clinicaltrials.gov/api/v2`

## Search Studies

```bash
# Search by condition
curl -sf "https://clinicaltrials.gov/api/v2/studies?query.cond=diabetes&pageSize=5&format=json" | jq '.studies[] | {nctId: .protocolSection.identificationModule.nctId, title: .protocolSection.identificationModule.briefTitle, status: .protocolSection.statusModule.overallStatus}'

# Search by intervention (drug/therapy)
curl -sf "https://clinicaltrials.gov/api/v2/studies?query.intr=semaglutide&pageSize=5&format=json" | jq '.studies[] | {nctId: .protocolSection.identificationModule.nctId, title: .protocolSection.identificationModule.briefTitle, status: .protocolSection.statusModule.overallStatus, phase: .protocolSection.designModule.phases}'

# Combined: condition + intervention
curl -sf "https://clinicaltrials.gov/api/v2/studies?query.cond=obesity&query.intr=tirzepatide&pageSize=5&format=json" | jq '.studies[] | {nctId: .protocolSection.identificationModule.nctId, title: .protocolSection.identificationModule.briefTitle, status: .protocolSection.statusModule.overallStatus}'

# Full-text search (any field)
curl -sf "https://clinicaltrials.gov/api/v2/studies?query.term=BPC-157+peptide&pageSize=5&format=json" | jq '.studies[] | {nctId: .protocolSection.identificationModule.nctId, title: .protocolSection.identificationModule.briefTitle, status: .protocolSection.statusModule.overallStatus}'

# By sponsor
curl -sf "https://clinicaltrials.gov/api/v2/studies?query.spons=Novo+Nordisk&pageSize=5&format=json" | jq '.studies[] | {nctId: .protocolSection.identificationModule.nctId, title: .protocolSection.identificationModule.briefTitle, status: .protocolSection.statusModule.overallStatus}'

# By location
curl -sf "https://clinicaltrials.gov/api/v2/studies?query.locn=Boston&query.cond=cancer&pageSize=5&format=json" | jq '.studies[] | {nctId: .protocolSection.identificationModule.nctId, title: .protocolSection.identificationModule.briefTitle}'
```

| Param | Type | Description |
|-------|------|-------------|
| `query.cond` | string | Condition or disease |
| `query.intr` | string | Intervention or treatment |
| `query.term` | string | Full-text search (any field) |
| `query.spons` | string | Sponsor or collaborator |
| `query.locn` | string | Location (city, state, country) |
| `pageSize` | int | Results per page (max 1000, default 10) |
| `pageToken` | string | Pagination token (from previous response) |
| `format` | string | `json` (default) or `csv` |
| `sort` | string | e.g., `LastUpdatePostDate:desc`, `EnrollmentCount:desc` |

## Filters

Append filters to narrow results:

```bash
# Only recruiting studies
curl -sf "https://clinicaltrials.gov/api/v2/studies?query.cond=alzheimer&filter.overallStatus=RECRUITING&pageSize=5&format=json" | jq '.studies[] | {nctId: .protocolSection.identificationModule.nctId, title: .protocolSection.identificationModule.briefTitle}'

# Phase 3 trials only
curl -sf "https://clinicaltrials.gov/api/v2/studies?query.intr=ozempic&filter.phase=PHASE3&pageSize=5&format=json" | jq '.studies[] | {nctId: .protocolSection.identificationModule.nctId, title: .protocolSection.identificationModule.briefTitle, phase: .protocolSection.designModule.phases}'

# Interventional studies with results
curl -sf "https://clinicaltrials.gov/api/v2/studies?query.term=GLP-1&filter.overallStatus=COMPLETED&filter.advanced=STUDY_RESULTS:WITH&pageSize=5&format=json" | jq '.studies[] | {nctId: .protocolSection.identificationModule.nctId, title: .protocolSection.identificationModule.briefTitle}'
```

| Filter | Values |
|--------|--------|
| `filter.overallStatus` | `RECRUITING`, `COMPLETED`, `ACTIVE_NOT_RECRUITING`, `NOT_YET_RECRUITING`, `TERMINATED`, `WITHDRAWN`, `SUSPENDED` (comma-separate for multiple) |
| `filter.phase` | `EARLY_PHASE1`, `PHASE1`, `PHASE2`, `PHASE3`, `PHASE4`, `NA` |
| `filter.studyType` | `INTERVENTIONAL`, `OBSERVATIONAL`, `EXPANDED_ACCESS` |
| `filter.sex` | `MALE`, `FEMALE`, `ALL` |
| `filter.advanced` | `STUDY_RESULTS:WITH` (has results), `STUDY_RESULTS:WITHOUT` |

## Single Study

```bash
# Full study record by NCT ID
curl -sf "https://clinicaltrials.gov/api/v2/studies/NCT05035095?format=json" | jq '{
  nctId: .protocolSection.identificationModule.nctId,
  title: .protocolSection.identificationModule.briefTitle,
  status: .protocolSection.statusModule.overallStatus,
  phase: .protocolSection.designModule.phases,
  enrollment: .protocolSection.designModule.enrollmentInfo,
  conditions: .protocolSection.conditionsModule.conditions,
  interventions: [.protocolSection.armsInterventionsModule.interventions[]? | {name, type, description}],
  sponsor: .protocolSection.sponsorCollaboratorsModule.leadSponsor,
  startDate: .protocolSection.statusModule.startDateStruct,
  completionDate: .protocolSection.statusModule.completionDateStruct
}'
```

## Study Detail Fields

The response is deeply nested under `protocolSection`:

| Path | Content |
|------|---------|
| `.identificationModule` | NCT ID, title, acronym |
| `.statusModule` | Overall status, start/completion dates |
| `.designModule` | Study type, phases, enrollment |
| `.conditionsModule` | Conditions/diseases studied |
| `.armsInterventionsModule` | Arms, interventions (drugs, procedures) |
| `.eligibilityModule` | Eligibility criteria, age range, sex |
| `.contactsLocationsModule` | Investigators, study locations |
| `.sponsorCollaboratorsModule` | Lead sponsor, collaborators |
| `.outcomesModule` | Primary/secondary outcome measures |
| `.resultsSection` | Results (if study is completed and posted) |

## Pagination

```bash
# First page
curl -sf "https://clinicaltrials.gov/api/v2/studies?query.cond=peptide&pageSize=100&format=json" | jq '{totalCount, nextPageToken, count: (.studies | length)}'

# Next page (use nextPageToken from previous response)
curl -sf "https://clinicaltrials.gov/api/v2/studies?query.cond=peptide&pageSize=100&pageToken=NEXT_PAGE_TOKEN&format=json" | jq '{totalCount, nextPageToken, count: (.studies | length)}'
```

## Important

- Rate limit: ~50 requests/minute per IP (informal).
- No API key needed.
- Status enums are uppercase (e.g., `RECRUITING`, not `recruiting`).
- Phase values include the `PHASE` prefix (e.g., `PHASE3`, not `3`).
- For drug pipeline research, combine `query.intr` (drug name) with `filter.phase` and `filter.overallStatus`.
- The `resultsSection` is only present for studies that have posted results.
