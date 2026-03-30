# Multi-Tab Workflows

## Open and manage tabs

```bash
# Open a new tab
playwright-cli tab-new https://example.com/page-a

# Open another tab
playwright-cli tab-new https://example.com/page-b

# List all tabs
playwright-cli tab-list

# Switch to a tab by index (0-based)
playwright-cli tab-select 0

# Close a tab
playwright-cli tab-close 2

# Close current tab
playwright-cli tab-close
```

## Research across multiple sites

```bash
playwright-cli open https://site-a.com
playwright-cli tab-new https://site-b.com
playwright-cli tab-new https://site-c.com

# Read from each tab
playwright-cli tab-select 0
playwright-cli snapshot

playwright-cli tab-select 1
playwright-cli snapshot

playwright-cli tab-select 2
playwright-cli snapshot
```

## Compare pages side by side

```bash
playwright-cli open https://example.com/v1
playwright-cli snapshot --filename=v1.yaml

playwright-cli tab-new https://example.com/v2
playwright-cli snapshot --filename=v2.yaml
```

## Parallel browsing with named sessions

For fully isolated browsing (separate cookies, storage):

```bash
playwright-cli -s=site1 open https://site1.com
playwright-cli -s=site2 open https://site2.com

playwright-cli -s=site1 snapshot
playwright-cli -s=site2 snapshot

playwright-cli close-all
```

See [Session management](session-management.md) for more on named sessions.
