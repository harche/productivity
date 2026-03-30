#!/usr/bin/env bash
#
# ocp-install.sh — OpenShift cluster lifecycle manager
#
# Usage:
#   ./ocp-install.sh download <version>
#   ./ocp-install.sh create  <version> <type> [cluster-name]
#   ./ocp-install.sh destroy <version> <cluster-dir>
#   ./ocp-install.sh debug   <version> <cluster-dir>
#   ./ocp-install.sh list    [version]
#   ./ocp-install.sh kubeconfig <version> <cluster-dir>
#
# Types: regular, sno, gpu, sno-cpu
# Platform: GCP (openshift-gce-devel)
#
# Secrets:
#   Pull secret read from OS secret store (OCP_PULL_SECRET).
#   SSH key read from ~/.ssh/id_rsa.pub.
#
#   One-time setup (macOS):
#     security add-generic-password -a "$USER" -s "OCP_PULL_SECRET" \
#       -w "$(cat ~/clusters/pull-secret-gcp.txt | python3 -c \
#       "import sys,json; print(json.dumps(json.load(sys.stdin), separators=(',',':')))")"
#
#   One-time setup (Linux):
#     cat ~/clusters/pull-secret-gcp.txt | python3 -c \
#       "import sys,json; print(json.dumps(json.load(sys.stdin), separators=(',',':')))" | \
#       secret-tool store --label="OCP Pull Secret" service ocp-install username "$USER" key OCP_PULL_SECRET
#
set -euo pipefail

CLUSTERS_DIR="${CLUSTERS_DIR:-$HOME/clusters}"
ARTIFACTS_BASE="https://openshift-release-artifacts.apps.ci.l2s4.p1.openshiftapps.com"
SSH_KEY_FILE="${SSH_KEY_FILE:-$HOME/.ssh/id_rsa.pub}"
GCP_PROJECT="openshift-gce-devel"
GCP_REGION="us-central1"
GCP_GPU_ZONE="us-central1-f"
BASE_DOMAIN="gcp.devcluster.openshift.com"
NAME_PREFIX="${OCP_NAME_PREFIX:-$USER}"

# ─── helpers ────────────────────────────────────────────────────────────────

die()  { echo "ERROR: $*" >&2; exit 1; }
info() { echo "==> $*"; }

major_minor() {
  # 4.21.3 → 4.21, 4.21.0-ec.1 → 4.21
  echo "$1" | sed -E 's/^([0-9]+\.[0-9]+).*/\1/'
}

version_dir() {
  echo "${CLUSTERS_DIR}/$(major_minor "$1")/${1}"
}

installer_bin() {
  echo "$(version_dir "$1")/openshift-install"
}

next_cluster_dir() {
  local vdir
  vdir="$(version_dir "$1")"
  local n=1
  while [[ -d "${vdir}/cluster${n}" ]]; do
    ((n++))
  done
  echo "cluster${n}"
}

random_suffix() {
  LC_ALL=C tr -dc 'a-z0-9' </dev/urandom | head -c 5 || true
}

get_pull_secret() {
  local secret="${OCP_PULL_SECRET:-}"
  if [[ -z "$secret" ]]; then
    case "$(uname -s)" in
      Darwin)
        # macOS: read from Keychain (-w doesn't work for long values; use -g and parse)
        secret="$(security find-generic-password -s "OCP_PULL_SECRET" -g 2>&1 \
          | grep '^password: "' | sed 's/^password: "//;s/"$//')" || true
        ;;
      Linux)
        # Linux: read from GNOME Keyring / libsecret via secret-tool
        secret="$(secret-tool lookup service ocp-install key OCP_PULL_SECRET 2>/dev/null)" || true
        ;;
    esac
  fi
  if [[ -z "$secret" ]]; then
    # Fallback: try file
    local fallback="${CLUSTERS_DIR}/pull-secret-gcp.txt"
    if [[ -f "$fallback" ]]; then
      secret="$(python3 -c "import sys,json; print(json.dumps(json.load(sys.stdin), separators=(',',':')))" < "$fallback")"
    else
      if [[ "$(uname -s)" == "Darwin" ]]; then
        die "Pull secret not found. Store it in Keychain:\n  security add-generic-password -a \"\$USER\" -s \"OCP_PULL_SECRET\" -w '\$(cat pull-secret.json)'"
      else
        die "Pull secret not found. Store it with secret-tool:\n  cat pull-secret.json | secret-tool store --label=\"OCP Pull Secret\" service ocp-install username \"\$USER\" key OCP_PULL_SECRET"
      fi
    fi
  fi
  echo "$secret"
}

require_ssh_key() {
  [[ -f "$SSH_KEY_FILE" ]] || die "SSH key not found at ${SSH_KEY_FILE}"
}

require_installer() {
  local bin
  bin="$(installer_bin "$1")"
  [[ -x "$bin" ]] || die "openshift-install not found for ${1}. Run: $0 download ${1}"
}

# ─── download ───────────────────────────────────────────────────────────────

cmd_download() {
  local version="${1:?Usage: $0 download <version>}"
  local vdir
  vdir="$(version_dir "$version")"
  local bin="${vdir}/openshift-install"

  if [[ -x "$bin" ]]; then
    info "openshift-install already exists at ${bin}"
    "${bin}" version
    return 0
  fi

  mkdir -p "$vdir"

  # Detect platform
  local os arch tarball
  os="$(uname -s | tr '[:upper:]' '[:lower:]')"
  arch="$(uname -m)"

  case "${os}-${arch}" in
    darwin-arm64)  tarball="openshift-install-mac-arm64-${version}.tar.gz" ;;
    darwin-x86_64) tarball="openshift-install-mac-${version}.tar.gz" ;;
    linux-x86_64)  tarball="openshift-install-linux-${version}.tar.gz" ;;
    linux-aarch64) tarball="openshift-install-linux-arm64-${version}.tar.gz" ;;
    *) die "Unsupported platform: ${os}-${arch}" ;;
  esac

  local url="${ARTIFACTS_BASE}/${version}/${tarball}"

  info "Downloading ${tarball} ..."
  if ! curl -fSL -o "${vdir}/${tarball}" "$url"; then
    # Fallback: try oc adm release extract
    info "Direct download failed. Trying oc adm release extract ..."
    if command -v oc &>/dev/null; then
      oc adm release extract --tools \
        --to="$vdir" \
        "quay.io/openshift-release-dev/ocp-release:${version}-x86_64" || \
        die "Failed to download openshift-install for ${version}"
    else
      die "Download failed and 'oc' not found for fallback extraction"
    fi
  fi

  info "Extracting ..."
  tar xzf "${vdir}/${tarball}" -C "$vdir" openshift-install 2>/dev/null || \
    tar xzf "${vdir}/${tarball}" -C "$vdir"
  chmod +x "$bin"

  info "Done. openshift-install ${version}:"
  "${bin}" version
}

# ─── install-config generation ──────────────────────────────────────────────

generate_config() {
  local type="$1" cluster_name="$2"
  local pull_secret ssh_key

  pull_secret="$(get_pull_secret)"
  ssh_key="$(cat "$SSH_KEY_FILE")"

  case "$type" in
    regular)
      cat <<EOF
additionalTrustBundlePolicy: Proxyonly
apiVersion: v1
baseDomain: ${BASE_DOMAIN}
compute:
- architecture: amd64
  hyperthreading: Enabled
  name: worker
  platform: {}
  replicas: 3
controlPlane:
  architecture: amd64
  hyperthreading: Enabled
  name: master
  platform: {}
  replicas: 3
metadata:
  name: ${cluster_name}
networking:
  clusterNetwork:
  - cidr: 10.128.0.0/14
    hostPrefix: 23
  machineNetwork:
  - cidr: 10.0.0.0/16
  networkType: OVNKubernetes
  serviceNetwork:
  - 172.30.0.0/16
platform:
  gcp:
    projectID: ${GCP_PROJECT}
    region: ${GCP_REGION}
publish: External
pullSecret: '${pull_secret}'
sshKey: ${ssh_key}
EOF
      ;;

    sno)
      cat <<EOF
additionalTrustBundlePolicy: Proxyonly
apiVersion: v1
baseDomain: ${BASE_DOMAIN}
compute:
- architecture: amd64
  hyperthreading: Enabled
  name: worker
  platform: {}
  replicas: 0
controlPlane:
  architecture: amd64
  hyperthreading: Enabled
  name: master
  platform:
    gcp:
      onHostMaintenance: Terminate
      type: a2-highgpu-2g
      zones:
        - ${GCP_GPU_ZONE}
  replicas: 1
metadata:
  name: ${cluster_name}
networking:
  clusterNetwork:
  - cidr: 10.128.0.0/14
    hostPrefix: 23
  machineNetwork:
  - cidr: 10.0.0.0/16
  networkType: OVNKubernetes
  serviceNetwork:
  - 172.30.0.0/16
platform:
  gcp:
    projectID: ${GCP_PROJECT}
    region: ${GCP_REGION}
publish: External
pullSecret: '${pull_secret}'
sshKey: ${ssh_key}
EOF
      ;;

    gpu)
      cat <<EOF
additionalTrustBundlePolicy: Proxyonly
apiVersion: v1
baseDomain: ${BASE_DOMAIN}
compute:
- architecture: amd64
  hyperthreading: Enabled
  name: worker
  platform:
    gcp:
      onHostMaintenance: Terminate
      type: a2-highgpu-1g
      zones:
        - ${GCP_GPU_ZONE}
  replicas: 3
controlPlane:
  architecture: amd64
  hyperthreading: Enabled
  name: master
  platform: {}
  replicas: 3
metadata:
  name: ${cluster_name}
networking:
  clusterNetwork:
  - cidr: 10.128.0.0/14
    hostPrefix: 23
  machineNetwork:
  - cidr: 10.0.0.0/16
  networkType: OVNKubernetes
  serviceNetwork:
  - 172.30.0.0/16
platform:
  gcp:
    projectID: ${GCP_PROJECT}
    region: ${GCP_REGION}
publish: External
pullSecret: '${pull_secret}'
sshKey: ${ssh_key}
EOF
      ;;

    sno-cpu)
      cat <<EOF
additionalTrustBundlePolicy: Proxyonly
apiVersion: v1
baseDomain: ${BASE_DOMAIN}
cpuPartitioningMode: AllNodes
compute:
- architecture: amd64
  hyperthreading: Enabled
  name: worker
  platform: {}
  replicas: 0
controlPlane:
  architecture: amd64
  hyperthreading: Enabled
  name: master
  platform:
    gcp:
      onHostMaintenance: Terminate
  replicas: 1
metadata:
  name: ${cluster_name}
networking:
  clusterNetwork:
  - cidr: 10.128.0.0/14
    hostPrefix: 23
  machineNetwork:
  - cidr: 10.0.0.0/16
  networkType: OVNKubernetes
  serviceNetwork:
  - 172.30.0.0/16
platform:
  gcp:
    projectID: ${GCP_PROJECT}
    region: ${GCP_REGION}
publish: External
pullSecret: '${pull_secret}'
sshKey: ${ssh_key}
EOF
      ;;

    *)
      die "Unknown type: ${type}. Valid types: regular, sno, gpu, sno-cpu"
      ;;
  esac
}

# ─── create ─────────────────────────────────────────────────────────────────

cmd_create() {
  local version="${1:?Usage: $0 create <version> <type> [cluster-name]}"
  local type="${2:?Usage: $0 create <version> <type> [cluster-name]}"
  local cluster_name="${3:-}"

  require_installer "$version"
  require_ssh_key

  # Auto-generate cluster name if not provided
  if [[ -z "$cluster_name" ]]; then
    local type_prefix
    case "$type" in
      regular) type_prefix="" ;;
      sno)     type_prefix="sno" ;;
      gpu)     type_prefix="gpu" ;;
      sno-cpu) type_prefix="cpu" ;;
    esac
    cluster_name="${NAME_PREFIX}${type_prefix}$(random_suffix)"
  fi

  local vdir cluster_dir
  vdir="$(version_dir "$version")"
  cluster_dir="$(next_cluster_dir "$version")"
  local install_dir="${vdir}/${cluster_dir}"

  mkdir -p "$install_dir"

  info "Cluster type:    ${type}"
  info "Cluster name:    ${cluster_name}"
  info "Version:         ${version}"
  info "Install dir:     ${install_dir}"
  info ""

  # Generate install-config
  generate_config "$type" "$cluster_name" > "${install_dir}/install-config.yaml"

  # Back up (consumed during install)
  cp "${install_dir}/install-config.yaml" "${install_dir}/install-config.yaml.backup"

  info "Generated install-config.yaml for type '${type}'"
  info ""

  # Confirm before proceeding
  echo "--- install-config.yaml (summary) ---"
  grep -E '^\s*(name|replicas|type|region|cpuPartitioning):' "${install_dir}/install-config.yaml.backup" || true
  echo "--------------------------------------"
  echo ""
  read -rp "Proceed with cluster creation? [y/N] " confirm
  [[ "$confirm" =~ ^[Yy]$ ]] || { info "Aborted."; exit 0; }

  info "Creating cluster (this will take 30-45 minutes) ..."
  local bin
  bin="$(installer_bin "$version")"
  "${bin}" create cluster --dir="$install_dir" --log-level=info

  info ""
  info "Cluster created successfully!"
  info ""
  info "Kubeconfig: export KUBECONFIG=${install_dir}/auth/kubeconfig"
  info "Console:    $(grep -o 'https://console-openshift.*' "${install_dir}/.openshift_install.log" 2>/dev/null | tail -1 || echo 'check install log')"
  info ""
  info "To destroy:  $0 destroy ${version} ${cluster_dir}"
}

# ─── destroy ────────────────────────────────────────────────────────────────

cmd_destroy() {
  local version="${1:?Usage: $0 destroy <version> <cluster-dir>}"
  local cluster_dir="${2:?Usage: $0 destroy <version> <cluster-dir>}"

  require_installer "$version"

  local vdir install_dir bin
  vdir="$(version_dir "$version")"
  install_dir="${vdir}/${cluster_dir}"
  bin="$(installer_bin "$version")"

  [[ -d "$install_dir" ]] || die "Cluster directory not found: ${install_dir}"

  info "Destroying cluster at ${install_dir} ..."
  read -rp "Are you sure? This cannot be undone. [y/N] " confirm
  [[ "$confirm" =~ ^[Yy]$ ]] || { info "Aborted."; exit 0; }

  "${bin}" destroy cluster --dir="$install_dir" --log-level=info

  info "Cluster destroyed."
}

# ─── debug ──────────────────────────────────────────────────────────────────

cmd_debug() {
  local version="${1:?Usage: $0 debug <version> <cluster-dir>}"
  local cluster_dir="${2:?Usage: $0 debug <version> <cluster-dir>}"

  local vdir install_dir
  vdir="$(version_dir "$version")"
  install_dir="${vdir}/${cluster_dir}"

  [[ -d "$install_dir" ]] || die "Cluster directory not found: ${install_dir}"

  # Resolve cluster name from backup config, metadata, or install log
  local cluster_name="" infra_id=""
  if [[ -f "${install_dir}/metadata.json" ]]; then
    cluster_name="$(python3 -c "import json; print(json.load(open('${install_dir}/metadata.json'))['clusterName'])" 2>/dev/null || true)"
    infra_id="$(python3 -c "import json; print(json.load(open('${install_dir}/metadata.json'))['infraID'])" 2>/dev/null || true)"
  fi
  if [[ -z "$cluster_name" ]] && [[ -f "${install_dir}/install-config.yaml.backup" ]]; then
    cluster_name="$(grep '^\s*name:' "${install_dir}/install-config.yaml.backup" | head -1 | awk '{print $2}')"
  fi
  # Fallback: extract cluster name from install log (api.<name>.gcp.devcluster...)
  if [[ -z "$cluster_name" ]] && [[ -f "${install_dir}/.openshift_install.log" ]]; then
    cluster_name="$(grep -o 'api\.[^.]*\.gcp' "${install_dir}/.openshift_install.log" 2>/dev/null \
      | head -1 | sed 's/^api\.//;s/\.gcp$//' || true)"
  fi
  # Fallback: try to find infra_id from log (lines like "Deleted network <infraID>-network")
  if [[ -z "$infra_id" ]] && [[ -f "${install_dir}/.openshift_install.log" ]]; then
    infra_id="$(grep -o 'Deleted network [^ ]*-network' "${install_dir}/.openshift_install.log" 2>/dev/null \
      | head -1 | sed 's/^Deleted network //;s/-network$//' || true)"
  fi

  echo ""
  echo "=========================================="
  echo " Cluster Debug: ${cluster_dir}"
  echo "=========================================="
  echo " Install dir:   ${install_dir}"
  echo " Cluster name:  ${cluster_name:-unknown}"
  echo " Infra ID:      ${infra_id:-unknown}"
  echo " Version:       ${version}"
  echo "=========================================="

  # ── 1. Local log analysis ──
  echo ""
  info "LOCAL LOGS"
  echo ""

  local install_log="${install_dir}/.openshift_install.log"
  if [[ -f "$install_log" ]]; then
    local log_size
    log_size="$(wc -c < "$install_log" | tr -d ' ')"
    echo "  Install log: ${install_log} ($(( log_size / 1024 )) KB)"
    echo ""

    # Check if install completed successfully
    if grep -q 'Install complete' "$install_log" 2>/dev/null; then
      echo "  Status: Install completed successfully"
      grep 'Install complete' "$install_log"
      echo ""
    elif grep -q 'Uninstallation complete' "$install_log" 2>/dev/null; then
      echo "  Status: Cluster was destroyed"
      echo ""
    fi

    # Show level=error lines (deduplicated)
    local error_count
    error_count="$(grep -c 'level=error' "$install_log" 2>/dev/null || echo 0)"
    if [[ "$error_count" -gt 0 ]]; then
      echo "  --- Errors (${error_count} total, showing unique) ---"
      grep 'level=error' "$install_log" | sed 's/time="[^"]*" //' | sort -u
      echo ""
    fi

    # Show level=fatal lines
    if grep -q 'level=fatal' "$install_log" 2>/dev/null; then
      echo "  --- Fatal ---"
      grep 'level=fatal' "$install_log"
      echo ""
    fi

    # Common failure patterns
    echo "  --- Failure Pattern Analysis ---"
    if grep -q 'Bootstrap failed to complete' "$install_log" 2>/dev/null; then
      echo "  BOOTSTRAP FAILURE: Bootstrap host failed to create temporary control plane"
      echo "  Likely causes: SSH key mismatch, instance didn't boot, ignition failure"
      echo "  Next step: check serial console output with: $0 debug ${version} ${cluster_dir} --gcp"
    fi
    if grep -q 'context deadline exceeded' "$install_log" 2>/dev/null; then
      echo "  TIMEOUT: Cluster API connection timed out"
    fi
    if grep -q 'quota' "$install_log" 2>/dev/null; then
      echo "  QUOTA: Possible GCP quota exceeded"
      grep -i 'quota' "$install_log" | head -3
    fi
    if grep -q 'resourceInUseByAnotherResource' "$install_log" 2>/dev/null; then
      echo "  RESOURCE CONFLICT: GCP resources still in use (stale resources from prior install)"
    fi
    if grep -q 'unable to authenticate' "$install_log" 2>/dev/null; then
      echo "  SSH AUTH FAILURE: Could not SSH to bootstrap node (wrong key or agent not running)"
    fi
    echo ""

    # Last 10 non-debug lines for context
    echo "  --- Last 10 significant log lines ---"
    grep -v 'level=debug' "$install_log" | tail -10
    echo ""
  else
    echo "  No install log found at ${install_log}"
    echo ""
  fi

  # Log bundles
  local -a bundles=("${install_dir}"/log-bundle-*.tar.gz)
  if [[ -e "${bundles[0]}" ]]; then
    echo "  --- Log Bundles ---"
    for b in "${bundles[@]}"; do
      echo "  $(basename "$b")  ($(du -h "$b" | cut -f1))"
    done
    echo ""
    echo "  To extract and inspect a bundle:"
    echo "    mkdir /tmp/logbundle && tar xzf <bundle> -C /tmp/logbundle"
    echo "    # Then check: bootstrap/journals/*, control-plane/*/journals/*"
    echo ""
  fi

  # ── 2. openshift-install gather bootstrap ──
  local bin
  bin="$(installer_bin "$version" 2>/dev/null || true)"
  if [[ -x "$bin" ]] && [[ -f "${install_dir}/metadata.json" ]]; then
    echo "  --- Gather Bootstrap Logs ---"
    echo "  Run this to collect bootstrap logs from the running cluster:"
    echo "    ${bin} gather bootstrap --dir=${install_dir}"
    echo ""
  fi

  # ── 3. GCP diagnostics ──
  if ! command -v gcloud &>/dev/null; then
    echo "  [gcloud not found — skipping GCP diagnostics]"
    echo "  Install: https://cloud.google.com/sdk/docs/install"
    return 0
  fi

  # Determine the filter prefix (infra_id or cluster_name)
  local filter_name="${infra_id:-$cluster_name}"
  if [[ -z "$filter_name" ]]; then
    echo "  [Cannot determine cluster name/infraID — skipping GCP diagnostics]"
    return 0
  fi

  echo ""
  info "GCP DIAGNOSTICS (project: ${GCP_PROJECT})"
  echo ""

  # 3a. List instances (single API call, filter locally for bootstrap/masters)
  local all_instances
  all_instances="$(gcloud compute instances list \
    --project="$GCP_PROJECT" \
    --filter="name~${filter_name}" \
    --format="value(name,zone,status,machineType.basename())" 2>/dev/null || true)"

  echo "  --- Compute Instances ---"
  if [[ -n "$all_instances" ]]; then
    printf "  %-40s  %-25s  %-10s  %s\n" "NAME" "ZONE" "STATUS" "TYPE"
    while IFS=$'\t' read -r iname izone istatus itype; do
      printf "  %-40s  %-25s  %-10s  %s\n" "$iname" "$izone" "$istatus" "$itype"
    done <<< "$all_instances"
  else
    echo "  (no instances found or gcloud error)"
  fi
  echo ""

  # 3b. Serial port output for bootstrap (last 50 lines)
  local bootstrap_instance
  bootstrap_instance="$(echo "$all_instances" | grep 'bootstrap' | head -1)"

  if [[ -n "$bootstrap_instance" ]]; then
    local bname bzone
    bname="$(echo "$bootstrap_instance" | cut -f1)"
    bzone="$(echo "$bootstrap_instance" | cut -f2)"
    echo "  --- Bootstrap Serial Console (last 50 lines) ---"
    echo "  Instance: ${bname} (${bzone})"
    gcloud compute instances get-serial-port-output "$bname" \
      --project="$GCP_PROJECT" \
      --zone="$bzone" 2>/dev/null | tail -50 || echo "  (could not retrieve serial output)"
    echo ""
  fi

  # Serial output for master nodes
  local master_instances
  master_instances="$(echo "$all_instances" | grep 'master')"

  if [[ -n "$master_instances" ]]; then
    echo "  --- Master Node Serial Console (last 20 lines each) ---"
    while IFS=$'\t' read -r mname mzone; do
      echo "  Instance: ${mname} (${mzone})"
      gcloud compute instances get-serial-port-output "$mname" \
        --project="$GCP_PROJECT" \
        --zone="$mzone" 2>/dev/null | tail -20 || echo "  (could not retrieve serial output)"
      echo ""
    done <<< "$master_instances"
  fi

  # 3c. GCP Cloud Logging (last 30 minutes of errors)
  echo "  --- GCP Cloud Logging (recent errors) ---"
  gcloud logging read \
    "resource.type=gce_instance AND textPayload:\"${filter_name}\" AND severity>=ERROR" \
    --project="$GCP_PROJECT" \
    --limit=20 \
    --format="table(timestamp,textPayload)" \
    --freshness=30m 2>/dev/null || echo "  (no log entries found or gcloud error)"
  echo ""

  # 3d. Firewall rules
  echo "  --- Firewall Rules ---"
  gcloud compute firewall-rules list \
    --project="$GCP_PROJECT" \
    --filter="name~${filter_name}" \
    --format="table(name,direction,allowed,targetTags)" 2>/dev/null || echo "  (none found)"
  echo ""

  # 3e. Disks (checking for orphaned disks)
  echo "  --- Persistent Disks ---"
  gcloud compute disks list \
    --project="$GCP_PROJECT" \
    --filter="name~${filter_name}" \
    --format="table(name,zone.basename(),sizeGb,status,users.basename())" 2>/dev/null || echo "  (none found)"
  echo ""

  echo "=========================================="
  echo " Debug complete"
  echo "=========================================="
}

# ─── list ───────────────────────────────────────────────────────────────────

cmd_list() {
  local filter_version="${1:-}"

  echo ""
  printf "%-12s  %-16s  %-10s  %-30s\n" "VERSION" "CLUSTER" "STATUS" "PATH"
  printf "%-12s  %-16s  %-10s  %-30s\n" "-------" "-------" "------" "----"

  local minor_dirs
  if [[ -n "$filter_version" ]]; then
    minor_dirs="${CLUSTERS_DIR}/$(major_minor "$filter_version")"
  else
    minor_dirs="${CLUSTERS_DIR}/4.*"
  fi

  for minor_dir in $minor_dirs; do
    [[ -d "$minor_dir" ]] || continue
    for ver_dir in "$minor_dir"/*/; do
      [[ -d "$ver_dir" ]] || continue
      ver_dir="${ver_dir%/}"
      local version
      version="$(basename "$ver_dir")"
      # Skip if doesn't look like a version
      [[ "$version" =~ ^[0-9]+\.[0-9]+ ]] || continue

      for cluster in "$ver_dir"/cluster*/; do
        [[ -d "$cluster" ]] || continue
        local cname status
        cname="$(basename "$cluster")"

        if [[ -f "${cluster}/.openshift_install.log" ]] && grep -q 'Uninstallation complete' "${cluster}/.openshift_install.log" 2>/dev/null; then
          status="DESTROYED"
        elif [[ -f "${cluster}/auth/kubeconfig" ]]; then
          status="ACTIVE"
        elif [[ -f "${cluster}/metadata.json" ]]; then
          status="ACTIVE"
        elif [[ -f "${cluster}/install-config.yaml" ]]; then
          status="CONFIG"
        elif [[ -f "${cluster}/.openshift_install.log" ]] || compgen -G "${cluster}/log-bundle-*.tar.gz" &>/dev/null; then
          status="DESTROYED"
        elif [[ -f "${cluster}/install-config.yaml.backup" ]]; then
          status="DESTROYED"
        else
          status="EMPTY"
        fi

        printf "%-12s  %-16s  %-10s  %-30s\n" "$version" "$cname" "$status" "$cluster"
      done
    done
  done
  echo ""
}

# ─── kubeconfig ─────────────────────────────────────────────────────────────

cmd_kubeconfig() {
  local version="${1:?Usage: $0 kubeconfig <version> <cluster-dir>}"
  local cluster_dir="${2:?Usage: $0 kubeconfig <version> <cluster-dir>}"

  local vdir install_dir kubeconfig
  vdir="$(version_dir "$version")"
  install_dir="${vdir}/${cluster_dir}"
  kubeconfig="${install_dir}/auth/kubeconfig"

  [[ -f "$kubeconfig" ]] || die "Kubeconfig not found: ${kubeconfig}"

  echo "export KUBECONFIG=${kubeconfig}"
}

# ─── main ───────────────────────────────────────────────────────────────────

usage() {
  cat <<EOF
Usage: $(basename "$0") <command> [args]

Commands:
  download  <version>                        Download openshift-install for a version
  create    <version> <type> [cluster-name]  Create a cluster
  destroy   <version> <cluster-dir>          Destroy a cluster
  debug     <version> <cluster-dir>          Diagnose a failed installation
  list      [version]                        List all clusters
  kubeconfig <version> <cluster-dir>         Print KUBECONFIG export command

Cluster types:
  regular   3 control-plane + 3 workers (standard instances)
  sno       Single Node OpenShift with GPU (a2-highgpu-2g)
  gpu       3 control-plane + 3 GPU workers (a2-highgpu-1g)
  sno-cpu   Single Node OpenShift, CPU only (cpuPartitioningMode)

Environment variables:
  CLUSTERS_DIR    Base directory (default: ~/clusters)
  SSH_KEY_FILE    SSH public key (default: ~/.ssh/id_rsa.pub)

Secrets:
  Pull secret is read from the OS secret store (OCP_PULL_SECRET).
  Falls back to \${CLUSTERS_DIR}/pull-secret-gcp.txt if not found.

  macOS (Keychain):
    security add-generic-password -a "\$USER" -s "OCP_PULL_SECRET" \\
      -w "\$(cat pull-secret.json | python3 -c \\
      "import sys,json; print(json.dumps(json.load(sys.stdin), separators=(',',':')))")"

  Linux (secret-tool / libsecret):
    cat pull-secret.json | python3 -c \\
      "import sys,json; print(json.dumps(json.load(sys.stdin), separators=(',',':')))" | \\
      secret-tool store --label="OCP Pull Secret" service ocp-install username "\$USER" key OCP_PULL_SECRET

Examples:
  $0 download 4.21.3
  $0 create 4.21.3 sno
  $0 create 4.21.3 gpu mycluster01
  $0 list
  $0 list 4.21
  $0 debug 4.21.3 cluster1
  $0 destroy 4.21.3 cluster1
  eval \$($0 kubeconfig 4.21.3 cluster1)

Download source: ${ARTIFACTS_BASE}
EOF
}

case "${1:-}" in
  download)   shift; cmd_download "$@" ;;
  create)     shift; cmd_create "$@" ;;
  destroy)    shift; cmd_destroy "$@" ;;
  debug)      shift; cmd_debug "$@" ;;
  list)       shift; cmd_list "$@" ;;
  kubeconfig) shift; cmd_kubeconfig "$@" ;;
  -h|--help|help|"")  usage ;;
  *)          die "Unknown command: $1. Run '$0 --help' for usage." ;;
esac
