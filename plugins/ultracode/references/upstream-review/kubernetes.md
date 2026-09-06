# Kubernetes review playbook

For changes to Kubernetes APIs, KEPs, feature gates, controllers, scheduling, storage, networking, or compatibility.

## History to gather

Use `gh`. Follow the linked issue, the KEP and its review comments (accepted resolutions and open objections, with links), the implementation PRs, review threads including resolved and outdated ones, and any reverts. When links are absent, search narrowly by feature or symbol. A previous approval or a resolved thread is evidence of a decision, not proof the code does what it says.

## Policy to cite rather than remember

- A KEP is warranted for API additions, feature-gate or default changes, graduation, persisted semantics, and compatibility promises. An ordinary corrective bug fix does not need one; do not demand it without a policy basis.
- Check the KEP's target release and production-readiness answers: gate lifecycle, skew, upgrade, downgrade, rollback, metrics, test plan, graduation criteria. Separate "the KEP promises this" from "the code does this".
- Cite the current version skew policy for the affected components; do not infer supported skew from memory.
- Honor staging ownership, dependency pinning, generated-code and boilerplate rules, and release-note requirements. Detect required regeneration; never regenerate the user's checkout.
- Compatibility and KEP approval questions go to maintainers as questions, separate from defects. Never issue approval, merge, or conformance claims.

## Challenge prompts

- Which valid sentinel (nil, empty, zero, omitted, unlimited) reaches the consumer, and does the consumer preserve its meaning across every served version and backend?
- With the gate disabled after it was enabled, what happens to state that was already persisted?
- What reads the old installed state while the new desired state is deferred?
- For each retry, what event or actor changes the blocking condition? A timer alone does not converge.
- Which independent operations does the new guard or early return suppress, and which writer actually repairs them under this gate and configuration? Inspect that writer.
- Would this test still pass if the intended side effect never occurred? What does the fake bypass: defaulting, validation, conflicts, clocks, real controller behavior?
- Did the CI job at this exact head SHA actually run the test on the relevant platform and build tags, or was it skipped or compile-only?
