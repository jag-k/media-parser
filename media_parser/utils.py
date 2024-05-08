import functools
import logging
import time


def generate_timer(logger: logging.Logger | None = None):
    return functools.partial(Timer, logger=logger)


def timeit(func):
    @functools.wraps(func)
    def wrapper_timer(*args, **kwargs):
        with Timer(func.__name__):
            return func(*args, **kwargs)

    return wrapper_timer


class Timer:
    def __init__(
        self,
        name,
        logger: logging.Logger | bool | None = None,
    ):
        self.name = name

        if logger and not isinstance(logger, logging.Logger):
            logger = logging.getLogger(__name__)

        self.logger = logger

    def __enter__(self):
        self.start = time.time()

    def __exit__(self, *args):
        self.end = time.time()

        if self.logger:
            self.logger.debug(f"{self.name} took {self.end - self.start} seconds")
