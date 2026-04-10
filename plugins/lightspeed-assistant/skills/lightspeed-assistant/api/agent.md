# OlsAgent

Cluster-scoped. Bundles an LLM provider, skills OCI image, and system prompt
into a reusable agent configuration.

**Source:** `lightspeed-operator/api/v1alpha1/agent_types.go`

## Spec Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `llm` | string | yes | Name of an OlsLlmProvider CR |
| `skills.image` | string | yes | OCI image reference containing skills (mounted in sandbox) |
| `systemPromptRef` | LocalObjectReference | no | ConfigMap with key `prompt` containing the system prompt text |

## System Prompt ConfigMap

The referenced ConfigMap must have a key named `prompt`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: analysis-prompt
  namespace: openshift-lightspeed
data:
  prompt: |
    You are an SRE agent. Analyze the cluster issue...
```

## Example

```yaml
apiVersion: ols.openshift.io/v1alpha1
kind: OlsAgent
metadata:
  name: analyzer
spec:
  llm: smart
  skills:
    image: image-registry.openshift-image-registry.svc:5000/openshift-lightspeed/my-adapter-skills:latest
  systemPromptRef:
    name: analysis-prompt
```

## kubectl Columns

```
NAME       LLM     AGE
analyzer   smart   1d
```

See also: api/provider.md (the LLM reference), api/workflow.md (references agents per step), guides/system-prompts.md
