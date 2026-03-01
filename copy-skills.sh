#!/usr/bin/env bash
# Install Claude Code skills from the skills registry into any project.
# Skills are organized by category: skills/<category>/<skill-name>/SKILL.md
#
# Usage:
#   copy-skills                            # interactive menu
#   copy-skills all                        # install all skills
#   copy-skills jira github slack          # install specific skills by name
#   copy-skills -c redhat                  # install all skills in a category
#   copy-skills --list                     # list skills grouped by category
#   copy-skills --help                     # show help
#   copy-skills -d /path/to/repo jira     # install into a specific repo

set -euo pipefail

# Resolve source relative to where this script lives
SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "$0" 2>/dev/null || realpath "$0")")" && pwd)"
SKILLS_SOURCE="$SCRIPT_DIR/skills"
SKILLS_DEST=""
CATEGORY_FILTER=""

usage() {
  cat <<EOF
Usage: $(basename "$0") [OPTIONS] [SKILL ...]

Install Claude Code skills from the registry into a project's .claude/skills/.

Arguments:
  SKILL ...              Skill names to install (e.g. jira github slack)
  all                    Install all available skills

Options:
  -c, --category CAT     Install all skills in a category (e.g. redhat, tools)
  -d, --dest DIR         Target project directory (default: current directory)
  -l, --list             List available skills grouped by category
  -h, --help             Show this help

Examples:
  $(basename "$0")                          # interactive menu
  $(basename "$0") all                      # install all skills
  $(basename "$0") jira github              # install jira and github
  $(basename "$0") -c redhat                # install all Red Hat skills
  $(basename "$0") -d ~/work/my-repo jira   # install jira into specific repo
EOF
  exit 0
}

# Parse options
args=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage ;;
    -l|--list)
      for category_dir in "$SKILLS_SOURCE"/*/; do
        category=$(basename "$category_dir")
        echo "$category/"
        for skill_dir in "$category_dir"/*/; do
          [[ -f "$skill_dir/SKILL.md" ]] && echo "  $(basename "$skill_dir")"
        done
      done
      exit 0
      ;;
    -c|--category)
      CATEGORY_FILTER="$2"
      shift 2
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
  echo "Error: Skills registry not found at $SKILLS_SOURCE" >&2
  exit 1
fi

# Discover all skills: builds parallel arrays of names, categories, and paths
skill_names=()
skill_categories=()
skill_paths=()

for category_dir in "$SKILLS_SOURCE"/*/; do
  category=$(basename "$category_dir")
  for skill_dir in "$category_dir"/*/; do
    if [[ -f "$skill_dir/SKILL.md" ]]; then
      skill_names+=("$(basename "$skill_dir")")
      skill_categories+=("$category")
      skill_paths+=("$skill_dir")
    fi
  done
done

if [[ ${#skill_names[@]} -eq 0 ]]; then
  echo "No skills found in $SKILLS_SOURCE" >&2
  exit 1
fi

# Find a skill index by name
find_skill() {
  local name="$1"
  for i in "${!skill_names[@]}"; do
    [[ "${skill_names[$i]}" == "$name" ]] && echo "$i" && return 0
  done
  return 1
}

# Get all categories
get_categories() {
  printf '%s\n' "${skill_categories[@]}" | sort -u
}

# Determine selected skill indices
selected=()

if [[ -n "$CATEGORY_FILTER" ]]; then
  # Category mode
  if [[ ! -d "$SKILLS_SOURCE/$CATEGORY_FILTER" ]]; then
    echo "Error: unknown category '$CATEGORY_FILTER' (available: $(get_categories | tr '\n' ' '))" >&2
    exit 1
  fi
  for i in "${!skill_names[@]}"; do
    [[ "${skill_categories[$i]}" == "$CATEGORY_FILTER" ]] && selected+=("$i")
  done
elif [[ ${#args[@]} -gt 0 ]]; then
  # Programmatic mode
  if [[ "${args[0]}" == "all" ]]; then
    for i in "${!skill_names[@]}"; do selected+=("$i"); done
  else
    for name in "${args[@]}"; do
      if idx=$(find_skill "$name"); then
        selected+=("$idx")
      else
        echo "Warning: unknown skill '$name', skipping" >&2
      fi
    done
  fi
else
  # Interactive mode: grouped menu
  echo "Available skills:"
  echo ""
  idx=1
  menu_map=()
  current_cat=""
  for i in "${!skill_names[@]}"; do
    if [[ "${skill_categories[$i]}" != "$current_cat" ]]; then
      current_cat="${skill_categories[$i]}"
      echo "  [$current_cat]"
    fi
    echo "    $idx) ${skill_names[$i]}"
    menu_map+=("$i")
    ((idx++))
  done
  echo ""
  echo "  a) All skills"

  # List categories for category selection
  mapfile -t cats < <(get_categories)
  for c in "${cats[@]}"; do
    echo "  $c) All $c skills"
  done

  echo "  q) Quit"
  echo ""
  read -rp "Select (e.g. 1 3 5, a for all, category name, q to quit): " input

  if [[ "$input" == "q" ]]; then
    echo "Cancelled."
    exit 0
  fi

  if [[ "$input" == "a" ]]; then
    for i in "${!skill_names[@]}"; do selected+=("$i"); done
  else
    # Check if input matches a category name
    matched_cat=false
    for c in "${cats[@]}"; do
      if [[ "$input" == "$c" ]]; then
        for i in "${!skill_names[@]}"; do
          [[ "${skill_categories[$i]}" == "$c" ]] && selected+=("$i")
        done
        matched_cat=true
        break
      fi
    done

    if [[ "$matched_cat" == false ]]; then
      for num in $input; do
        idx=$((num - 1))
        if [[ $idx -ge 0 && $idx -lt ${#menu_map[@]} ]]; then
          selected+=("${menu_map[$idx]}")
        else
          echo "Warning: invalid selection '$num', skipping" >&2
        fi
      done
    fi
  fi
fi

if [[ ${#selected[@]} -eq 0 ]]; then
  echo "No valid skills selected." >&2
  exit 1
fi

# Copy selected skills (flat into destination — Claude Code expects skill-name/SKILL.md)
mkdir -p "$SKILLS_DEST"
for i in "${selected[@]}"; do
  cp -r "${skill_paths[$i]}" "$SKILLS_DEST/${skill_names[$i]}"
  echo "Installed: ${skill_names[$i]} (${skill_categories[$i]})"
done

echo ""
echo "Done. ${#selected[@]} skill(s) installed to $SKILLS_DEST/"
