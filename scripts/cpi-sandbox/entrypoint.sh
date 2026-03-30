#!/usr/bin/env bash
# Container entrypoint: firewall, plugin sync, then claude.
set -euo pipefail

# ── 1. Firewall ─────────────────────────────────────────────────────
echo "[entrypoint] Setting up firewall..."
sudo /usr/local/bin/init-firewall.sh || echo "[entrypoint] Firewall setup failed (non-fatal in dev mode)"

# ── 2. Trust OneCLI CA certificate if present ───────────────────────
if [ -f "/tmp/onecli-proxy-ca.pem" ]; then
  export NODE_EXTRA_CA_CERTS="/tmp/onecli-proxy-ca.pem"
  export SSL_CERT_FILE="/tmp/onecli-proxy-ca.pem"
  echo "[entrypoint] OneCLI CA certificate loaded"
fi

# ── 3. Plugin sync from mounted marketplaces ────────────────────────
MARKETPLACE_DIR="/home/node/.config/cpi"
if [ -d "$MARKETPLACE_DIR" ] && [ "$(ls -A "$MARKETPLACE_DIR" 2>/dev/null)" ]; then
  echo "[entrypoint] Syncing plugins from mounted marketplaces..."
  for mp_link in "$MARKETPLACE_DIR"/*/; do
    manifest="${mp_link}.claude-plugin/marketplace.json"
    if [ -f "$manifest" ]; then
      mp_name=$(jq -r '.name' "$manifest")
      echo "[entrypoint] Marketplace: $mp_name"
      # Install each plugin from this marketplace
      jq -r '.plugins[].name' "$manifest" | while read -r plugin; do
        plugin_id="${plugin}@${mp_name}"
        echo "[entrypoint]   Installing $plugin_id"
        claude plugin install --scope local "$plugin_id" 2>/dev/null || true
      done
    fi
  done
  echo "[entrypoint] Plugin sync complete."
fi

# ── 4. Launch Claude Code ───────────────────────────────────────────
echo "[entrypoint] Starting Claude Code..."
exec claude --dangerously-skip-permissions "$@"
