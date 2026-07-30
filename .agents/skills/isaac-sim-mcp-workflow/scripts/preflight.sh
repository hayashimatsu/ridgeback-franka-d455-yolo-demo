#!/usr/bin/env bash
set -eu

profile_path="${1:-PROJECT_PROFILE.md}"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

command -v claude >/dev/null 2>&1 || fail "claude CLI is not available"
command -v uv >/dev/null 2>&1 || fail "uv is not available"
test -f "$profile_path" || fail "$profile_path is missing"

if grep -q 'REPLACE_ME' "$profile_path"; then
  fail "$profile_path still contains REPLACE_ME placeholders"
fi

server_output="$(claude mcp get isaac-sim 2>&1)" || {
  printf '%s\n' "$server_output" >&2
  fail "Claude Code cannot resolve the isaac-sim MCP server"
}

printf '%s\n' "$server_output"
printf '%s\n' "$server_output" | grep -q 'Connected' || {
  fail "the isaac-sim MCP server is registered but not connected"
}
printf 'PASS: local project profile and Claude Code MCP registration are ready.\n'
printf 'NOTE: confirm the active stage and timeline inside Isaac Sim before mutation.\n'
