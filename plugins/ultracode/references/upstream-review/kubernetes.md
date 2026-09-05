# Kubernetes review playbook

Use for changed Kubernetes contracts, not as a mandatory checklist for every PR. The command owns orchestration, preservation, and evidence rules. Read the target repository's current contributor, API, test, and release guidance before assuming a policy. Combine with the node/runtime or test-infra playbook when the change crosses those boundaries.

## Enhancement and historical contract

- Identify the owning component/SIG and the user-observable behavior being changed. Follow the linked issue, KEP, implementation PRs, relevant review replies, and reverts using `gh`; search narrowly by feature/symbol when links are absent.
- Determine whether the change implements or alters an enhancement. API additions, feature-gate/default changes, graduation, persisted semantics, and compatibility promises warrant checking the applicable KEP. Do not demand a new KEP for an ordinary corrective bug fix without a policy basis.
- Check the KEP revision/status and target release: design, alternatives, feature-gate lifecycle, test plan, production-readiness questions, metrics, graduation criteria, skew, upgrade, downgrade, and rollback. Distinguish a missing implementation requirement from a proposal that still needs a maintainer decision.
- Include substantive KEP review comments, not only its final text. Record accepted resolutions and open objections with links; do not let a previous approval or a resolved thread replace source verification.
- For a KEP/document review, test the proposed invariants and feasibility across affected components. Label planned behavior as planned; do not claim runtime implementation or test coverage exists merely because the proposal describes it.

## APIs, configuration, and stored state

Trace input -> validation/defaulting -> conversion/serialization -> consumers -> persisted/observed state.

- Check nil versus empty versus zero, explicit versus omitted fields, quantities/units, integer width/rounding, and unknown/unsupported values. Compare every affected version/backend rather than assuming shared representations imply shared semantics.
- Check API conventions and compatibility: served/storage versions, protobuf/JSON/OpenAPI, field ownership and patch/apply behavior, status/spec boundaries, admission, authorization, and error contracts where changed.
- For feature gates, inspect enabled, disabled, defaulted, and previously-enabled states. Does disabling the gate prevent new use, handle existing state, and undo effects where promised? What happens when components disagree on the gate or supported version?
- Check rolling upgrade and rollback with old clients, mixed control-plane/node versions, persisted objects/checkpoints, and existing running workloads. Do not infer supported skew from memory; cite the current policy and applicable enhancement contract.
- Confirm defaults and validation agree with scheduler, controller, kubelet, runtime, and user-facing documentation. A valid configuration must not become unusable merely because a lower layer interprets a sentinel differently.

## Reconciliation and cross-component behavior

- Follow desired state, cached state, observed state, and actual side effects separately. Examine stale informer reads, optimistic concurrency, conflicts, retries, idempotency, duplicate events, and interrupted reconciliations.
- Check ownership/finalizers/garbage collection and cleanup after partial creation or deletion. Establish who repairs drift after restart, failure, cancellation, or leader change.
- For each retry, identify the event or actor that makes progress and verify it does not depend on the deferred operation succeeding first. A timer alone does not provide convergence.
- Enumerate independent operations suppressed by a new guard or early return. Check whether other writers really repair them under the same feature/configuration; inspect those writers rather than citing their existence.
- For scheduling/resource changes, compare requests, limits, allocatable/capacity, admission, accounting, and enforcement. For storage/networking changes, trace CSI/CNI or external-controller contracts and asynchronous cleanup where relevant; scope dependent versions explicitly.
- Evaluate security at actual boundaries: namespace/tenant isolation, RBAC/admission, node-to-control-plane trust, privilege changes, path handling, and sensitive data in errors/events/metrics.
- Check scale consequences: API calls, watch/list behavior, workqueue growth, lock contention, event storms, metric cardinality, and failure amplification. Require a workload and causal cost, not a generic performance warning.

## Tests and delivery

- Inspect relevant unit, integration, e2e, node-e2e, upgrade/skew, and conformance tests according to the changed contract. Separate a demonstrated coverage gap from a demand for more tests without a defect hypothesis.
- Prefer counterexamples across feature-off/on, old/new state, retry/partial failure, and backend/value boundaries. Fakes may bypass API defaulting, validation, conflicts, clocks, and real controller/runtime behavior; state what they cannot prove.
- Inspect the actual CI job and head SHA before treating results as evidence. Skipped Linux/build-tagged tests, permissive mocks, and compile-only checks do not establish runtime behavior.
- Honor staging ownership, dependency pinning, generated-code rules, boilerplate, release-note requirements, and project test commands. Detect required generation without regenerating the user's checkout during review.
- Surface compatibility or KEP approval questions separately from code defects; do not issue approval, merge, or conformance claims on behalf of maintainers.

## Challenge prompts

- Which valid sentinel reaches the consumer, and does the consumer preserve its meaning?
- What reads the old installed state while the new desired state is deferred?
- Which alternative repair path works with this exact gate, version, and restart state?
- Would this test still pass if the intended side effect never occurred?

Use these to challenge a causal hypothesis, not to manufacture findings. Include consequential exclusions and unresolved contracts in the review record.
