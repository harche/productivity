#!/usr/bin/env bash
# Copy Claude Code skills into any project's .claude/skills/
# Resolves source from the script's own location, so it works from anywhere.
#
# Usage:
#   copy-skills                     # interactive menu
#   copy-skills all                 # copy all skills
#   copy-skills jira github slack   # copy specific skills by name
#   copy-skills --list              # list available skills
#   copy-skills --help              # show help
#   copy-skills -d /path/to/repo jira  # copy into a specific repo

set -euo pipefail

# Resolve source relative to where this script lives
SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "$0" 2>/dev/null || realpath "$0")")" && pwd)"
SKILLS_SOURCE="$SCRIPT_DIR/.claude/skills"
SKILLS_DEST=""

usage() {
  cat <<EOF
Usage: $(basename "$0") [OPTIONS] [SKILL ...]

Copy Claude Code skills into a project's .claude/skills/ directory.

Arguments:
  SKILL ...         Skill names to copy (e.g. jira github slack)
  all               Copy all available skills

Options:
  -d, --dest DIR    Target project directory (default: current directory)
  -l, --list        List available skills
  -h, --help        Show this help

Examples:
  $(basename "$0")                          # interactive menu
  $(basename "$0") all                      # copy all skills
  $(basename "$0") jira github              # copy jira and github
  $(basename "$0") -d ~/work/my-repo jira   # copy jira into specific repo
EOF
  exit 0
}

# Parse options
args=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage ;;
    -l|--list)
      ls "$SKILLS_SOURCE"
      exit 0
      ;;
    -d|--dest)
      SKILLS_DEST="$2/.claude/skills"
      shift 2
      ;;
    *) args+=("$1"); shift ;;
  esac
done

SKILLS_DEST="${SKILLS_DEST:-.claude/skills}"

# Verify source exists
if [[ ! -d "$SKILLS_SOURCE" ]]; then
  echo "Error: Skills source not found at $SKILLS_SOURCE" >&2
  exit 1
fi

# Get available skills
mapfile -t skills < <(ls "$SKILLS_SOURCE")

if [[ ${#skills[@]} -eq 0 ]]; then
  echo "No skills found in $SKILLS_SOURCE" >&2
  exit 1
fi

# Validate a skill name exists
validate_skill() {
  local name="$1"
  for s in "${skills[@]}"; do
    [[ "$s" == "$name" ]] && return 0
  done
  return 1
}

# Determine selected skills
selected=()

if [[ ${#args[@]} -gt 0 ]]; then
  # Programmatic mode: args provided
  if [[ "${args[0]}" == "all" ]]; then
    selected=("${skills[@]}")
  else
    for name in "${args[@]}"; do
      if validate_skill "$name"; then
        selected+=("$name")
      else
        echo "Warning: unknown skill '$name', skipping (available: ${skills[*]})" >&2
      fi
    done
  fi
else
  # Interactive mode: show menu
  echo "Available skills:"
  echo ""
  for i in "${!skills[@]}"; do
    echo "  $((i + 1))) ${skills[$i]}"
  done
  echo ""
  echo "  a) All skills"
  echo "  q) Quit"
  echo ""
  read -rp "Select skills (e.g. 1 3 5, a for all, q to quit): " input

  if [[ "$input" == "q" ]]; then
    echo "Cancelled."
    exit 0
  fi

  if [[ "$input" == "a" ]]; then
    selected=("${skills[@]}")
  else
    for num in $input; do
      idx=$((num - 1))
      if [[ $idx -ge 0 && $idx -lt ${#skills[@]} ]]; then
        selected+=("${skills[$idx]}")
      else
        echo "Warning: invalid selection '$num', skipping" >&2
      fi
    done
  fi
fi

if [[ ${#selected[@]} -eq 0 ]]; then
  echo "No valid skills selected." >&2
  exit 1
fi

# Copy selected skills
mkdir -p "$SKILLS_DEST"
for skill in "${selected[@]}"; do
  cp -r "$SKILLS_SOURCE/$skill" "$SKILLS_DEST/"
  echo "Copied: $skill"
done

echo ""
echo "Done. ${#selected[@]} skill(s) copied to $SKILLS_DEST/"
