#!/usr/bin/env bash
# Removes delegate-router's symlinks. Your config and the watch state stay unless you pass --purge.
# Your own rules (LOCAL.md in the config folder) always stay.
set -euo pipefail

REPO="$(cd "$(dirname "$0")" && pwd -P)"
for pair in "skills/delegate:$HOME/.claude/skills/delegate" "skills/delegate:$HOME/.agents/skills/delegate" \
            "agents/opus-implementer.md:$HOME/.claude/agents/opus-implementer.md"; do
  target="$REPO/${pair%%:*}" path="${pair#*:}"
  if [ -L "$path" ]; then
    if [ "$(readlink "$path")" = "$target" ]; then rm "$path"; echo "removed $path"
    else echo "left    $path (not ours)"; fi
  fi
done
if [ "${1:-}" = "--purge" ]; then
  CONF_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/delegate-router"
  rm -f "$CONF_DIR/config.env"
  rmdir "$CONF_DIR" 2>/dev/null || true
  rm -rf "${XDG_STATE_HOME:-$HOME/.local/state}/delegate-router"
  echo "removed config and state"
  [ -e "$CONF_DIR/LOCAL.md" ] && echo "kept    $CONF_DIR/LOCAL.md (your own rules)"
  true
fi
