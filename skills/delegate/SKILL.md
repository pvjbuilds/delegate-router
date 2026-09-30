---
name: delegate
description: "Hand bulky, already-decided implementation work from the agent you are working in (Claude Code or Codex CLI) to another paid model: Codex (GPT models), Gemini via the Antigravity `agy` CLI, or a Claude Opus subagent. Saves the main session's quota and context. Picks the model from ROUTING.md unless the user names one, and never routes back to the host's own model (except an Opus subagent under an Opus host, which keeps the main context clean). Use for mechanical, large work: scaffolding, boilerplate, repetitive edits across many files, test stubs, docstrings, format conversions, a fully specified function or module, or bulk reading of media and long documents. Also use when the user says /delegate, \"delegate this\", \"send this to Codex/Gemini/Claude\", or \"don't burn tokens on this\". The host always plans, specs and verifies; the delegate only types. Do NOT delegate debugging, architecture, cross-file refactors, security code, anything subtle, or work under ~40 lines."
---

# Delegate

**Host** = the agent running this skill (Claude Code or Codex CLI). **Delegate** = another
model the user also pays for, reached through its own CLI. Each has its own quota.
**Bulk typing happens in the delegate. Thinking happens in the host.**

| Host | Delegate |
| --- | --- |
| Read the codebase, understand the flow | — |
| Decide the design, pick the files | — |
| Write a spec with every decision already made | — |
| — | Type the code / read the media |
| Run it, read the diff, verify | — |
| Fix or re-delegate | — |

**Verification is always the host's.** "Done" from a delegate is not evidence. Run the check,
read the diff, and confirm it did what was asked *and nothing else*.

## 1. Judge: every time, before delegating

Delegating costs the host tokens too: it writes the spec and reads the result.

**Delegate when ALL of these hold:**

1. **Bulk:** roughly 40+ lines of output, the same edit across 3+ files, or a large
   media/document read.
2. **Decided:** no design judgement left. Every choice is in the spec.
3. **Verifiable:** a command proves it worked (a test, a run, a diff check).
4. **Contained:** one file, or files that needn't be reasoned about together.

**Never delegate:**
- Debugging. Root-causing needs the whole picture.
- Architecture, interface design, or naming the rest of the codebase depends on.
- Cross-file refactors whose edits must stay consistent.
- Security, auth, money or trust-boundary code. A strong reviewer may *review* it; no delegate types it.
- Anything under ~40 lines. **The spec would be longer than the code.**
- Anything the user is actively following along with.

**The honest test:** *if writing the spec takes longer than writing the code, write the
code.* Say so in one line and move on.

## 2. Pick the model

1. **Check what's installed and new** (offline itself, under a second; with `BACKGROUND=1` it
   may start a detached online check, at most every 12 h):
   `python3 <this skill's folder>/scripts/model_watch.py status`
   It prints the delegate CLIs on this machine, and any new model release it found. If it
   reports something new, tell the user once in one line, then carry on with the current map.
2. **The user named a model?** Use it. Done.
3. **Otherwise read [ROUTING.md](ROUTING.md)** (same folder) and take the row that matches the
   task. Walk its candidates in order and take the first one that is **installed** and is
   **not the host's own model**. One exception: under an Opus host, the `opus-implementer`
   subagent is allowed, because it keeps file reads and tool turns out of the main context.
   Don't route from memory.

## 2b. Scout before the spec (optional, needs Jev)

Only when `JEV=1` in `~/.config/delegate-router/config.env`. Otherwise skip this step.

**When:** the task's files aren't named yet, and about 5+ candidate files would otherwise be
read just to find the ones that matter.

**Data gate:** scouting sends file paths and contents to TypeSafe. Only public or
low-sensitivity code. **Never** client work, secrets or config, credentials, personal data.

```bash
cd <repo> && rg -l <term> | uv run --quiet <this skill's folder>/scripts/jev.py scout "<the task in one sentence>" --top 15
```

1. **Read only the top files** needed to design the spec, plus files the task names, and any
   `skipped:` or `(cut)` file that could matter. **A low score is not proof.**
2. **Put the confirmed file list in the spec**: "Read only these files: …; don't explore
   beyond them unless one imports something you need."
3. **Verification never uses Jev.** Read the full diff yourself.

## 3. Run it

Write the spec to a temp file first (`packet.md`) and pass it in. **Never print a delegate's
full output into the host's context**: read its short summary and the diff.

### Codex (`codex exec`): agent mode, edits real files

```bash
codex exec -m <model> -c model_reasoning_effort=<effort> \
  --ignore-user-config --ignore-rules -c features.apps=false \
  -s workspace-write -C <repo> -o <tmp>/delegate-out.md \
  "$(cat <tmp>/packet.md)" < /dev/null
```

- **Always pass `-m` and the effort.** Codex's own default model may not be the one you want.
- **Isolation flags.** The sandbox confines shell commands, not integrations, and a packet
  can carry injected instructions. `--ignore-user-config` skips your `config.toml` (and the
  MCP servers set there), `--ignore-rules` skips execpolicy rules that could allow a command
  outside the sandbox, and `features.apps=false` turns off apps, which are on by default.
  Plugins and admin-managed config can still apply. Login still works; it isn't in that file.
- **`-o`** writes only the final message to a file. **`< /dev/null`** prevents a stdin hang.
- **Sandbox:** `workspace-write` to implement, `read-only` to review. Never full access, never
  a `--dangerously-bypass-*` flag.
- Outside a git repo, add `--skip-git-repo-check`.
- **Put this in every packet:** "Do not remove or weaken any existing test." Codex's sandbox
  has no network by default, and some models delete tests they can't run or try workarounds
  when access is denied.
- Run it in the background when the host allows it.

### Gemini (`agy -p`): plan mode, text out

```bash
mkdir -p <tmp>/handoff && cd <tmp>/handoff && \
  agy -p "$(cat <tmp>/packet.md)" --model <model> --sandbox --mode plan \
  < /dev/null > <tmp>/gemini-out.txt 2> <tmp>/gemini-err.txt
```

- **Input files:** copy only the files it needs into the handoff folder, name them in the
  prompt, delete the copies afterwards. File content goes to Google.
- **Code output:** end the spec with "Output ONLY code, no markdown fences, no commentary".
  Strip fences anyway, then write the result to the target file with a short script.
- `agy -p` is an agent with tools. `--mode plan` stops it editing and `--sandbox` restricts its
  terminal. The handoff folder only decides what it is pointed at: **it is not a read
  boundary**, and `agy` has no switch to turn off your integrations. Send it only packets you
  wrote, never untrusted text. Use its text output only; it doesn't generate images.

### Claude: the `opus-implementer` subagent

- **Host is Claude Code:** use the Agent tool with `subagent_type: "opus-implementer"` and the
  full spec. **Don't pass `model`**: a per-call model overrides the agent definition
  (Opus at medium effort). It spends Claude quota; what it saves is the host's context.
  It runs with **the host session's own permissions**, not a separate sandbox: the same
  prompts and rules as if the host did the edit. For OS-level confinement, turn on Claude
  Code's sandbox (`/sandbox`).
- **Host is Codex:** run it as a CLI from the repo root. If the Codex session is sandboxed
  (`workspace-write`, not full access), the call runs inside that sandbox and inherits its
  write limits:

  ```bash
  cd <repo> && claude -p --agent opus-implementer --permission-mode acceptEdits \
    "$(cat <tmp>/packet.md)" < /dev/null > <tmp>/claude-out.md
  ```

  Codex's sandbox blocks network by default. **Don't approve the escalation**: an approved
  command runs outside the sandbox. Set `network_access = true` in `~/.codex/config.toml`
  instead (see the README), which keeps the sandbox. Without network, `claude` reports
  "Not logged in".
- A user hook that writes outside the repo (a cache, a log) fails inside Codex's sandbox and
  can block the prompt while `claude` still exits 0. Check `claude-out.md`, not the exit code.
  If a hook is the cause, add `--settings '{"disableAllHooks":true}'` for this call only.
- The agent reports back **only** the files changed and the check result, not the code.
- **Claude as a read-only reviewer** (either host): no command tools, no user settings or MCP,
  file tools confined to the repo:

  ```bash
  cd <repo> && claude -p --restricted --strict-mcp-config --tools "Read,Grep,Glob" \
    --model claude-opus-5-5 --effort medium --permission-mode plan --no-session-persistence \
    "$(cat <tmp>/packet.md)" < /dev/null > <tmp>/review.md
  ```

## 4. Write the spec

Decisions already made. Name the file, the function, the imports, and what must not change.

Bad, because it needs judgement the delegate doesn't have:
> Add caching to the API layer.

Good, because it is mechanical:
> In `src/api/fetch.py`, wrap `get_user` in `functools.lru_cache(maxsize=512)`. Add
> `import functools` with the other stdlib imports. Change nothing else in the file.

Always end with the scope fence **"Change nothing else."**

## 5. The loop

1. **Judge.** Apply the four gates. If any fails, write the code in the host and say why in one line.
2. **Pick.** The user's named model, otherwise ROUTING.md (installed, not the host).
3. **Scout** (only with Jev on, when 2b applies).
4. **Spec.** Include the scope fence. For Codex, add the test-safety line.
5. **Run.** On failure or quota-out, fall through to the next candidate; don't retry the same model.
6. **Verify.** Run the check. Read the diff. Confirm the scope was respected.
7. **Report.** Tell the user what went to which model, what came back and what needed fixing.
   Never present unverified output as done.

If the output is wrong, decide once: re-delegate with a tighter spec, or fix it in the host.
A second failure means the task wasn't delegable.

**Cost note:** report the saving when it's material, e.g. "~200 lines typed on Codex quota;
this session paid for the spec and the review." Don't claim a saving when the spec and
review cost as much as the code would have.
