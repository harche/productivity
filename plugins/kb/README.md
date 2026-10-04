# kb

A short skill that tells agents to look up GitHub, OpenShift Node and Jira related knowledge in
[pg_kb](https://github.com/harche/pg_kb), a personal PostgreSQL knowledge base, using plain SQL
through `psql`. Needs a running pg_kb install (database `kb`).

```sh
claude plugin install --scope local kb@productivity-tools
```

Full schema docs and query idioms live in the pg_kb repo (`docs/`).
