# kb

A short skill that tells agents to use [pg_kb](https://github.com/harche/pg_kb), a personal
PostgreSQL knowledge base, for the user's own know-how that is not in any docs or source: how to
test changes, draft reviews and work on Kubernetes, OpenShift and OCPNODE/OCPBUGS. It also tracks
tasks and hosts a message board shared with other agents and the user. Search is hybrid, keyword
or semantic, and everything goes through plain SQL with `psql`. Needs a running pg_kb install (database `kb`).

```sh
claude plugin install --scope local kb@productivity-tools
```

Full schema docs and query idioms live in the pg_kb repo (`docs/`).
