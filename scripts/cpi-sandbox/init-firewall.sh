#!/usr/bin/env bash
# Network lockdown for Claude Code sandbox container.
# Default-deny outbound, allowlist only what's needed.
set -euo pipefail

echo "[firewall] Configuring network lockdown..."

# Create ipsets for allowed IPs
ipset create allowed_ips hash:net -exist 2>/dev/null || true
ipset flush allowed_ips

# ── Resolve and add allowed hosts ───────────────────────────────────
add_host() {
  local host="$1"
  for ip in $(dig +short "$host" A 2>/dev/null | grep -E '^[0-9]'); do
    ipset add allowed_ips "$ip/32" -exist 2>/dev/null || true
  done
  for ip in $(dig +short "$host" AAAA 2>/dev/null | grep -E '^[0-9a-f]'); do
    ipset add allowed_ips "$ip/128" -exist 2>/dev/null || true
  done
}

# Anthropic API
add_host "api.anthropic.com"
add_host "statsig.anthropic.com"
add_host "sentry.io"
add_host "statsig.com"

# Google / Vertex AI (for proxied requests via OneCLI on host)
# Not needed if all traffic goes through host proxy, but allow just in case
add_host "us-east5-aiplatform.googleapis.com"
add_host "oauth2.googleapis.com"

# GitHub (for git operations and gh CLI)
if command -v curl &>/dev/null; then
  for prefix in web api git; do
    curl -sf "https://api.github.com/meta" 2>/dev/null | \
      jq -r ".${prefix}[]? // empty" 2>/dev/null | \
      while read -r cidr; do
        ipset add allowed_ips "$cidr" -exist 2>/dev/null || true
      done
  done
fi
add_host "github.com"
add_host "api.github.com"

# npm registry
add_host "registry.npmjs.org"

# VS Code extensions (for devcontainer use)
add_host "marketplace.visualstudio.com"
add_host "vscode.blob.core.windows.net"
add_host "update.code.visualstudio.com"

# OneCLI gateway (host.docker.internal resolves to host)
# This is critical — all credential-proxied requests go through here
add_host "host.docker.internal"

# ── iptables rules ──────────────────────────────────────────────────

# Flush existing rules
iptables -F OUTPUT 2>/dev/null || true

# Allow loopback
iptables -A OUTPUT -o lo -j ACCEPT

# Allow established connections
iptables -A OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allow DNS
iptables -A OUTPUT -p udp --dport 53 -j ACCEPT
iptables -A OUTPUT -p tcp --dport 53 -j ACCEPT

# Allow SSH
iptables -A OUTPUT -p tcp --dport 22 -j ACCEPT

# Allow host network (for OneCLI proxy)
HOST_GW=$(ip route | grep default | awk '{print $3}')
if [ -n "$HOST_GW" ]; then
  HOST_NET=$(echo "$HOST_GW" | sed 's/\.[0-9]*$/.0\/16/')
  iptables -A OUTPUT -d "$HOST_NET" -j ACCEPT
fi

# Allow ipset destinations
iptables -A OUTPUT -m set --match-set allowed_ips dst -j ACCEPT

# Reject everything else (REJECT gives immediate feedback vs DROP)
iptables -A OUTPUT -j REJECT --reject-with icmp-port-unreachable

# Set default policy
iptables -P OUTPUT DROP

echo "[firewall] Network lockdown active."

# ── Self-test ───────────────────────────────────────────────────────
if curl -sf --max-time 3 "https://example.com" >/dev/null 2>&1; then
  echo "[firewall] WARNING: example.com is reachable — lockdown may be incomplete"
else
  echo "[firewall] Verified: arbitrary outbound blocked"
fi

if curl -sf --max-time 3 "https://api.github.com/zen" >/dev/null 2>&1; then
  echo "[firewall] Verified: GitHub reachable"
fi

echo "[firewall] Done."
