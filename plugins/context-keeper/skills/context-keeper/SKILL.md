---
name: context-keeper
description: Capture the current state of a project as a mind-map knowledge base using Mermaid diagrams that render on GitHub. Gathers information from Slack threads, Google Docs, Jira issues, and other sources, investigates claims with real evidence, and produces a visual, navigable knowledge base of what was decided, why, what's still open, and where things stand now. Use when the user wants to document a project, track decisions, or synthesize scattered discussions into a single source of truth.
---

# Context Keeper

Build and maintain mind-map knowledge bases from scattered discussions across Slack, Google Docs, Jira, and other sources. Uses Mermaid mindmap diagrams for visual navigation — renders natively on GitHub.

This skill is for the common pattern where decisions and context live across many places — a Slack thread kicks off a discussion, a Google Doc captures proposals, Jira tracks the work, and follow-up threads refine the plan. Context Keeper synthesizes all of that into a mind-map knowledge base that both humans and AI agents can navigate effectively.

## When to Use This Skill

- User shares a Slack thread or Google Doc and wants it documented
- User wants to track an evolving discussion or decision process
- User asks to "write up", "summarize", or "document" a topic from multiple sources
- User wants to update existing project docs with new information
- User has scattered context across sources and wants it organized

## Dependencies

This skill uses other plugins for data fetching. Invoke them as needed:
- **slack** — fetch Slack messages and threads (`/slack`)
- **google** — read Google Docs (`/google`)
- **redhat-support** — read Jira issues (`/redhat-support`)
- **github** — read GitHub issues/PRs (`/github`)

If a source plugin isn't available, ask the user to paste the content directly.

## Workflow

### Phase 1: Gather

Fetch content from all sources the user provides. For each source:

1. **Slack threads** — Use the slack skill to fetch the thread. Resolve user IDs to names for readability.
2. **Google Docs** — Use `gog docs cat <docId>` to read the document.
3. **Jira issues** — Use the redhat-support skill to read the issue and its comments.
4. **GitHub issues/PRs** — Use `gh` to read the content and discussion.
5. **User-provided context** — The user may explain things verbally. Capture this too.

Don't rush to generate docs. Read everything first, then ask clarifying questions if the structure or decisions aren't clear.

### Phase 2: Investigate

Don't just summarize what the sources say — actively verify claims, resolve open questions, and fill gaps. Source documents often contain assumptions, unknowns, or assertions that haven't been validated. Your job is to chase them down.

- **Identify open questions and unknowns.** If a doc says "it's not clear whether X is true", go find out. Search Slack, Jira, GitHub, and docs for evidence.
- **Validate claimed pros and cons.** If someone claims "webhooks cause scalability issues", look for real incidents or discussions that confirm or contradict this. If someone says "this is easy to implement", look for evidence of similar efforts and how they went.
- **Check all sides.** If a decision was made, make sure the cons of the chosen option are investigated just as thoroughly as the cons of the rejected options. One-sided advocacy is not analysis. A good knowledge base captures why the chosen approach might fail, not just why it was chosen.
- **Use parallel research.** When investigating multiple independent questions (e.g., pros/cons of 4 different options), launch subagents in parallel to research each one simultaneously. This is much faster than sequential investigation.
- **Track what you found and what's still unknown.** Every open question should end up in one of three states: resolved with evidence, partially answered with what's known so far, or explicitly flagged as still unknown.

### Phase 3: Synthesize

After gathering and investigating, build a mental model of:

- **What is the problem/topic?** — The core question being discussed.
- **What options or approaches exist?** — Different proposals, with their trade-offs, backed by evidence.
- **What was decided (if anything)?** — The chosen approach and why.
- **What's still open?** — Unresolved questions, pending decisions. Mark whether they're partially answered or completely unknown.
- **Who are the key people?** — Authors, decision makers, stakeholders.
- **What are the key terms?** — Technical jargon the reader needs to understand.

Share your understanding with the user before generating the knowledge base. Present it as a **draft mindmap structure** — the major branches, key sub-branches, and where open questions sit. This is the critical organizing step: the mindmap topology you design here becomes the backbone of the entire document. Every branch you choose implies a section; every level of nesting implies a level of detail. Get alignment on the structure before writing any detail.

### Phase 4: Structure

Generate a mind-map knowledge base in the user's current working directory. **The mindmap is the backbone** — it defines the document structure, not the other way around. You don't write sections and then add a mindmap on top; you design the mindmap first, and sections flow from it.

The knowledge base consists of just two files:

| File | Purpose |
|---|---|
| `README.md` | The knowledge base — overview mindmap at top, detail sections that hang off each branch, sub-mindmaps for complex branches |
| `CLAUDE.md` | AI agent entry point — concise context, section index, key terms (under 50 lines) |

#### Step 1: Design the overview mindmap

This is the most important step. The overview mindmap placed right after the title defines the entire document's structure. Each branch becomes a section, each sub-branch becomes a sub-section. The topology you choose here determines how the knowledge is organized. Keep nodes to 2-6 words — they're labels, not sentences.

Immediately below every Mermaid mindmap, add a **linked navigation list** — a nested markdown list that mirrors the mindmap structure with clickable anchor links and brief descriptions. The Mermaid diagram is the visual rendering for humans on GitHub; the linked list is how AI agents navigate the knowledge base. Both must always stay in sync.

#### Step 2: Write sections for each branch

Every major branch in the overview mindmap becomes a `##` section in README.md. Section order follows the mindmap left to right. If a branch has sub-branches, those become `###` headings within the section. **No section should exist without a corresponding mindmap node** (except Sources, Key People, Key Terms which are standard scaffolding).

#### Step 3: Add sub-mindmaps for complex branches

When a section has its own internal complexity (3+ sub-topics, multiple options, design areas), add a sub-mindmap at the top of that section. This sub-mindmap in turn defines the sub-section structure. The same rule applies: every sub-mindmap node must have a corresponding heading, and vice versa. Each sub-mindmap also gets its own linked navigation list below it.

#### Content separation

Problem/landscape sections present options with theoretical pros/cons; decision sections present investigated evidence and analysis. Don't duplicate evidence across sections — put it in the decision section and reference from others.

See [references/doc-structure.md](references/doc-structure.md) for templates, mindmap guidelines, and formatting conventions.

### Phase 5: Evolve

Knowledge bases aren't write-once. When updating, **start from the mindmap** — it's the source of truth for structure:

1. **Read the overview mindmap first** — this is the structural map. Understand the current topology before diving into detail sections. The mindmap tells you what exists and how it's organized.
2. **Decide what changes structurally** — does a new branch need to be added? An existing one removed or renamed? A sub-branch promoted or demoted? Make structural decisions at the mindmap level, not by editing prose.
3. **Update all mindmap diagrams and their linked navigation** — modify the overview mindmap, any affected sub-mindmaps, and their corresponding linked navigation lists to reflect the new structure. This comes before touching any detail text.
4. **Update corresponding sections** — add, remove, or rewrite detail sections to match the updated mindmaps. Every branch must have a section, every section must have a branch.
5. **Propagate corrections** — when new information contradicts existing content, search for and update every reference. Stale data undermines the whole knowledge base.
6. **Track decision changes** — if a decision changed, note what changed and why. Don't silently overwrite.
7. **Keep CLAUDE.md in sync** — if the mindmap structure changed (sections added, removed, renamed), update the section index.

## Important

- **Link everything.** Every Jira issue, Slack thread, Google Doc, GitHub PR, or strategy document you mention must be a clickable link. Bare references like "OCPSTRAT-918" or "the original doc" are not acceptable — always use `[OCPSTRAT-918](https://issues.redhat.com/browse/OCPSTRAT-918)` or `[original doc](https://docs.google.com/document/d/...)`. Links are how readers find depth. If you don't have a URL for something, use the available plugins to look it up, or ask the user.
- **Be balanced, not an advocate.** When documenting a decision, give the chosen option's cons just as much rigor as the rejected options' cons. If you find yourself writing mostly about why something is great, step back and ask what could go wrong. A knowledge base that only captures the happy path is incomplete.
- **Don't over-document.** Capture decisions, rationale, and open questions — not meeting minutes or play-by-play transcripts. The goal is a knowledge base, not a log.
- **Prefer updating to appending.** A clean, current document is more useful than one with a changelog at the bottom.
- **Keep CLAUDE.md under 50 lines.** It loads into every conversation. It should contain just enough for an AI agent to orient itself and know where to look for details.
- **Use the user's language.** Mirror the terminology from the source discussions, don't impose your own jargon.
- **Mindmap is the source of truth for structure.** Every `##` section must have a corresponding branch in the overview mindmap, and every mindmap branch must have a corresponding section. If they diverge, update the sections to match the mindmap. The same applies to sub-mindmaps and their `###` headings.
