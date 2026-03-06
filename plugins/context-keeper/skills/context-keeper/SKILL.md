---
name: context-keeper
description: Extract context from Slack threads, Google Docs, Jira issues, and other sources, then build and maintain structured markdown knowledge bases that track evolving discussions, debates, and decisions. Use this skill whenever the user wants to summarize or document a discussion, track a decision-making process, create project notes from scattered sources, build a knowledge base from conversations, or asks you to "write up" or "document" what was discussed. Also trigger when the user shares multiple source links (Slack, Google Docs, Jira) and wants them synthesized into coherent documentation, or when they ask you to update existing project docs with new information from ongoing discussions.
---

# Context Keeper

Build and maintain structured markdown knowledge bases from scattered discussions across Slack, Google Docs, Jira, and other sources.

This skill is for the common pattern where decisions and context live across many places — a Slack thread kicks off a discussion, a Google Doc captures proposals, Jira tracks the work, and follow-up threads refine the plan. Context Keeper synthesizes all of that into a navigable documentation tree that both humans and AI agents can use effectively.

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

Share your understanding with the user before generating docs. A quick summary like "Here's what I understand — does this capture it?" saves rework.

### Phase 4: Structure

Generate a documentation tree in the user's current working directory. The structure uses **progressive disclosure** — a reader (human or AI) starts with the overview and drills into details only as needed.

See [references/doc-structure.md](references/doc-structure.md) for the file structure, templates, and formatting conventions.

### Phase 5: Evolve

Knowledge bases aren't write-once. As discussions continue, the user will come back with new Slack threads, updated docs, or changed decisions. When updating:

1. **Read existing docs first** — understand what's already captured before making changes.
2. **Update in place** — modify existing files rather than creating new ones, unless a genuinely new topic emerges.
3. **Track decision changes** — if a decision changed, note what changed and why. Don't silently overwrite.
4. **Keep cross-references valid** — if you add or rename a file, update all links.
5. **Update CLAUDE.md** — if the project context changed materially, reflect it there.

## Important

- **Link everything.** Every Jira issue, Slack thread, Google Doc, GitHub PR, or strategy document you mention must be a clickable link. Bare references like "OCPSTRAT-918" or "the original doc" are not acceptable — always use `[OCPSTRAT-918](https://issues.redhat.com/browse/OCPSTRAT-918)` or `[original doc](https://docs.google.com/document/d/...)`. Links are how readers find depth. If you don't have a URL for something, use the available plugins to look it up, or ask the user. This applies to every file you generate — CLAUDE.md, README.md, and all docs.
- **Be balanced, not an advocate.** When documenting a decision, give the chosen option's cons just as much rigor as the rejected options' cons. If you find yourself writing mostly about why something is great, step back and ask what could go wrong. A knowledge base that only captures the happy path is incomplete.
- **Don't over-document.** Capture decisions, rationale, and open questions — not meeting minutes or play-by-play transcripts. The goal is a knowledge base, not a log.
- **Prefer updating to appending.** A clean, current document is more useful than one with a changelog at the bottom.
- **Keep CLAUDE.md under 50 lines.** It loads into every conversation. It should contain just enough for an AI agent to orient itself and know where to look for details.
- **Use the user's language.** Mirror the terminology from the source discussions, don't impose your own jargon.
