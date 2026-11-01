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
aa = tmp / "aa.json"
benchlm = tmp / "benchlm.json"
bench = tmp / "results.tsv"


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
        "CODEX_BIN": CODEX, "AGY_BIN": AGY, "CLAUDE_BIN": CLAUDE, "BACKGROUND": "0",
        "ARTIFICIAL_ANALYSIS_API_KEY": "", "DELEGATE_ROUTER_AA_URL": aa.as_uri(),
        "DELEGATE_ROUTER_BENCHLM_URL": benchlm.as_uri(), "DELEGATE_ROUTER_BENCH": str(bench)}
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


# --- routes: ROUTING.md rows re-checked against a benchmark snapshot ---
TABLE = """Snapshot: 2099-01-01
| Task | Candidates | CLI and model ID | Effort |
|---|---|---|---|
| **Bulk code** from a spec | 1. Sol<br>2. Opus | `codex` · `gpt-6-sol`<br>`opus-implementer` · `claude-opus-5-5` | high<br>medium |
| **Images**: files | 1. Flash | `agy` · `gemini-3.8-flash-high` | (in the ID) |
"""
KEY = {"ARTIFICIAL_ANALYSIS_API_KEY": "SECRET"}


def scores(rows, x=1.0):
    """rows: slug -> (coding, price). Intelligence index is fixed so only coding decides."""
    aa.write_text(json.dumps({"data": [{"slug": s, "evaluations": {"artificial_analysis_coding_index": c * x,
                  "artificial_analysis_intelligence_index": 50 * x}, "pricing": {"price_1m_blended_3_to_1": p,
                  "price_1m_input_tokens": p, "price_1m_output_tokens": p}}
                  for s, (c, p) in rows.items()]}))


def benched(*models):
    bench.write_text("date\tcli\tmodel\teffort\ttask\tresult\tseconds\tinput_tokens\toutput_tokens\n" + "".join(
        "2026-11-01\tcodex\t{}\t{}\t{}\tPASS\t1\t100\t1\n".format(m, e, t) for m, e in models for t in ("1", "2")))


def routes(rows, page_models="", bench_rows=(("gpt-6-sol", "high"),), **env):
    bench.unlink(missing_ok=True)
    if bench_rows:
        benched(*bench_rows)
    scores(rows)
    page_text = "<code>claude-opus-5-5</code>" + page_models
    shutil.rmtree(tmp / "state", ignore_errors=True)
    (skill / "ROUTING.md").write_text(TABLE)
    page.write_text(page_text)
    notes.write_text("")
    watch("run", **{**KEY, **env})
    return watch("routes", **env)


def test_rescale_alone_changes_no_route():
    rows = {"gpt-6-sol-high": (70, 10), "claude-opus-6-medium": (69, 20)}
    out = routes(rows, "<code>claude-opus-6</code>")
    assert "ROUTE" not in out, out
    scores(rows, 0.8)
    watch("run", **KEY)
    out = watch("status")
    assert "ROUTE" not in out and out.count("scores rescaled (median x0.8") == 1, out
    assert "0 change(s)" in out, out


def test_dominating_benched_model_is_applied():
    out = routes({"gpt-6-sol-high": (70, 10), "claude-opus-6-medium": (75, 10)}, "<code>claude-opus-6</code>",
                 (("gpt-6-sol", "high"), ("claude-opus-6", "medium")), AUTO_ROUTE="1")
    assert "ROUTE Bulk code: gpt-6-sol high -> claude-opus-6 medium (applied). coding index 75" in out, out
    assert "/task vs $" in out and "/1M" not in out, out


def test_unbenched_or_auto_off_is_only_proposed():
    rows = {"gpt-6-sol-high": (70, 10), "claude-opus-6-medium": (75, 10)}
    out = routes(rows, "<code>claude-opus-6</code>", AUTO_ROUTE="1")
    assert "-> claude-opus-6 medium (proposed)" in out and "Bench it: python3 bench/bench.py claude claude-opus-6 medium" in out, out
    out = routes(rows, "<code>claude-opus-6</code>", (("gpt-6-sol", "high"), ("claude-opus-6", "medium")))
    assert "-> claude-opus-6 medium (proposed)" in out and "Bench it" not in out, out


def test_the_holders_own_model_at_another_effort_is_never_a_challenger():
    # price per token is the same at every effort, so an effort change can't be judged on it
    out = routes({"gpt-6-sol-high": (70, 10), "gpt-6-sol-medium": (72, 10)}, bench_rows=(("gpt-6-sol", "high"), ("gpt-6-sol", "medium")), AUTO_ROUTE="1")
    assert "ROUTE" not in out, out


def test_tie_margin_is_one_percent_on_a_measured_cheaper_run():
    both = (("gpt-6-sol", "high"), ("claude-opus-6", "medium"))
    assert "(proposed)" in routes({"gpt-6-sol-high": (70, 10), "claude-opus-6-medium": (69.4, 9)}, "<code>claude-opus-6</code>", both)
    assert "ROUTE" not in routes({"gpt-6-sol-high": (70, 10), "claude-opus-6-medium": (68.9, 9)}, "<code>claude-opus-6</code>", both)
    assert "ROUTE" not in routes({"gpt-6-sol-high": (70, 10), "claude-opus-6-medium": (69.4, 9)}, "<code>claude-opus-6</code>")


def test_an_unbenched_challenger_must_be_no_dearer_per_token_and_claims_no_cost_per_task():
    out = routes({"gpt-6-sol-high": (70, 10), "claude-opus-6-medium": (75, 5)}, "<code>claude-opus-6</code>", AUTO_ROUTE="1")
    assert "(proposed). coding index 75 vs 70, $5/1M vs $10/1M per token, cost per task not measured" in out, out
    assert "ROUTE" not in routes({"gpt-6-sol-high": (70, 10), "claude-opus-6-medium": (95, 11)}, "<code>claude-opus-6</code>")


def test_cost_per_task_comes_from_bench_tokens():
    # cheaper per token, but three times the tokens on our bench: costlier per task, so no change
    tsv([("gpt-6-sol", "high", t, 100) for t in "12"] + [("claude-opus-6", "medium", t, 300) for t in "12"])
    out = again({"gpt-6-sol-high": (70, 10), "claude-opus-6-medium": (75, 5)}, AUTO_ROUTE="1")
    assert "ROUTE" not in out, out
    tsv([("gpt-6-sol", "high", t, 100) for t in "12"] + [("claude-opus-6", "medium", t, 150) for t in "12"])
    out = again({"gpt-6-sol-high": (70, 10), "claude-opus-6-medium": (75, 5)}, AUTO_ROUTE="1")
    assert "-> claude-opus-6 medium (applied). coding index 75 vs 70, $0.0015/task vs $0.002/task" in out, out


def test_each_row_is_judged_on_its_own_benchmark():
    (skill / "ROUTING.md").write_text(TABLE + "| **Hard reasoning**: maths | 1. Sol | `codex` · `gpt-6-sol` | high |\n")
    ev = lambda t, h, i: {"terminalbench_v4_0": t, "hle": h, "artificial_analysis_intelligence_index": i}  # noqa: E731
    aa.write_text(json.dumps({"data": [
        {"slug": "gpt-6-sol-high", "evaluations": ev(0.3, 0.5, 50), "pricing": {"price_1m_blended_3_to_1": 10}},
        {"slug": "claude-opus-6-medium", "evaluations": ev(0.4, 0.6, 40), "pricing": {"price_1m_blended_3_to_1": 10}}]}))
    shutil.rmtree(tmp / "state", ignore_errors=True)
    page.write_text("<code>claude-opus-5-5</code><code>claude-opus-6</code>")
    notes.write_text("")
    watch("run", **KEY)
    out = watch("routes")
    assert "ROUTE Bulk code: gpt-6-sol high -> claude-opus-6 medium (proposed). Terminal-Bench v4 0.4 vs 0.3" in out, out
    assert "ROUTE Hard reasoning: gpt-6-sol high -> claude-opus-6 medium (proposed). HLE 0.6 vs 0.5" in out, out


def test_xhigh_max_and_uncatalogued_models_are_never_picked():
    out = routes({"gpt-6-sol-high": (70, 10), "claude-opus-6-xhigh": (90, 1), "claude-opus-6-max": (95, 1),
                  "gpt-9-nova-high": (99, 1)}, "<code>claude-opus-6</code>")
    assert "ROUTE" not in out, out


def test_holder_gone_from_catalogs_moves_the_next_candidate_up():
    out = routes({"gpt-6-sol-high": (70, 10)}, CODEX_BIN=stub(bindir / "codex2", 'echo \'{"models":[]}\'\n'))
    assert "ROUTE Bulk code: gpt-6-sol high -> claude-opus-5-5 medium (applied)" in out, out


def test_without_a_key_benchlm_only_proposes():
    benchlm.write_text(json.dumps({"items": [{"slug": "gpt-6-sol", "scores": {"displayCategoryScores": {"coding": 70}}},
                                             {"slug": "claude-opus-6", "scores": {"displayCategoryScores": {"coding": 80}}}]}))
    out = routes({}, "<code>claude-opus-6</code>", (("gpt-6-sol", "high"), ("claude-opus-6", "high")),
                 ARTIFICIAL_ANALYSIS_API_KEY="", AUTO_ROUTE="1")
    assert "-> claude-opus-6 high (proposed). coding 80" in out and "no price data" in out, out
    out = routes({}, "<code>claude-opus-6</code>", ARTIFICIAL_ANALYSIS_API_KEY="")
    assert "ROUTE" not in out, out  # no prices and no bench run: nothing to stand on


def test_failed_snapshot_keeps_the_last_one_and_never_shows_the_key():
    routes({"gpt-6-sol-high": (70, 10), "claude-opus-6-medium": (75, 10)}, "<code>claude-opus-6</code>")
    before = json.loads((tmp / "state/state.json").read_text())["snapshot"]
    aa.write_text("not json")
    out = watch("run", **KEY) + watch("status", **KEY)
    out += watch("run", DELEGATE_ROUTER_AA_URL=(tmp / "missing.json").as_uri(), **KEY)
    assert json.loads((tmp / "state/state.json").read_text())["snapshot"] == before
    assert out.count("ROUTE") == 1 and "SECRET" not in out, out
    log = tmp / "state/watch.log"
    assert "SECRET" not in (log.read_text() if log.exists() else "")


def test_routes_prints_only_route_lines_offline():
    out = routes({"gpt-6-sol-high": (70, 10), "claude-opus-6-medium": (75, 10)}, "<code>claude-opus-6</code>")
    calls.unlink(missing_ok=True)
    assert all(line.startswith("delegate-router: ROUTE") for line in out.splitlines()) and out, out
    assert "installed CLIs" not in watch("routes") and not calls.exists()
    watch("ack")
    assert "ROUTE" not in watch("routes")


def test_routing_md_is_never_written():
    routes({"gpt-6-sol-high": (70, 10), "claude-opus-6-medium": (75, 10)}, "<code>claude-opus-6</code>",
           (("gpt-6-sol", "high"), ("claude-opus-6", "medium")), AUTO_ROUTE="1")
    assert (skill / "ROUTING.md").read_text() == TABLE


def tsv(rows):
    """rows: (model, effort, task, tokens) -> results.tsv, every task PASS."""
    bench.write_text("date\tcli\tmodel\teffort\ttask\tresult\tseconds\tinput_tokens\toutput_tokens\n" + "".join(
        "d\tc\t{}\t{}\t{}\tPASS\t1\t{}\t{}\n".format(m, e, t, k, "" if k == "" else 0) for m, e, t, k in rows))


def mw_module():
    sys.path.insert(0, str(SCRIPT.parent))
    import model_watch as mw
    mw.BENCH = bench
    return mw


def again(rows, **env):
    scores(rows)
    watch("run", **{**KEY, **env})
    return watch("routes", **env)


def test_aa_key_is_never_sent_over_http_or_through_a_redirect():
    import http.server
    import threading
    seen = []

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            seen.append((self.path, self.headers.get("x-api-key")))
            if self.path == "/hop":
                self.send_response(302)
                self.send_header("Location", "/target")
                self.end_headers()
            else:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"data": []}')

        def log_message(self, *a):
            pass
    srv = http.server.HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = "http://127.0.0.1:{}".format(srv.server_port)
    mw = mw_module()
    try:
        mw.fetch(base + "/hop", {"x-api-key": "k"}, redirects=False)
    except Exception:
        pass
    assert [p for p, _ in seen] == ["/hop"], seen  # the redirect was not followed
    seen.clear()
    routes({"gpt-6-sol-high": (70, 10)}, DELEGATE_ROUTER_AA_URL=base + "/hop")
    assert all(k is None for _, k in seen), seen
    srv.shutdown()


def test_applied_override_is_the_holder_and_its_bench_gate():
    tsv([("gpt-6-sol", "high", t, 101) for t in "12"] + [("claude-opus-6", "medium", t, 50) for t in "12"]
        + [("claude-opus-7", "medium", t, 80) for t in "12"])
    scores({"gpt-6-sol-high": (70, 10), "claude-opus-6-medium": (75, 10)})
    shutil.rmtree(tmp / "state", ignore_errors=True)
    (skill / "ROUTING.md").write_text(TABLE)
    page.write_text("<code>claude-opus-5-5</code><code>claude-opus-6</code><code>claude-opus-7</code>")
    notes.write_text("")
    watch("run", AUTO_ROUTE="1", **KEY)
    out = again({"gpt-6-sol-high": (70, 10), "claude-opus-6-medium": (75, 10), "claude-opus-7-medium": (80, 10)},
                AUTO_ROUTE="1")
    assert "-> claude-opus-6 medium (applied)" in out, out
    assert "claude-opus-7" not in out, out  # scores higher but costs more per task on our bench
    out = again({"gpt-6-sol-high": (76, 10), "claude-opus-6-medium": (75, 25)}, AUTO_ROUTE="1")
    assert "override claude-opus-6 medium dropped; back to ROUTING.md (gpt-6-sol high)." in out, out
    assert "(applied)" not in out, out


def test_table_skips_unsafe_candidates():
    (skill / "ROUTING.md").write_text(TABLE.replace("`codex` · `gpt-6-sol`", "`bash` · `gpt-6-sol`")
                                      .replace("high<br>medium", "xhigh<br>medium"))
    assert mw_module().table() == {"Bulk code": [("claude-opus-5-5", "medium", "opus-implementer")]}
    (skill / "ROUTING.md").write_text(TABLE.replace("`gpt-6-sol`", "`rm -rf ~`"))
    assert mw_module().table()["Bulk code"][0][0] == "claude-opus-5-5"


def test_notices_are_capped_at_ten():
    routes({"gpt-6-sol-high": (70, 10)})
    st = json.loads((tmp / "state/state.json").read_text())
    st["notices"] = ["n{}".format(i) for i in range(12)]
    st["routes"] = {"Bulk code": {"model": "claude-opus-6", "effort": "medium", "cli": "claude", "index": "x",
                                  "source": "aa", "was": "gpt-6-sol high", "at": "d"}}
    (tmp / "state/state.json").write_text(json.dumps(st))
    watch("run", **KEY)
    assert len(json.loads((tmp / "state/state.json").read_text())["notices"]) == 10


def test_bench_gate_uses_the_holders_tasks_and_known_tokens():
    mw = mw_module()
    price = {"in": 10, "out": 10}
    tsv([("h", "high", "1", 100), ("c", "high", "1", 50), ("c", "high", "9", 999)])
    assert mw.bench_cost(mw.bench_rows(), ("c", "high"), ("h", "high"), price, price) == (0.0005, 0.001)
    tsv([("h", "high", "1", 100), ("c", "high", "1", "")])
    assert mw.bench_cost(mw.bench_rows(), ("c", "high"), ("h", "high"), price, price) == (None, 0.001)
    tsv([("h", "high", "1", 100), ("h", "high", "2", 100), ("c", "high", "1", 50)])
    assert mw.bench_cost(mw.bench_rows(), ("c", "high"), ("h", "high"), price, price) is None
    tsv([("h", "high", "1", 100)])
    bench.write_text(bench.read_text() + "d\tc\tc\thigh\t1\tFAIL\t1\t50\t0\n")
    assert mw.bench_cost(mw.bench_rows(), ("c", "high"), ("h", "high"), price, price) is False


def test_non_numeric_scores_become_none():
    aa.write_text(json.dumps({"data": [{"slug": "gpt-6-sol-high", "artificial_analysis_coding_index": "75",
                                        "pricing": {"price_1m_blended_3_to_1": True}}]}))
    shutil.rmtree(tmp / "state", ignore_errors=True)
    (skill / "ROUTING.md").write_text(TABLE)
    watch("run", **KEY)
    s = json.loads((tmp / "state/state.json").read_text())["snapshot"]["scores"]["gpt-6-sol-high"]
    assert s["coding"] is None and s["price"] is None, s


def test_odd_state_never_crashes_status():
    fresh()
    st = json.loads((tmp / "state/state.json").read_text())
    st.update(routes=None, proposals={"Bulk code": None, "Review": {"model": "x"}}, notices=None)
    (tmp / "state/state.json").write_text(json.dumps(st))
    watch("status")
    st.update(routes={"Bulk code": 3}, notices=[None])
    (tmp / "state/state.json").write_text(json.dumps(st))
    watch("routes")


def test_bare_record_is_ignored_when_effort_records_exist():
    mw = mw_module()
    assert mw.record({"m-high": {}, "m": {}}, "m", "low")[0] is None
    assert mw.record({"m": {}}, "m", "low")[0] == "m"


def test_failed_fetch_still_fails_over_on_the_last_snapshot():
    routes({"gpt-6-sol-high": (70, 10)})
    aa.write_text("not json")
    empty = stub(bindir / "codex2", 'echo \'{"models":[]}\'\n')
    watch("run", CODEX_BIN=empty, **KEY)
    assert "-> claude-opus-5-5 medium (applied)" in watch("routes")


def test_web_catalog_without_its_cli_does_not_count():
    out = routes({"gpt-6-sol-high": (70, 10), "claude-opus-6-medium": (75, 10)}, "<code>claude-opus-6</code>",
                 CLAUDE_BIN=str(tmp / "no-claude"))
    assert "ROUTE" not in out, out


def test_same_winner_refreshes_its_entry():
    rows = {"gpt-6-sol-high": (70, 10), "claude-opus-6-medium": (75, 10)}
    assert "Bench it" in routes(rows, "<code>claude-opus-6</code>")
    watch("ack")
    assert "ROUTE" not in again({**rows, "claude-opus-6-medium": (76, 10)})  # same proposal: stays acked
    benched(("gpt-6-sol", "high"), ("claude-opus-6", "medium"))
    st = json.loads((tmp / "state/state.json").read_text())
    st["proposals"]["Bulk code"]["acked"] = False
    (tmp / "state/state.json").write_text(json.dumps(st))
    out = again(rows)
    assert "(proposed)" in out and "Bench it" not in out and "coding index 75 " in out, out


def test_a_stale_snapshot_never_applies_a_benchmark_change():
    rows = {"gpt-6-sol-high": (70, 10), "claude-opus-6-medium": (75, 10)}
    assert "(proposed)" in routes(rows, "<code>claude-opus-6</code>", AUTO_ROUTE="1")
    benched(("gpt-6-sol", "high"), ("claude-opus-6", "medium"))
    aa.write_text("not json")
    watch("run", AUTO_ROUTE="1", **KEY)
    assert "(applied)" not in watch("routes"), "a failed fetch judged on old scores"


def test_failover_needs_no_snapshot_at_all():
    shutil.rmtree(tmp / "state", ignore_errors=True)
    (skill / "ROUTING.md").write_text(TABLE)
    page.write_text("<code>claude-opus-5-5</code>")
    notes.write_text("")
    aa.write_text("not json")
    empty = stub(bindir / "codex2", 'echo \'{"models":[]}\'\n')
    watch("run", CODEX_BIN=empty, **KEY)
    assert "-> claude-opus-5-5 medium (applied)" in watch("routes")


def test_a_reapplied_route_clears_its_old_drop_notice():
    page_models = "<code>claude-opus-6</code>"
    win, lose = {"gpt-6-sol-high": (70, 10), "claude-opus-6-medium": (75, 10)}, {"gpt-6-sol-high": (76, 10), "claude-opus-6-medium": (75, 20)}
    routes(win, page_models, bench_rows=(("gpt-6-sol", "high"), ("claude-opus-6", "medium")), AUTO_ROUTE="1")
    assert "dropped" in again(lose, AUTO_ROUTE="1")
    out = again(win, AUTO_ROUTE="1")
    assert "-> claude-opus-6 medium (applied)" in out and "dropped" not in out, out


def test_an_acked_proposal_returns_once_it_is_benched():
    rows = {"gpt-6-sol-high": (70, 10), "claude-opus-6-medium": (75, 10)}
    assert "Bench it" in routes(rows, "<code>claude-opus-6</code>")
    watch("ack")
    benched(("gpt-6-sol", "high"), ("claude-opus-6", "medium"))
    out = again(rows)
    assert "(proposed)" in out and "Bench it" not in out, out


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
