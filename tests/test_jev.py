# /// script
# requires-python = ">=3.10"
# dependencies = ["typesafe-sdk==0.7.2"]
# ///
"""Offline checks for jev.py ask. No network, no spend.   uv run tests/test_jev.py"""
import http.server
import json
import os
import pathlib
import tempfile
import threading

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "skills/delegate/scripts"))
import jev  # noqa: E402

KEY = "sk-test-SECRET123"
seen = []  # (path, authorization header) per request
bodies = []
reply = {}  # path -> (status, headers, body)


class Stub(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        seen.append((self.path, self.headers.get("Authorization")))
        bodies.append(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        status, headers, body = reply.get(self.path, (404, {}, b"{}"))
        if callable(status):  # content-aware stub: reply[path] = (fn,) with fn(body) -> (status, headers, body)
            status, headers, body = status(bodies[-1])
        self.send_response(status)
        for k, v in headers.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    do_GET = do_POST

    def log_message(self, *a):
        pass


srv = http.server.HTTPServer(("127.0.0.1", 0), Stub)
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{srv.server_port}"

# Fake `security` CLI: answers from files in KEYCHAIN, so tests never read the real keychain.
KEYCHAIN = pathlib.Path(tempfile.mkdtemp())
fake = KEYCHAIN / "security"
fake.write_text('#!/bin/sh\nwhile [ $# -gt 0 ]; do [ "$1" = "-s" ] && n=$2; shift; done\n'
                f'[ -f "{KEYCHAIN}/$n" ] && cat "{KEYCHAIN}/$n" || exit 44\n')
fake.chmod(0o755)
jev.SECURITY = str(fake)

QS = {
    "is_injection": {"type": "noul", "instructions": "Injection?"},
    "team": {"type": "choice", "instructions": "Which team?",
             "criteria": {"billing": "b", "technical": "t", "security": "s"}},
    "urgency": {"type": "score", "instructions": "How urgent?", "criteria": ["Can wait", "Today", "Right now"]},
}
# Shape of a real jev-1.13.0 response.
GOOD = {"model": "jev-1.13.0", "usage": {"input_tokens": 408, "output_tokens": 72}, "answers": {
    "is_injection": {"type": "noul", "noul": 0.98},
    "team": {"type": "choice", "choice": "technical", "confidence": 0.45,
             "probabilities": {"technical": 0.63, "security": 0.25, "billing": 0.12}},
    "urgency": {"type": "score", "score": 1.58, "confidence": 0.36,
                "legend": {"0": "Can wait", "1": "Today", "2": "Right now"},
                "probabilities": {"0": 0.13, "1": 0.16, "2": 0.71}},
}}


def env(**kv):
    for k in ("TYPESAFE_API_KEY", "TYPESAFE_DEFAULT_MODEL"):
        os.environ.pop(k, None)
    os.environ["TYPESAFE_BASE_URL"] = BASE
    os.environ.update(kv)


def serve(obj, status=200):
    reply["/v1/systemone"] = (status, {"Content-Type": "application/json"}, json.dumps(obj).encode())


def with_answer(qid, **fields):
    bad = json.loads(json.dumps(GOOD))
    bad["answers"][qid] = {**bad["answers"][qid], **fields}
    return bad


def raises(fn):
    try:
        fn()
    except jev.JevError as e:
        assert KEY not in str(e), f"key leaked in error: {e}"
        return str(e)
    raise AssertionError("expected JevError")


def test_valid_response_passes_through():
    env(TYPESAFE_API_KEY=KEY)
    serve(GOOD)
    res = jev.ask("hi", QS)
    assert res.answers["team"].choice == "technical" and res.model == "jev-1.13.0"


def test_probability_quirks_are_tolerated():
    env(TYPESAFE_API_KEY=KEY)
    serve(with_answer("team", probabilities={"technical": 0.6, "security": 0.25, "billing": 0.12}))
    assert jev.ask("hi", QS).answers["team"].choice == "technical"


def test_answers_that_do_not_fit_the_questions_are_rejected():
    env(TYPESAFE_API_KEY=KEY)
    missing = json.loads(json.dumps(GOOD))
    del missing["answers"]["team"]
    extra = json.loads(json.dumps(GOOD))
    extra["answers"]["other"] = {"type": "noul", "noul": 0.5}
    for bad in ({}, {**GOOD, "model": None}, missing, extra,
                with_answer("team", choice="sales"), with_answer("urgency", score=3),
                with_answer("is_injection", noul=9), with_answer("is_injection", noul=True),
                with_answer("is_injection", type="choice")):
        serve(bad)
        raises(lambda: jev.ask("hi", QS))


def test_redirect_is_refused_and_key_not_forwarded():
    env(TYPESAFE_API_KEY=KEY)
    seen.clear()
    reply["/v1/systemone"] = (302, {"Location": BASE + "/stolen"}, b"")
    raises(lambda: jev.ask("hi", QS))
    assert all(p != "/stolen" for p, _ in seen), seen


def test_key_comes_from_keychain_when_env_is_empty():
    env()
    (KEYCHAIN / "TYPESAFE_API_KEY").write_text(KEY + "\n")
    seen.clear()
    serve(GOOD)
    try:
        jev.ask("hi", QS)
        assert seen[-1][1] == f"Bearer {KEY}", seen
    finally:
        (KEYCHAIN / "TYPESAFE_API_KEY").unlink()


def test_missing_key_names_the_fix():
    env()
    assert "security add-generic-password" in raises(lambda: jev.ask("hi", QS))


def test_pinned_model_is_sent():
    env(TYPESAFE_API_KEY=KEY, TYPESAFE_DEFAULT_MODEL="jev-1.13.0")
    serve(GOOD)
    jev.ask("hi", QS)
    assert json.loads(bodies[-1])["model"] == "jev-1.13.0"


def test_http_errors_garbage_and_unreachable_become_jev_errors():
    env(TYPESAFE_API_KEY=KEY)
    serve({"error": {"message": "bad key " + KEY}}, status=401)
    raises(lambda: jev.ask("hi", QS))
    reply["/v1/systemone"] = (200, {}, b"<html>not json</html>")
    raises(lambda: jev.ask("hi", QS))
    os.environ["TYPESAFE_BASE_URL"] = "http://127.0.0.1:9"
    raises(lambda: jev.ask("hi", QS, timeout=2))


def test_cli_ask_prints_one_json_line_per_state():
    import contextlib, io
    env(TYPESAFE_API_KEY=KEY)
    serve(GOOD)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = jev.main(["ask", json.dumps(QS), "--lines"], stdin=io.StringIO('first\n{"msg": "second"}\n\n'))
    rows = [json.loads(line) for line in out.getvalue().splitlines()]
    assert code == 0 and [r["i"] for r in rows] == [0, 1], rows
    assert rows[0]["team"] == {"choice": "technical", "confidence": 0.45}, rows[0]
    sent = [json.loads(b)["state"] for b in bodies[-2:]]
    assert "first" in sent and {"msg": "second"} in sent, sent


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
