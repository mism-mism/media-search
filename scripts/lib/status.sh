#!/usr/bin/env bash
# Shared PASS / FAIL / SKIP status helpers for verify and hooks.
# shellcheck shell=bash

: "${PASSED:=0}"
: "${FAILED:=0}"
: "${SKIPPED:=0}"
: "${VERIFY_FAILED:=0}"

pass() {
  echo "[PASS] $1"
  PASSED=$((PASSED + 1))
}

fail() {
  echo "[FAIL] $1 - $2"
  FAILED=$((FAILED + 1))
  VERIFY_FAILED=1
}

skip() {
  echo "[SKIP] $1 - reason=$2"
  SKIPPED=$((SKIPPED + 1))
}

print_summary() {
  echo
  if [[ "${VERIFY_FAILED}" -eq 0 ]]; then
    echo "Verification: PASSED"
  else
    echo "Verification: FAILED"
  fi
  echo "Passed: ${PASSED}"
  echo "Failed: ${FAILED}"
  echo "Skipped: ${SKIPPED}"
}
