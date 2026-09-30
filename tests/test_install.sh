#!/usr/bin/env bash
# Offline checks for install.sh and uninstall.sh: temp HOME, stub CLIs, nothing outside the temp dir.
#   bash tests/test_install.sh
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd -P)"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT
mkdir -p "$T/bin"
for c in claude codex; do printf '#!/bin/sh\n' > "$T/bin/$c"; chmod +x "$T/bin/$c"; done
export HOME="$T/home" XDG_CONFIG_HOME="$T/home/.config" XDG_STATE_HOME="$T/home/.state"
export PATH="$T/bin:/usr/bin:/bin" TYPESAFE_API_KEY="sk-test-NEVERPRINT"
CONF="$XDG_CONFIG_HOME/delegate-router/config.env"
fail() { echo "FAIL: $*"; exit 1; }
ok() { echo "ok $1"; }

out="$(bash "$REPO/install.sh" --yes)"
[ "$(readlink "$HOME/.claude/skills/delegate")" = "$REPO/skills/delegate" ] || fail "claude link"
[ "$(readlink "$HOME/.agents/skills/delegate")" = "$REPO/skills/delegate" ] || fail "codex link"
[ "$(readlink "$HOME/.claude/agents/opus-implementer.md")" = "$REPO/agents/opus-implementer.md" ] || fail "agent link"
grep -qx BACKGROUND=1 "$CONF" && grep -qx AUTO_UPDATE_CLI=0 "$CONF" && grep -qx JEV=0 "$CONF" || fail "defaults: $(cat "$CONF")"
echo "$out" | grep -q network_access || fail "codex network snippet missing"
ok defaults_link_both_hosts_and_write_safe_config

echo "CODEX_BIN=/opt/codex" >> "$CONF"
# answers: Claude Code, Codex, background, auto-update, Jev
out="$(printf 'y\ny\nn\ny\ny\n' | bash "$REPO/install.sh")"
grep -qx BACKGROUND=0 "$CONF" && grep -qx AUTO_UPDATE_CLI=1 "$CONF" && grep -qx JEV=1 "$CONF" || fail "answers: $(cat "$CONF")"
grep -qx CODEX_BIN=/opt/codex "$CONF" || fail "user line dropped"
case "$out" in *NEVERPRINT*) fail "key printed" ;; esac
echo "$out" | grep -q "TYPESAFE_API_KEY is set" || fail "key presence not reported"
ok answers_are_saved_and_the_key_is_never_printed

bash "$REPO/install.sh" --yes < /dev/null > /dev/null
grep -qx BACKGROUND=0 "$CONF" && grep -qx JEV=1 "$CONF" || fail "re-run lost earlier answers"
[ "$(grep -c '^JEV=' "$CONF")" = 1 ] || fail "duplicate keys"
ok rerun_keeps_earlier_answers

bash "$REPO/uninstall.sh" > /dev/null
rm -f "$HOME/.claude/agents/opus-implementer.md"
mkdir -p "$HOME/.agents/skills/delegate"
echo mine > "$HOME/.agents/skills/delegate/SKILL.md"
ln -s /elsewhere "$HOME/.claude/agents/opus-implementer.md"
out="$(printf 'y\ny\n' | bash "$REPO/install.sh")"
[ "$(cat "$HOME/.agents/skills/delegate/SKILL.md")" = mine ] || fail "clobbered a real folder"
[ "$(readlink "$HOME/.claude/agents/opus-implementer.md")" = /elsewhere ] || fail "clobbered a foreign symlink"
[ "$(echo "$out" | grep -c SKIP)" = 2 ] || fail "skips not reported: $out"
ok never_clobbers_what_isnt_ours

out="$(bash "$REPO/uninstall.sh")"
[ ! -e "$HOME/.claude/skills/delegate" ] || fail "claude link left behind"
[ -d "$HOME/.agents/skills/delegate" ] && [ -L "$HOME/.claude/agents/opus-implementer.md" ] || fail "uninstall removed a foreign path"
[ -f "$CONF" ] || fail "config removed without --purge"
bash "$REPO/uninstall.sh" --purge > /dev/null
[ ! -e "$CONF" ] || fail "--purge kept config"
ok uninstall_removes_only_ours_and_purge_is_opt_in

rm -rf "$HOME"
PATH="$T/nothing:/usr/bin:/bin" bash "$REPO/install.sh" --yes > /dev/null
[ ! -e "$HOME/.claude" ] && [ ! -e "$HOME/.agents" ] || fail "linked a host that isn't installed"
ok no_host_no_links
