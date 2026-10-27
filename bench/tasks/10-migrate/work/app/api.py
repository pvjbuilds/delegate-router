from . import logger


def handle():
    getattr(logger, "log")("warn", "slow request")
