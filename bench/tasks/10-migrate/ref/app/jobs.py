from .logger import log as emit


def run():
    emit("job queued")
    emit("job 7 failed", "error")
