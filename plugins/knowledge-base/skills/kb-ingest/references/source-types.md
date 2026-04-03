# Source Types and Default KB Schema

## Source Types

### Conversation Transcripts (.jsonl)

Claude Code conversation files. See [conversation-parsing.md](conversation-parsing.md) for the JSONL format.

**Saved as:** `raw/<descriptive-name>.md` (synthesized findings, not raw JSONL)

### URLs

Web articles, GitHub issues/PRs, tweets, Reddit threads, documentation pages.

**Processing by URL type:**

| URL pattern | How to fetch |
|-------------|-------------|
| `github.com/.../issues/N` | `gh issue view N -R owner/repo` |
| `github.com/.../pull/N` | `gh pr view N -R owner/repo` |
| `github.com/.../tree/...` or `github.com/.../blob/...` | `gh api` to list/read files |
| `x.com/user/status/ID` | Twitter skill if available, else web browser |
| `reddit.com/r/.../comments/...` | Reddit skill if available, else web browser |
| `*.md` on GitHub | `gh api repos/.../contents/path` with base64 decode |
| Everything else | Web browser or `curl` + html-to-markdown |

**Saved as:** `raw/<descriptive-name>.md` with source URL in frontmatter

### Files

Markdown, PDF, images, CSV, Python, plain text.

**Saved as:** Copy to `raw/` preserving filename, add frontmatter if markdown.

### Pasted Text

Text the user pastes directly in conversation.

**Saved as:** `raw/<descriptive-name>.md` with `source_type: text` in frontmatter

## Default KB Schema (AGENTS.md)

When initializing a new KB, create this `AGENTS.md`:

```markdown
# Knowledge Base Schema

This is a personal knowledge base maintained by an LLM agent. The human rarely edits the wiki directly — the LLM writes, organizes, and maintains it.

## Directory Structure

\```
.
├── AGENTS.md          # This file — schema and instructions for the LLM
├── raw/               # Source documents (articles, papers, notes, images, data)
├── wiki/              # LLM-compiled wiki (structured .md files)
│   ├── _index.md      # Master index of all wiki articles
│   └── <topic>/       # Topic directories containing articles
├── outputs/           # Query results, reports, slides, visualizations
└── tools/             # Helper scripts (search, lint, etc.)
\```

## Workflow

### 1. Ingest
- Human adds source material to `raw/` (articles, papers, images, datasets)
- Sources can be `.md`, `.pdf`, `.png`, `.csv`, `.py`, `.txt`, etc.

### 2. Compile
- LLM reads new sources in `raw/` and integrates them into `wiki/`
- Each concept gets its own `.md` article in an appropriate topic directory
- Articles include: summary, key concepts, backlinks to sources, links to related articles
- `wiki/_index.md` is kept up to date with a brief summary of every article

### 3. Query
- Human asks questions; LLM researches answers using the wiki
- LLM reads `_index.md` first to orient, then dives into relevant articles
- Complex answers are saved as `.md` files in `outputs/`

### 4. Lint
- Periodically run health checks: find inconsistencies, missing data, broken links
- Suggest new articles for interesting connections between concepts

## Wiki Article Format

Each wiki article should follow this structure:

\```markdown
# Article Title

Brief summary (1-2 sentences).

## Key Points
- ...

## Details
...

## Sources
- [[raw/filename.md]] — description
- [[raw/another.md]] — description

## Related
- [[wiki/topic/related-article.md]]
\```

## Conventions
- All paths are relative to the repo root
- Use `[[wikilinks]]` for internal links (Obsidian-compatible)
- Images referenced in articles should be in the same directory or `raw/`
- Keep article summaries in `_index.md` under ~1 line each
- Topic directory names: lowercase, hyphens, no spaces
```

## Default Obsidian Config

**`.obsidian/app.json`:**
```json
{
  "showLineNumber": true,
  "strictLineBreaks": false,
  "readableLineLength": true,
  "useMarkdownLinks": false,
  "showFrontmatter": true
}
```

**`.obsidian/core-plugins.json`:**
```json
[
  "file-explorer",
  "global-search",
  "graph",
  "backlink",
  "page-preview",
  "tag-pane",
  "outgoing-link",
  "outline",
  "word-count",
  "file-recovery"
]
```

**`.gitignore`:**
```
.obsidian/workspace.json
.obsidian/workspace-mobile.json
.obsidian/plugins/
.obsidian/themes/
.DS_Store
.playwright-cli/
.claude/
```
