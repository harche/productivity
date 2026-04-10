# Writing Skills for LightspeedProposal Agents

Skills are structured instructions that give an agent domain expertise.
They're packaged as OCI images and mounted as volumes in the agent sandbox.

Each adapter example includes its own skills — integrators write skills
tailored to their use case.

## Skill Structure

A skill is a directory with a `SKILL.md` and optional reference docs:

```
my-skill/
├── SKILL.md              # core instructions (always loaded)
└── references/           # deep-dive docs (fetched on demand)
    ├── setup.md
    └── advanced.md
```

### SKILL.md Format

```markdown
---
name: my-skill
description: What this skill does and when to use it.
allowed-tools: Bash(oc:*) Bash(kubectl:*)
---

# My Skill

Instructions for the agent on how to use this skill.
Include examples, rules, and reference material.

## References

|references/setup.md — Environment setup, auth, connectivity
|references/advanced.md — Edge cases, complex workflows, troubleshooting
```

The `allowed-tools` field defines which tools the agent can use
when this skill is active.

## Progressive Disclosure Pattern

Skills use the same progressive disclosure pattern as the
[OpenShift documentation index](https://github.com/harche/openshift-docs-md):
**SKILL.md is self-contained for common cases**, with `references/`
for deep dives the agent fetches only when needed.

### Why This Matters

Agent context windows are finite. A skill that dumps 2000 lines of
reference material into every conversation wastes tokens on content
the agent may never need. Instead:

1. **SKILL.md** — always loaded. Contains the 80% case: prerequisites,
   critical rules, common patterns, and a compressed index of references.
2. **references/** — fetched on demand. Contains the 20%: detailed command
   syntax, edge cases, API payloads, troubleshooting trees.

### The Compressed Index Format

Reference the `references/` docs using the pipe-delimited format.
This tells the agent what's available without loading the content:

```markdown
## References

|references/cluster-access.md — Discovery, auth, port-forward setup
|references/querying.md — Instant, range, series, labels, PromQL
|references/validation.md — Check config, rules, metrics, unit testing
|references/tsdb.md — Cardinality analysis, block listing, data dump
```

The format is `|path — description`. The agent reads the index,
decides which reference is relevant, and fetches only that file.

For skills with many references, use the grouped format:

```markdown
## References

|references:{cluster-access.md,querying.md,validation.md,tsdb.md}
```

### When to Split vs. Keep Inline

| Keep in SKILL.md | Move to references/ |
|---|---|
| Prerequisites and setup | Detailed API payloads |
| Critical rules (things that caused real failures) | Full command reference |
| Common patterns (5-10 most used) | Edge cases and workarounds |
| The compressed index of references | Troubleshooting decision trees |
| One-liner examples | Multi-step walkthroughs |

**Rule of thumb:** If a section is >50 lines and only needed for
specific scenarios, it belongs in `references/`.

## Adapter Examples as Templates

Each adapter in `examples/adapters/` ships its own skills tailored
to its domain. Use these as starting points:

| Adapter | Skills | Good example of |
|---|---|---|
| `alertmanager/` | cluster-ops, prometheus, platform-docs, rbac-security | Prometheus querying with critical rules |
| `acs/` | acs-image-scanner, cluster-ops, platform-docs, rbac-security, redhat-support | API-heavy skill (ACS scan + catalog search) |
| `gitops/` | cluster-ops, github, platform-docs, rbac-security | CLI wrapper skill (gh commands) |

### Anatomy of a Well-Structured Skill

The `alertmanager/skills/prometheus/SKILL.md` is a good reference:

1. **Frontmatter** — name, description, allowed-tools
2. **Prerequisites** — what must be installed/configured
3. **Critical Rules** — lessons from real failures (e.g., "never use `!=` in PromQL")
4. **Setup Pattern** — the one-shot setup block agents reuse every time
5. **Common Patterns** — table of PromQL for frequent questions
6. **References** — compressed index pointing to 4 deep-dive docs
7. **Important** — closing guardrails

## Writing Your Own Skills

### Step 1: Pick a Domain

What does your adapter need the agent to know? Examples:
- How to query your monitoring system
- How to interact with your CI/CD pipeline
- How to search your internal knowledge base
- Platform-specific operations (patching, scaling, troubleshooting)

### Step 2: Write SKILL.md

Start with the common case. What does the agent need to do 80% of the time?

```markdown
---
name: my-cicd
description: Trigger and monitor CI/CD pipelines via Tekton.
allowed-tools: Bash(oc:*) Bash(tkn:*)
---

# CI/CD Pipeline Operations

Trigger, monitor, and troubleshoot Tekton pipelines.

## Prerequisites

- `tkn` CLI must be available
- ServiceAccount must have `tekton.dev` API access

## Common Operations

### Trigger a pipeline run
...

### Check pipeline status
...

## References

|references/triggers.md — EventListener setup, TriggerTemplate, TriggerBinding
|references/troubleshooting.md — Failed tasks, timeout handling, workspace issues
```

### Step 3: Write Reference Docs

Each reference doc should be independently useful — an agent that
fetches `references/troubleshooting.md` shouldn't need to also read
`references/setup.md` to understand it.

Good reference doc structure:
```markdown
# Troubleshooting Tekton Pipelines

## Common Failure Modes

### Task timeout
...

### Workspace volume not bound
...
```

### Step 4: Package as OCI Image

Each adapter has a `Containerfile.skills`:

```dockerfile
FROM scratch
COPY skills/ /
```

Build and push:
```bash
podman build -t <registry>/my-adapter-skills:latest -f Containerfile.skills .
podman push <registry>/my-adapter-skills:latest
```

### Step 5: Wire to an Agent

Reference the skills image in your OlsAgent CR:

```yaml
apiVersion: ols.openshift.io/v1alpha1
kind: OlsAgent
metadata:
  name: my-analyzer
spec:
  llm: smart
  skills:
    image: <registry>/my-adapter-skills:latest
  systemPromptRef:
    name: my-analysis-prompt
```

## Reusing Shared Skills

The `lightspeed-skills/` repo contains reusable skills. Copy the ones
you need into your adapter's `skills/` directory:

| Skill | What it does |
|---|---|
| `cluster-ops` | Cluster inspection, patching, scaling, troubleshooting |
| `platform-docs` | OpenShift and Kubernetes documentation lookup |
| `prometheus` | PromQL queries, metric discovery, alerting rules |
| `github` | PR, issue, actions, and repo operations via `gh` CLI |
| `rbac-security` | Minimum-privilege RBAC permission mapping |
| `redhat-support` | Red Hat Knowledge Base, Jira, support cases |
| `operator-catalog` | OLM catalog browsing, subscriptions, CR examples |
| `escalation` | Structured issue filing with diagnostics |

Pick exactly the skills your agents need — don't include everything.

## Skill Profiles

The `lightspeed-skills/` repo ships pre-built Containerfile profiles
that bundle subsets of skills for common workflow patterns. Each profile
produces a smaller, purpose-built image instead of including all skills.

| Profile | Containerfile | Skills included | Use case |
|---|---|---|---|
| `base` | `Containerfile` | All skills | Development, testing, full-featured agents |
| `remediate` | `Containerfile.remediate` | cluster-ops, prometheus, platform-docs | Alert-driven remediation (analyze + fix) |
| `escalate` | `Containerfile.escalate` | escalation, github, redhat-support, platform-docs | Structured issue filing with diagnostics |
| `design` | `Containerfile.design` | operator-catalog, platform-docs, rbac-security | Architecture review, operator selection, RBAC |
| `monitor` | `Containerfile.monitor` | prometheus, platform-docs | Monitoring-only agents (metric queries, alert rules) |

Build a profile with `make docker-build-<profile>` (e.g.,
`make docker-build-remediate`), or build all profiles at once
with `make docker-build-all`. The base image (`make docker-build`)
includes every skill.

### Choosing a Profile

Match the profile to your workflow:

- **Full remediation workflow** — use `remediate` for analysis/execution
  agents, `monitor` for verification agents that only check metrics.
- **Advisory + escalation** — use `escalate` to file issues when
  remediation is not automated.
- **Operator installation planning** — use `design` for agents that
  evaluate OLM catalogs and plan RBAC.
- **Custom adapter** — start with `base` during development, then
  create a custom Containerfile that copies only the skills you need.

See also: api/agent.md (skills field), developing/deploying.md (build + push)
