# Test-infra and Prow review playbook

For CI jobs, Prow plugins and controllers, job configuration, and test infrastructure. Resolve where the Prow and job implementation actually lives and which revision is deployed; not all of it is still in kubernetes/test-infra.

## Follow the full job contract

Trace event -> trust and selection -> configuration -> checkout, build, test -> artifacts and status -> merge or release consequence. Establish which refs the job fetches and tests: PR head, base plus head merge, release branch, or a dependency revision. Confirm the deployed controller, plugin, or image understands any new configuration field. Use `gh` for prior job changes, review threads, incidents, and reverts.

## Safety

Do not trigger remote jobs or rehearsals, reproduce credential exposure, or read live cluster secrets without authorization; live jobs cost credentials, money, and cluster resources. Existing logs and artifacts may contain secrets: read only what the evidence needs and never republish them. Run generators or write-producing validation only in an isolated copy that includes the local changes.

## Challenge prompts

- Can this job report success without testing the intended code? Zero tests selected, wrong checkout, stale cache, a pipeline that hides a failed stage, exit status swallowed, success before background work finishes.
- Can an allowed PR, comment, label, or configuration change cross into a credentialed or privileged execution context? Which event payloads, scripts, image references, and artifact paths are attacker-controlled, and does a maintainer comment really make arbitrary PR code safe to run with credentials?
- What completes a required status context if the new selection rule, branch filter, or rename means the job never runs? Tide and branch protection will block on it.
- What changes the condition a retry is waiting for, and who removes the pods, clusters, leases, locks, and external resources after it stops or the controller restarts?
- A retry that turns red green: did the second attempt run the same work, or skip it?
- Is the rollout order between job config, plugins, controllers, CRDs, runner utilities, and images enforced anywhere, or just assumed?
- YAML parsed is not YAML valid. Did repository-specific validation, generated outputs, job-name uniqueness, and negative selection examples get checked?
