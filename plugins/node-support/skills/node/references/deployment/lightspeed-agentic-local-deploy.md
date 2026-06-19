# Deploying Lightspeed Agentic From Local Sources

Run **local, uncommitted** Lightspeed agentic changes (operator + console plugin) on a
test OpenShift cluster — no CI, no Konflux round-trip. Build the images **in-cluster**
(`oc start-build`) so they land in the internal registry at the node's arch; this avoids
the three walls that sink `make deploy-local` from a laptop (see "Why not deploy-local").

Repos (submodules of the `lightspeed` workspace — work in a git worktree):
`lightspeed-agentic-operator/` and `lightspeed-agentic-console/`. Namespace:
`openshift-lightspeed`. Console plugin needs **OCP 4.21+**.

## Procedure

Set once: `export KUBECONFIG=<path>` (ask the user which cluster), `NS=openshift-lightspeed`,
`REG=image-registry.openshift-image-registry.svc:5000`.

**0. Preflight (read-only):** `oc whoami` (cluster-admin), `oc get clusterversion version -o jsonpath='{.status.desired.version}'` (≥4.21 for console).

**1. Base resources (only if the cluster is empty).** Use the operator's quickstart to
lay down CRDs + namespace + `ApprovalPolicy`:
`bash lightspeed-agentic-operator/hack/quickstart/install.sh`.
⚠️ Quickstart installs **upstream `:main`** images and **GitHub `main` CRDs** — *not* your
local changes. Steps 2–4 then overwrite it with local builds. If the cluster already has
the operator, skip this.

**2. Operator — regenerate, build in-cluster, deploy:**
```bash
cd lightspeed-agentic-operator
make manifests                                                   # regen CRDs from your Go types
oc -n $NS new-build --name=lightspeed-agentic-operator --binary --strategy=docker   # one-time
oc -n $NS start-build lightspeed-agentic-operator --from-dir=. --follow             # builds on a node, pushes to internal registry
make deploy \
  IMG=$REG/$NS/lightspeed-agentic-operator:latest \
  OPERATOR_NAMESPACE=$NS \
  SANDBOX_IMAGE=quay.io/redhat-user-workloads/crt-nshift-lightspeed-tenant/lightspeed-agentic-sandbox:main \
  SANDBOX_MODE=bare-pod
```
`make deploy` applies your regenerated CRDs + RBAC and creates the **`controller-manager`**
Deployment pointing at the internal image.

**3. Console plugin — build in-cluster, point the operator at it:**
```bash
cd ../lightspeed-agentic-console
# repo has NO .dockerignore — add one or the build uploads node_modules (~600M):
printf 'node_modules\ndist\n.git\n.yarn\n' > .dockerignore
oc -n $NS new-build --name=lightspeed-agentic-console --binary --strategy=docker      # one-time
oc -n $NS start-build lightspeed-agentic-console --from-dir=. --follow
# the operator deploys the plugin; it reads the image from --agentic-console-image (skips when empty):
oc -n $NS patch deploy controller-manager --type=json \
  -p '[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--agentic-console-image='$REG'/'$NS'/lightspeed-agentic-console:latest"}]'
```
On restart the operator's console reconciler `CreateOrUpdate`s the
`lightspeed-agentic-console-plugin` Deployment to your image — **don't patch that
Deployment yourself, the operator reverts it.**

**4. Remove the rival operator (if you ran quickstart).** Quickstart's Deployment is
`lightspeed-agentic-operator`; kustomize's is `controller-manager`. Two controllers in the
same namespace fight over the same CRs — delete the quickstart one:
`oc -n $NS delete deploy/lightspeed-agentic-operator`.

**5. Verify.** Pods Running, images are the internal refs, CRD reflects your change:
```bash
oc get pods -n $NS                                               # controller-manager + console-plugin Running
oc get crd analysisresults.agentic.openshift.io -o yaml | grep -A3 estimatedImpact   # e.g. confirm a dropped field is gone
```

## Why not `make deploy-local`

`deploy-local` does a **local `podman build` + push** to the integrated registry. From a
laptop that fails three ways at once — in-cluster build dodges all three:

- **Arch:** arm64 laptop vs amd64 nodes; the build target doesn't force `--platform`, so the
  pushed image won't run. In-cluster builds on the node's arch.
- **No token under cert auth:** `system:admin` (client-cert kubeconfig) has no bearer token,
  so `oc whoami -t | podman login` fails (*"no token is currently in use"*).
- **Untrusted registry route:** podman rejects the ingress-CA route cert
  (`x509: … unknown authority`); the push target omits `--tls-verify=false`.

If you *must* push locally anyway, get a token without clobbering the cert kubeconfig:
`cp $KUBECONFIG /tmp/k && KUBECONFIG=/tmp/k oc login -u kubeadmin -p "$(cat <auth>/kubeadmin-password)" <server>`.

## Gotchas

- **Makefile deploy defaults are footguns.** `OPERATOR_NAMESPACE` defaults to `default`
  and `SANDBOX_IMAGE` defaults to a **mock** agent — always pass the real values (step 2).
- **Internal registry ref for pulls.** Reference images as `$REG/$NS/<app>:latest`; the
  Deployment's SA already has `system:image-puller` for its own namespace, so **no pull
  secret** is needed. The external default-route ref would need node CA trust + a token.
- **Base-image pull auth.** Operator base `registry.redhat.io/*` needs entitlement; the
  cluster global pull secret (`openshift-config/pull-secret`) normally has it. Console
  bases are public `registry.access.redhat.com/*`. Build pods also need egress for
  `go mod download` / `npm ci`.
- **`.dockerignore`:** operator already has one (ignores `bin/ config/ cli/`); console has
  **none** — add it, or `start-build` uploads `node_modules/`.
- **Idle after deploy.** The operator does nothing until an `LLMProvider` + `Agent` exist.
- Use a git **worktree** for the local changes; deploy scripts tag worktree images
  `wt-<name>` on some paths — the in-cluster build above uses `:latest` regardless.

## Quick Reference

| Step | Command |
|------|---------|
| Operator build | `oc -n openshift-lightspeed start-build lightspeed-agentic-operator --from-dir=. --follow` |
| Operator deploy | `make deploy IMG=image-registry.openshift-image-registry.svc:5000/openshift-lightspeed/lightspeed-agentic-operator:latest OPERATOR_NAMESPACE=openshift-lightspeed SANDBOX_IMAGE=quay.io/redhat-user-workloads/crt-nshift-lightspeed-tenant/lightspeed-agentic-sandbox:main SANDBOX_MODE=bare-pod` |
| Console build | `oc -n openshift-lightspeed start-build lightspeed-agentic-console --from-dir=. --follow` |
| Console image flag | `oc -n openshift-lightspeed patch deploy controller-manager --type=json -p '[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--agentic-console-image=image-registry.openshift-image-registry.svc:5000/openshift-lightspeed/lightspeed-agentic-console:latest"}]'` |
| Delete rival operator | `oc -n openshift-lightspeed delete deploy/lightspeed-agentic-operator` |
| Verify rollout | `oc rollout status deploy/controller-manager -n openshift-lightspeed --timeout=120s` |
| Check deployed image | `oc get deploy controller-manager -n openshift-lightspeed -o jsonpath='{.spec.template.spec.containers[0].image}'` |
