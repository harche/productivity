# Component Deploy Details

## Operator

- **Build file:** `Dockerfile` (Go multi-stage build)
- **Image tag:** `lightspeed-operator:latest`
- **Deployment:** `lightspeed-operator-controller-manager`
- **After type/RBAC changes:** run `make manifests` before building
- **CRD-only update:** `bin/kustomize build config/crd | oc apply -f -`
- **Redeploy script:** `hack/redeploy-operator.sh`
- **Warning:** Never use `bin/kustomize build config/default | oc apply` — corrupts image refs

## Agent

- **Build file:** `Dockerfile` (Ubuntu + Node.js + Claude Agent SDK)
- **Image tag:** `lightspeed-agent:latest`
- **NOT a Deployment** — runs via SandboxTemplate/SandboxClaim
- **Rollout:** delete the SandboxClaim, operator recreates it
- **Redeploy script:** `hack/redeploy-agent.sh`
- **Serves:** HTTPS on port 8080 (`/chat`, `/analyze`, `/execute`, `/health`)

## Console Plugin

- **Build file:** `Dockerfile` (Node.js webpack + nginx)
- **Image tag:** `lightspeed-console-plugin:latest`
- **Deployment:** `lightspeed-console-plugin` (managed by operator)
- **Placeholder image:** operator may set `__REPLACE_LIGHTSPEED_CONSOLE_PLUGIN__` — patch manually
- **Redeploy script:** `hack/redeploy-console.sh`
- **i18n warnings:** translation key warnings are harmless

## Skills

- **Build file:** `Containerfile` (multiple profiles)
- **Image tag:** `lightspeed-skills:latest`
- **NOT a Deployment** — mounted as OCI image volume in the agent pod
- **Rollout:** `redeploy-skills.sh` pushes the image and restarts the agent
- **Redeploy script:** `hack/redeploy-skills.sh`

## Troubleshooting

- **Image push auth error:** Token expired. `oc create token builder -n openshift-lightspeed --duration=10m`
- **ImagePullBackOff:** Image not pushed to correct registry path. Check `oc get istag -n openshift-lightspeed`
- **Operator CrashLoop after CRD changes:** Run `make manifests`, reapply CRDs, then redeploy
- **Console placeholder image:** Patch deployment image manually (see above)
- **Agent not picking up new image:** Delete SandboxClaim, let operator recreate
