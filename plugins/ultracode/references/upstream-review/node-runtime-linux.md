# Node, runtime, and Linux review playbook

Use when a change depends on node/runtime/Linux behavior. Apply the command's read-only and local-preservation rules. Read relevant project instructions for every dependency source inspected. Follow only causal dependencies; unrelated kernel archaeology is not additional coverage.

## Establish the real stack

Record the relevant kubelet/CRI client and server, CRI-O or other runtime, conmon, OCI runtime (crun/runc), cgroup library, systemd, kernel, OS/architecture, and feature configuration. Distinguish versions pinned by the repository from deployment versions supplied by the user and versions merely assumed.

- Inspect vendored code, dependency manifests/locks, image digests, build options, and runtime selection. Prefer the implementation actually built over current upstream main.
- Use `gh` for GitHub source/history/review evidence and pinned revisions. For non-GitHub kernel/systemd documentation or source, use the available read-only source retrieval mechanism and cite its version. Missing source or deployment details are explicit limits, not permission to invent behavior.
- Kernel/systemd versions and distribution backports can change behavior. Do not generalize a test on one host to every supported deployment.
- Identify relevant axes: cgroup v1/v2, systemd/cgroupfs, rootful/rootless, controllers enabled, swap support, security policy, CPU/NUMA topology, and existing versus newly created workloads. Investigate only axes that can change the claim.

## Trace operations to the decisive layer

Possible chains include kubelet -> CRI request -> CRI-O -> OCI configuration -> crun/runc -> library/systemd property or syscall -> kernel. Not every stack uses every link; establish the actual path.

At each relevant boundary inspect:
- Value semantics: pointer presence, zero, negative/unlimited, empty/omitted, quantity units, sign/width, rounding, and saturation.
- Whether a value causes a write at all; the distinction between a requested value, omitted setting, installed limit, observed usage, and effective hierarchical constraint.
- Ordering, atomicity, partial success, and which independent resource updates are suppressed on failure.
- Return codes, wrapping, propagation, retry policy, and whether errors describe the actual failed operation.

Read kernel documentation and implementation when the userspace contract is insufficient or disputed. Verify conditions on the relevant write/syscall, including synchronous work and side effects, rather than treating a successful write as harmless. Stop descending once the claim is established; a userspace no-op may already settle it.

## Resource management and progress

- Compare accounting definitions end to end: total usage, working set, reclaimable cache, RSS, swap, hierarchical usage, available memory, and capacity/allocatable. Trace which installed or desired value supplies each observation.
- For memory limit changes, distinguish reclaim, pressure, OOM, and rejection. Establish cgroup version, flags, and kernel/runtime behavior; do not assume v1 and v2 or all runtime backends behave alike.
- Review CPU shares/weight/quota/cpuset, topology and NUMA, PID limits, huge pages, I/O, and unified settings when they share the update path. A memory guard must not silently suppress unrelated reconciliation.
- Treat safety and liveness independently: preventing immediate harm does not prove eventual enforcement. Identify what lowers usage or changes the failure condition, and whether eviction/reclaim sees the pending target or only the old installed limit.
- Check stable above-target usage without unrelated pressure, recoverable and persistent read/write failures, equality boundaries, and no-write sentinels. Trace other writers before claiming either permanent drift or guaranteed recovery.
- Validate proposed split updates or retries against backend side effects; removing one field may not make every remaining write independent or safe.

## Lifecycle, isolation, and cleanup

- Trace sandbox/container creation, start, stop, exit, remove, and restart recovery. Consider failed intermediate steps, idempotent requests, timeouts/cancellation, concurrent calls, and orphaned resources.
- Check process supervision, signals, wait/reap behavior, PID reuse, exit status, file descriptors, sockets, logs, and goroutine/process lifetime where changed. State the ordering necessary to trigger a race.
- Inspect namespace entry/ownership, user mappings, capabilities, seccomp, SELinux, cgroup delegation, rootless constraints, and privilege boundaries rather than assuming a root-only test covers them.
- For mounts/storage, follow path resolution, symlinks, propagation, bind mounts, read-only behavior, labeling, cleanup, and restart. Identify the attacker-controlled input before claiming an escape or escalation.
- Include persisted cgroup settings, OCI/runtime state, checkpoints, and live workloads across configuration changes or upgrades. Fresh creation is not a substitute for existing-state testing.

## Verification and counterexamples

- Match host/VM kernel, systemd, cgroup mode, runtime, and architecture to the claim. A container shares its host kernel; an ordinary container does not establish host-systemd behavior.
- Prefer safe unit/source checks first. Live cgroup, namespace, OOM, mount, or privileged-runtime experiments need an explicitly authorized disposable environment, never the user's host or live cluster by default.
- Explain what a fake bypasses. Assert the intended side effect and independent preserved behavior, not only an error or call count. Distinguish package compilation from execution and source proof from a live reproduction.
- Examples for adversarial checking: a nonnil zero setting that the backend omits; a new guard blocking another resource; a larger installed memory limit preventing pressure toward a smaller pending target; an update that succeeds only for newly created state.
- These examples are hypotheses, not canned findings. Prove reachability and the base-versus-target difference, and test the strongest counterargument before accepting or dismissing them.
