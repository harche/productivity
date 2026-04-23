#!/bin/bash
# Composite: roster-sync [--force]
# Downloads team-roster-*.json attachments from a Jira config issue to ~/.node-assistant/

[[ -n "${_COMPOSITE_ROSTER_SYNC_LOADED:-}" ]] && return 0
_COMPOSITE_ROSTER_SYNC_LOADED=1

NODE_ASSISTANT_DIR="${HOME}/.node-assistant"
NODE_ASSISTANT_CONFIG_ISSUE="${NODE_ASSISTANT_CONFIG_ISSUE:-OCPNODE-4230}"

cmd_roster_sync() {
  local force=false
  [[ "${1:-}" == "--force" ]] && force=true

  mkdir -p "$NODE_ASSISTANT_DIR"

  local issue_json
  issue_json=$(_curl "${JIRA_BASE}/rest/api/3/issue/${NODE_ASSISTANT_CONFIG_ISSUE}?fields=attachment")

  local roster_attachments
  roster_attachments=$(python3 -c "
import json, sys
data = json.loads(sys.argv[1])
attachments = data.get('fields', {}).get('attachment', [])
matches = []
for a in attachments:
    name = a.get('filename', '')
    if name.startswith('team-roster-') and name.endswith('.json'):
        matches.append({'id': str(a['id']), 'filename': name})
print(json.dumps(matches))
" "$issue_json")

  local count
  count=$(python3 -c "import json,sys; print(len(json.loads(sys.argv[1])))" "$roster_attachments")

  if [[ "$count" -eq 0 ]]; then
    echo '{"synced":[],"skipped":[],"message":"No team-roster-*.json attachments found on '"${NODE_ASSISTANT_CONFIG_ISSUE}"'"}'
    return 0
  fi

  local synced=() skipped=()
  local max_age_seconds=$((7 * 86400))

  while IFS= read -r line; do
    local att_id att_filename
    att_id=$(echo "$line" | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")
    att_filename=$(echo "$line" | python3 -c "import json,sys; print(json.load(sys.stdin)['filename'])")

    local dest="${NODE_ASSISTANT_DIR}/${att_filename}"

    if [[ "$force" == "false" && -f "$dest" ]]; then
      local file_age
      file_age=$(( $(date +%s) - $(stat -f %m "$dest" 2>/dev/null || stat -c %Y "$dest" 2>/dev/null || echo 0) ))
      if (( file_age < max_age_seconds )); then
        skipped+=("$att_filename")
        _log "INFO" "Skipping ${att_filename} (${file_age}s old, <7d)"
        continue
      fi
    fi

    _log "INFO" "Downloading ${att_filename} (attachment ${att_id})"
    _curl -L -o "$dest" "${JIRA_BASE}/rest/api/3/attachment/content/${att_id}"
    synced+=("$att_filename")

  done < <(python3 -c "
import json, sys
for item in json.loads(sys.argv[1]):
    print(json.dumps(item))
" "$roster_attachments")

  python3 -c "
import json, sys
synced = [x for x in sys.argv[1].split(',') if x] if sys.argv[1] else []
skipped = [x for x in sys.argv[2].split(',') if x] if sys.argv[2] else []
print(json.dumps({
    'synced': synced,
    'skipped': skipped,
    'configIssue': sys.argv[3],
    'directory': sys.argv[4],
}))
" "$(IFS=,; echo "${synced[*]:-}")" "$(IFS=,; echo "${skipped[*]:-}")" "$NODE_ASSISTANT_CONFIG_ISSUE" "$NODE_ASSISTANT_DIR"
}
