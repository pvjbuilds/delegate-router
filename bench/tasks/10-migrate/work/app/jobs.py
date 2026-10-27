from .logger import log as emit


def run():
    emit("info", "job queued")
    emit("error", "job 7 failed")
