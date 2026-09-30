#!/usr/bin/env bash
# Interactive setup for delegate-router. Safe to re-run: your earlier answers become the defaults.
#
#   ./install.sh          ask each question (Enter takes the default)
#   ./install.sh --yes    take every default, no questions
#
# It only creates symlinks into this folder and writes one config file. It never edits your
# Claude Code or Codex settings; it prints the optional snippets instead.
set -euo pipefail

REPO="$(cd "$(dirname "$0")" && pwd -P)"
SKILL="$REPO/skills/delegate"
AGENT="$REPO/agents/opus-implementer.md"
CONF_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/delegate-router"
CONF="$CONF_DIR/config.env"
YES=0
[ "${1:-}" = "--yes" ] && YES=1

say() { printf '%s\n' "$*"; }
have() { command -v "$1" >/dev/null 2>&1; }

# ask "question" default(y|n) -> returns 0 for yes. Reads stdin; EOF or Enter takes the default.
ask() {
  local a=""
  if [ "$YES" = 0 ]; then
    if [ "$2" = y ]; then printf '%s [Y/n] ' "$1"; else printf '%s [y/N] ' "$1"; fi
    read -r a || { a=""; say; }
  fi
  case "${a:-$2}" in [Yy]*) return 0 ;; *) return 1 ;; esac
}

# prev KEY default -> the value from an earlier install, else the default
prev() {
  local v=""
  [ -f "$CONF" ] && v="$(sed -n "s/^[[:space:]]*$1[[:space:]]*=[[:space:]]*['\"]\{0,1\}\([01]\)['\"]\{0,1\}[[:space:]]*\$/\1/p" "$CONF" | tail -n 1)"
  printf '%s' "${v:-$2}"
}
yn() { [ "$1" = 1 ] && printf y || printf n; }

# link TARGET PATH: create our symlink; never touch anything that isn't exactly ours
link() {
  local target="$1" path="$2"
  if [ -L "$path" ]; then
    if [ "$(readlink "$path")" = "$target" ]; then say "  ok     $path"
    else say "  SKIP   $path is a symlink to $(readlink "$path"); remove it yourself to use this one"; fi
  elif [ -e "$path" ]; then
    say "  SKIP   $path already exists and isn't ours; move it aside and re-run"
  else
    mkdir -p "$(dirname "$path")"
    ln -s "$target" "$path"
    say "  ok     $path"
  fi
}
unlink_ours() { if [ -L "$2" ] && [ "$(readlink "$2")" = "$1" ]; then rm "$2"; say "  removed $2"; fi; }

say "delegate-router setup"
say

# 1. What's here
have python3 || { say "python3 is required (3.9 or newer). Install it and re-run."; exit 1; }
found=""
for c in claude codex agy uv; do have "$c" && found="$found $c"; done
say "Found on PATH:${found:- nothing}"
have claude || have codex || have agy || say "No delegate CLI found yet (claude, codex, agy). The skill needs at least two agents to route between."
say

# 2. Hosts. A host that isn't on this machine keeps its earlier answer.
cc="$(prev INSTALL_CLAUDE_CODE 1)"; cx="$(prev INSTALL_CODEX 1)"; said_codex=0
if have claude || [ -d "$HOME/.claude" ]; then
  if ask "Install the skill for Claude Code (~/.claude/skills)?" "$(yn "$cc")"; then
    cc=1; link "$SKILL" "$HOME/.claude/skills/delegate"
  else cc=0; unlink_ours "$SKILL" "$HOME/.claude/skills/delegate"; fi
fi
if have codex || [ -d "$HOME/.codex" ]; then
  if ask "Install the skill for Codex CLI (~/.agents/skills)?" "$(yn "$cx")"; then
    cx=1; said_codex=1; link "$SKILL" "$HOME/.agents/skills/delegate"
  else cx=0; unlink_ours "$SKILL" "$HOME/.agents/skills/delegate"; fi
fi
if have claude; then
  say "Claude Opus delegate: installing the opus-implementer agent (used by both hosts)."
  link "$AGENT" "$HOME/.claude/agents/opus-implementer.md"
fi
say

# 3. Choices
bg=0; up=0; jev=0
ask "Check for new model releases in the background (at most every 12 h, when the skill runs)?" "$(yn "$(prev BACKGROUND 1)")" && bg=1
if ask "When a new model is announced, update that CLI and run a one-word read-only probe?" "$(yn "$(prev AUTO_UPDATE_CLI 0)")"; then up=1; fi
say
say "Jev (optional, TypeSafe, paid per call, about \$0.0001 each): judges release notes and"
say "ranks which files a task needs before the spec is written. It sends text to TypeSafe:"
say "only use it on public or low-sensitivity code, never client work, secrets or personal data."
if ask "Turn on Jev?" "$(yn "$(prev JEV 0)")"; then
  jev=1
  have uv || say "  NOTE   Jev runs through uv, which isn't on PATH: https://docs.astral.sh/uv/"
  if [ -n "${TYPESAFE_API_KEY:-}" ]; then
    say "  ok     TYPESAFE_API_KEY is set in this shell"
  elif [ -x /usr/bin/security ] && /usr/bin/security find-generic-password -s TYPESAFE_API_KEY >/dev/null 2>&1; then
    say "  ok     TYPESAFE_API_KEY is in the keychain"
  else
    say "  NOTE   No TYPESAFE_API_KEY yet. Export it, or on macOS store it (you'll be asked for it):"
    say "         security add-generic-password -a \"\$USER\" -s TYPESAFE_API_KEY -w"
    say "         Until then Jev calls fail and the watch just retries on its next run."
  fi
fi

# 4. Config: keep any lines we don't own (e.g. CODEX_BIN). A symlinked config belongs to
# someone else (dotfiles): leave it and its target alone.
mkdir -p "$CONF_DIR"
if [ -L "$CONF" ]; then
  say
  say "  SKIP   $CONF is a symlink; not writing through it. Set these in it yourself:"
  say "         INSTALL_CLAUDE_CODE=$cc INSTALL_CODEX=$cx BACKGROUND=$bg AUTO_UPDATE_CLI=$up JEV=$jev"
else
tmp="$(mktemp "$CONF_DIR/.config.XXXXXX")"
{
  say "# Written by install.sh; re-run it to change these. See config.example.env."
  say "INSTALL_CLAUDE_CODE=$cc"
  say "INSTALL_CODEX=$cx"
  say "BACKGROUND=$bg"
  say "AUTO_UPDATE_CLI=$up"
  say "JEV=$jev"
  [ -f "$CONF" ] && grep -Ev '^[[:space:]]*(#|(INSTALL_CLAUDE_CODE|INSTALL_CODEX|BACKGROUND|AUTO_UPDATE_CLI|JEV)[[:space:]]*=)' "$CONF" || true
} > "$tmp"
mv "$tmp" "$CONF"
say
say "Saved $CONF"
fi

# 5. Optional snippets
if [ "$said_codex" = 1 ] && have claude; then
  say
  say "Codex host: its sandbox blocks network, so the Claude delegate call asks for approval."
  say "Don't approve it (that runs it outside the sandbox). Add this to ~/.codex/config.toml:"
  say
  say "  [sandbox_workspace_write]"
  say "  network_access = true"
fi
say
say "Optional, Claude Code: to see new-model notices at session start, add this to the"
say "\"hooks\" object in ~/.claude/settings.json:"
say
say "  \"SessionStart\": [{\"hooks\": [{\"type\": \"command\","
say "    \"command\": \"python3 '$SKILL/scripts/model_watch.py' status\"}]}]"
say
say "Done. Restart Claude Code or Codex, then ask it to delegate a task, or type /delegate."
say "Update later with: git -C '$REPO' pull"
