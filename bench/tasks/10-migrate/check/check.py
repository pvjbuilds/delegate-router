import doctest
import importlib
import inspect
import subprocess
import sys
from pathlib import Path


work = Path(sys.argv[1]).resolve()
EXPECTED = "\n".join([
    "[INFO] boot",
    "[DEBUG] connect sqlite:///app.db",
    "audit info: db opened",
    "[WARN] cache miss user:7",
    "[INFO] job queued",
    "[ERROR] job 7 failed",
    "[DEBUG] hook fired",
    "plain line",
    "[WARN] slow request",
    "[INFO] report ready",
    "[INFO] invoice 12",
    "[ERROR] invoice 13 failed",
    "audit alert: refund issued",
]) + "\n"

result = subprocess.run(
    [sys.executable, "-m", "app"], cwd=work, capture_output=True, text=True
)
assert result.returncode == 0 and result.stdout == EXPECTED, (
    f"returncode: {result.returncode}\n"
    f"actual stdout: {result.stdout!r}\nactual stderr: {result.stderr!r}"
)

result = subprocess.run(
    [sys.executable, "-m", "doctest", "app/logger.py"], cwd=work
)
assert result.returncode == 0, "logger doctests failed"

sys.path.insert(0, str(work))
logger = importlib.import_module("app.logger")
audit = importlib.import_module("app.audit")
parameters = inspect.signature(logger.log).parameters
assert list(parameters) == ["msg", "level"], str(inspect.signature(logger.log))
assert parameters["level"].default == "info", "level must default to info"
parameters = inspect.signature(audit.log).parameters
assert list(parameters) == ["level", "msg"], str(inspect.signature(audit.log))
assert all(p.default is inspect.Parameter.empty for p in parameters.values()), (
    "audit parameters must have no defaults"
)

examples = doctest.DocTestFinder().find(logger.log)
assert sum(len(test.examples) for test in examples) >= 2, "logger doctests missing"

try:
    logger.log("x", "nope")
except ValueError:
    pass
else:
    raise AssertionError("invalid logger level must raise ValueError")

expected_files = {
    "__init__.py", "logger.py", "audit.py", "boot.py", "db.py", "cache.py",
    "jobs.py", "hooks.py", "api.py", "report.py", "billing.py", "__main__.py",
}
actual_files = {
    str(path.relative_to(work / "app"))
    for path in (work / "app").rglob("*")
    if path.is_file() and "__pycache__" not in path.relative_to(work / "app").parts
    and path.suffix != ".pyc"
}
assert actual_files == expected_files, (
    f"unexpected app file set: {actual_files!r}; expected: {expected_files!r}"
)
