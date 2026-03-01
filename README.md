# Productivity Assistant

AI-powered productivity hub with Claude Code skills for software engineering workflows — Jira, GitHub, Slack, OpenShift/Kubernetes docs, support cases, and more.

## Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/harche/productivity.git
cd productivity
```

### 2. Set up a workspace

Clone a project into `workspace/` and install skills:

```bash
cd workspace
git clone https://github.com/openshift/kubernetes.git && cd kubernetes

# Install skills — the repo already has .git, so you're good to go
../../copy-skills.sh jira github openshift-docs
```

Now open Claude Code in that directory and start asking questions.

**No git repo?** If you're working in a plain folder (not a git repo), run `git init` first. This creates a `.git` boundary so Claude Code only discovers skills installed in that folder — not from parent directories.

```bash
mkdir -p workspace/scratch && cd workspace/scratch
git init

../../copy-skills.sh support-cases knowledge-base jira
```

### 3. Install skills

```bash
# Interactive menu
./copy-skills.sh

# Install by name
./copy-skills.sh jira github slack

# Install by category
./copy-skills.sh -c redhat          # jira, support-cases, knowledge-base, openshift-docs
./copy-skills.sh -c tools           # github, gmail, slack, playwright-cli, kubernetes-docs

# Install all
./copy-skills.sh all

# Install into a specific directory
./copy-skills.sh -d ~/work/my-repo jira github

# List available skills
./copy-skills.sh --list
```

## Available Skills

### Red Hat (`-c redhat`)

| Skill | Description |
|-------|-------------|
| `jira` | View, search, create, and update Jira issues |
| `support-cases` | View, search, and manage Red Hat support cases |
| `knowledge-base` | Search Red Hat Knowledge Base articles and solutions |
| `openshift-docs` | Search and read OpenShift Container Platform documentation |

### Tools (`-c tools`)

| Skill | Description |
|-------|-------------|
| `github` | GitHub repos, PRs, issues, and actions via `gh` CLI |
| `gmail` | Gmail, Google Calendar, Drive, and Docs via `gog` CLI |
| `slack` | Read, search, and send Slack messages via browser session |
| `playwright-cli` | Browser automation: navigate, interact, screenshot, scrape |
| `kubernetes-docs` | Search and read upstream Kubernetes documentation |

## How It Works

Skills live in `skills/<category>/<skill>/` as the source of truth. `copy-skills.sh` copies them into a project's `.claude/skills/` directory, where Claude Code auto-discovers them.

The key concept: **Claude Code stops discovering skills at `.git` boundaries.** So each workspace project only sees its own installed skills — not the parent repo's. This is why you `git init` even in scratch folders.

```
productivity/                   # This repo
├── skills/                     # Skill registry (source of truth)
│   ├── redhat/
│   │   ├── jira/
│   │   ├── support-cases/
│   │   ├── knowledge-base/
│   │   └── openshift-docs/
│   └── tools/
│       ├── github/
│       ├── gmail/
│       ├── slack/
│       ├── playwright-cli/
│       └── kubernetes-docs/
├── copy-skills.sh              # Installs skills into any project
└── workspace/                  # Your projects (gitignored)
    └── my-project/
        └── .claude/skills/     # Installed skills (auto-discovered)
            ├── jira/
            └── github/
```

## Authentication

Skills that call APIs (Jira, GitHub, support cases, etc.) need tokens. Tokens are stored in macOS Keychain and loaded as environment variables via `~/.zshrc`. Check each skill's `SKILL.md` for which env vars it expects.

```bash
# Store a token
security add-generic-password -a "$USER" -s "TOKEN_NAME" -w "your-token" -U
```

## Example Workflows

**Investigate a support case and check related Jira bugs:**
```bash
mkdir -p workspace/case-12345 && cd workspace/case-12345
git init
../../copy-skills.sh support-cases jira knowledge-base
# Open Claude Code and ask about the case
```

**Work on an OpenShift project with docs at hand:**
```bash
cd workspace/my-ocp-project
../../copy-skills.sh openshift-docs github jira
```

**Quick Kubernetes docs lookup:**
```bash
mkdir -p workspace/k8s && cd workspace/k8s
git init
../../copy-skills.sh kubernetes-docs
```
