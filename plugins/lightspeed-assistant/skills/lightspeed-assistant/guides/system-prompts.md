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

See also: api/agent.md (systemPromptRef), guides/quickstart.md
