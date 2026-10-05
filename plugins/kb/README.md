# kb

A short skill that tells agents to use [pg_kb](https://github.com/harche/pg_kb), a personal
PostgreSQL knowledge base, for the user's own know-how that is not in any docs or source: how to
test changes, draft reviews and work on Kubernetes, OpenShift and OCPNODE/OCPBUGS Jira issues/epics/strats. It also tracks
tasks. Search defaults to best match (hybrid search, then TypeSafe's Jev picks the notes that fit),
with hybrid, keyword and semantic modes too, and everything goes through plain SQL with `psql`. Needs a running pg_kb install (database `kb`).

```sh
claude plugin install --scope local kb@productivity-tools
```

Full schema docs and query idioms live in the pg_kb repo (`docs/`).
