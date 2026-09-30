review_mode: cross-provider (2026-09-30, decided by the maintainer)

# Shared Project Contract

**Read at entry:** [Project](#project), [Current state](#current-state) and the relevant
[Decisions](#decisions-and-assumptions) before substantive work. If your machine-level
instructions name a cross-project rules file, read it too.

**Verify** with the offline suite before claiming a change works:
`python3 tests/test_model_watch.py && bash tests/test_install.sh`, plus
`uv run -q tests/test_jev.py && uv run -q tests/test_scout.py` when `jev.py` changes.

**Review:** cross-provider. A change to the installer, the watcher's update/probe path, or the
Jev data handling gets a read-only review from a model of another provider before release.

**Update this file** when a decision is made or the state moves. Keep it short.

## Project

delegate-router: an agent skill for Claude Code and Codex CLI that hands bulk, decided work to
another model the user already pays for, picked from `skills/delegate/ROUTING.md`.

- `skills/delegate/SKILL.md`: the skill, host-neutral.
- `skills/delegate/ROUTING.md`: the task-to-model map. `Snapshot:` line is parsed by the watcher.
- `skills/delegate/scripts/model_watch.py`: update path. Must run on Python 3.9 (macOS system).
- `skills/delegate/scripts/jev.py`: optional Jev ask + scout (PEP 723, run with uv).
- `agents/opus-implementer.md`: Claude Opus subagent used by both hosts.
- `install.sh` / `uninstall.sh`: interactive setup; symlinks only, never clobbers.
- `docs/workflow.json`: archify source for the README diagram.

## Decisions and assumptions

- 2026-09-30: Clone + `install.sh`, not a plugin, for v1: plugins can't ask setup questions.
  The layout stays plugin-ready.
- 2026-09-30: No launchd/systemd job. The 12 h background check is started by
  `model_watch.py status` when the skill runs; a machine that never delegates needs no alerts.
- 2026-09-30: ROUTING.md gives reasons in its own words and links the trackers; no benchmark
  figures are copied from them.
- 2026-09-30: The installer prints the Codex `network_access` and SessionStart hook snippets
  instead of editing user settings.
- Verified live 2026-09-30: `agy -p --model <slug> --sandbox` and the `claude -p
  --setting-sources ""` probe both answer `ok`; a Codex host (workspace-write + network_access)
  runs `claude -p --agent opus-implementer` and the file lands. Without network, claude says
  "Not logged in". User hooks that write outside the repo can block it inside the sandbox.

## Current state

2026-09-30: v1.0.0 in preparation, private. Astra medium review, three rounds (the maximum):
round 1, 13 findings; round 2, 4 new plus partial fixes; round 3, 4 more. All fixed, round 3's
in the commit after `7b2e9c1` (installer skips a config it didn't write; each fetch has a
total deadline and a timed-out updater's children are killed; Codex delegates and probes also
run `--ignore-rules -c features.apps=false`; stricter probe stubs). Round 3's fixes have not
been reviewed by another model.
Documented limits: a Claude Code host's subagent has the host's permissions; `agy` has no
integrations switch; Codex plugins and admin config still apply; `*_BIN` is watcher-only;
`status` may start the 12 h check.
Not yet done: tag, public flip (needs the maintainer's go on the SHA).
