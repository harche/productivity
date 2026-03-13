# Productivity Assistant

Claude Code plugin marketplace — Jira, GitHub, Slack, Kubernetes/OpenShift docs, Red Hat support cases, Red Hat Knowledge Base, OpenShift cluster management, and more.

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

A shell function that wraps `claude plugin install/uninstall` with short names, dependency resolution, deduplication, and tab completion.

**Add to your `~/.zshrc`:**

```bash
# ── Productivity Plugin Installer ────────────────────────────────────
cpi() {
  _cpi_resolve() {
    case "$1" in
      github)            echo "github@productivity-tools" ;;
      slack)             echo "playwright-cli@productivity-tools slack@productivity-tools" ;;
      google)            echo "google@productivity-tools" ;;
      redhat-detective)  echo "redhat-detective@productivity-tools" ;;
      context-keeper)    echo "playwright-cli@productivity-tools slack@productivity-tools google@productivity-tools redhat-detective@productivity-tools github@productivity-tools context-keeper@productivity-tools" ;;
      cluster-installer) echo "cluster-installer@productivity-tools" ;;
      playwright-cli)    echo "playwright-cli@productivity-tools" ;;
      ibkr)              echo "playwright-cli@productivity-tools ibkr@productivity-tools" ;;
      twitter)           echo "playwright-cli@productivity-tools twitter@productivity-tools" ;;
      youtube)           echo "youtube@productivity-tools" ;;
      polymarket)        echo "polymarket@productivity-tools" ;;
      dev-digest)        echo "redhat-detective@productivity-tools github@productivity-tools dev-digest@productivity-tools" ;;
      market-news)       echo "polymarket@productivity-tools playwright-cli@productivity-tools twitter@productivity-tools market-news@productivity-tools" ;;
      *) echo ""; return 1 ;;
    esac
  }

  _cpi_collect() {
    local names=("$@") seen=() result=()
    for name in "${names[@]}"; do
      if [[ "$name" == "all" ]]; then
        _cpi_collect github slack google redhat-detective context-keeper cluster-installer playwright-cli \
                     ibkr twitter youtube polymarket dev-digest market-news
        return
      fi
      local plugins=$(_cpi_resolve "$name") || { echo "Unknown plugin: $name"; continue; }
      for p in $plugins; do
        if [[ ! " ${seen[*]} " =~ " $p " ]]; then
          seen+=("$p")
          result+=("$p")
        fi
      done
    done
    echo "${result[@]}"
  }

  case "$1" in
    install|i)
      shift
      local to_add=($(_cpi_collect "$@"))
      for p in "${to_add[@]}"; do claude plugin install --scope local "$p" || return 1; done
      ;;
    uninstall|remove)
      shift
      local to_rm=($(_cpi_collect "$@"))
      local reversed=()
      for p in "${to_rm[@]}"; do reversed=("$p" "${reversed[@]}"); done
      for p in "${reversed[@]}"; do claude plugin uninstall --scope local "$p"; done
      ;;
    list)
      local all_plugins=(github slack google redhat-detective context-keeper cluster-installer playwright-cli
                         ibkr twitter youtube polymarket dev-digest market-news)
      local installed=$(claude plugin list --json 2>/dev/null | jq -r --arg pwd "$PWD" \
        '.[] | select(.projectPath == $pwd and (.id | endswith("@productivity-tools"))) | "\(.id | split("@")[0])\t\(if .enabled then "✔" else "✘" end)\t\(.version)"')
      for p in "${all_plugins[@]}"; do
        local match=$(echo "$installed" | grep "^${p}	")
        if [[ -n "$match" ]]; then
          local st=$(echo "$match" | cut -f2)
          local ver=$(echo "$match" | cut -f3)
          printf "  %-20s %s  %s\n" "$p" "$st" "$ver"
        else
          printf "  %s\n" "$p"
        fi
      done
      ;;
    *)
      echo "Usage: cpi <install|uninstall|list> <plugin> [plugin...]"
      echo ""
      echo "Plugins:"
      echo "  github  slack  google  redhat-detective  context-keeper"
      echo "  cluster-installer  playwright-cli"
      echo "  ibkr  twitter  youtube  polymarket"
      echo "  dev-digest  market-news"
      echo "  all"
      ;;
  esac
}

_cpi() {
  local plugins=(github slack google redhat-detective context-keeper cluster-installer playwright-cli
                 ibkr twitter youtube polymarket dev-digest market-news all)
  if (( CURRENT == 2 )); then
    compadd install uninstall list
  else
    compadd "${plugins[@]}"
  fi
}
compdef _cpi cpi
```

Then reload: `source ~/.zshrc`

**Usage:**

```bash
cpi list                                # show all plugins, mark installed ones
cpi install github                      # install one plugin
cpi install redhat-detective github     # install multiple (deps resolved automatically)
cpi install all                         # install everything
cpi uninstall slack                     # remove a plugin and its deps
cpi uninstall all                       # remove everything
cpi                                 # show help
```

Tab completion works at every position — type `cpi install red<TAB>` to complete `redhat-detective`.

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
```bash
cpi install redhat-detective github
```

**Get a daily developer briefing — what needs your attention across Jira and GitHub:**
```bash
cpi install dev-digest
```

**Spin up a cluster and start working:**
```bash
cpi install cluster-installer redhat-detective github
```
