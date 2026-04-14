# Deploying CVO Lightspeed Integration

This sets up the Lightspeed proposal system so CVO creates upgrade readiness assessments automatically.

## Prerequisites

- Lightspeed operator already installed on the cluster
- LightspeedProposal, OlsAgent, OlsWorkflow CRDs exist:
  ```bash
  oc get crd lightspeedproposals.ols.openshift.io olsagents.ols.openshift.io olsworkflows.ols.openshift.io
  ```

## Step 1: Build and Push Skills Image

The skills image contains SKILL.md files and reference docs for the agent. Built from `lightspeed/Containerfile.skills`:

```bash
docker build -f lightspeed/Containerfile.skills -t localhost/cvo-skills:latest --platform linux/amd64 lightspeed/
docker tag localhost/cvo-skills:latest quay.io/USER/cvo-skills:latest
docker push quay.io/USER/cvo-skills:latest
```

## Step 2: Apply System Prompts

The system prompts are ConfigMaps in `openshift-lightspeed` namespace. Remove the feature-gate annotation for testing on non-TechPreview clusters:

```bash
cat install/0000_00_cluster-version-operator_50_lightspeed-prompts.yaml | \
  sed 's/release.openshift.io\/feature-gate: LightspeedProposals//' | \
  oc apply -f -
```

## Step 3: Apply Agent Definitions

Update the skills image reference to your quay.io repo:

```bash
SKILLS_IMG="quay.io/USER/cvo-skills:latest"

cat install/0000_00_cluster-version-operator_51_lightspeed-agents.yaml | \
  sed 's|release.openshift.io/feature-gate: LightspeedProposals||' | \
  sed "s|quay.io/openshift/lightspeed-cvo-skills:latest|${SKILLS_IMG}|" | \
  oc apply -f -
```

## Step 4: Apply Workflows

```bash
cat install/0000_00_cluster-version-operator_52_lightspeed-workflows.yaml | \
  sed 's|release.openshift.io/feature-gate: LightspeedProposals||' | \
  oc apply -f -
```

## Step 5: Verify Setup

```bash
# Check all resources created
oc get configmaps -n openshift-lightspeed | grep ota
oc get olsagents -n openshift-lightspeed
oc get olsworkflows -n openshift-lightspeed

# Check lightspeed operator sees them
oc get pods -n openshift-lightspeed
```

## Cleanup

```bash
oc delete olsworkflows ota-advisory ota-readiness ota-upgrade -n openshift-lightspeed
oc delete olsagents ota-advisor ota-verifier -n openshift-lightspeed
oc delete configmaps ota-advisory-prompt ota-verification-prompt -n openshift-lightspeed
oc delete lightspeedproposals --all -n openshift-lightspeed
```
