# Gmail

Search, read, send, and manage Gmail emails, threads, labels, and drafts.

## Search

```bash
# Search threads (grouped by conversation)
gog gmail search '<gmail-query>' [--max=10] [--all]

# Search individual messages
gog gmail messages search '<gmail-query>' [--max=10] [--all] [--include-body]
```

Gmail query syntax: `from:`, `to:`, `subject:`, `newer_than:`, `older_than:`, `has:attachment`, `is:unread`, `label:`, `in:inbox`, `in:sent`, `filename:pdf`, etc.

## Read

```bash
# Get a single message
gog gmail get <messageId> [--format=full|metadata|raw]

# Get a full thread with all messages
gog gmail thread get <threadId> [--full] [--download]

# List attachments in a thread
gog gmail thread attachments <threadId>

# Download a specific attachment
gog gmail attachment <messageId> <attachmentId> [--out-dir=DIR]

# Get Gmail web URL for a thread
gog gmail url <threadId>
```

## Send

**IMPORTANT: Always confirm with the user before sending emails.**
**IMPORTANT: When replying to a thread or message, ALWAYS use `--quote` to preserve the email chain.**

```bash
# Send a new email
gog gmail send --to "a@example.com" --subject "Subject" --body "Body text"

# Send with CC, BCC, attachments
gog gmail send --to "a@example.com" --cc "b@example.com" --subject "Subject" \
  --body "Body" --attach file1.pdf --attach file2.png

# Reply to a thread (--quote preserves the email chain)
gog gmail send --thread-id <threadId> --reply-all --quote --body "Reply text"

# Reply to a specific message (--quote preserves the email chain)
gog gmail send --reply-to-message-id <messageId> --reply-all --quote --body "Reply"

# Send HTML email
gog gmail send --to "a@example.com" --subject "Subject" --body-html "<h1>Hello</h1>"

# Body from file or stdin
gog gmail send --to "a@example.com" --subject "Subject" --body-file message.txt
gog gmail send --to "a@example.com" --subject "Subject" --body-file -  # stdin

# Dry run (preview without sending)
gog gmail send --to "a@example.com" --subject "Test" --body "Test" --dry-run
```

## Labels

```bash
# List all labels
gog gmail labels list

# Get label details (including counts)
gog gmail labels get <labelIdOrName>

# Create a label
gog gmail labels create "<name>"

# Add/remove labels on threads
gog gmail labels modify <threadId> --add-labels "UNREAD,Label_123" --remove-labels "INBOX"

# Delete a label
gog gmail labels delete <labelIdOrName>
```

## Threads

```bash
# Modify labels on a thread
gog gmail thread modify <threadId> --add-labels "STARRED" --remove-labels "UNREAD"
```

## Drafts

```bash
# List drafts
gog gmail drafts list [--max=10]

# Get draft details
gog gmail drafts get <draftId>

# Create a draft
gog gmail drafts create --to "a@example.com" --subject "Subject" --body "Body"

# Update a draft
gog gmail drafts update <draftId> --body "Updated body"

# Send a draft (ALWAYS confirm with user first)
gog gmail drafts send <draftId>

# Delete a draft
gog gmail drafts delete <draftId>
```

## Batch Operations

```bash
# Modify labels on multiple messages
gog gmail batch modify <msgId1> <msgId2> --add-labels "Label_1" --remove-labels "UNREAD"

# Permanently delete messages (ALWAYS confirm with user first)
gog gmail batch delete <msgId1> <msgId2>
```

## Settings

```bash
# Filters
gog gmail settings filters list
gog gmail settings filters get <filterId>

# Vacation responder
gog gmail settings vacation get
gog gmail settings vacation set --enable --subject "OOO" --body "I'm away"

# Forwarding
gog gmail settings forwarding list
gog gmail settings autoforward get

# Send-as aliases
gog gmail settings sendas list

# Delegates
gog gmail settings delegates list
```

## Common Workflows

**Check inbox for recent unread emails:**
```bash
gog gmail search 'is:unread newer_than:1d' --json
```

**Find and read a specific email thread:**
```bash
gog gmail search 'from:boss@company.com subject:review'
gog gmail thread get <threadId> --full
```

**Reply to a thread:**
```bash
gog gmail send --thread-id <threadId> --reply-all --body "Thanks, I'll look into it." --quote
```

**Archive emails (remove from inbox):**
```bash
gog gmail thread modify <threadId> --remove-labels "INBOX"
```

**Mark as read:**
```bash
gog gmail thread modify <threadId> --remove-labels "UNREAD"
```
