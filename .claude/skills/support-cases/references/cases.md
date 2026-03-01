# Cases

View, comment on, and manage support cases.

## View Case

```bash
# Full case details (includes comments)
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://api.access.redhat.com/support/v1/cases/{caseNumber}" \
  | python3 -m json.tool

# Extract key fields
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://api.access.redhat.com/support/v1/cases/{caseNumber}" \
  | python3 -c "
import sys, json
c = json.load(sys.stdin)
print(f'Case:     {c.get(\"uri\", \"\").split(\"/\")[-1]}')
print(f'Summary:  {c[\"summary\"]}')
print(f'Status:   {c[\"status\"]}')
print(f'Severity: {c[\"severity\"]}')
print(f'Product:  {c[\"product\"]} {c.get(\"version\", \"\")}')
print(f'Type:     {c.get(\"caseType\", \"N/A\")}')
print(f'Owner:    {c.get(\"ownerId\", \"Unassigned\")}')
print(f'Contact:  {c.get(\"contactName\", \"N/A\")}')
print(f'Created:  {c[\"createdDate\"]}')
print(f'Modified: {c[\"lastModifiedDate\"]}')
print(f'Escalated: {c.get(\"customerEscalation\", False)}')
print(f'CritSit:  {c.get(\"critSit\", False)}')
print()
print('Description:')
print(c.get('description', 'N/A')[:500])
"
```

## Case Fields

| Field | Description |
|---|---|
| `summary` | Case title |
| `description` | Detailed problem description |
| `status` | Current status (see Status Values below) |
| `severity` | Severity level (see Severity Values below) |
| `product` | Red Hat product name |
| `version` | Product version |
| `caseType` | Case type (e.g., "Defect / Bug", "Configuration Issue") |
| `ownerId` | Red Hat case owner name |
| `contactName` | Customer contact name |
| `contactSSOName` | Customer SSO username |
| `accountNumberRef` | Customer account number |
| `createdDate` | ISO 8601 creation timestamp |
| `lastModifiedDate` | ISO 8601 last modified timestamp |
| `createdById` | Creator display name |
| `lastModifiedById` | Last modifier display name |
| `customerEscalation` | Whether customer requested escalation (boolean) |
| `critSit` | Critical situation flag (boolean) |
| `requestManagementEscalation` | Management escalation requested (boolean) |
| `internalStatus` | Internal-facing status |
| `origin` | Case origin (e.g., "Web", "Phone") |
| `openshiftClusterID` | OpenShift cluster ID if applicable |
| `hotfixRequested` | Hotfix requested flag |
| `hotfixDelivered` | Hotfix delivered flag |
| `apiTags` | List of internal tags |

### Status Values

Common status values:
- `Waiting on Red Hat`
- `Waiting on Customer`
- `Closed`

### Severity Values

- `1 (Urgent)` — Production system down
- `2 (High)` — Significant business impact
- `3 (Normal)` — Standard issue
- `4 (Low)` — Minor issue or question

## Comments

```bash
# List all comments on a case
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://api.access.redhat.com/support/v1/cases/{caseNumber}/comments" \
  | python3 -m json.tool

# Format comments for readability
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://api.access.redhat.com/support/v1/cases/{caseNumber}/comments" \
  | python3 -c "
import sys, json
comments = json.load(sys.stdin)
for c in comments:
    visibility = c.get('visibility', 'Unknown')
    public = 'Public' if c.get('isPublic') else 'Internal'
    print(f'--- [{public}/{visibility}] {c[\"createdBy\"]} ({c[\"createdDate\"]}) ---')
    body = c.get('commentBody', '')
    print(body[:500])
    if len(body) > 500:
        print(f'... ({len(body)} chars total)')
    print()
"

# Add a comment (ALWAYS confirm with user first)
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST "https://api.access.redhat.com/support/v1/cases/{caseNumber}/comments" \
  -d '{"commentBody": "Comment text here (max 32K characters)"}' \
  | python3 -m json.tool
```

### Comment Fields

| Field | Description |
|---|---|
| `commentBody` | Comment text content |
| `isPublic` | Whether visible to customer (boolean) |
| `visibility` | "Customer" or "Associate" |
| `createdBy` | Author display name |
| `createdDate` | ISO 8601 timestamp |
| `createdByType` | "Associate" or "Customer" |
| `caseNumber` | Parent case number |
| `id` | Comment ID |

## Attachments

```bash
# List attachments on a case
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://api.access.redhat.com/support/v1/cases/{caseNumber}/attachments" \
  | python3 -m json.tool
```

## Multiple Cases from Jira

When Jira bugs reference SFDC case numbers (e.g., from `customfield_12313441`), you can look up each case:

```bash
# Look up multiple cases from a Jira bug's SFDC links
for case_id in 04378910 04382468 04388043; do
  echo "=== Case $case_id ==="
  curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
    "https://api.access.redhat.com/support/v1/cases/$case_id" \
    | python3 -c "
import sys, json
c = json.load(sys.stdin)
print(f'  Summary:  {c[\"summary\"]}')
print(f'  Status:   {c[\"status\"]}')
print(f'  Severity: {c[\"severity\"]}')
print(f'  Product:  {c[\"product\"]} {c.get(\"version\", \"\")}')
print(f'  Contact:  {c.get(\"contactName\", \"N/A\")}')
print(f'  Modified: {c[\"lastModifiedDate\"]}')
"
  echo
done
```
