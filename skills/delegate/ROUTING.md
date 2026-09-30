# Routing map: which model gets which task

Snapshot: 2026-09-30

The delegate skill reads this file to pick a model. Benchmarks are a prior, not proof: **a
check run on the actual task beats any benchmark.** Route by neutral benchmarks, don't run
trial calls to confirm them, and switch only when real output disappoints.

`git pull` in the repo brings a newer snapshot. `model_watch.py status` says when this file
is more than 60 days old or when your CLIs list a model it doesn't cover yet.

## How to read a row

Walk the candidates in order and take the first one that:

1. **is installed** (`model_watch.py status` lists the CLIs), and
2. **is not the host's own model.** Same model, same quota: no gain. One exception: inside
   Claude Code, the `opus-implementer` subagent is allowed even when the host is Opus,
   because it keeps the file reads and tool turns out of the main context.

Other models on the host's subscription are allowed (a Codex host may send trivial edits to
a cheaper Codex model), but they draw on the same quota.

If nothing in a row qualifies, the host does the work itself.

## Default route

| Task | Candidates, in order | CLI and model ID | Effort |
|---|---|---|---|
| **Bulk code** from a written spec: new module, boilerplate, test stubs, many-file mechanical edits | 1. GPT-6.1 Sol<br>2. Claude Opus 5.5 | `codex` · `gpt-6.1-sol`<br>`opus-implementer` · `claude-opus-5-5` | high<br>medium |
| **Must be right**: correctness matters more than quota, terminal-heavy agent work, or a spec the first pick already failed | 1. Claude Opus 5.5<br>2. GPT-6.1 Sol | `opus-implementer` · `claude-opus-5-5`<br>`codex` · `gpt-6.1-sol` | medium<br>high |
| **Trivial edits**: reformatting, renames, mechanical find-and-replace | 1. GPT-6 Luna<br>2. Claude Opus 5.5 | `codex` · `gpt-6-luna`<br>`opus-implementer` · `claude-opus-5-5` | medium<br>medium |
| **Media and long reads**: images, PDF, video, audio, long documents | 1. Gemini 3.8 Flash<br>2. Claude Opus 5.5 | `agy` · `gemini-3.8-flash-high`<br>`opus-implementer` · `claude-opus-5-5` | (in the ID)<br>medium |
| **Single-file text** with no repo access: a conversion, a fixture, a draft | 1. Gemini 3.8 Flash<br>2. GPT-6.1 Sol | `agy` · `gemini-3.8-flash-high`<br>`codex` · `gpt-6.1-sol` | (in the ID)<br>medium |
| **Hard reasoning**: maths, proofs, algorithms, science, very large documents | 1. GPT-6 Astra | `codex` · `gpt-6-astra` | low, raise only if needed |
| **Review**: security review, second opinion on a design or a diff | 1. GPT-6 Astra (read-only)<br>2. Claude Opus 5.5 (read-only) | `codex -s read-only` · `gpt-6-astra`<br>`claude -p --permission-mode plan` | low<br>medium |

**Quota out.** A usage-limit error usually names its reset time. Say it in one line and fall
through to the next candidate; don't stall. If a CLI call fails, report that model as
missing, never quietly drop it.

## Why these picks

In our own words; the numbers live on the trackers linked at the bottom.

- **GPT-6.1 Sol** is the default typist. On independent intelligence indexes it lands close to
  Opus at medium effort for a fraction of the cost per task, and it runs on the Codex plan's
  separate quota. Good enough for fully specified packets. After a failed run, escalate to
  Opus rather than retrying Sol.
- **Claude Opus 5.5 at medium effort** is the must-be-right choice and the fallback for
  everything. It leads on agentic tool use and production software engineering. Medium is its
  knee: each step up costs much more per point gained.
- **Claude Sonnet 5.5 is not routed.** It is cheaper per token but uses far more tokens, so it
  costs more per task at equal quality. **Compare cost per task, not price per token.**
- **GPT-6 Astra** leads on maths, science, abstract reasoning, very long-context retrieval and
  security work. It is slow and expensive, so it gets hard problems and reviews, not bulk typing.
- **Gemini 3.8 Flash** is fast and cheap, and strong at video and other media. It is weak at
  multi-step agent work, so it only runs in completion mode: text in, text out.
- **GPT-6 Luna** is very cheap and fast but clearly weaker. Mechanical edits only.
- **Not routed:** Claude Haiku 4.5 (last in every field), Claude Fable 5.1 (Opus 5.5 scores
  higher and costs less), older GPT and Gemini tiers.

## Rules

- **High effort is the ceiling for a delegate.** xhigh and max buy a few points at 2–3× the
  cost per task.
- **Reviewers run read-only.** A packet can carry injected instructions; only an implementer
  gets write access.
- **Caveats to put in every packet:**
  - Codex models: "Do not remove or weaken any existing test." Some GPT models try
    workarounds when access is denied, and Codex's sandbox has no network by default.
  - Gemini: reads media, but does not generate images, has no shell and cannot edit files.
- **Handoff overhead** (writing the spec, reading the report and the diff) is real. Worth it for
  another quota pool or for keeping the host's context clean; not worth it to move work to a
  model that costs more per task.

## When two models disagree (council)

1. **Blind first.** The reviewer gets the artifact and what it must satisfy, never the host's
   conclusion.
2. **Adversarial prompt:** "Find what is wrong. Don't validate. If nothing is wrong after a
   thorough look, say so explicitly."
3. **Classify each finding:** the brief was unclear → real, fix it → real trade-off, the user
   decides → noise.
4. **Tiebreak:** a benchmark lead settles it only if the question sits squarely in that
   model's lead area **and** the gap is bigger than the error bar. Otherwise run a check on
   the real task, or take it to the user.
5. **Three rounds at most**, then the user decides.

## Keeping this current

- **For users:** `git pull`. The watch (`model_watch.py`) tells you when a release lands before
  this file catches up. With `AUTO_UPDATE_CLI=1` it also updates the CLI and proves the model
  answers.
- **Release notes the watch reads:** the Codex changelog, OpenAI news, Anthropic's release
  notes, the Claude Code changelog and Google's Gemini API changelog. Plan access is decided by
  the vendor's own wording ("available in Codex and ChatGPT", "for Pro subscribers").
- **For the maintainer, on a new model (~15 min):**
  1. Confirm plan access in the vendor's release notes.
  2. Re-read the trackers below for every model in the table, not just the new one.
  3. Redo the route table and "Why these picks". Bump the snapshot date.
  4. For a new Opus, update `model:` in `agents/opus-implementer.md`.
  5. Commit, then run `model_watch.py ack`.

**Trackers**, in order of trust: [Artificial Analysis](https://artificialanalysis.ai) (runs its
own evals, publishes cost per task) · [BenchLM](https://benchlm.ai) (per-field scores, shows
uncertainty) · [llm-stats](https://llm-stats.com). Vendor launch posts pick favourable benchmarks.
