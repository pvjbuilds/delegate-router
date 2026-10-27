from . import audit, logger


DSN = "sqlite:///app.db"


def open_db():
    logger.log(f"connect {DSN}", "debug")
    audit.log("info", "db opened")
