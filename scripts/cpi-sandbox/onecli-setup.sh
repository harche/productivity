#!/usr/bin/env bash
# Bootstrap OneCLI: start gateway, sync secrets from Keychain, refresh GCP tokens.
# Usage: bash onecli-setup.sh
set -euo pipefail

ONECLI_CONTAINER="cpi-onecli"
ONECLI_IMAGE="ghcr.io/onecli/onecli:latest"
ONECLI_DASHBOARD_PORT=10254
ONECLI_GATEWAY_PORT=10255
ONECLI_DATA_VOLUME="cpi-onecli-data"
CPI="$(dirname "$0")/../../cpi"

# ── Start OneCLI if not running ─────────────────────────────────────
start_onecli() {
  if docker ps --format '{{.Names}}' | grep -q "^${ONECLI_CONTAINER}$"; then
    echo "[onecli] Already running."
    return 0
  fi

  if docker ps -a --format '{{.Names}}' | grep -q "^${ONECLI_CONTAINER}$"; then
    echo "[onecli] Starting stopped container..."
    docker start "$ONECLI_CONTAINER"
  else
    echo "[onecli] Starting OneCLI (dashboard :${ONECLI_DASHBOARD_PORT}, gateway :${ONECLI_GATEWAY_PORT})..."
    docker run -d \
      --name "$ONECLI_CONTAINER" \
      --pull always \
      -p "${ONECLI_DASHBOARD_PORT}:10254" \
      -p "${ONECLI_GATEWAY_PORT}:10255" \
      -v "${ONECLI_DATA_VOLUME}:/app/data" \
      --restart unless-stopped \
      "$ONECLI_IMAGE"
  fi

  # Wait for gateway to be ready
  echo "[onecli] Waiting for gateway..."
  for i in $(seq 1 30); do
    if curl -sf "http://localhost:${ONECLI_DASHBOARD_PORT}/api/health" >/dev/null 2>&1; then
      echo "[onecli] Gateway ready."
      return 0
    fi
    sleep 1
  done
  echo "[onecli] ERROR: Gateway failed to start within 30s" >&2
  return 1
}

# ── Sync secrets via cpi ───────────────────────────────────────────
sync_secrets() {
  if [ -x "$CPI" ] || command -v cpi &>/dev/null; then
    local cmd="${CPI}"
    [ -x "$cmd" ] || cmd="cpi"
    echo "[onecli] Syncing secrets from Keychain via cpi..."
    python3 "$cmd" secret sync
  else
    echo "[onecli] WARNING: cpi not found, cannot sync secrets" >&2
  fi
}

# ── Vertex AI token refresh ────────────────────────────────────────
# TODO: Remove this once onecli/onecli#oauth2 lands (adds native "oauth2"
# secret type with background token refresh in the gateway). See /tmp/onecli
# for the PR branch. Once merged, register Vertex AI as:
#   cpi secret add vertex-ai -s gcp-service-account-key -t oauth2 \
#     --host '*.googleapis.com'
# and delete refresh_vertex_token + start_token_refresh_daemon below.
#
# GCP OAuth2 tokens expire every hour. Fetches fresh token from host
# gcloud credentials and upserts into OneCLI.
refresh_vertex_token() {
  local token
  token=$(gcloud auth print-access-token 2>/dev/null) || {
    echo "[onecli] WARNING: gcloud auth print-access-token failed." >&2
    return 1
  }
  curl -sf -X POST "http://localhost:${ONECLI_DASHBOARD_PORT}/api/secrets" \
    -H "Content-Type: application/json" \
    -d "{
      \"name\": \"vertex-ai-token\",
      \"type\": \"bearer\",
      \"value\": \"${token}\",
      \"hostPattern\": \"*.googleapis.com\",
      \"upsert\": true
    }" >/dev/null 2>&1 && {
    echo "[onecli] Vertex AI token refreshed."
  } || {
    echo "[onecli] WARNING: Failed to upsert Vertex AI token" >&2
    return 1
  }
}

# ── Token refresh daemon ───────────────────────────────────────────
start_token_refresh_daemon() {
  local pidfile="${HOME}/.config/cpi/vertex-refresh.pid"
  mkdir -p "${HOME}/.config/cpi"

  if [ -f "$pidfile" ]; then
    local old_pid
    old_pid=$(cat "$pidfile")
    if kill -0 "$old_pid" 2>/dev/null; then
      echo "[onecli] Token refresh daemon already running (PID $old_pid)."
      return 0
    fi
    rm -f "$pidfile"
  fi

  (
    echo $$ > "$pidfile"
    trap 'rm -f "$pidfile"; exit 0' INT TERM
    while true; do
      refresh_vertex_token || true
      sleep 2700  # 45 minutes
    done
  ) &

  echo "[onecli] Token refresh daemon started (PID $!, every 45m)."
}

# ── Main ────────────────────────────────────────────────────────────
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  start_onecli
  sync_secrets
  refresh_vertex_token || true
  start_token_refresh_daemon
  echo ""
  echo "[onecli] Setup complete."
  echo "[onecli] Dashboard: http://localhost:${ONECLI_DASHBOARD_PORT}"
  echo "[onecli] Gateway:   http://localhost:${ONECLI_GATEWAY_PORT}"
  echo "[onecli] Secrets managed via: cpi secret list"
fi
