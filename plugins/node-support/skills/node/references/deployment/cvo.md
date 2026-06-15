# Deploying a Custom CVO to a Test Cluster

Build a custom Cluster Version Operator binary and run it on an OpenShift cluster
for testing. Build commands (`go build`, `Dockerfile`) are discoverable from the
CVO repo — this file is only the non-obvious parts.

## The Non-Obvious Model

CVO does **not** run from a plain Deployment image you can swap. It runs from a
**release payload** — a container image bundling every OpenShift manifest plus the
CVO binary. To test your binary you must rebuild a payload that grafts your binary
onto the cluster's current release, then point CVO at it:

```bash
CURRENT=$(oc get clusterversion version -o jsonpath='{.status.desired.image}')
oc adm release new --from-release="$CURRENT" \
  --to-image-base=quay.io/USER/cvo-dev:$TAG \
  --to-image=quay.io/USER/cvo-dev:release-$TAG -a /tmp/pull-secret-combined.json
```

This pulls ~190 component images from the current release, swaps the CVO base
image for yours, and pushes the assembled payload (2–5 min).

## Gotchas

- **Two patches, not one.** Patching the CVO deployment needs *both* the container
  image **and** the `--release-image` arg (`args[1]`). The image patch changes the
  binary; the arg patch tells CVO where to read manifests. Miss either and it fails
  or degrades.
  ```bash
  oc patch -n openshift-cluster-version deployment cluster-version-operator --type json --patch="[
    {\"op\":\"replace\",\"path\":\"/spec/template/spec/containers/0/image\",\"value\":\"$RELEASE\"},
    {\"op\":\"replace\",\"path\":\"/spec/template/spec/containers/0/args/1\",\"value\":\"--release-image=$RELEASE\"}]"
  ```

- **Unique tag every build.** Never reuse `:latest` — Docker layer caching leaves an
  old binary in the pod. Confirm by comparing binary file sizes (pod vs. local
  `_output/...`); a mismatch means a stale cached layer, rebuild with a fresh tag.

- **`oc adm release new` needs quay *write* creds.** The cluster pull-secret is
  read-only, so the push fails with `unauthorized`. Merge your quay.io auth into a
  copy of the pull-secret first. It also needs `quay.io/openshift-release-dev` read
  access (from console.redhat.com/openshift/install/pull-secret) to pull components.
  It cannot read local Docker-daemon images — push to a registry first.

- **Leader-election lag.** After the pod restarts, CVO takes up to ~3 min to acquire
  the lease before doing anything. Silence early on is normal; watch the logs for
  `acquired`/`leader`.

## Safety

- **Disposable test clusters only — never production.** CVO continuously reconciles
  manifests from the payload; a bad manifest can degrade the cluster.
- **Save the original image + `args[1]` before patching** so you can restore by
  re-patching with the saved values.

## Quick Reference

| Step | Command |
|------|---------|
| Save original (for restore) | `oc get deploy cluster-version-operator -n openshift-cluster-version -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}{.spec.template.spec.containers[0].args[1]}'` |
| Current release image | `oc get clusterversion version -o jsonpath='{.status.desired.image}'` |
| Cluster pull-secret | `oc get secret pull-secret -n openshift-config -o jsonpath='{.data.\.dockerconfigjson}' \| base64 -d` |
| Wait for rollout | `oc rollout status deployment/cluster-version-operator -n openshift-cluster-version --timeout=180s` |
| Verify binary | `oc exec -n openshift-cluster-version deployment/cluster-version-operator -- ls -la /usr/bin/cluster-version-operator` |
| CVO logs | `oc logs -n openshift-cluster-version -l k8s-app=cluster-version-operator --tail=200` |
