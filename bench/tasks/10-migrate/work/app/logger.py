LEVELS = ("debug", "info", "warn", "error")


def log(level, msg):
    """Print a message at the given level.

    >>> log("info", "hi")
    [INFO] hi
    >>> log("warn", "disk 91%")
    [WARN] disk 91%
    """
    if level not in LEVELS:
        raise ValueError(f"bad level: {level!r}")
    print(f"[{level.upper()}] {msg}")
