import functools
import logging
import time

import sentry_sdk
from sentry_sdk.tracing import Transaction


def generate_timer(logger: logging.Logger | bool | None = None, transaction: Transaction | bool = None):
    return functools.partial(Timer, logger=logger, transaction=transaction)


def timeit(func):
    @functools.wraps(func)
    def wrapper_timer(*args, **kwargs):
        with Timer(func.__name__):
            return func(*args, **kwargs)

    return wrapper_timer


class Timer:
    def __init__(self, name, logger: logging.Logger | bool | None = None, transaction: Transaction | bool = None):
        self.name = name

        if logger and not isinstance(logger, logging.Logger):
            logger = logging.getLogger(__name__)

        self.logger = logger

        if transaction and not isinstance(transaction, Transaction):
            transaction = sentry_sdk.Hub.current.scope.transaction

        self.transaction = transaction

    def __enter__(self):
        self.start = time.time()

    def __exit__(self, *args):
        self.end = time.time()

        if self.transaction:
            self.transaction.set_measurement(self.name, self.end - self.start, "seconds")

        if self.logger:
            self.logger.debug(f"{self.name} took {self.end - self.start} seconds")
