# Writing System Prompts

System prompts shape agent behavior for each workflow step. They're
stored as ConfigMaps and referenced by OlsAgent CRs.

## ConfigMap Format

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: my-analysis-prompt
  namespace: openshift-lightspeed
data:
  prompt: |
    Your prompt text here...
```

Key must be `prompt`. Referenced via `agent.spec.systemPromptRef.name`.

> **Note:** `systemPromptRef` is optional. If omitted, the operator uses
> the agent's skills and the default query context without a custom system
> prompt. This is useful for agents that rely entirely on skill instructions.

## What the Agent Receives

When the operator calls an agent, it sends:
- **System prompt** — from the ConfigMap (sets role and constraints)
- **Query** — the proposal request + context
- **Context** — target namespaces, attempt number, previous failure history
- **Output schema** — JSON schema for structured response (per phase)

## Prompt per Step

### Analysis Prompt
Guide the agent to: diagnose root cause, assess confidence, propose
remediation actions, specify RBAC needs, plan verification steps.

```
You are an SRE agent. Analyze the reported issue using read-only tools.

Your tools: oc (read-only), promtool, curl
Your output must include: diagnosis, proposal, rbac, verification plan

Rules:
- Never execute write operations during analysis
- Always specify minimum-privilege RBAC rules with justifications
- Assess risk level (low/medium/high/critical) for proposed actions
```

### Execution Prompt
Guide the agent to: execute the approved plan exactly, verify each
action inline, report what was done.

```
You are an execution agent. Execute the approved remediation plan.

Your tools: oc (read-write), promtool, curl
Execute only the approved actions. Verify each action succeeded.
Report actions taken with success/failure status.
```

### Verification Prompt
Guide the agent to: independently verify the fix, check metrics,
confirm the original issue is resolved.

```
You are a verification agent. Independently verify the remediation.

Your tools: oc (read-only), promtool
Check that the original issue is resolved.
Do not rely on the execution agent's self-report.
```

## Tips

- Be explicit about allowed tools and read/write permissions
- Analysis prompts should request structured output matching the CRD types
- Keep prompts focused — one role per prompt
- Include context about what previous attempts found (the operator handles
  this automatically via `previousAttempts` in the query context)

## Custom Output Schemas

The `outputSchema` field on OlsAgent lets adapters extend the agent's
structured output with custom component types. The operator merges the
custom schema with its base schema (options, diagnosis, proposal, etc.)
before sending to the agent. If not set, the operator uses the default
schema.

### When to Use outputSchema

Use it when your adapter needs the agent to return structured data
beyond the standard diagnosis/proposal/RBAC/verification fields.
Examples:

- **MCO diagnostics** — return pool status and bad config details as
  typed components that consumers can parse
- **ACS scanning** — return vulnerability scan results alongside the
  remediation proposal
- **Custom dashboards** — return data in a shape your UI expects

### Example: MCO Advisory Agent

The `mco-advisory` adapter (see `examples/adapters/mco-advisory/workflow.yaml`)
defines an `outputSchema` that requires the agent to return `mco_pool_status`
and `mco_bad_config` components:

```yaml
apiVersion: ols.openshift.io/v1alpha1
kind: OlsAgent
metadata:
  name: mco-analyzer
spec:
  llm: smart
  skills:
    image: image-registry.openshift-image-registry.svc:5000/openshift-lightspeed/lightspeed-alertmanager-skills:latest
  systemPromptRef:
    name: mco-analysis-prompt
  outputSchema:
    description: >-
      Include structured component data about the MCP status and the
      problematic MachineConfig.
    type: array
    minItems: 1
    items:
      oneOf:
      - type: object
        properties:
          type:
            type: string
            const: mco_pool_status
          pool:
            type: string
          degraded:
            type: boolean
          message:
            type: string
        required: ["type", "pool", "degraded", "message"]
      - type: object
        properties:
          type:
            type: string
            const: mco_bad_config
          machineConfigName:
            type: string
          issue:
            type: string
          content:
            type: string
        required: ["type", "machineConfigName", "issue", "content"]
```

The agent returns these components in the `components` array of each
remediation option. The operator stores them as-is on the proposal
status. Consumers (the console, downstream systems) interpret them
based on the `type` field.

For built-in component types rendered by the console (`lightspeed_*`),
see `examples/adapters/custom-components/README.md`.

See also: api/agent.md (systemPromptRef, outputSchema), guides/quickstart.md
