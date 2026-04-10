---
name: kb-lint
description: Run health checks on a knowledge base to find broken links, orphaned sources, missing cross-references, stale data, and gaps in coverage. Suggests new articles, connections between existing articles, and improvements to link hints. Use when the user says "lint the KB", "check for gaps", "health check", or periodically after adding many sources to ensure consistency and completeness.
---

# KB Lint

Run health checks on a knowledge base to find inconsistencies, gaps, and opportunities for improvement.

## Required Input

**KB path** — absolute path to the knowledge base directory.

## Checks to Run

### 1. Broken Wikilinks

Scan all `wiki/` articles for `[[wikilinks]]` that point to files that don't exist. Report each broken link with the file it's in and what it points to.

### 2. Orphaned Raw Sources

Find files in `raw/` that aren't referenced by any wiki article's `## Sources` section. These are sources that were ingested but never compiled.

**Action:** Suggest compiling them or confirm they should be removed.

### 3. Orphaned Wiki Articles

Find wiki articles that have no entries in their `## Sources` section, or whose sources have been deleted from `raw/`.

**Action:** Flag for review — the article may need sources added or may be outdated.

### 4. Index Consistency

Compare `wiki/_index.md` against actual wiki articles:
- Articles that exist but aren't in the index
- Index entries that point to articles that don't exist
- Summaries that are stale or empty

### 5. Missing Cross-References

Find pairs of wiki articles that share:
- Common source documents (both reference the same raw source)
- Common topics (based on frontmatter `topics` field)
- Common outbound links (both link to the same external URL)

If they don't already link to each other in their `## Related` sections, suggest adding cross-references.

### 6. Link Hint Coverage

Check raw source frontmatter and wiki article Sources sections for links that lack hints. Links without hints reduce the navigability of the KB.

**Action:** Suggest hints based on the context where the link appears.

### 7. Topic Coverage Gaps

Analyze the raw sources and wiki articles to identify:
- Clusters of related links that don't have a wiki article
- Topics mentioned frequently across sources but not covered by an article
- External links that appear in multiple sources (suggesting an important concept worth documenting)

**Action:** Suggest new article candidates with proposed outlines.

### 8. Stale Content Detection

If web access is available, spot-check a sample of external links to see if they're still reachable. Flag any that return 404 or redirect.

## Output Format

Present findings as a structured report:

```markdown
## KB Health Report — [KB Name]

### Broken Links (N found)
- `wiki/topic/article.md` line 45: `[[wiki/missing.md]]` — not found

### Orphaned Sources (N found)
- `raw/source.md` — not referenced by any wiki article

### Index Issues (N found)
- `wiki/topic/article.md` — exists but not in _index.md

### Missing Cross-References (N suggestions)
- `wiki/a.md` and `wiki/b.md` share source `raw/x.md` but don't link to each other

### Links Without Hints (N found)
- `wiki/topic/article.md`: [PR #123](url) — no hint

### Suggested New Articles (N suggestions)
- **Topic Name** — mentioned in N sources, no dedicated article. Proposed outline: ...

### Summary
- Total articles: N
- Total sources: N  
- Health score: N% (broken links, orphans, missing refs as % of total)
```

## Logging

After completing the lint, append an entry to `log.md` in the KB root:

```markdown
## [YYYY-MM-DD] lint | Health check

- **Broken links:** N
- **Orphaned sources:** N
- **Index issues:** N
- **Missing cross-refs:** N suggestions
- **Health score:** N%
```

## Important

- **Read-only by default.** Lint reports problems and suggests fixes — it doesn't modify files unless the user explicitly asks to apply fixes.
- **Prioritize actionable findings.** A lint report full of minor style issues is noise. Focus on things that affect navigability and accuracy: broken links, orphaned content, missing connections.
- **Suggest, don't prescribe.** Topic coverage gaps are suggestions, not requirements. The user decides what's worth documenting.
