# -*- coding: utf-8 -*-


###############################################################################


from concurrent.futures import Executor, Future, \
    ThreadPoolExecutor as BaseThreadPoolExecutor, \
    ProcessPoolExecutor as BaseProcessPoolExecutor

from .mixins import PoolOfPoolsMixin


###############################################################################


class SequentalExecutor(PoolOfPoolsMixin, Executor):

    # noinspection PyUnusedLocal
    def __init__(self, *args, **kwargs):
        super(SequentalExecutor, self).__init__()
        self._max_workers = 1

    def submit(self, fn, *args, **kwargs):
        future = Future()
        try:
            result = fn(*args, **kwargs)
        except Exception as exc:
            future.set_exception(exc)
        else:
            future.set_result(result)
        return future


class ThreadPoolExecutor(PoolOfPoolsMixin, BaseThreadPoolExecutor):
    pass


class ProcessPoolExecutor(PoolOfPoolsMixin, BaseProcessPoolExecutor):
    pass
