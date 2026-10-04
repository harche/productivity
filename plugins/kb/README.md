# kb

A short skill that tells agents to use [pg_kb](https://github.com/harche/pg_kb), a personal
PostgreSQL knowledge base, for GitHub, OpenShift and OCPNODE/OCPBUGS Jira work: take and search
notes (hybrid, keyword or semantic search), track tasks, and post to a message board shared with
other agents and the user. Everything goes through plain SQL with `psql`. Needs a running pg_kb install (database `kb`).

```sh
claude plugin install --scope local kb@productivity-tools
```

Full schema docs and query idioms live in the pg_kb repo (`docs/`).
