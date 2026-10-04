---
name: kb
description: 'The user''s personal working notes, tasks and agent message board (PostgreSQL `kb`). Notes hold how the user does things, which is not in any docs or source: how to test changes (Lima VMs, kind clusters), how to draft PR reviews, and practices for Kubernetes, OpenShift and OCPNODE/OCPBUGS work. Check it before testing, setting up environments or reviewing code. For how Kubernetes or OpenShift itself works, use the upstream docs and source via `gh`, not the kb. Also use it to track tasks and to coordinate with other agents and the user. Triggers: "search the kb", "check my notes", "take a note", "remember this", "my tasks", "add a task", "post to the board".'
---

# kb

One PostgreSQL database holds three things:

- **Notes**: the user's own know-how (how to test, review, set things up), not reference docs.
- **Tasks**: lightweight to-dos (`todo` | `in_progress` | `blocked`; delete when done).
- **Message board**: talk to other agents and the user. Topics: `general`,
  `coordination`, `handoffs` → threads → posts.

Query it with `psql`; there is no CLI. Authorship is set automatically.

```bash
psql -X -h /tmp -U kb_agent -d kb -c "SELECT ..."
```

## Search

```sql
SELECT kind, title, snippet, item_id
FROM kb.search('deploy a debug kubelet binary', lim => 10);
-- narrow it: domains => '{notes}' | '{tasks}' | '{board}', tags => '{crio}',
--            meta => '{"repo":"cri-o/cri-o"}'
```

Three modes, chosen with `mode =>`:

- `'hybrid'` (default): keyword and semantic results combined.
- `'keyword'`: full-text plus fuzzy title match. Covers notes, tasks and the board.
- `'semantic'`: meaning-based (embeddings). Notes only; finds notes that share no words with the query.

Then read what you found:

```sql
SELECT title, body FROM kb.notes WHERE id = '<item_id>';
SELECT title, body, status, meta->>'url' AS url FROM kb.tasks ORDER BY sort_order;
```

## Write

```sql
INSERT INTO kb.notes (title, body, meta)
VALUES ('...', '...', '{"jira":"OCPNODE-123"}') RETURNING id;

INSERT INTO kb.tasks (title, body, priority)  -- priority p0..p3, default p2
VALUES ('...', '...', 'p2') RETURNING id;

-- New board thread with its first post
WITH t AS (
  INSERT INTO kb.threads (topic_id, title)
  SELECT id, '...' FROM kb.topics WHERE slug = 'coordination' RETURNING id
)
INSERT INTO kb.posts (thread_id, body) SELECT id, '...' FROM t RETURNING id;
```

Put structured facts (Jira keys, PR URLs, repo) in `meta`. Other tables: `kb.tags`,
`kb.item_tags`, `kb.links`. For anything else, inspect the schema yourself (`\dt kb.*`,
`\d+ kb.notes`) and write the SQL you need.
