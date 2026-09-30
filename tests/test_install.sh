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

printf 'y\nn\n' | bash "$REPO/install.sh" > /dev/null  # keep Claude Code, decline Codex
[ ! -e "$HOME/.agents/skills/delegate" ] || fail "declined Codex is still linked"
bash "$REPO/install.sh" --yes < /dev/null > /dev/null
[ ! -e "$HOME/.agents/skills/delegate" ] || fail "--yes re-linked a declined host"
grep -qx INSTALL_CODEX=0 "$CONF" || fail "host answer not saved: $(cat "$CONF")"
printf 'y\ny\n' | bash "$REPO/install.sh" > /dev/null
ok host_answers_are_remembered

printf 'BACKGROUND = 0\n' >> "$CONF"  # the watcher accepts spaces around =
printf 'y\ny\ny\n' | bash "$REPO/install.sh" > /dev/null
[ "$(grep -c BACKGROUND "$CONF")" = 1 ] && grep -qx BACKGROUND=1 "$CONF" || fail "spaced key survived: $(cat "$CONF")"
rm "$CONF" && printf '# mine\nBACKGROUND=0\n' > "$T/dotfiles.env" && ln -s "$T/dotfiles.env" "$CONF"
out="$(bash "$REPO/install.sh" --yes < /dev/null)"
[ -L "$CONF" ] && [ "$(cat "$T/dotfiles.env")" = "$(printf '# mine\nBACKGROUND=0')" ] || fail "config symlink target was modified"
echo "$out" | grep -q "SKIP.*$CONF" || fail "no SKIP for a symlinked config: $out"
rm "$CONF" && printf '# hand-written\nBACKGROUND=0\n' > "$CONF"
out="$(bash "$REPO/install.sh" --yes < /dev/null)"
[ "$(cat "$CONF")" = "$(printf '# hand-written\nBACKGROUND=0')" ] || fail "a config we didn't write was rewritten"
echo "$out" | grep -q "SKIP.*$CONF" || fail "no SKIP for a foreign config: $out"
rm "$CONF"
bash "$REPO/install.sh" --yes < /dev/null > /dev/null
ok config_spelling_is_normalised_and_a_config_we_didnt_write_is_left_alone

bash "$REPO/uninstall.sh" > /dev/null
rm -f "$HOME/.claude/agents/opus-implementer.md"
mkdir -p "$HOME/.agents/skills/delegate"
echo mine > "$HOME/.agents/skills/delegate/SKILL.md"
ln -s /elsewhere "$HOME/.claude/agents/opus-implementer.md"
ln -s "$REPO/../elsewhere" "$HOME/.claude/skills/delegate"  # inside-looking, but not our target
out="$(printf 'y\ny\n' | bash "$REPO/install.sh")"
[ "$(cat "$HOME/.agents/skills/delegate/SKILL.md")" = mine ] || fail "clobbered a real folder"
[ "$(readlink "$HOME/.claude/agents/opus-implementer.md")" = /elsewhere ] || fail "clobbered a foreign symlink"
[ "$(readlink "$HOME/.claude/skills/delegate")" = "$REPO/../elsewhere" ] || fail "replaced a link that only looked like ours"
[ "$(echo "$out" | grep -c SKIP)" = 3 ] || fail "skips not reported: $out"
ok never_clobbers_what_isnt_ours

bash "$REPO/uninstall.sh" > /dev/null
[ -L "$HOME/.claude/skills/delegate" ] || fail "uninstall removed a link that only looked like ours"
rm "$HOME/.claude/skills/delegate"
printf 'y\ny\n' | bash "$REPO/install.sh" > /dev/null
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
