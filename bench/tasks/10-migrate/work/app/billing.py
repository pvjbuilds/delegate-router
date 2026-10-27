from . import audit
from .logger import log


def charge():
    for level, text in [("info", "invoice 12"), ("error", "invoice 13 failed")]:
        log(level, text)
    audit.log("alert", "refund issued")
