# Productivity Assistant

AI-powered productivity hub with Claude Code plugins for software engineering workflows — Jira, GitHub, Slack, OpenShift/Kubernetes docs, support cases, and more.

## Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/harche/productivity.git
cd productivity
```

### 2. Install plugins in any project

In the target repo, use Claude Code's native plugin system:

```bash
# Add the marketplace (one-time)
/plugin marketplace add harche/productivity

# Install individual plugins
/plugin install jira@productivity-tools
/plugin install github@productivity-tools

# Browse all available plugins
/plugin
```

### 3. Use a workspace project

Clone a project into `workspace/` and install plugins:

```bash
cd workspace
git clone https://github.com/openshift/kubernetes.git && cd kubernetes
```

Then in Claude Code:
```
/plugin marketplace add harche/productivity
/plugin install jira@productivity-tools github@productivity-tools openshift-docs@productivity-tools
```

**No git repo?** If you're working in a plain folder (not a git repo), run `git init` first. This creates a `.git` boundary so Claude Code only discovers skills installed in that folder — not from parent directories.

## Available Plugins

### Red Hat (category: `redhat`)

| Plugin | Description |
|--------|-------------|
| `jira` | View, search, create, and update Jira issues |
| `support-cases` | View, search, and manage Red Hat support cases |
| `knowledge-base` | Search Red Hat Knowledge Base articles and solutions |
| `openshift-docs` | Search and read OpenShift Container Platform documentation |
| `ocp-cluster` | Create, destroy, debug, and manage OpenShift clusters on GCP |

### Tools (category: `tools`)

| Plugin | Description |
|--------|-------------|
| `github` | GitHub repos, PRs, issues, and actions via `gh` CLI |
| `gmail` | Gmail, Google Calendar, Drive, and Docs via `gog` CLI |
| `slack` | Read, search, and send Slack messages via browser session |
| `playwright-cli` | Browser automation: navigate, interact, screenshot, scrape |
| `kubernetes-docs` | Search and read upstream Kubernetes documentation |

## Bulk Install by Category

To auto-install a group of plugins in a repo, add this to `.claude/settings.json`:

**All Red Hat plugins:**
```json
{
  "extraKnownMarketplaces": {
    "productivity-tools": {
      "source": { "source": "github", "repo": "harche/productivity" }
    }
  },
  "enabledPlugins": {
    "jira@productivity-tools": true,
    "support-cases@productivity-tools": true,
    "knowledge-base@productivity-tools": true,
    "openshift-docs@productivity-tools": true,
    "ocp-cluster@productivity-tools": true
  }
}
```

**All Tools plugins:**
```json
{
  "extraKnownMarketplaces": {
    "productivity-tools": {
      "source": { "source": "github", "repo": "harche/productivity" }
    }
  },
  "enabledPlugins": {
    "github@productivity-tools": true,
    "gmail@productivity-tools": true,
    "slack@productivity-tools": true,
    "playwright-cli@productivity-tools": true,
    "kubernetes-docs@productivity-tools": true
  }
}
```

**All plugins:**
```json
{
  "extraKnownMarketplaces": {
    "productivity-tools": {
      "source": { "source": "github", "repo": "harche/productivity" }
    }
  },
  "enabledPlugins": {
    "jira@productivity-tools": true,
    "support-cases@productivity-tools": true,
    "knowledge-base@productivity-tools": true,
    "openshift-docs@productivity-tools": true,
    "ocp-cluster@productivity-tools": true,
    "github@productivity-tools": true,
    "gmail@productivity-tools": true,
    "slack@productivity-tools": true,
    "playwright-cli@productivity-tools": true,
    "kubernetes-docs@productivity-tools": true
  }
}
```

Plugins are auto-installed when the repo folder is trusted in Claude Code.

## How It Works

Plugins live in `plugins/<name>/` as the source of truth, cataloged by `.claude-plugin/marketplace.json`. Users add this repo as a marketplace and install individual plugins via `/plugin install`.

The key concept: **Claude Code stops discovering skills at `.git` boundaries.** So each workspace project only sees its own installed plugins — not the parent repo's.

```
productivity/                       # This repo
├── .claude-plugin/
│   └── marketplace.json            # Marketplace catalog (10 plugins)
├── plugins/                        # Plugin registry (source of truth)
│   ├── jira/
│   │   ├── .claude-plugin/plugin.json
│   │   └── skills/jira/SKILL.md
│   ├── github/
│   ├── gmail/
│   ├── slack/
│   ├── playwright-cli/
│   ├── kubernetes-docs/
│   ├── support-cases/
│   ├── knowledge-base/
│   ├── openshift-docs/
│   └── ocp-cluster/
└── workspace/                      # Your projects (gitignored)
    └── my-project/                 # Plugins installed via /plugin install
```

## Example Workflows

**Investigate a support case and check related Jira bugs:**
```
/plugin marketplace add harche/productivity
/plugin install support-cases@productivity-tools
/plugin install jira@productivity-tools
/plugin install knowledge-base@productivity-tools
```

**Work on an OpenShift project with docs at hand:**
```
/plugin install openshift-docs@productivity-tools
/plugin install github@productivity-tools
/plugin install jira@productivity-tools
```

**Quick Kubernetes docs lookup:**
```
/plugin install kubernetes-docs@productivity-tools
```
