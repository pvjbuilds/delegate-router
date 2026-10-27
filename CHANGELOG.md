# Changelog

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
