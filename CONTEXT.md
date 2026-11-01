review_mode: cross-provider (2026-09-30, decided by the maintainer)

# Shared Project Contract

**Read at entry:** [Project](#project), [Current state](#current-state) and the relevant
[Decisions](#decisions-and-assumptions) before substantive work. If your machine-level
instructions name a cross-project rules file, read it too.

**Verify** with the offline suite before claiming a change works:
`python3 tests/test_model_watch.py && bash tests/test_install.sh && python3 bench/bench.py --selfcheck`, plus
`uv run -q tests/test_jev.py && uv run -q tests/test_scout.py` when `jev.py` changes.
Before asking the maintainer for a release go on a `model_watch.py` change, also run it live
on throwaway state and read the alerts (the offline suite missed two flaws on 2026-11-01):
`S=$(mktemp -d); DELEGATE_ROUTER_STATE=$S AUTO_UPDATE_CLI=0 BACKGROUND=0 python3 skills/delegate/scripts/model_watch.py run; DELEGATE_ROUTER_STATE=$S BACKGROUND=0 python3 skills/delegate/scripts/model_watch.py routes`

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
- `bench/`: routine-task bench. `bench.py` runs a model CLI on a temp copy of each task's
  `work/`; a hidden `check/check.py` grades it; rows go to `results.tsv`. `ref/` holds a
  reference answer so `--selfcheck` can prove each check fails untouched and passes on it.

## Decisions and assumptions

- 2026-09-30: Clone + `install.sh`, not a plugin, for v1: plugins can't ask setup questions.
  The layout stays plugin-ready.
- 2026-09-30: No launchd/systemd job. The 12 h background check is started by
  `model_watch.py status` when the skill runs; a machine that never delegates needs no alerts.
- 2026-09-30: ROUTING.md gives reasons in its own words and links the trackers; no benchmark
  figures are copied from them.
- 2026-10-27: The maintainer replaced "don't run trial calls" with: benchmarks pick a new
  model's first route, then it runs the bench against the route's current holder first.
- 2026-10-27: Terra medium tied Sol high on the bench (10/10, fewer tokens). The maintainer
  kept code on Sol. The bench section in the README is maintainer-only and names no token cost.
- 2026-10-27: One installed copy. Anything only one user wants (paths, effort limits, data
  gates, figures) lives in their `LOCAL.md`, never in the repo; it wins over SKILL.md and
  ROUTING.md. The installer never creates or edits it.
- 2026-11-01: Routes are re-checked by the 12 h check. A challenger must dominate the holder
  within one snapshot; tie margin 1% (the maintainer's choice). Figures stay in state, never in
  the repo. The Artificial Analysis key is optional; the BenchLM fallback only proposes.
  `AUTO_ROUTE` defaults to 0.
- 2026-11-01 (v1.4.0, maintainer's picks): each route has its own benchmark (code: coding index,
  else Terminal-Bench v4; Must be right: Terminal-Bench v4; Hard reasoning: HLE; Review:
  intelligence index). Cost is cost per task measured on `bench/` tokens x AA input/output
  prices; only measured runs apply. Unbenched proposals need a higher score at no more per-token
  price and say cost per task is not measured. The AA API has no cost-per-task or token fields.
- 2026-11-01: Another subscription first (maintainer, public repo): a row's first installed
  candidate on a plan other than the host's wins; the host's plan only when none is installed.
  Must be right and Trivial edits keep plain order. The maintainer's own `LOCAL.md` turns it off.
- 2026-09-30: The installer prints the Codex `network_access` and SessionStart hook snippets
  instead of editing user settings.
- Verified live 2026-09-30: `agy -p --model <slug> --sandbox` and the `claude -p
  --setting-sources ""` probe both answer `ok`; a Codex host (workspace-write + network_access)
  runs `claude -p --agent opus-implementer` and the file lands. Without network, claude says
  "Not logged in". User hooks that write outside the repo can block it inside the sandbox.

## Current state

2026-09-30: v1.0.0 released, public; v1.0.1 the same day, README and this file only
(requirements line, keywords). Astra medium review, three rounds (the maximum), all
findings fixed; round 3's fixes were not re-reviewed by another model. The maintainer kept
the history and accepted the documented limits: a Claude Code host's subagent has the host's
permissions; `agy` has no integrations switch; Codex plugins and admin config still apply;
`*_BIN` is watcher-only; `status` may start the 12 h check.
2026-10-27: v1.1.0 prepared: `bench/` (10 tasks with `--selfcheck`), an image route
(GPT-6.1 Terra), Claude Haiku 5.5 listed as not routed, the bench rule in ROUTING.md.
2026-10-27: v1.2.0 released (tagged 2026-11-01): one installed copy. The maintainer's `~/.claude/skills/delegate`
links to this repo; a user's own rules go in `~/.config/delegate-router/LOCAL.md`, which the
skill reads first and which wins; `uninstall.sh --purge` keeps it.
2026-11-01: v1.3.0 released: route re-check (`AUTO_ROUTE`, `routes`), Terra
first for Bulk code. GPT-6 Astra low review, two rounds (12 then 8 findings); real ones fixed
with tests; round 2's three fixes not re-reviewed. Kept by design: falling back to the ROUTING.md
default needs no bench; an installed but signed-out CLI still counts; an applied route's figures
refresh only when it changes.
2026-11-01: v1.3.1 released: first live AA run (719 records). The holder's own model at another
effort is no longer a challenger. AA publishes no coding index today, so Bulk code and Trivial
edits are skipped (logged) until it does; the reasoning rows are judged.
2026-11-01: v1.4.0 released: another subscription first; per-row benchmarks and bench-measured
cost per task (see Decisions).
Not reviewed by another model. Live AA dry-run: three proposals (Hard reasoning, Review,
Trivial edits), nothing applied.
2026-11-01: v1.4.1 released, docs only: diagram re-rendered (archify, `docs/workflow.json`; PNGs are
playwright crops of the light/dark views), README FAQ as headings, install-with-an-agent prompt,
GitHub release pages for v1.2.0-v1.4.1, new description, social preview uploaded (Praj). Public-repo
checklist (search and agents): vault RULES §11.
Candidates for v1.5: opt-in auto-update (the background check runs `git pull --ff-only` on new
tagged releases; off by default; needs a cross-provider review), a bench task for long agentic
work, bench hardening (run model CLIs with integrations off, a stronger task 3, record CLI
timeouts apart from check failures), keep custom Codex providers in delegate calls (`--ignore-user-config` drops them today),
a generic "any CLI" delegate row, other main agents.
