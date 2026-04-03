# Compilation Guide

## Topic Identification

When reading raw sources, identify topics by looking for:

1. **Explicit subject areas** — what is the source about? (e.g., "workload partitioning", "pod autoscaling")
2. **Recurring concepts** — terms that appear across multiple sources
3. **Natural groupings** — sources that discuss the same system, workflow, or problem domain

Map topics to directory names using lowercase-hyphens:
- "Workload Partitioning" → `wiki/workload-partitioning/`
- "Pod Autoscaling" → `wiki/pod-autoscaling/`
- "CRI-O Configuration" → `wiki/crio-configuration/`

## Article Synthesis Patterns

### From Documentation Sources

Documentation is typically well-structured already. The wiki article should:
- Distill the key information (don't reproduce the entire doc)
- Add practical context: when would you use this? Common pitfalls?
- Include the most important commands/YAML snippets
- Link back to the full source for complete reference

### From Conversation Transcripts

Conversations contain discoveries, debugging sessions, and decisions. The wiki article should:
- Lead with the conclusion/finding, not the investigation path
- Include evidence: metrics, cgroup data, config snippets
- Capture decisions and their rationale
- Note what was tried and didn't work (saves future time)

### From Multiple Sources on the Same Topic

When several sources cover the same concept:
- Identify what each source contributes uniquely
- Synthesize a coherent narrative, not a source-by-source summary
- Note and resolve contradictions between sources (with dates for context)
- List all sources in the Sources section

## Cross-Linking Strategy

### When to Cross-Link

Add a `[[wikilink]]` when:
- An article mentions a concept that has its own article
- Two articles describe different aspects of the same system
- One article's findings depend on understanding another's content

### Link Placement

- **In body text**: use inline wikilinks naturally: "This interacts with [[wiki/scheduling/taints-and-tolerations.md|taints and tolerations]]"
- **In Related section**: list all articles that share concepts, even if not referenced in the body

## Handling Large Compilations

For 10+ raw sources, organize the work:

1. **Group sources by topic** — read all sources first, then cluster
2. **Assign to parallel agents** — one agent per topic area
3. **Each agent creates articles independently** — they don't need to coordinate
4. **Parent agent merges** — update `_index.md` with all new entries, add cross-links between topic areas

## Article Quality Checklist

Before finalizing an article:
- [ ] Summary is 1-2 sentences and stands alone
- [ ] Key Points capture the essentials someone would scan for
- [ ] Details section has practical content (commands, configs, examples)
- [ ] Every claim traces to a source
- [ ] Every link has a hint
- [ ] Related section links to overlapping articles
- [ ] Article is indexed in `_index.md`
