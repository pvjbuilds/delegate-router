# /// script
# requires-python = ">=3.10"
# dependencies = ["typesafe-sdk==0.7.2"]
# ///
"""Offline checks for jev.py scout. No network, no spend.   uv run tests/test_scout.py"""
import contextlib
import http.server
import io
import json
import os
import pathlib
import tempfile
import threading

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "skills/delegate/scripts"))
import jev  # noqa: E402

bodies = []  # every request body the stub received, decoded


class Stub(http.server.BaseHTTPRequestHandler):
    """Answers by file content: RELEVANT 0.9, MAYBE 0.5, BOOM -> HTTP 400, else 0.05."""
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0))).decode()
        bodies.append(body)
        content = json.loads(body)["state"]["content"]
        if "BOOM" in content:
            self.send_response(400)
            self.end_headers()
            return
        p = 0.9 if "RELEVANT" in content else 0.5 if "MAYBE" in content else 0.05
        out = {"model": "jev-1.13.0", "usage": {"input_tokens": 1000, "output_tokens": 10},
               "answers": {"needed": {"type": "noul", "noul": p}}}
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(out).encode())

    def log_message(self, *a):
        pass


srv = http.server.HTTPServer(("127.0.0.1", 0), Stub)
threading.Thread(target=srv.serve_forever, daemon=True).start()
os.environ.update(TYPESAFE_BASE_URL=f"http://127.0.0.1:{srv.server_port}", TYPESAFE_API_KEY="sk-test-x")


def repo(files):
    root = pathlib.Path(tempfile.mkdtemp())
    for name, text in files.items():
        p = root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(text if isinstance(text, bytes) else text.encode())
    os.chdir(root)
    bodies.clear()
    return root


def run(*argv, stdin=""):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = jev.main(["scout", *argv], stdin=io.StringIO(stdin))
    return code, out.getvalue()


def test_files_are_ranked_most_needed_first():
    repo({"src/a.py": "RELEVANT", "src/b.py": "MAYBE", "src/c.py": "nothing"})
    code, out = run("fix the retry bug", ".")
    ranked = [line.split()[1] for line in out.splitlines() if line[:1].isdigit()]
    assert code == 0 and ranked == ["src/a.py", "src/b.py", "src/c.py"], out
    assert "3 scored" in out and "$" in out, out
    assert "fix the retry bug" in bodies[0]


def test_paths_can_be_piped_in_from_rg():
    repo({"a.py": "RELEVANT", "b.py": "MAYBE", "c.py": "x"})
    _, out = run("task", stdin="a.py\nc.py\n")
    assert "a.py" in out and "c.py" in out and "b.py" not in out, out
    assert len(bodies) == 2


def test_secrets_binaries_and_escapes_are_never_sent():
    outside = pathlib.Path(tempfile.mkdtemp()) / "other.py"
    outside.write_text("OUTSIDE-ROOT")
    root = repo({
        ".env": "SECRET-ENV",
        "config/api_token.json": "SECRET-NAME",
        "certs/server.pem": "SECRET-PEM",
        "deploy.py": "SECRET-BODY\n-----BEGIN RSA PRIVATE KEY-----\nabc",
        "settings.py": 'API_KEY = "SECRET-HARDCODED-123456"',
        "logo.png": b"\x89PNG\x00\x00SECRET-BINARY",
        "client.py": 'HEADERS = {"Authorization": "Bearer SECRETabcdefghijklmnop12345"}',
        "app.cfg": "api_key: SECRET9abcdefghijklmnop1234",
        "ok.py": "RELEVANT",
    })
    (root / "link.py").symlink_to(outside)
    _, out = run("task", ".")
    sent = "".join(bodies)
    assert "SECRET" not in sent and "OUTSIDE-ROOT" not in sent, sent
    assert len(bodies) == 1 and "9 skipped" in out, out
    assert "skipped: " in out and ".env" in out and "link.py" in out, out  # names shown, never contents


def test_big_files_are_capped_and_marked_cut():
    repo({"big.py": "x" * 50_000})
    _, out = run("task", "big.py")
    assert len(json.loads(bodies[0])["state"]["content"]) <= jev.CAP
    assert "big.py  (cut)" in out, out


def test_every_scored_file_is_listed_by_default():
    repo({f"f{i:02}.py": "x" for i in range(20)})
    _, out = run("task", ".")
    assert sum(line[:1].isdigit() for line in out.splitlines()) == 20, out


def test_one_failed_file_is_reported_and_the_scan_goes_on():
    repo({"a.py": "RELEVANT", "bad.py": "BOOM"})
    code, out = run("task", ".")
    assert code == 0 and "ERR" in out and "bad.py" in out and "a.py" in out, out
    assert "1 error" in out, out


def test_a_raw_question_replaces_the_task_template():
    repo({"a.py": "RELEVANT"})
    run("--ask", "Does this file contain a TODO?", ".")
    q = json.loads(bodies[0])["questions"]["needed"]["instructions"]
    assert q.startswith("Does this file contain a TODO?"), q


def test_too_many_files_is_refused_before_any_spend():
    repo({f"f{i}.py": "x" for i in range(5)})
    code, out = run("--max", "3", "task", ".")
    assert code == 2 and not bodies and "rg -l" in out, out


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
