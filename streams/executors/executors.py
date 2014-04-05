# -*- coding: utf-8 -*-
"""
This module has implementation of executors wrapped by
:py:class:`streams.executors.mixins.PoolOfPoolsMixin` and applicable to work
with :py:class:`streams.poolofpools.PoolOfPools`.

Basically all of them are thin extensions of classes from
:py:mod:`concurrent.futures`.
"""


###############################################################################


from concurrent.futures import Executor, Future, \
    ThreadPoolExecutor as BaseThreadPoolExecutor, \
    ProcessPoolExecutor as BaseProcessPoolExecutor

from .mixins import PoolOfPoolsMixin


###############################################################################


class SequentalExecutor(PoolOfPoolsMixin, Executor):
    """
    Debug executor. No concurrency, it just yields elements one by one.
    """

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
    """
    Implementation of :py:class:`concurrent.futures.ThreadPoolExecutor`
    applicable to work with :py:class:`streams.poolofpools.PoolOfPools`.
    """
    pass


class ProcessPoolExecutor(PoolOfPoolsMixin, BaseProcessPoolExecutor):
    """
    Implementation of :py:class:`concurrent.futures.ProcessPoolExecutor`
    applicable to work with :py:class:`streams.poolofpools.PoolOfPools`.
    """
    pass
