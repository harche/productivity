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
psql -X -A -h /tmp -U kb_agent -d kb -c "SELECT ..."
```

Always pass `-A`: the default aligned output pads every line to the widest one, which
makes a note body 10x larger. Add `-t` when you read a body, to get just its text.

## Search

```sql
SELECT kind, title, snippet, jev_prob, item_id
FROM kb.search('deploy a debug kubelet binary', mode => 'jev');
-- narrow it: domains => '{notes}' | '{tasks}', tags => '{crio}',
--            meta => '{"repo":"cri-o/cri-o"}'
```

Use `mode => 'jev'` (best match). A hybrid search finds candidates, then a decision model
(TypeSafe's Jev) picks the ones that fit, so you get one to three rows, or none:

- **One row**: read it.
- **Two or three rows**: close alternatives, best first (`jev_prob` says how close). Read the
  first; read the next only if the first doesn't cover the question.
- **No rows**: nothing in the KB fits. Say so, or rephrase once. To see every partial match,
  use `mode => 'hybrid', lim => 5` and judge by title and snippet.

The other modes return ranked lists: `'hybrid'` (keyword and semantic combined, the default
when `mode` is omitted), `'keyword'` (full-text plus fuzzy title; notes and tasks) and
`'semantic'` (embeddings; notes only).

```sql
SELECT title, body FROM kb.notes WHERE id = '<item_id>';   -- psql -X -A -t ...
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
