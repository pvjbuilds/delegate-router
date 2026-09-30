"""Offline checks for model_watch.py: stub CLIs, local pages, temp state, no network, no spend.

    python3 tests/test_model_watch.py
"""
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time

REPO = pathlib.Path(__file__).resolve().parent.parent
tmp = pathlib.Path(tempfile.mkdtemp())
skill = tmp / "skill"
(skill / "scripts").mkdir(parents=True)
shutil.copy(REPO / "skills/delegate/scripts/model_watch.py", skill / "scripts")
SCRIPT = skill / "scripts/model_watch.py"
bindir = tmp / "bin"
cask = tmp / "Caskroom/codex/1.0"
for d in (bindir, cask):
    d.mkdir(parents=True)
calls = tmp / "calls.log"
notes = tmp / "notes.html"
page = tmp / "models.html"


def stub(path, body):
    path.write_text("#!/bin/sh\n" + body)
    path.chmod(0o755)
    return str(path)


# Codex lists gpt-6.2-sol only after "brew upgrade" ran; its probe reply comes from PROBE_REPLY.
CODEX = stub(cask / "codex", f"""echo codex "$@" >> {calls}
if [ "$1" = debug ]; then
  if grep -q brew {calls}; then echo '{{"models":[{{"slug":"gpt-6.2-sol","visibility":"list"}},{{"slug":"gpt-6-sol","visibility":"list"}}]}}'
  else echo '{{"models":[{{"slug":"gpt-6-sol","visibility":"list"}},{{"slug":"gpt-hidden","visibility":"hide"}}]}}'; fi
else case "$*" in *"-s read-only"*--ignore-user-config*--ignore-rules*features.apps=false*) r="${{PROBE_REPLY:-ok}}";; *) r=unsafe;; esac
  while [ "$1" != -o ]; do shift; done; echo "$r" > "$2"; fi
""")
stub(bindir / "brew", f'echo brew "$@" >> {calls}\nsleep "${{BREW_SLEEP:-0}}"\n')
AGY = stub(bindir / "agy", f"""echo agy "$@" >> {calls}
if [ "$1" = -p ]; then case "$*" in *"--sandbox --mode plan"*) echo ok;; *) echo unsafe;; esac; exit; fi
printf 'gemini-3.8-flash-high\\tGemini 3.8 Flash (High)\\n'
printf 'rm -rf ~;echo\\tEvil\\n'
""")
CLAUDE = stub(bindir / "claude", f"""echo claude "$@" >> {calls}
case "$*" in *"--tools  --strict-mcp-config --setting-sources  --no-session-persistence"*) echo ok;; *) echo unsafe;; esac
""")  # a probe passes only with the isolation flags; an empty value shows as a double space
JEV = stub(bindir / "jev", f"""echo jev >> {calls}
i=0; while read -r l; do echo "{{\\"i\\": $i, \\"new_model\\": ${{JEV_SCORE:-0.9}}}}"; i=$((i+1)); done
""")
BASE = {**os.environ, "PATH": f"{bindir}:/usr/bin:/bin", "DELEGATE_ROUTER_STATE": str(tmp / "state"),
        "DELEGATE_ROUTER_CONFIG": str(tmp / "config.env"), "DELEGATE_ROUTER_NOTES": notes.as_uri(),
        "DELEGATE_ROUTER_CLAUDE_URL": page.as_uri(), "DELEGATE_ROUTER_JEV": JEV,
        "CODEX_BIN": CODEX, "AGY_BIN": AGY, "CLAUDE_BIN": CLAUDE, "BACKGROUND": "0"}
ON = {"JEV": "1", "AUTO_UPDATE_CLI": "1"}


def watch(*args, **env):
    r = subprocess.run([sys.executable, str(SCRIPT), *args], env={**BASE, **env}, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return r.stdout


def fresh(routing="Snapshot: 2099-01-01\n"):
    shutil.rmtree(tmp / "state", ignore_errors=True)
    calls.unlink(missing_ok=True)
    (skill / "ROUTING.md").write_text(routing)
    page.write_text("<code>claude-opus-5-5</code>")
    notes.write_text("<h2>GPT-6.1 Sol</h2><p>gpt-6.1-sol is now the default.</p>")
    watch("run", **ON)  # first run: catalogs are taken as known, pages only seed the baseline
    assert "jev" not in calls.read_text()


def announce(text):
    notes.write_text(text + "<p>gpt-6.1-sol is now the default.</p>")


def test_first_run_is_quiet_and_lists_installed_clis():
    fresh()
    out = watch("status")
    assert "installed CLIs: claude, codex, agy" in out, out
    assert "NEW" not in out and "new in your" not in out, out


def test_release_is_confirmed_updated_and_probed_read_only():
    fresh()
    announce("<p>gpt-6.2-sol is available in Codex for Plus and Pro.</p>")
    watch("run", **ON)
    log = calls.read_text()
    assert log.count("jev") == 1 and "brew upgrade --cask codex" in log, log
    assert "exec -m gpt-6.2-sol -s read-only --skip-git-repo-check --ignore-user-config --ignore-rules --ephemeral" in log, log
    out = watch("status")
    assert "NEW RELEASE gpt-6.2-sol (codex): probe passed (updated)" in out, out
    watch("run", **ON)
    assert calls.read_text().count("jev") == 1  # never asked twice
    watch("ack")
    assert "gpt-6.2-sol" not in watch("status")


def test_probe_needs_exactly_ok():
    fresh()
    announce("<p>gpt-6.2-sol is available in Codex.</p>")
    watch("run", PROBE_REPLY="ok, and I also ran rm", **ON)
    assert "probe failed" in watch("status")


def test_rejected_name_is_asked_again_only_when_its_text_changes():
    fresh()
    announce("<p>gpt-6.2-sol is coming to the API next quarter.</p>")
    watch("run", JEV_SCORE="0.1", **ON)
    watch("run", JEV_SCORE="0.1", **ON)
    log = calls.read_text()
    assert log.count("jev") == 1 and "brew" not in log, log
    assert "gpt-6.2-sol" not in watch("status")
    announce("<p>gpt-6.2-sol is now available in Codex for Plus and Pro.</p>")
    watch("run", **ON)
    assert calls.read_text().count("jev") == 2 and "brew upgrade" in calls.read_text()


def test_jev_outage_retries_next_run():
    fresh()
    announce("<p>gpt-6.2-sol is available in Codex.</p>")
    watch("run", DELEGATE_ROUTER_JEV="/nonexistent", **ON)
    assert "brew" not in calls.read_text()
    watch("run", **ON)
    assert "brew upgrade" in calls.read_text()


def test_defaults_record_the_lead_without_jev_updates_or_probes():
    fresh()
    announce("<p>gpt-6.2-sol is available in Codex.</p>")
    watch("run")
    log = calls.read_text()
    assert "jev" not in log and "brew" not in log and "exec" not in log, log
    assert "gpt-6.2-sol (codex): seen in release notes, not probed" in watch("status")


def test_unknown_install_channel_is_never_updated():
    fresh()
    plain = stub(bindir / "codex", open(CODEX).read().split("\n", 1)[1])
    announce("<p>gpt-6.2-sol is available in Codex.</p>")
    watch("run", CODEX_BIN=plain, **ON)
    assert "brew" not in calls.read_text()
    assert "unknown install channel" in watch("status")


def test_other_providers_update_themselves_and_probe_with_isolation_flags():
    fresh()
    page.write_text("<code>claude-opus-5-5</code>")
    announce("<p>claude-opus-6 and gemini-3.8-flash are available to Pro subscribers.</p>")
    watch("run", **ON)
    log = calls.read_text()
    assert "claude update" in log and "agy update" in log, log
    assert "claude -p --model claude-opus-6 --tools  --strict-mcp-config" in log, log
    assert "agy -p Reply with exactly: ok --model gemini-3.8-flash-high --sandbox --mode plan" in log, log
    out = watch("status")
    assert "claude-opus-6 (claude): probe passed" in out and "gemini-3.8-flash (agy): probe passed" in out, out


def test_unsafe_names_from_a_cli_are_never_printed():
    fresh()
    out = watch("status")
    assert "rm -rf" not in out and "evil" not in out.lower(), out
    assert "gemini-3.8-flash-high" not in out  # known since the first run


def test_new_catalog_model_is_flagged_until_acked():
    fresh()
    page.write_text("<code>claude-opus-5-5</code> <code>claude-opus-6</code>")
    watch("run")
    out = watch("status")
    assert "not in ROUTING.md yet: claude-opus-6" in out and " ack" in out, out
    watch("ack")
    assert "claude-opus-6" not in watch("status")


def test_stale_map_is_reported():
    fresh(routing="Snapshot: 2020-01-01\n")
    assert "days old" in watch("status")


def test_status_stays_offline_and_background_can_be_switched_off():
    fresh()
    state = json.loads((tmp / "state/state.json").read_text())
    state["last_run"] = 0
    (tmp / "state/state.json").write_text(json.dumps(state))
    calls.unlink()
    watch("status")
    time.sleep(1)
    assert not calls.exists()  # BACKGROUND=0: no detached run, no CLI or network calls
    watch("status", BACKGROUND="1")
    for _ in range(50):
        if calls.exists() and "debug models" in calls.read_text():
            break
        time.sleep(0.1)
    assert "debug models" in calls.read_text()  # the detached run happened


def test_scheduled_run_skips_when_a_recent_run_exists():
    fresh()
    calls.unlink()
    watch("run", "--if-due")
    assert not calls.exists()  # the first run was seconds ago
    state = json.loads((tmp / "state/state.json").read_text())
    state["last_run"] = 0
    (tmp / "state/state.json").write_text(json.dumps(state))
    watch("run", "--if-due")
    assert "debug models" in calls.read_text()


def test_run_stops_at_its_budget():
    fresh()
    announce("<p>gpt-6.2-sol and gpt-6.3-luna are available in Codex.</p>")
    t = time.time()
    watch("run", BREW_SLEEP="5", DELEGATE_ROUTER_BUDGET="1", **ON)
    assert time.time() - t < 4, "the update ran past the budget"
    assert "exec -m" not in calls.read_text()  # no probe started after the budget ran out


def test_nothing_goes_online_after_the_deadline():
    calls.unlink(missing_ok=True)
    os.environ.update({k: BASE[k] for k in ("DELEGATE_ROUTER_STATE", "DELEGATE_ROUTER_CONFIG", "DELEGATE_ROUTER_JEV")})
    sys.path.insert(0, str(SCRIPT.parent))
    import model_watch as mw
    import urllib.request
    opened = []
    real, urllib.request.urlopen = urllib.request.urlopen, lambda *a, **k: opened.append(a)
    try:
        mw.DEADLINE[0] = time.time() - 1
        assert mw.claude_catalog() is None and mw.ask_jev([{"text": "x"}]) is None
    finally:
        urllib.request.urlopen, mw.DEADLINE[0] = real, float("inf")
    assert not opened, "a page was fetched after the deadline"
    assert "jev" not in (calls.read_text() if calls.exists() else ""), "Jev was asked after the deadline"


def test_a_slow_page_is_cut_off_at_the_deadline():
    import socket
    import threading
    sys.path.insert(0, str(SCRIPT.parent))
    import model_watch as mw
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)

    def drip():
        c = srv.accept()[0]
        c.sendall(b"HTTP/1.0 200 OK\r\n\r\n")
        try:
            for _ in range(100):  # 5 s of one byte every 50 ms
                c.sendall(b"x")
                time.sleep(0.05)
        except OSError:
            pass
        c.close()
    threading.Thread(target=drip, daemon=True).start()
    mw.DEADLINE[0] = time.time() + 0.3
    t = time.time()
    try:
        mw.fetch("http://127.0.0.1:{}/".format(srv.getsockname()[1]))
    except Exception:
        pass
    finally:
        mw.DEADLINE[0] = float("inf")
    assert time.time() - t < 1.5, "a dripping page outlived the deadline"


def test_a_timed_out_update_leaves_no_children_behind():
    fresh()
    announce("<p>gpt-6.2-sol is available in Codex.</p>")
    watch("run", BREW_SLEEP="7.25", DELEGATE_ROUTER_BUDGET="1", **ON)
    time.sleep(0.3)
    left = subprocess.run(["pgrep", "-f", "sleep 7.25"], capture_output=True, text=True).stdout
    assert not left.strip(), "the updater's child outlived the run"


def test_config_file_is_read_and_env_wins():
    fresh()
    (tmp / "config.env").write_text("# comment\nJEV=1\nAUTO_UPDATE_CLI='1'\n")
    try:
        announce("<p>gpt-6.2-sol is available in Codex.</p>")
        watch("run", JEV_SCORE="0.1")
        assert "jev" in calls.read_text() and "brew" not in calls.read_text()
        announce("<p>gpt-6.3-sol is available in Codex.</p>")
        watch("run", JEV="0")
        assert calls.read_text().count("jev") == 1
    finally:
        (tmp / "config.env").unlink()


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
