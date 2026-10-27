from . import audit, logger


DSN = "sqlite:///app.db"


def open_db():
    logger.log("debug", f"connect {DSN}")
    audit.log("info", "db opened")
