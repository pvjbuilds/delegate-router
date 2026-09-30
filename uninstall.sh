#!/usr/bin/env bash
# Removes delegate-router's symlinks. Your config and the watch state stay unless you pass --purge.
set -euo pipefail

REPO="$(cd "$(dirname "$0")" && pwd -P)"
for path in "$HOME/.claude/skills/delegate" "$HOME/.agents/skills/delegate" \
            "$HOME/.claude/agents/opus-implementer.md"; do
  if [ -L "$path" ]; then
    case "$(readlink "$path")" in
      "$REPO"/*) rm "$path"; echo "removed $path" ;;
      *) echo "left    $path (not ours)" ;;
    esac
  fi
done
if [ "${1:-}" = "--purge" ]; then
  rm -rf "${XDG_CONFIG_HOME:-$HOME/.config}/delegate-router" "${XDG_STATE_HOME:-$HOME/.local/state}/delegate-router"
  echo "removed config and state"
fi
