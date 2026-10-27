def log(level, msg):
    if level not in ("info", "alert"):
        raise ValueError(f"bad level: {level!r}")
    print(f"audit {level}: {msg}")
