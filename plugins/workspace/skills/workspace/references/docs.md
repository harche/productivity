# Google Docs Reference

Full command reference for Google Docs via `gog docs`.

## Read a Doc

```bash
# Print as plain text
gog docs cat <docId>

# Read a specific tab
gog docs cat <docId> --tab="Tab Name"

# Read all tabs
gog docs cat <docId> --all-tabs

# Limit bytes read
gog docs cat <docId> --max-bytes=50000
```

## Get Doc Metadata

```bash
gog docs info <docId>
```

## List Tabs

```bash
gog docs list-tabs <docId>
```

## Create a Doc

**Always confirm with the user before creating documents.**

```bash
# Create an empty doc
gog docs create "My Document"

# Create in a specific folder
gog docs create "My Document" --parent=<folderId>

# Create from a markdown file
gog docs create "My Document" --file=content.md
```

## Write Content

**Always confirm with the user before writing to documents.**

```bash
# Append text to a doc
gog docs write <docId> "New content to append"

# Replace all content
gog docs write <docId> "Replacement content" --replace

# Write from a file
gog docs write <docId> --file=content.txt

# Write from stdin
gog docs write <docId> --file=-

# Write markdown with formatting conversion
gog docs write <docId> --file=content.md --replace --markdown
```

## Insert Text

```bash
gog docs insert <docId> "Text to insert"
```

## Delete Text

```bash
gog docs delete <docId> --start=10 --end=50
```

## Find and Replace

```bash
gog docs find-replace <docId> "old text" "new text"
```

## Update Content

```bash
gog docs update <docId>
```

## Export

```bash
# Export as PDF (default)
gog docs export <docId>

# Export as other formats
gog docs export <docId> --format=pdf
gog docs export <docId> --format=docx
gog docs export <docId> --format=txt

# Export to a specific path
gog docs export <docId> --out=./report.pdf
```

## Copy a Doc

```bash
gog docs copy <docId> "Copy Title" [--parent=<folderId>]
```

## Comments

```bash
gog docs comments list <docId>
gog docs comments create <docId> --content="Please review"
```
