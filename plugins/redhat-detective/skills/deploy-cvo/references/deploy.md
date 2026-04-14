# Deploying Custom CVO to Cluster

## Step 1: Save the Original Image

Before patching, save the original CVO image so you can restore it:

```bash
ORIGINAL_IMAGE=$(oc get deployment cluster-version-operator -n openshift-cluster-version -o jsonpath='{.spec.template.spec.containers[0].image}')
ORIGINAL_ARG=$(oc get deployment cluster-version-operator -n openshift-cluster-version -o jsonpath='{.spec.template.spec.containers[0].args[1]}')
echo "Original image: ${ORIGINAL_IMAGE}"
echo "Original arg: ${ORIGINAL_ARG}"
```

Save these values — you'll need them to restore.

## Step 2: Patch the CVO Deployment

The CVO deployment needs TWO patches — the container image AND the `--release-image` argument:

```bash
RELEASE="quay.io/USER/cvo-dev:release-TAG"

imagePatch='{"op":"replace","path":"/spec/template/spec/containers/0/image","value":"'"$RELEASE"'"}'
releaseImageArgPatch='{"op":"replace","path":"/spec/template/spec/containers/0/args/1","value":"--release-image='"$RELEASE"'"}'

oc patch -n openshift-cluster-version deployment cluster-version-operator \
  --type json \
  --patch="[$imagePatch,$releaseImageArgPatch]"
```

**Both patches are required.** The image patch changes what binary runs. The arg patch tells CVO where to find the release manifests. Missing either causes failures.

## Step 3: Wait for Rollout

```bash
oc rollout status deployment/cluster-version-operator -n openshift-cluster-version --timeout=180s
```

## Step 4: Verify Binary

```bash
# Compare file sizes — they MUST match
oc exec -n openshift-cluster-version deployment/cluster-version-operator -- ls -la /usr/bin/cluster-version-operator
ls -la _output/linux/amd64/cluster-version-operator
```

If sizes don't match, the release payload has a cached old binary. Rebuild with a new unique tag.

## Step 5: Wait for Leader Election

CVO uses leader election. After pod restart, it takes up to ~3 minutes to acquire the lease:

```bash
oc logs -n openshift-cluster-version -l k8s-app=cluster-version-operator --tail=100 | grep -E "acquired|leader"
```

## Restoring the Original CVO

```bash
imagePatch='{"op":"replace","path":"/spec/template/spec/containers/0/image","value":"'"$ORIGINAL_IMAGE"'"}'
releaseImageArgPatch='{"op":"replace","path":"/spec/template/spec/containers/0/args/1","value":"'"$ORIGINAL_ARG"'"}'

oc patch -n openshift-cluster-version deployment cluster-version-operator \
  --type json \
  --patch="[$imagePatch,$releaseImageArgPatch]"
```
