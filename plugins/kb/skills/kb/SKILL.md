---
name: kb
description: 'The user''s personal notes on how they do their work: upstream and downstream GitHub PRs and issues (Kubernetes, OpenShift, CRI-O and related), and their team''s Jira (OCPNODE, OCPBUGS). The notes say how the user does the work, not what the code does. Search them before you explain or review a PR or issue, test a change, or pick up a Jira item, and follow their steps. For code, PR history and upstream docs, use `gh`. The kb also holds the user''s tasks. Triggers: "search the kb", "check my notes", "remember this", "my tasks", "add a task".'
---

# kb

One PostgreSQL database holds two things:

- **Notes**: the user's own know-how (how to test, review, set things up), not reference docs.
- **Tasks**: lightweight to-dos (`todo` | `in_progress` | `blocked`; delete when done).

Query it with `psql`; there is no CLI. Authorship is set automatically.

```bash
psql -X -h /tmp -U kb_agent -d kb -c "SELECT ..."
```

## Search

```sql
SELECT kind, title, snippet, item_id
FROM kb.search('deploy a debug kubelet binary', lim => 5);
-- narrow it: domains => '{notes}' | '{tasks}', tags => '{crio}',
--            meta => '{"repo":"cri-o/cri-o"}'
```

Three modes, chosen with `mode =>`:

- `'hybrid'` (default): keyword and semantic results combined.
- `'keyword'`: full-text plus fuzzy title match. Covers notes and tasks.
- `'semantic'`: meaning-based (embeddings). Notes only; finds notes that share no words with the query.

Judge the results by title and snippet, then read only the one or two notes that fit;
don't read every hit. If nothing fits, rephrase and search again before reading more.

```sql
SELECT title, body FROM kb.notes WHERE id = '<item_id>';
SELECT title, body, status, meta->>'pr_url' AS pr_url FROM kb.tasks ORDER BY sort_order;
```

## Write

Search first; if a note on the topic exists, update it instead of adding a near-duplicate:
`SELECT item_id, title FROM kb.search('<title words>', domains => '{notes}', lim => 5);`

Write every note so a future search finds it:

- **Markdown** by default. Use `format = 'text'` or `'html'` only when the user asks for it.
- **Title**: specific, in the words someone would search for ("Test Linux-only kubelet
  changes in a Lima VM", not "Testing notes"). Titles weigh most in search.
- **Body**: self-contained, with the exact commands, paths, flags and error messages.
- **Tags**: 2–5 plain, lower-case tags (`lima`, `kind`, `pr-review`); they also count as
  search words. Reuse existing tags before inventing synonyms. No `:` or `/` in tags.
- **meta**: facts to filter on, with these keys: `jira`, `pr_url`, `repo`.
- **Links**: connect the note to related notes or tasks.

```sql
-- existing tags
SELECT tag, count(*) FROM kb.item_tags GROUP BY tag ORDER BY 2 DESC LIMIT 30;

-- note and its tags in one statement ($md$ quoting avoids escaping the body)
WITH n AS (
  INSERT INTO kb.notes (title, body, meta)
  VALUES ('Test Linux-only kubelet changes in a Lima VM', $md$...$md$,
          '{"repo":"kubernetes/kubernetes"}')
  RETURNING id)
INSERT INTO kb.item_tags (item_id, tag)
SELECT id, t FROM n, unnest('{lima,kubelet,testing}'::text[]) t RETURNING item_id;

-- link to related notes
SELECT item_id, title, distance FROM kb.similar('<note id>', 5);
INSERT INTO kb.links (src_id, dst_id, rel)   -- rel: relates | references | derived_from | ...
VALUES ('<note id>', '<other id>', 'relates') ON CONFLICT DO NOTHING;
```

Tasks:

```sql
INSERT INTO kb.tasks (title, body, priority, meta)  -- priority p0..p3, default p2
VALUES ('...', '...', 'p2', '{"jira":"OCPNODE-123"}') RETURNING id;
```

**Delete** by `id` only, after showing the user what will go. Tags, links, embeddings and search entries are cleaned up automatically.

Tags, `meta` and links work the same on tasks. For anything else,
inspect the schema yourself (`\dt kb.*`, `\d+ kb.notes`) and write the SQL you need.
