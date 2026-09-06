# Node, runtime, and Linux review playbook

For changes whose behavior depends on kubelet, CRI, CRI-O, conmon, crun/runc, cgroups, systemd, or the kernel.

## Establish the real stack first

Pin down which kubelet, CRI-O or runtime, conmon, OCI runtime, cgroup library, systemd, kernel, OS, and architecture the change actually runs against. Read the vendored code, dependency manifests, image digests, and build options; review the implementation that is built, not upstream main. Distinguish versions pinned by the repository from versions the user says are deployed from versions merely assumed. Kernel and systemd behavior varies by version and distro backport; a result on one host does not generalize.

Identify only the axes that can change the claim: cgroup v1 or v2, systemd or cgroupfs, rootful or rootless, enabled controllers, swap, security policy, CPU and NUMA topology, existing versus newly created workloads.

## Trace to the decisive layer

The chain may run kubelet -> CRI request -> CRI-O -> OCI config -> crun/runc -> libcontainer or systemd property -> syscall -> kernel. Establish the actual path and stop descending once the claim is settled; a userspace no-op often settles it. Go to kernel documentation or source when the userspace contract is insufficient or disputed, and cite the version.

## Safety

Unit and source checks first. Live cgroup, namespace, OOM, mount, or privileged-runtime experiments need an explicitly authorized disposable environment, never the user's host or a live cluster. A container shares its host kernel and does not establish host-systemd behavior.

## Challenge prompts

- Does this value cause a write at all? Distinguish requested value, omitted setting, installed limit, observed usage, and effective hierarchical constraint.
- Does a non-nil zero, negative, or unlimited value survive the boundary, or does the backend omit or reinterpret it?
- When one field's write fails, which independent resource updates in the same path are now suppressed, and who retries them?
- Preventing immediate harm is not enforcement. What eventually lowers usage or changes the failure condition, and does eviction or reclaim see the pending target or only the old installed limit?
- Does the change work for existing containers and persisted cgroup or OCI state, or only for fresh creation?
- What ordering of create, start, stop, exit, remove, restart, timeout, or concurrent call triggers the race? Name it.
- Which attacker-controlled input reaches the path resolution, mount, namespace, capability, seccomp, SELinux, or user-mapping decision?
- What does the fake bypass, and does the test assert the intended side effect rather than an error or call count?
