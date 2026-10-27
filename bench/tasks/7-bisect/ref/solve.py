import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

work = Path(sys.argv[1]).resolve()
env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")


def git(*args):
    return subprocess.check_output(["git", *args], cwd=work, env=env, text=True).strip()


first = git("log", "--format=%H", "--grep=^step 1$", "main")
tmp = Path(tempfile.mkdtemp())
try:
    script = tmp / "test.py"
    script.write_text('import subprocess, sys\nr = subprocess.run(["python3", "test_total.py"], capture_output=True, text=True)\nsys.exit(0 if r.returncode == 0 else 1 if "AssertionError" in r.stderr else 125)\n')
    git("bisect", "start", "main", first)
    try:
        subprocess.run(["git", "bisect", "run", "python3", str(script)], cwd=work, env=env, check=True)
        bad = git("rev-parse", "refs/bisect/bad")
        (work / "FIRST_BAD.txt").write_text(bad + "\n")
    finally:
        git("bisect", "reset")
finally:
    shutil.rmtree(tmp)
