---
name: kb
description: Look things up in the personal PostgreSQL knowledge base (database `kb`) with plain SQL. Use it for GitHub, OpenShift Node team and Jira related questions (kubelet, CRI-O, MCO, debug binaries, CVO, OCPNODE/OCPBUGS, PRs and issues being tracked) and whenever the user says "search the kb", "what do we know about", "check my notes" or "my tasks".
---

# kb: look it up in PostgreSQL

Notes (including the imported node-support and devkit docs), an agent message board and
lightweight tasks live in one PostgreSQL database. Query it with `psql`; there is no CLI.

```bash
psql -X -h /tmp -U kb_agent -d kb -c "SELECT ..."
```

Search everything (notes rank by keywords and meaning; board and tasks by keywords):

```sql
SELECT kind, title, snippet, item_id
FROM kb.search('deploy a debug kubelet binary', lim => 10);
-- narrow it: domains => '{notes}' | '{board}' | '{tasks}', tags => '{plugin:node-support}',
--            meta => '{"repo":"cri-o/cri-o"}', mode => 'keyword'
```

Then read what you found:

```sql
SELECT title, body FROM kb.notes WHERE id = '<item_id>';
SELECT title, body, status, meta->>'url' AS url FROM kb.tasks ORDER BY sort_order;
```

Main tables: `kb.notes`, `kb.tasks`, `kb.topics` / `kb.threads` / `kb.posts`, `kb.tags`,
`kb.item_tags`, `kb.links`. Every table has a `meta jsonb` column with structured facts
(Jira keys, PR URLs, repo). For anything else, inspect the schema yourself (`\dt kb.*`,
`\d+ kb.notes`) and write the SQL you need.
