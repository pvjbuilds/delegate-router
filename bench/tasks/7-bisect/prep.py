import datetime
import os
from pathlib import Path
import subprocess
import sys

work = Path(sys.argv[1]).resolve()
env = dict(os.environ, GIT_CONFIG_NOSYSTEM="1",
           GIT_AUTHOR_DATE="2026-01-01T00:00:00+00:00",
           GIT_COMMITTER_DATE="2026-01-01T00:00:00+00:00")


def git(*args):
    return subprocess.run(["git", "-c", "user.name=bench", "-c", "user.email=bench@example.invalid",
                           "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null",
                           "-c", "init.defaultBranch=main", *args], cwd=work, env=env, check=True)


def calc(iterable="items", name="q"):
    return ("from util import money\n\ndef total(items):\n    result = 0\n"
            f"    for {name}, p in {iterable}:\n        result += {name} * p\n"
            "    return money(result)\n")


git("init")
for n in range(1, 41):
    date = (datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
            + datetime.timedelta(minutes=n)).isoformat()
    env.update(GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date)
    with (work / "NOTES.txt").open("a") as f:
        f.write(f"step {n}\n")
    if n == 1:
        (work / "util.py").write_text("def money(x):\n    return round(x, 2)\n")
        (work / "calc.py").write_text("from util import money\n\ndef total(items):\n    return money(sum(q * p for q, p in items))\n")
        (work / "test_total.py").write_text('from calc import total\nassert total([(2, 1.5), (1, 4.25), (3, 0.5)]) == 8.75, total([(2, 1.5), (1, 4.25), (3, 0.5)])\nprint("ok")\n')
    if n == 9:
        (work / "calc.py").write_text(calc())
    if n == 18:
        (work / "util.py").write_text("def money(x)\n    return round(x, 2)\n")
    if n == 22:
        (work / "util.py").write_text("def money(x):\n    return round(x, 2)\n")
    if n == 26:
        (work / "calc.py").write_text(calc("items[:-1]"))
    if n == 33:
        (work / "calc.py").write_text(calc("items[:-1]", "qty"))
    git("add", ".")
    git("commit", "-m", f"step {n}")
