from functools import partial

from .logger import log


warn = partial(log, level="warn")


def miss(key):
    warn(f"cache miss {key}")
