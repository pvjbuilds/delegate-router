#!/usr/bin/env python3
"""Routine-task bench: run one model on every task, check each result, log pass, time and tokens.

Each task is tasks/<name>/{prompt.md, work/, check/check.py}, plus optional prep.py (builds state
the model starts from, e.g. a git repo) and ref/ (a reference answer: files copied over the work
copy, or ref/solve.py). The model only ever sees a temp copy of work/; check.py gets that copy's
path and fails by raising. Images (*.png, *.jpg) in work/ are attached for Codex with -i.
Rows go to results.tsv. CLIs are found on PATH, or set CODEX_BIN, CLAUDE_BIN, AGY_BIN.
"""
import argparse, json, os, shutil, subprocess, sys, tempfile, time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent
IMAGES = ("*.png", "*.jpg", "*.jpeg")


def binary(cli):
    path = os.environ.get(cli.upper() + "_BIN") or shutil.which(cli)
    if not path:
        sys.exit(f"{cli} not found: put it on PATH or set {cli.upper()}_BIN")
    return path


def command(cli, model, effort, prompt, cwd):
    if cli == "codex":
        images = [a for img in sorted(p for g in IMAGES for p in Path(cwd).glob(g)) for a in ("-i", str(img))]
        return [binary(cli), "exec", *images, "-m", model, "-c", f"model_reasoning_effort={effort}",
                "-s", "workspace-write", "-C", cwd, "--skip-git-repo-check", "--json", prompt]
    if cli == "claude":
        # shortcut: Bash is limited to git and python3, enough for the current tasks; widen it if a task needs more.
        return [binary(cli), "-p", "--model", model, "--effort", effort, "--output-format", "json",
                "--permission-mode", "acceptEdits", "--allowedTools", "Bash(git:*) Bash(python3:*)", prompt]
    return [binary(cli), "-p", prompt, "--model", model, "--sandbox"]


def tokens(stdout):
    """(input incl. cached, output) from the last usage object the CLI printed; agy prints none."""
    usage = None
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict) and isinstance(event.get("usage"), dict):
            usage = event["usage"]
    if not usage:
        return "", ""
    inp = usage.get("input_tokens", 0) + usage.get("cache_read_input_tokens", 0) + usage.get("cache_creation_input_tokens", 0)
    return inp, usage.get("output_tokens", 0) + usage.get("reasoning_output_tokens", 0)


def setup(task, tmp):
    shutil.copytree(task / "work", tmp, dirs_exist_ok=True)
    if (task / "prep.py").exists():
        subprocess.run([sys.executable, "-I", task / "prep.py", tmp], check=True, capture_output=True)


def check(task, tmp):
    return subprocess.run([sys.executable, "-I", task / "check/check.py", tmp], capture_output=True, text=True)


def tasks(only):
    found = sorted((t for t in (HERE / "tasks").iterdir() if t.is_dir()), key=lambda t: int(t.name.split("-")[0]))
    return [t for t in found if not only or t.name in only or t.name.split("-")[0] in only]


def run(cli, model, effort, only):
    rows = []
    for task in tasks(only):
        with tempfile.TemporaryDirectory() as tmp:
            setup(task, tmp)
            start = time.time()
            try:
                out = subprocess.run(command(cli, model, effort, (task / "prompt.md").read_text(), tmp),
                                     cwd=tmp, capture_output=True, text=True, timeout=600, stdin=subprocess.DEVNULL).stdout
            except subprocess.TimeoutExpired:
                out = ""
            secs = round(time.time() - start)
            result = check(task, tmp)
            ok = "PASS" if result.returncode == 0 else "FAIL"
            inp, outp = tokens(out)
            rows.append([datetime.now().strftime("%Y-%m-%d %H:%M"), cli, model, effort, task.name, ok, secs, inp, outp])
            print("\t".join(map(str, rows[-1][4:])), result.stderr.strip().splitlines()[-1:] if ok == "FAIL" else "", flush=True)
    log = HERE / "results.tsv"
    new = not log.exists()
    with log.open("a") as f:
        if new:
            f.write("date\tcli\tmodel\teffort\ttask\tresult\tseconds\tinput_tokens\toutput_tokens\n")
        f.writelines("\t".join(map(str, r)) + "\n" for r in rows)
    passed = sum(r[5] == "PASS" for r in rows)
    print(f"{model} {effort}: {passed}/{len(rows)} passed, {sum(r[6] for r in rows)} s")


def selfcheck(only):
    """A task is sound when its check fails on the untouched work and passes on the reference."""
    bad = 0
    for task in tasks(only):
        if not (task / "ref").exists():
            print(f"{task.name}\tno ref/, skipped")
            continue
        with tempfile.TemporaryDirectory() as tmp:
            setup(task, tmp)
            untouched = check(task, tmp).returncode != 0
            if (task / "ref/solve.py").exists():
                subprocess.run([sys.executable, "-I", task / "ref/solve.py", tmp], check=True, capture_output=True)
            else:
                shutil.copytree(task / "ref", tmp, dirs_exist_ok=True)
            result = check(task, tmp)
            ok = untouched and result.returncode == 0
            bad += not ok
            print(f"{task.name}\tuntouched {'fails' if untouched else 'PASSES (bad)'}\tref {'passes' if result.returncode == 0 else 'FAILS (bad)'}",
                  result.stderr.strip().splitlines()[-1:] if result.returncode else "")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cli", nargs="?", choices=["codex", "claude", "agy"])
    ap.add_argument("model", nargs="?", help="model ID as the CLI takes it, e.g. gpt-6.1-sol")
    ap.add_argument("effort", nargs="?", default="medium")
    ap.add_argument("--task", action="append", help="run only this task (name or number); repeatable")
    ap.add_argument("--selfcheck", action="store_true", help="prove each check fails untouched and passes on ref/; runs no model")
    a = ap.parse_args()
    if a.selfcheck:
        selfcheck(a.task)
    if not a.model:
        ap.error("cli and model are required")
    run(a.cli, a.model, a.effort, a.task)
