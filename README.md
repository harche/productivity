# Productivity Assistant

Claude Code plugin marketplace — Jira, GitHub, Slack, Kubernetes/OpenShift docs, Red Hat support cases, Red Hat Knowledge Base, OpenShift cluster management, and more.

## Quick Start

```bash
# Add the marketplace (one-time)
claude plugin marketplace add harche/productivity

# Install the plugin installer, then use it to set up everything else
claude plugin install --scope local plugin-installer@productivity-tools
```

Once `plugin-installer` is installed, restart Claude Code and ask it to install what you need:

```
/plugin-installer install redhat-detective and github
```

It will resolve dependencies, check for missing CLI tools, offer to install them, warn about missing API tokens, and run the install commands for you.

> **Tip:** Once you're done installing plugins, you can remove `plugin-installer` to keep things tidy — you can always add it back later:
> ```bash
> claude plugin uninstall plugin-installer@productivity-tools --scope local
> ```

### Manual Install

You can also install plugins directly without the installer:

```bash
claude plugin install --scope local redhat-detective@productivity-tools
claude plugin install --scope local github@productivity-tools

# Browse all available plugins
claude plugin
```

## Available Plugins

See the **[Plugin Catalog](docs/plugin-catalog.md)** for the full list of plugins, dependencies, prerequisites, and install commands.

## Authentication & Secrets

Some plugins require API tokens stored in the OS secret store. See the [Plugin Catalog — Prerequisites](docs/plugin-catalog.md#prerequisites) for which tokens are needed and how to obtain them.

### Storing Tokens

**macOS (Keychain):**

```bash
# Jira PAT
security add-generic-password -a "$USER" -s "JIRA_API_TOKEN" -w "your-jira-token" -U

# Red Hat API offline token
security add-generic-password -a "$USER" -s "RH_API_OFFLINE_TOKEN" -w "your-offline-token" -U

# OpenShift pull secret (compact JSON)
security add-generic-password -a "$USER" -s "OCP_PULL_SECRET" \
  -w "$(cat pull-secret.json | python3 -c 'import sys,json; print(json.dumps(json.load(sys.stdin), separators=(",",":")))')" -U
```

**Linux (secret-tool / libsecret):**

```bash
# Jira PAT (enter token at the "Password:" prompt)
secret-tool store --label="JIRA_API_TOKEN" service jira key JIRA_API_TOKEN

# Red Hat API offline token
secret-tool store --label="RH_API_OFFLINE_TOKEN" service redhat key RH_API_OFFLINE_TOKEN

# OpenShift pull secret
cat pull-secret.json | python3 -c 'import sys,json; print(json.dumps(json.load(sys.stdin), separators=(",",":")))' | \
  secret-tool store --label="OCP Pull Secret" service ocp-install username "$USER" key OCP_PULL_SECRET
```

| Platform | Secret store | Install |
|----------|-------------|---------|
| macOS | Keychain (built-in) | — |
| Linux | libsecret / GNOME Keyring | `sudo dnf install libsecret` (Fedora) or `sudo apt install libsecret-tools` (Ubuntu/Debian) |

## Example Workflows

**Investigate a support case — Jira, KB, docs, and metrics in one plugin:**
```
/plugin-installer install redhat-detective and github
```

**Get a daily developer briefing — what needs your attention across Jira and GitHub:**
```
/plugin-installer install dev-digest, redhat-detective, and github
```

**Spin up a cluster and start working:**
```
/plugin-installer install cluster-installer, redhat-detective, and github
```
