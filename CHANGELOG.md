# Changelog

## v1.4.1 (2026-11-01)

**Docs**
- The README diagram shows another subscription first and the bench that gates route changes.
- README: install with an AI agent, which model a Codex host picks, how this differs from
  OpenRouter or LiteLLM; FAQ entries are headings, so they can be linked.
- `docs/social-preview.png` for the GitHub social preview.

## v1.4.0 (2026-11-01)

**Changed**
- Routing prefers a model on another of your subscriptions (OpenAI via `codex`, Anthropic via
  `claude`/`opus-implementer`, Google via `agy`), so delegated work spreads across your plans.
  It falls back to the host's plan only when no other is installed, and says so. Must be right
  and Trivial edits keep their plain order. A `LOCAL.md` can turn this off.
- Each route is judged on the score that fits it: coding index (Terminal-Bench v4 while AA
  publishes none) for code, Terminal-Bench v4 for Must be right, HLE for Hard reasoning, the
  intelligence index for Review.
- Cost is cost per task, measured: the tokens each model spent on `bench/` at its input and
  output prices. Only a measured run is applied. An unbenched model is proposed only if it scores
  higher and costs no more per token, and the alert says its cost per task is not measured.
- Without an AA key, BenchLM only proposes models the bench already passed.

## v1.3.1 (2026-11-01)

**Fixed**
- The route check no longer proposes the holder's own model at a higher effort. AA's price per
  token is the same at every effort, so such a change always looked free; it costs 2-3x per task.
- `watch.log` says "no aa coding score" instead of "no aa record" when a model has a record but
  no score on the row's index.

## v1.3.0 (2026-11-01)

**Added**
- Routes that keep themselves current: the 12 h check re-checks the Default route rows against
  a fresh benchmark snapshot (Artificial Analysis with an optional key, else BenchLM) and
  alerts when a model your CLIs list beats a holder. `AUTO_ROUTE=1` applies benched changes;
  `model_watch.py routes` prints only the route lines. README: "Routes that keep themselves
  current".
- Bulk code now routes to GPT-6.1 Terra at medium first, GPT-6.1 Sol at high second.

## v1.2.0 (2026-10-27)

**Added**
- Your own rules: the skill reads `~/.config/delegate-router/LOCAL.md` (or under
  `$XDG_CONFIG_HOME`) first when it exists, and where it disagrees with SKILL.md or
  ROUTING.md, it wins. It sits outside the repo, so `git pull` never touches it. README:
  "Your own rules".

**Fixed**
- `uninstall.sh --purge` deleted the whole config folder. It now removes `config.env` and the
  state folder and keeps `LOCAL.md`. The install test covers both.

## v1.1.0 (2026-10-27)

**Added**
- `bench/`: a routine-task bench for the maintainer. `bench.py` runs one model CLI (`codex`,
  `claude` or `agy`) on ten tasks; a hidden check grades a temp copy of each result, and pass,
  seconds and tokens go to `bench/results.tsv`. `--selfcheck` proves the checks of tasks 6–10
  fail on the untouched files and pass on a reference answer, with no model call. `--task N` runs one task.
- Tasks 6 to 10 are hard on purpose: a bug fix whose causes sit in other files, a `git bisect`
  where some commits can't run, reading a table and a chart from a screenshot, a long
  version-range spec (73 hidden cases), and a signature change through indirect calls.
- An image route: screenshots, scanned pages and charts go to GPT-6.1 Terra (`codex exec -i`),
  with Gemini 3.8 Flash as fallback.

**Changed**
- ROUTING.md: benchmarks pick a new model's first route; the bench decides whether it keeps it.
  This replaces "don't run trial calls to confirm them".
- ROUTING.md lists Claude Haiku 5.5 (`claude-haiku-5-5`) as not routed, replacing Haiku 4.5,
  and names GPT-6.1 Terra, so the watcher counts both as covered.
- The offline check now includes `python3 bench/bench.py --selfcheck`.

**Bench result, 2026-10-27:** GPT-6.1 Sol high and GPT-6.1 Terra medium both passed 10/10.
Code stays with Sol: the bench doesn't yet test the long agentic work where trackers put Sol
ahead.

## v1.0.1 (2026-09-30)

- README requirements line and keywords.

## v1.0.0 (2026-09-30)

- First public release: the delegate skill, ROUTING.md, `model_watch.py`, optional Jev scout,
  `opus-implementer` agent, `install.sh` and `uninstall.sh`.
