# Code Comments

One-shot inline code review with source comments.

- Leave a question anywhere in the code: `# AQ: why is this hardcoded?`
- Run `/code-comments:code-comments`
- The agent replies inline with `# AA: ...` directly below, visible in your
  normal diff. Code changes only when you ask (`fix` / `apply` / `change`).
- Run `/code-comments:code-comments clean` to strip all `AQ`/`AA` lines.

Use whatever comment prefix is valid for the file (`#`, `//`, `<!-- -->`,
`--`, ...). An `AQ` already followed by `AA` is done, so re-running is safe.

## Install

```sh
claude plugin install --scope local code-comments@productivity-tools
```
