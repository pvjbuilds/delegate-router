from pathlib import Path
import subprocess
import sys

work = Path(sys.argv[1]).resolve()


def git(*args):
    return subprocess.check_output(["git", *args], cwd=work, text=True).strip()


expected = git("log", "--format=%H", "--grep=^step 26$", "main")
assert len(expected) == 40 and "\n" not in expected, "step 26 missing or ambiguous"
answer = work / "FIRST_BAD.txt"
assert answer.is_file(), "FIRST_BAD.txt missing"
assert answer.read_text().strip() == expected, "wrong first bad commit"
assert git("symbolic-ref", "HEAD") == "refs/heads/main", "not on main"
last = git("log", "--format=%H", "--grep=^step 40$", "--all")
assert len(last) == 40 and "\n" not in last, "step 40 missing or ambiguous"
assert git("rev-parse", "main") == last, "main moved"
assert not (work / ".git/BISECT_START").exists(), "bisect still active"
status = subprocess.check_output(["git", "status", "--porcelain"], cwd=work, text=True)
assert [line for line in status.splitlines() if line != "?? FIRST_BAD.txt"] == [], "worktree changed"
