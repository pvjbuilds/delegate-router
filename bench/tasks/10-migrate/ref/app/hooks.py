from . import logger


HANDLERS = {"log": logger.log, "print": print}


def fire(name, *args):
    HANDLERS[name](*args)


def run():
    fire("log", "hook fired", "debug")
    fire("print", "plain line")
