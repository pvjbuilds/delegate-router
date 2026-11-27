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
- 2026-11-19 (maintainer): no paid score source, ever. The repo is for anyone on the internet and the
  maintainer does not keep routes current for them; it is a framework in which each user's own agent
  re-checks routes when a lab releases models. AA Pro is out; free-tier gaps get a free fallback.
- 2026-11-20 (maintainer): GPT-6.2 Sol at medium replaces GPT-6.1 Sol in every row, though the bench
  rule alone would keep 6.1 (6.2 medium costs ~$0.02 more per task, both 10/10). GPT-6.2 Astra low
  takes Hard reasoning and Review.
- 2026-11-20: cost per task prices cached input at the cache-hit rate (AA `price_1m_cache_hit_tokens`,
  bench `cached_tokens`); missing data on either side puts both on full rate. The figure is a mean per
  task, and a challenger must pass every task the holder passed. Codex follow-up rounds resume the
  session (SKILL.md).
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
2026-11-20: v1.4.2 released (maintainer's go 2026-11-19): score-source fix.
AA retired `/api/v2/data/llms/models` (410) on 2026-11-04 and `snapshot()` swallowed it, so the
route check judged nothing for two weeks without a word. Now: AA `/api/v2/language/models/free`,
paged; every failure is a `scores:` notice that `ack` keeps. GPT-6.2 Astra medium review, four
rounds (7, 4, 5, 2 findings; all real ones fixed with tests; round 4's two fixes not re-reviewed,
mutation-checked 2/2); README now leads with Jev. Live: 763 AA records. Known limit: AA's free tier has no Terminal-Bench, HLE or (mostly) coding index, so only
Review is judged; a free per-row fallback is a v1.5 candidate. The model list for proposals
comes from Anthropic's public models page, so a model the user can't use (Fable 5.2) can be
proposed. `skills/delegate/SKILL.md` has an uncommitted, maintainer-only edit that must not ship.
2026-11-20: v1.5.0 released (maintainer's go 2026-11-20 01:55, conditional on the review): GPT-6.2
routes, cache-priced cost per task, per-task pass gate, `cached_tokens` in bench (backfilled from
Codex session logs, 60/60 rows), resume for follow-up rounds, README rewritten (Jev first, SEO FAQ),
diagram with a Jev lane. GPT-6.2 Astra medium review, two rounds (9 then 7 findings; round 2 resumed
the round 1 thread, sandbox stayed read-only in both turns). Fixed with tests, mutation-checked
(9/10 then 1/1 after a boundary test; 6/6): a known failure now blocks a partial bench; an
unreadable, blank or impossible cached count is unknown, never zero; unreadable token columns no
longer hide a FAIL row; `tokens()` blanks missing totals; `write_log` upgrades a pre-cached log and
repairs an empty file or a missing final newline; ROUTING.md and README wording matches the gate.
Round 2's fixes were not re-reviewed. Not fixed, on purpose: bench adds `reasoning_output_tokens` to
output (Codex may already count them in `output_tokens`; behaviour since v1.4, historical rows
recorded that way; a v1.6 candidate with a re-bench); concurrent bench runs on a legacy log (no
locking). Live dry-run: Review -> GPT-6.2 Sol high at $0.108 vs $0.261/task; the maintainer pins
Review to Astra in his LOCAL.md.
2026-11-27: v1.6.0 released (maintainer's go 2026-11-27 19:06), from branch `v1.6-fixes`: (1) bench no longer adds
`reasoning_output_tokens` to output: Codex `output_tokens` already include them (total = input + output in
38/38 session logs); the old test expecting the doubled count was wrong. Historical Codex rows in `results.tsv`
still carry the double count (~5% extra output charge); re-bench or backfill is the maintainer's call.
(2) An incomplete catalog never moves a route: an empty read keeps the last good list (and empty lists saved by
v1.5 are cleared), and a model whose catalog CLI is installed but unread is unknown, not gone, so its override
stays and the holder doesn't fail over. Tests use a list without the holder to mean "holder gone". Tests first,
mutation-checked 9/9 (3 misses got a test), GPT-6.2 Astra low review, one round (6 findings: 1 fixed;
deferred: `gone()` guesses the CLI from the model prefix instead of the row's CLI, failover can skip a candidate
whose catalog is unread; known limit: a Codex catalog with every model hidden reads as broken; 1 rejected).
The branch also holds `dbd2482` (Gemini 4 Hydrogen benched, not routed; data only). Live run on throwaway
state 2026-11-27: catalogs codex 10 / agy 10 / claude 23, no drop; same Review proposal as the v1.5 dry-run.
Candidates for v1.7: the two deferred review items above, opt-in auto-update (the background check runs `git pull --ff-only` on new
tagged releases; off by default; needs a cross-provider review), a bench task for long agentic
work, bench hardening (run model CLIs with integrations off, a stronger task 3, record CLI
timeouts apart from check failures), keep custom Codex providers in delegate calls (`--ignore-user-config` drops them today),
a generic "any CLI" delegate row, other main agents.
