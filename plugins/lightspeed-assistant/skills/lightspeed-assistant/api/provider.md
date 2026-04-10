# OlsLlmProvider

Cluster-scoped. Defines an LLM backend configuration.

**Source:** `lightspeed-operator/api/v1alpha1/llmprovider_types.go`

## Spec Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | yes | Provider type. Enum: `anthropic_vertex`, `azure_openai`, `openai`, `watsonx`, `rhoai_vllm`, `rhelai_vllm` |
| `model` | string | yes | Model name (e.g., `claude-opus-4-6`, `claude-haiku-4-5-20251001`) |
| `credentialsSecretRef` | LocalObjectReference | yes | Secret with provider credentials |
| `url` | string | no | API URL. Optional for providers with well-known endpoints. Must match `^https?://.*$` |

## Credentials Secret

The referenced Secret format depends on the provider type. For
`anthropic_vertex`, it contains the GCP service account JSON.

## Example

```yaml
apiVersion: ols.openshift.io/v1alpha1
kind: OlsLlmProvider
metadata:
  name: smart
spec:
  type: anthropic_vertex
  model: claude-opus-4-6
  credentialsSecretRef:
    name: llm-credentials
```

## kubectl Columns

```
NAME    TYPE               MODEL             AGE
smart   anthropic_vertex   claude-opus-4-6   1d
```

See also: api/agent.md (references provider by name)
