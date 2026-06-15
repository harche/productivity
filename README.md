# Productivity Assistant

Claude Code plugin marketplace — Jira, GitHub, Kubernetes/OpenShift docs, Red Hat support cases, Red Hat Knowledge Base, OpenShift cluster management, and more.

## Quick Start

```bash
# Add the marketplace (one-time)
claude plugin marketplace add harche/productivity
```

Then install plugins with:

```bash
claude plugin install --scope local <name>@productivity-tools
```

Or use the **`cpi` helper** for faster installs with automatic dependency resolution — see [Shell Helper](#shell-helper-cpi) below.

## Shell Helper (`cpi`)

A Python CLI that manages plugins across multiple Claude Code marketplaces. It reads each marketplace's `marketplace.json` to auto-discover plugins and resolve dependencies — no hardcoded plugin lists.

**Install:**

```bash
# From your clone of this repo:
ln -sf "$(pwd)/scripts/cpi" ~/.local/bin/cpi
```

**Register marketplaces:**

```bash
# From your clone of this repo:
cpi add .
```

**Tab completion (add to `~/.zshrc`):**

```bash
eval "$(cpi completions zsh)"
```

**Usage:**

```bash
cpi list                                # all plugins across all marketplaces
cpi install workspace                   # install one plugin
cpi install trading node-support        # install multiple (deps auto-resolved)
cpi install all                         # install everything
cpi uninstall google                    # remove a plugin and its deps
cpi search node                         # search by name or description
```

**How it works:**

- `~/.config/cpi/` holds symlinks to marketplace repos — one per marketplace
- `cpi add <path>` reads `.claude-plugin/marketplace.json`, creates the symlink
- All commands auto-discover plugins and resolve `dependencies` across marketplaces
- Cross-marketplace deps work seamlessly (e.g., a plugin in marketplace B can depend on one in marketplace A)
- Tab completion is dynamic — it queries the registered marketplaces at completion time

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

# FRED API key (free from https://fred.stlouisfed.org/docs/api/api_key.html)
security add-generic-password -s "fred-api-key" -a "fred" -w "your-fred-api-key" -U

# Semantic Scholar API key (optional, free from https://www.semanticscholar.org/product/api)
security add-generic-password -s "semantic-scholar-api-key" -a "$USER" -w "your-s2-api-key" -U

# OpenAlex API key (free from https://openalex.org/settings/api)
security add-generic-password -s "openalex-api-key" -a "$USER" -w "your-openalex-api-key" -U
```

**Linux (secret-tool / libsecret):**

```bash
# Jira PAT (enter token at the "Password:" prompt)
secret-tool store --label="JIRA_API_TOKEN" service jira key JIRA_API_TOKEN

# Red Hat API offline token
secret-tool store --label="RH_API_OFFLINE_TOKEN" service redhat key RH_API_OFFLINE_TOKEN
```

| Platform | Secret store | Install |
|----------|-------------|---------|
| macOS | Keychain (built-in) | — |
| Linux | libsecret / GNOME Keyring | `sudo dnf install libsecret` (Fedora) or `sudo apt install libsecret-tools` (Ubuntu/Debian) |

## Example Workflows

**Investigate a support case — Jira, KB, docs, and metrics in one plugin:**
```bash
cpi install node-support
```
