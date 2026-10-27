LEVELS = ("debug", "info", "warn", "error")


def log(msg, level="info"):
    """Print a message at the given level.

    >>> log("hi")
    [INFO] hi
    >>> log("disk 91%", "warn")
    [WARN] disk 91%
    """
    if level not in LEVELS:
        raise ValueError(f"bad level: {level!r}")
    print(f"[{level.upper()}] {msg}")
