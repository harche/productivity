# Google Drive

List, search, upload, download, and manage files in Google Drive.

## List Files

```bash
# List files in root folder
gog drive ls [--max=20]

# List files in a specific folder
gog drive ls --parent=<folderId>

# My Drive only (exclude shared drives)
gog drive ls --no-all-drives

# With Drive query filter
gog drive ls --query="mimeType='application/pdf'"
```

## Search

```bash
# Full-text search across Drive
gog drive search "<query>" [--max=20]

# Raw Drive query language
gog drive search "mimeType='application/vnd.google-apps.document'" --raw-query

# My Drive only
gog drive search "report" --no-all-drives
```

## Get File Metadata

```bash
gog drive get <fileId>
```

## Download

```bash
# Download a file
gog drive download <fileId> [--out=path]

# Export Google Docs formats
gog drive download <fileId> --format=pdf
gog drive download <fileId> --format=docx
gog drive download <fileId> --format=txt
gog drive download <fileId> --format=csv    # Sheets
gog drive download <fileId> --format=xlsx   # Sheets
gog drive download <fileId> --format=pptx   # Slides
```

## Upload

**IMPORTANT: Always confirm with the user before uploading files.**

```bash
# Upload a file
gog drive upload ./report.pdf

# Upload to a specific folder
gog drive upload ./report.pdf --parent=<folderId>

# Upload with a custom name
gog drive upload ./report.pdf --name="Q1 Report.pdf"

# Replace an existing file (preserves sharing/permissions)
gog drive upload ./report-v2.pdf --replace=<fileId>

# Convert to native Google format
gog drive upload ./doc.docx --convert
gog drive upload ./data.csv --convert-to=sheet
```

## Create Folder

```bash
gog drive mkdir "New Folder" [--parent=<folderId>]
```

## Move, Rename, Copy

```bash
# Move file to a different folder
gog drive move <fileId> --to=<folderId>

# Rename
gog drive rename <fileId> "New Name"

# Copy
gog drive copy <fileId> "Copy Name" [--parent=<folderId>]
```

## Delete

**IMPORTANT: Always confirm with the user before deleting files.**

```bash
# Move to trash
gog drive delete <fileId>

# Permanently delete
gog drive delete <fileId> --permanent
```

## Sharing & Permissions

```bash
# Share with a user
gog drive share <fileId> --to=user --email="user@example.com" --role=reader
gog drive share <fileId> --to=user --email="user@example.com" --role=writer

# Share with anyone (link sharing)
gog drive share <fileId> --to=anyone --role=reader

# Share with a domain
gog drive share <fileId> --to=domain --domain="example.com" --role=reader

# List permissions
gog drive permissions <fileId>

# Remove a permission
gog drive unshare <fileId> <permissionId>
```

## URLs & Comments

```bash
# Get web URL for a file
gog drive url <fileId>

# Manage comments
gog drive comments list <fileId>
gog drive comments create <fileId> --content="Review this section"
```

## Shared Drives

```bash
gog drive drives
```
