#!/usr/bin/env bash
# Resolve changed files and feature directories from git diff.
# Compatible with bash 3.2 (macOS).
# shellcheck shell=bash

MAIN_BRANCH="${MAIN_BRANCH:-main}"

list_changed_files() {
  local base="" head="HEAD"
  if [[ -n "${BASE_SHA:-}" ]]; then
    if [[ "${BASE_SHA}" =~ ^0+$ ]]; then
      # Invalid push base (e.g. first commit): empty diff scope
      return 0
    fi
    base="${BASE_SHA}"
    head="${HEAD_SHA:-HEAD}"
    git diff --name-only "${base}...${head}" 2>/dev/null && return 0
  fi

  if [[ -n "${GITHUB_BASE_REF:-}" ]] && git rev-parse --verify "origin/${GITHUB_BASE_REF}" >/dev/null 2>&1; then
    git diff --name-only "origin/${GITHUB_BASE_REF}...HEAD" 2>/dev/null && return 0
  fi

  if git rev-parse --verify "origin/${MAIN_BRANCH}" >/dev/null 2>&1; then
    git diff --name-only "origin/${MAIN_BRANCH}...HEAD" 2>/dev/null && return 0
  fi

  if git rev-parse --verify "${MAIN_BRANCH}" >/dev/null 2>&1; then
    git diff --name-only "${MAIN_BRANCH}...HEAD" 2>/dev/null && return 0
  fi

  if git rev-parse --verify HEAD >/dev/null 2>&1; then
    {
      git diff --name-only HEAD
      git diff --name-only --cached
      git ls-files --others --exclude-standard
    } | sort -u
    return 0
  fi

  git ls-files --others --exclude-standard 2>/dev/null | sort -u
}

# Echo unique feature directory names (NNN-slug) touched under specs/
resolve_features_from_changed_files() {
  local f feat
  local out=""
  while IFS= read -r f || [[ -n "$f" ]]; do
    [[ -z "$f" ]] && continue
    case "$f" in
      specs/[0-9][0-9][0-9]-*)
        feat="${f#specs/}"
        feat="${feat%%/*}"
        case "$feat" in
          [0-9][0-9][0-9]-*)
            case " $out " in
              *" $feat "*) ;;
              *)
                out="$out $feat"
                echo "$feat"
                ;;
            esac
            ;;
        esac
        ;;
    esac
  done
}

# Return 0 if path is explicitly spec-exempt (A1').
path_is_spec_exempt() {
  local p="$1"
  case "$p" in
    README|README.md|README.*) return 0 ;;
    CLAUDE.md|GEMINI.md) return 0 ;;
    .gitignore|.gitattributes|.editorconfig) return 0 ;;
    LICENSE|LICENSE.md|LICENSE.*) return 0 ;;
    .github/copilot-instructions.md) return 0 ;;
    .github/pull_request_template.md) return 0 ;;
    docs/REFERENCES.md|docs/PRODUCT.md|docs/DOMAIN.md|docs/GLOSSARY.md) return 0 ;;
  esac
  case "$p" in
    .cursor/*) return 0 ;;
    metrics/*) return 0 ;;
    docs/adr/*) return 0 ;;
    docs/_templates/*) return 0 ;;
    specs/_template/*) return 0 ;;
    specs/README.md) return 0 ;;
    harness/logs/*) return 0 ;;
  esac
  return 1
}

# Return 0 if any changed file requires a feature spec (not exempt).
changed_files_require_spec() {
  local f
  while IFS= read -r f || [[ -n "$f" ]]; do
    [[ -z "$f" ]] && continue
    case "$f" in
      specs/[0-9][0-9][0-9]-*) continue ;;
    esac
    if ! path_is_spec_exempt "$f"; then
      return 0
    fi
  done
  return 1
}

constitution_changed() {
  local f
  while IFS= read -r f || [[ -n "$f" ]]; do
    [[ "$f" == "CONSTITUTION.md" ]] && return 0
  done
  return 1
}

# Return 0 if BASE_SHA is missing/zero (no valid diff base for push health).
base_sha_is_invalid() {
  local b="${BASE_SHA:-}"
  [[ -z "$b" ]] && return 1
  [[ "$b" =~ ^0+$ ]] && return 0
  return 1
}

# stdin: changed files. Args: feature name.
# Return 0 if every changed path is under specs/<feat>/ or harness/reviews/<feat>/.
# Return 1 if empty input or any other path present.
is_draft_feature_spec_only() {
  local feat="$1"
  local f
  local any=0
  while IFS= read -r f || [[ -n "$f" ]]; do
    [[ -z "$f" ]] && continue
    any=1
    case "$f" in
      specs/"$feat"/*|specs/"$feat") continue ;;
      harness/reviews/"$feat"/*|harness/reviews/"$feat") continue ;;
      *) return 1 ;;
    esac
  done
  [[ "$any" -eq 1 ]]
}
