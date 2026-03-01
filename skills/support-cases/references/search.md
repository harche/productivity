# Search & Filter

Search and filter support cases using the filter endpoint.

## Filter Endpoint

```bash
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST "https://api.access.redhat.com/support/v1/cases/filter" \
  -d '{FILTER_JSON}' \
  | python3 -m json.tool
```

## Filter Parameters

| Parameter | Type | Description |
|---|---|---|
| `maxResults` | int | Max cases to return (default varies) |
| `offset` | int | Skip N cases for pagination |
| `keyword` | string | Text search across case summary and description |
| `status` | string | Filter by status (e.g., "Closed", "Waiting on Red Hat", "Waiting on Customer") |
| `product` | string | Filter by product name (e.g., "OpenShift Container Platform") |
| `startDate` | string | ISO 8601 datetime, cases created after this date |
| `endDate` | string | ISO 8601 datetime, cases created before this date |

## Response Format

```json
{
  "totalCount": 43,
  "cases": [
    {
      "summary": "...",
      "status": "...",
      "severity": "...",
      "product": "...",
      "version": "...",
      "caseType": "...",
      "createdDate": "...",
      "lastModifiedDate": "...",
      "comments": [...]
    }
  ]
}
```

## Pagination

```bash
# First page
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST "https://api.access.redhat.com/support/v1/cases/filter" \
  -d '{"maxResults": 10, "offset": 0}' \
  | python3 -m json.tool

# Next page
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST "https://api.access.redhat.com/support/v1/cases/filter" \
  -d '{"maxResults": 10, "offset": 10}' \
  | python3 -m json.tool
```

## Common Queries

### List All Open Cases

```bash
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST "https://api.access.redhat.com/support/v1/cases/filter" \
  -d '{"maxResults": 20}' \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'Total open cases: {data[\"totalCount\"]}')
print(f'{\"Case\":<12} {\"Status\":<25} {\"Severity\":<15} {\"Summary\"}')
print('-' * 100)
for c in data['cases']:
    case_num = c.get('uri', '').split('/')[-1]
    print(f'{case_num:<12} {c[\"status\"]:<25} {c[\"severity\"]:<15} {c[\"summary\"][:50]}')
"
```

### Search by Keyword

```bash
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST "https://api.access.redhat.com/support/v1/cases/filter" \
  -d '{"maxResults": 10, "keyword": "search term here"}' \
  | python3 -m json.tool
```

### Filter by Product

```bash
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST "https://api.access.redhat.com/support/v1/cases/filter" \
  -d '{"maxResults": 10, "product": "OpenShift Container Platform"}' \
  | python3 -m json.tool
```

### Closed Cases

```bash
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST "https://api.access.redhat.com/support/v1/cases/filter" \
  -d '{"maxResults": 10, "status": "Closed"}' \
  | python3 -m json.tool
```

### Cases Created in Date Range

```bash
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST "https://api.access.redhat.com/support/v1/cases/filter" \
  -d '{"maxResults": 10, "startDate": "2026-02-01T00:00:00Z", "endDate": "2026-02-28T23:59:59Z"}' \
  | python3 -m json.tool
```

### Tabular Output

```bash
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST "https://api.access.redhat.com/support/v1/cases/filter" \
  -d '{"maxResults": 20, "keyword": "upgrade"}' \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'Total: {data[\"totalCount\"]} cases')
print()
for c in data['cases']:
    case_num = c.get('uri', '').split('/')[-1]
    print(f'{case_num} [{c[\"status\"]}] [{c[\"severity\"]}]')
    print(f'  {c[\"summary\"]}')
    print(f'  Product: {c[\"product\"]} {c.get(\"version\", \"\")}')
    print(f'  Contact: {c.get(\"contactName\", \"N/A\")} | Owner: {c.get(\"ownerId\", \"N/A\")}')
    print(f'  Created: {c[\"createdDate\"]} | Modified: {c[\"lastModifiedDate\"]}')
    print()
"
```
