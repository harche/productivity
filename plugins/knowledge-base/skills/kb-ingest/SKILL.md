---
name: kb-ingest
description: Ingest sources into an LLM-maintained knowledge base and compile them into structured wiki articles. Sources can be Claude Code conversation transcripts (JSONL files), URLs, markdown files, PDFs, images, or pasted text. Use this skill when the user wants to add knowledge to a KB, says "add this to the KB", shares a conversation file, or wants to capture learnings from a session. Also triggers when a user wants to initialize a new knowledge base. After ingesting, this skill automatically compiles the source into wiki articles.
---

# KB Ingest

Add source material to a knowledge base and compile it into structured wiki articles. This is the primary entry point for growing a knowledge base.

## What This Skill Does

1. Accepts a source (conversation JSONL, URL, file, pasted text)
2. Processes it into a structured raw source document in `raw/`
3. Automatically compiles new/updated wiki articles in `wiki/`
4. Updates the master index

## Required Input

The user must provide two things:

1. **KB path** — absolute path to the knowledge base directory (e.g., `/Users/harpatil/Projects/Karpathy-KB`)
2. **Source** — one of:
   - A Claude Code conversation transcript (`.jsonl` file path, typically under `~/.claude/projects/`)
   - A URL (web article, GitHub issue/PR, tweet, Reddit thread)
   - A file path (`.md`, `.pdf`, `.png`, `.csv`, `.py`, `.txt`)
   - Pasted text in the conversation

If the user doesn't specify the KB path, ask for it.

## Workflow

### Step 1: Discover or Initialize the KB

Read `AGENTS.md` (or `CLAUDE.md` if it's a symlink) from the KB path to understand the schema — directory structure, article format, conventions.

If the KB path is empty or doesn't exist:

1. Create the directory structure: `raw/`, `wiki/`, `outputs/`, `tools/`
2. Set up Obsidian vault config (`.obsidian/app.json`, `.obsidian/core-plugins.json`)
3. Create `AGENTS.md` with a default schema. See [references/source-types.md](references/source-types.md) for the default schema.
4. Create `wiki/_index.md` as the master index
5. Symlink `CLAUDE.md -> AGENTS.md`
6. Initialize git repo with appropriate `.gitignore`

### Step 2: Process the Source

Each source type has a different processing path:

#### Conversation Transcripts (JSONL)

Claude Code conversations are stored as `.jsonl` files (one JSON object per line). Read the file directly — it's typically 1-5MB. See [references/conversation-parsing.md](references/conversation-parsing.md) for the JSONL format.

The extraction process:

1. Read the JSONL file line by line
2. For each line, parse the JSON object — look at the `type` field
3. Extract messages where `type` is `user` or `assistant`
4. The actual text is in `.message.content` — it's either a string or an array of content blocks (look for blocks where `type` is `text`)
5. Skip noise: lines starting with `<local-command`, `<command-`, `<bash-`, `<task-notification`, `Base directory for this skill`
6. Identify the substantive topics, decisions, findings, and technical details
7. Synthesize a structured raw source document — not a transcript, but distilled findings organized by topic

The synthesized document should capture:
- What was investigated and why
- Key findings with evidence
- Decisions made and their rationale
- Technical details (commands, configs, YAML, metrics)
- All URLs, issue numbers, PR numbers mentioned

#### URLs

Fetch the content using available tools (web browser skill, `curl`, `gh` for GitHub URLs). Convert to markdown and save to `raw/`. For GitHub issues/PRs, use `gh issue view` or `gh pr view`. For tweets, use the twitter skill if available.

#### Files

Copy the file to an appropriate subdirectory in `raw/`. For markdown files, read and optionally enhance with a metadata frontmatter block.

#### Pasted Text

Save to `raw/` as a markdown file with a descriptive filename.

### Step 3: Add Link Manifest Frontmatter

Every raw source document gets a YAML frontmatter block with metadata and a link manifest. The link manifest is the key innovation — it captures all outbound links with hints about what knowledge they point to, so someone (human or LLM) can reconstruct the full knowledge by following them.

```yaml
---
title: Descriptive Title of the Source
source_type: conversation | url | file | text
source_path: original path or URL
date: YYYY-MM-DD
topics:
  - topic-1
  - topic-2
links:
  - url: https://github.com/org/repo/pull/123
    hint: PR implementing the feature discussed
  - url: https://issues.redhat.com/browse/PROJ-456
    hint: Customer ticket reporting the original problem
  - url: https://docs.example.com/page
    hint: Official documentation for the API used
---
```

**Writing good link hints:**
- A hint should tell someone whether the link is worth following for their question
- Include what kind of knowledge the link contains, not just what it is
- Bad: `GitHub PR` / Good: `PR implementing inject_gomaxprocs precreate hook in CRI-O`
- Bad: `Jira ticket` / Good: `Customer ticket: 512-core baremetal thread explosion, Westpac Banking`

### Step 4: Compile into Wiki

After saving the raw source, automatically compile it into wiki articles. Invoke the kb-compile skill logic:

1. Read `AGENTS.md` for the wiki article format
2. Read `wiki/_index.md` to understand existing articles
3. For the new source:
   - Identify which concepts/topics it covers
   - Check if wiki articles already exist for those topics
   - **If new topic**: create new article(s) in appropriate `wiki/<topic>/` directory
   - **If existing topic**: update the existing article with new information, add the new source to the `## Sources` section
4. Update `wiki/_index.md` with entries for any new articles

When creating or updating wiki articles:
- Follow the format defined in `AGENTS.md`
- Use `[[wikilinks]]` for internal cross-references (Obsidian-compatible)
- In the `## Sources` section, include link hints from the frontmatter:
  ```markdown
  ## Sources
  - [[raw/crio-gomaxprocs-investigation.md]] — CRI-O GOMAXPROCS hook and customer case analysis
  - [PR #9860](https://github.com/cri-o/cri-o/pull/9860) — PR implementing inject_gomaxprocs precreate hook
  - [OCPBUGS-61881](https://redhat.atlassian.net/browse/OCPBUGS-61881) — 512-core baremetal thread explosion, Westpac Banking
  ```

### Step 5: Report

Tell the user what was created/updated:
- Raw source file path and size
- Number of links captured with hints
- Wiki articles created or updated
- Updated index entries

## Important

- **Synthesize, don't transcribe.** Raw source docs should be distilled knowledge, not conversation logs. Someone reading the raw source should understand the findings without needing the original conversation.
- **Every link gets a hint.** A link without a hint is a dead end. The hint is what makes the knowledge base navigable — it tells you whether following that link will answer your question.
- **Preserve provenance.** Every claim in a wiki article should trace back to a source. Never introduce information that isn't grounded in the raw sources.
- **Use the KB's own schema.** Always read `AGENTS.md` first. Different KBs may have different article formats, directory conventions, or topic structures. Don't assume.
- **Incremental, not destructive.** When updating existing articles, add to them — don't overwrite existing content unless it's contradicted by newer evidence. If there's a contradiction, note both with dates.
