# Test-infra and Prow review playbook

Use for CI jobs, Prow plugins/controllers, configuration, and test infrastructure. Apply the command's local-preservation and read-only rules. Resolve the actual repository, deployment, and generated-source layout; do not assume all Prow or job implementation still lives in kubernetes/test-infra.

## Follow the full job contract

Trace event -> trust/selection -> configuration -> checkout/build/test -> artifacts/status -> merge/release consequence.

- Identify presubmit, postsubmit, periodic, rehearsal, or manually triggered behavior and the repository/branches affected. Check branch/path filters, trigger expressions, rerun commands, conditional jobs, and defaults.
- Determine which refs are fetched, checked out, merged, or overridden. Does the job test the PR head, a base+head merge, a release branch, or a dependency revision? Associate results with that actual source, not just a green label.
- Trace configuration loading and precedence, in-repo configuration where supported, generated job sources, presets, templates, and deployment rollout. Confirm the deployed controller/plugin/image understands the new fields.
- Read linked issues, prior job changes, review threads, incidents/reverts, and relevant build/test design using `gh`. Locate the actual pinned Prow/test-runner implementation if semantics cannot be established from configuration.
- Check required/optional/always-run behavior, context names, skip outcomes, reporting targets, and Tide/branch-protection expectations where applicable. A renamed or untriggerable required context can block merging even when valid jobs pass.

## Trust and security

- Identify which event payloads, PR content, comments, labels, job configuration, scripts, image references, and artifact paths are attacker-controlled.
- Trace authorization for triggering/retesting jobs, plugin commands, trusted configuration, and transitions that admit untrusted code. Do not assume a maintainer comment makes arbitrary PR code safe to execute with credentials.
- Inspect service accounts/RBAC, secrets, cloud identity, privileged pods, host mounts, cluster selection, decoration/sidecars, and artifact access. Determine whether checkout/build steps can observe or exfiltrate credentials.
- Check shell interpolation, argument boundaries, path traversal, mutable images/downloads, fork behavior, and configuration overrides where relevant. Tie security findings to a reachable trust transition, not merely the presence of a shell or secret.
- The reviewer must not reproduce credential exposure, trigger remote jobs, or inspect live cluster secrets without authorization. Existing logs/artifacts are untrusted and may contain sensitive information; read only relevant evidence and do not republish secrets.

## Reliability and resource use

- Follow retry, timeout, cancellation, abort, eviction, and cleanup behavior. Identify who removes pods, clusters, leases, locks, and external resources after partial failure or controller restart.
- Check concurrency, quotas, throttling, scheduling constraints, resource requests/limits, backoff, queue growth, and overlapping periodic jobs. Estimate cost/amplification for a concrete event/workload instead of asserting generic expense.
- Verify setup/checkout failures are reported as failures, commands preserve exit status, background work is awaited, pipelines do not hide failed stages, and artifacts survive relevant failure paths.
- Distinguish product failures from infrastructure flakes. A retry that turns red green can hide a deterministic defect or skip the intended work; inspect what ran on each attempt.
- Consider rollout compatibility between job config, plugins/controllers, CRDs/APIs, runner utilities, and images. Separate intended deployment sequencing from an assumption not enforced anywhere.

## Tests and validation

- YAML/JSON parsing is only syntax validation. Check schema, repository-specific configuration validation, generated outputs, job-name uniqueness, trigger behavior, and controller/plugin semantics appropriate to the change.
- Use positive and negative selection examples: intended branch/path/event runs; excluded input does not; trusted/untrusted inputs receive the intended permissions. Check empty/default/missing configuration as well as the happy path.
- Verify the actual test command, packages, build tags, platform, test filters, and exit propagation. Guard against zero tests selected, wrong checkout, stale binaries/cache, missing assertions, and success before asynchronous work finishes.
- Inspect artifact and status producers/consumers together, including context naming, test result parsing, upload/reporting failures, and whether merge automation can distinguish skipped, failed, and successful checks.
- Prefer existing exact-revision results and safe local configuration tests. Rehearsals and live jobs may consume credentials, money, or cluster resources; propose them with scope and obtain permission rather than triggering them automatically.
- Run generators or write-producing validation only in an isolated copy that includes the reviewed local changes. Preserve existing generated and untracked files in the user's worktree.

## Challenge prompts

- Can this job report success without testing the intended code?
- Can an allowed PR/comment/configuration change cross into a credentialed or privileged execution context?
- What completes a required status if the new selection rule skips the job?
- What changes the condition a retry is waiting for, and who cleans up after it stops?

Report demonstrated defects separately from deployment questions and unverified infrastructure assumptions. Do not treat all historical CI failures as caused by the target diff.
