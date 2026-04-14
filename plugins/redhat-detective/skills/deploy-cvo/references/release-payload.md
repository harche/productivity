# Creating a Release Payload with Custom CVO

CVO runs from a **release payload image** — a container image containing all OpenShift manifests plus the CVO binary. You can't just swap the CVO binary; you must build a new release payload.

## Step 1: Tag and Push the Base Image

Use a **unique tag** for each build to avoid caching issues:

```bash
TAG="v$(date +%s)"
docker tag localhost/cvo-dev:latest quay.io/USER/cvo-dev:${TAG}
docker push quay.io/USER/cvo-dev:${TAG}
```

## Step 2: Get the Current Release Image

```bash
CURRENT_RELEASE=$(oc get clusterversion version -o jsonpath='{.status.desired.image}')
echo "Current release: ${CURRENT_RELEASE}"
```

## Step 3: Get the Pull Secret

The release payload references images from `quay.io/openshift-release-dev` which require authentication:

```bash
oc get secret pull-secret -n openshift-config -o jsonpath='{.data.\.dockerconfigjson}' | base64 -d > /tmp/pull-secret.json
```

## Step 4: Add Quay.io Write Credentials

`oc adm release new` needs to PUSH the release payload to your quay.io repo. The pull secret only has read access. Add your quay.io credentials:

```bash
# Get your quay.io auth from docker credential store
QUAY_AUTH=$(docker-credential-osxkeychain get <<< "quay.io" 2>/dev/null | python3 -c "import json,sys,base64; d=json.load(sys.stdin); print(base64.b64encode(f'{d[\"Username\"]}:{d[\"Secret\"]}'.encode()).decode())")

# Merge into pull secret
python3 -c "
import json
with open('/tmp/pull-secret.json') as f:
    ps = json.load(f)
ps['auths']['quay.io/USER'] = {'auth': '${QUAY_AUTH}'}
with open('/tmp/pull-secret-combined.json', 'w') as f:
    json.dump(ps, f)
"
```

Replace `USER` with your quay.io username.

## Step 5: Build the Release Payload

```bash
oc adm release new \
  --from-release="${CURRENT_RELEASE}" \
  --to-image-base=quay.io/USER/cvo-dev:${TAG} \
  --to-image=quay.io/USER/cvo-dev:release-${TAG} \
  -a /tmp/pull-secret-combined.json
```

This takes 2-5 minutes. It:
1. Pulls all 191 component images from the current release
2. Replaces the CVO component's base image with yours
3. Pushes the assembled release payload to your repo

## Troubleshooting

| Error | Fix |
|-------|-----|
| `unauthorized: access to the requested resource is not authorized` (during push) | Your quay.io creds aren't in the pull secret. See Step 4. |
| `unauthorized` (during pull of component images) | The pull secret doesn't have `quay.io/openshift-release-dev` access. Get it from console.redhat.com/openshift/install/pull-secret. |
| Old binary in pod after deploy | Docker layer caching. Use a unique tag (Step 1), never reuse `:latest`. |
| `unable to read image localhost/...` | `oc adm release new` can't access Docker daemon images directly. Push to a registry first. |
