---
name: kb-compile
description: Compile or recompile wiki articles from raw sources in a knowledge base. Reads all raw source documents, identifies topics and concepts, and creates or updates structured wiki articles with summaries, cross-links, and source attribution. Use when the user says "compile the wiki", "update wiki from raw", "recompile", or when multiple sources have been added to raw/ and the wiki needs to catch up. Also used internally by kb-ingest after adding a new source.
---

# KB Compile

Read raw sources and compile them into structured, cross-linked wiki articles. This is the "build step" of the knowledge base — it transforms a pile of source documents into a navigable wiki.

## Required Input

**KB path** — absolute path to the knowledge base directory.

If the user doesn't provide it, ask.

## Workflow

### Step 1: Read the Schema

Read `AGENTS.md` (or `CLAUDE.md`) from the KB root. This defines:
- The wiki article format (headings, sections, structure)
- Directory conventions (topic naming, nesting)
- Any project-specific conventions

### Step 2: Inventory

Take stock of what exists:

1. **Read `wiki/_index.md`** — understand what articles already exist and their summaries
2. **List all files in `raw/`** — these are the sources to compile from
3. **List all files in `wiki/`** — these are the existing articles
4. **Diff** — identify:
   - Raw sources not yet reflected in any wiki article (new sources)
   - Raw sources that have been modified since their wiki articles were last updated
   - Wiki articles whose sources have been removed (orphans)

### Step 3: Plan the Compilation

Before writing, plan what articles to create or update:

1. Read new/changed raw sources
2. Identify the **topics and concepts** they cover
3. Map each concept to an existing or new wiki article
4. Group related sources that should feed into the same article
5. If the compilation is large (10+ new articles), share the plan with the user for confirmation

### Step 4: Compile Articles

For each new or updated article:

1. **Read all relevant raw sources** for that topic
2. **Synthesize** — don't just copy content. Distill key points, identify patterns, resolve contradictions between sources
3. **Follow the article format** from `AGENTS.md`. Typically:
   - Title and brief summary
   - Key Points (bullets)
   - Details (synthesized content with practical examples)
   - Sources (with link hints from raw source frontmatter)
   - Related (wikilinks to other wiki articles)
4. **Preserve link hints** — when a raw source has links in its frontmatter, carry those into the wiki article's Sources section with their hints
5. **Cross-link** — add `[[wikilinks]]` to related articles wherever concepts overlap

### Step 5: Update the Index

Update `wiki/_index.md`:
- Add one-line summaries for new articles
- Update summaries for modified articles
- Group articles by topic section
- Remove entries for deleted articles

### Step 6: Log the Operation

Append an entry to `log.md` in the KB root:

```markdown
## [YYYY-MM-DD] compile | Description

- **Articles created:** N (list paths)
- **Articles updated:** N (list paths)
- **Articles unchanged:** N
- **Index updated:** yes/no
```

### Step 7: Report

Tell the user:
- Number of articles created/updated/unchanged
- Any structural changes (new topic directories)
- Suggested follow-ups (related topics that could be added)

## Compilation at Scale

When compiling many sources at once (e.g., initial bulk import), use parallel subagents — one per topic area. Each agent:
- Gets a subset of the raw sources
- Creates articles for its topic
- The parent agent then updates `_index.md` with all new entries

See [references/compilation-guide.md](references/compilation-guide.md) for patterns on topic identification and article synthesis.

## Important

- **Read AGENTS.md first.** Every KB may have its own article format. Don't assume a structure — read the schema.
- **Synthesize, don't copy.** Wiki articles should be easier to read than the raw sources. Distill, organize, and connect.
- **Link hints are load-bearing.** When carrying links from raw sources to wiki articles, always include the hint. A link without a hint is a dead end.
- **Incremental updates preserve existing work.** When updating an article, add new information — don't discard existing content unless it's contradicted.
- **Topic directories use lowercase-hyphens.** No spaces, no uppercase, no underscores.
