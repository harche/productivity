# Verifying CVO Deployment

## Check CVO Pod

```bash
oc get pods -n openshift-cluster-version -l k8s-app=cluster-version-operator
```

Expect: 1/1 Running, no restarts.

## Verify Correct Binary

```bash
# Compare sizes — must match
oc exec -n openshift-cluster-version deployment/cluster-version-operator -- ls -la /usr/bin/cluster-version-operator
ls -la _output/linux/amd64/cluster-version-operator
```

## Check CVO Logs

```bash
# Look for successful startup and feature flags
oc logs -n openshift-cluster-version -l k8s-app=cluster-version-operator --tail=100 | grep -E "CVO features|Payload loaded|Created LightspeedProposal|already exists"
```

Key log lines to look for:
- `CVO features for version X.Y.Z enabled at startup` — confirms feature gate state
- `Payload loaded` — confirms release payload loaded successfully
- `Created LightspeedProposal` — confirms proposal was created
- `already exists, skipping` — confirms dedup is working (on subsequent cycles)

## Check Proposals

```bash
# List all proposals
oc get lightspeedproposals -n openshift-lightspeed

# View full agent output for a proposal
oc get lightspeedproposal NAME -n openshift-lightspeed -o jsonpath='{.status}' | python3 -m json.tool

# View just the request that was sent to the agent
oc get lightspeedproposal NAME -n openshift-lightspeed -o jsonpath='{.spec.request}'
```

## Check Readiness Data

The readiness JSON is embedded in the proposal's `spec.request`. To extract just the JSON:

```bash
oc get lightspeedproposal NAME -n openshift-lightspeed -o jsonpath='{.spec.request}' | \
  sed -n '/```json/,/```/p' | sed '1d;$d' | python3 -m json.tool
```

## Expected Proposal Lifecycle

```
Phase: ""        → Pending (just created)
Phase: Analyzing → Agent is running readiness assessment
Phase: Proposed  → Agent completed, recommendation available in status
Phase: Escalated → Agent couldn't determine, needs human review
Phase: Failed    → Agent encountered an error
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| No proposals created | Feature gate not bypassed, or no available updates | Check `shouldCreateLightspeedProposals()` returns true. Check `oc get clusterversion version -o jsonpath='{.status.availableUpdates}'` |
| Proposal stuck in Analyzing | Agent sandbox issue, RBAC, or skills image pull failure | Check lightspeed operator logs: `oc logs -n openshift-lightspeed deployment/lightspeed-operator-controller-manager --tail=100` |
| Proposal in Escalated | Agent couldn't complete analysis, possibly missing tools or API access | Check agent pod logs in `openshift-lightspeed` namespace |
| Duplicate proposals | Old binary running (dedup fix not deployed) | Verify binary sizes match (see above) |
| `DNS-1035 label invalid` | Dots in proposal name | Ensure `sanitize()` replaces dots with hyphens |
| `CRD not found` in logs | LightspeedProposal CRD not installed | Install lightspeed operator first |
| Binary size mismatch | Docker layer caching | Use `--no-cache` and unique tags |
