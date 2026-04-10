# Cluster Reference

## Internal Registry

- **Internal service URL:** `image-registry.openshift-image-registry.svc:5000`
- **Get external route:**
  ```bash
  oc get route default-route -n openshift-image-registry -o jsonpath='{.spec.host}'
  ```

## Push Authentication

Get a short-lived token for pushing images:

```bash
TOKEN=$(oc create token builder -n openshift-lightspeed --duration=10m)
```

## Push Command (skopeo)

```bash
REGISTRY=$(oc get route default-route -n openshift-image-registry -o jsonpath='{.spec.host}')
TOKEN=$(oc create token builder -n openshift-lightspeed --duration=10m)

skopeo copy --dest-tls-verify=false --dest-creds="unused:${TOKEN}" \
  "docker-daemon:<local-image-tag>" \
  "docker://${REGISTRY}/openshift-lightspeed/<image-name>:latest"
```

## Usage with Deploy Scripts

All deploy and redeploy scripts require the `KUBECONFIG` environment variable:

```bash
KUBECONFIG=/path/to/kubeconfig bash hack/redeploy-operator.sh
```

Available scripts: `deploy-operator.sh`, `redeploy-operator.sh`,
`redeploy-agent.sh`, `redeploy-console.sh`, `redeploy-skills.sh`,
`redeploy-all.sh`. All accept `--skip-build` to reuse existing local images.
