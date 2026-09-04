#!/usr/bin/env bash
# Feature path / front-matter helpers.
# shellcheck shell=bash

extract_fm() {
  local file="$1"
  local key="$2"
  awk -v key="$key" '
    BEGIN { in_fm=0 }
    NR==1 && $0=="---" { in_fm=1; next }
    in_fm && $0=="---" { exit }
    in_fm {
      if ($0 ~ ("^" key ":")) {
        sub("^[^:]+:[[:space:]]*", "")
        gsub(/"/, "")
        print
        exit
      }
    }
  ' "$file"
}

resolve_feature_arg() {
  # Sets FEATURE_NAME from $1 or FEATURE env (expects NNN-slug).
  local arg="${1:-${FEATURE:-}}"
  if [[ -z "$arg" ]]; then
    return 1
  fi
  arg="${arg#specs/}"
  arg="${arg%/}"
  if [[ ! "$arg" =~ ^[0-9]{3}-[a-z0-9]+(-[a-z0-9]+)*$ ]]; then
    echo "error: invalid feature id '$arg' (expected NNN-slug)" >&2
    return 2
  fi
  FEATURE_NAME="$arg"
  FEATURE_DIR="${ROOT:-.}/specs/${FEATURE_NAME}"
  return 0
}

is_empty_oq_token() {
  local t
  t="$(echo "$1" | tr '[:upper:]' '[:lower:]' | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
  case "$t" in
    ""|"-"|"none"|"n/a"|"na"|"none remaining"|"none remaining."|"none." ) return 0 ;;
    *) return 1 ;;
  esac
}

# Count unresolved open questions in spec.md + clarify.md. Echo count.
count_open_questions() {
  local feature_dir="$1"
  local spec="$feature_dir/spec.md"
  local clarify="$feature_dir/clarify.md"
  local count=0
  local line in_section=0

  if [[ -f "$spec" ]]; then
    in_section=0
    while IFS= read -r line || [[ -n "$line" ]]; do
      if [[ "$line" =~ ^##[[:space:]]+[Oo]pen[[:space:]]+[Qq]uestions ]]; then
        in_section=1
        continue
      fi
      if [[ "$in_section" -eq 1 && "$line" =~ ^##[[:space:]] ]]; then
        break
      fi
      if [[ "$in_section" -eq 1 && "$line" =~ ^-[[:space:]]+(.*) ]]; then
        local body="${BASH_REMATCH[1]}"
        if ! is_empty_oq_token "$body"; then
          count=$((count + 1))
        fi
      fi
    done <"$spec"
  fi

  if [[ -f "$clarify" ]]; then
    # Table rows with status unresolved
    while IFS= read -r line || [[ -n "$line" ]]; do
      if [[ "$line" =~ ^\| ]]; then
        if echo "$line" | grep -qiE '\|[[:space:]]*unresolved[[:space:]]*\|'; then
          # skip header separator
          if [[ ! "$line" =~ ^\|[[:space:]]*-+ ]]; then
            count=$((count + 1))
          fi
        fi
      fi
    done <"$clarify"

    in_section=0
    while IFS= read -r line || [[ -n "$line" ]]; do
      if [[ "$line" =~ ^##[[:space:]]+[Uu]nresolved[[:space:]]+[Ii]tems ]]; then
        in_section=1
        continue
      fi
      if [[ "$in_section" -eq 1 && "$line" =~ ^##[[:space:]] ]]; then
        break
      fi
      if [[ "$in_section" -eq 1 && "$line" =~ ^-[[:space:]]+(.*) ]]; then
        local body="${BASH_REMATCH[1]}"
        if ! is_empty_oq_token "$body"; then
          count=$((count + 1))
        fi
      fi
    done <"$clarify"
  fi

  echo "$count"
}

checklist_has_unchecked() {
  local file="$1"
  [[ -f "$file" ]] || return 1
  grep -qE '^[[:space:]]*- \[ \] ' "$file"
}
