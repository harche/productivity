---
name: plugin-installer
description: Install and manage plugins from the productivity-tools marketplace. Use when the user asks to install, set up, or add plugins, asks what plugins are available, or wants to check prerequisites for a plugin.
allowed-tools: Bash(claude:*) Bash(which:*) Bash(uname:*) Bash(security:*) Bash(secret-tool:*) Bash(brew:*) Bash(dnf:*) Bash(apt:*) Bash(npm:*) Read AskUserQuestion
---

# Plugin Installer

You help users discover, install, and set up plugins from the productivity-tools marketplace.

## Data Source

The plugin catalog is at `${CLAUDE_PLUGIN_ROOT}/plugin-catalog.md`. **Always read this file first** before doing anything. It contains:

- Available plugins (tables under **## Plugins** and **## Agent Plugins**)
- Plugin dependencies (the **Dependencies** column)
- CLI tool prerequisites (the **## Prerequisites > ### CLI Tools** table)
- API token prerequisites (the **## Prerequisites > ### API Tokens** table)
- Auth methods for plugins that don't need manual tokens

Parse the markdown tables to extract the information you need.

## Listing plugins

When the user asks what's available:

1. Read the catalog.
2. Check what's already installed:
   ```bash
   claude plugin list 2>/dev/null
   ```
3. Show all plugins grouped by category with descriptions. Mark already-installed plugins.

## Installing plugins

When the user asks to install one or more plugins:

1. **Read the catalog.**
2. **Check what's already installed:**
   ```bash
   claude plugin list 2>/dev/null
   ```
3. **Resolve dependencies.** Look up the plugin in the catalog tables. If the Dependencies column lists other plugins, add them to the install list. Skip any that are already installed.
   - For plugins with optional dependencies (e.g. `context-keeper`), use `AskUserQuestion` with `multiSelect: true` to let the user pick which ones to install. Each option should have the dependency plugin name as the label and a brief description. Only include the selected plugins in the install list.
4. **Check CLI prerequisites.** For every plugin in the install list, look up the CLI Tools table. For each required tool:
   ```bash
   which <tool> 2>/dev/null
   ```
   If missing, detect the platform:
   ```bash
   uname -s  # Darwin = macOS, Linux = Linux
   ```
   Look up the install command from the catalog's CLI Tools table. Ask the user if they'd like to install it. If yes, run the command.
5. **Check API token prerequisites.** For every plugin in the install list, look up the API Tokens table. For each required token:
   - macOS: `security find-generic-password -s "<TOKEN_NAME>" -w 2>/dev/null`
   - Linux: `secret-tool lookup key "<TOKEN_NAME>" 2>/dev/null`
   If missing, warn the user and show the "How to obtain" link from the catalog. **Don't block installation** — tokens aren't needed until runtime.
6. **Show the install plan.** List everything that will be installed in order (dependencies first, then the requested plugin). Include any warnings about missing tokens.
7. **Ask for confirmation.**
8. **Install in dependency order:**
   ```bash
   claude plugin install --scope local <name>@productivity-tools
   ```
9. **Report results.** Summarize what was installed and any remaining setup steps (e.g., missing tokens, `gh auth login`).

## Recommending plugins

When the user describes what they want to do (e.g., "set me up for OpenShift debugging", "I want to track Jira and GitHub"), recommend the relevant set of plugins and offer to install them all.

## Guidelines

- Always read the catalog file first — never hardcode plugin names or dependencies.
- Install dependencies before the plugins that need them.
- Default to `--scope local` unless the user asks for a different scope.
- If `claude plugin list` is not available or fails, proceed without checking existing installations.
- Be concise — show the plan, get confirmation, execute.
- Never install anything without asking first.
- When a CLI tool install command says "See repo README", tell the user they need to install it manually and provide the link.
