from . import logger


def handle():
    getattr(logger, "log")("slow request", "warn")
