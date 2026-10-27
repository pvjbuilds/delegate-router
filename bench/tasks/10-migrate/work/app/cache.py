from functools import partial

from .logger import log


warn = partial(log, "warn")


def miss(key):
    warn(f"cache miss {key}")
