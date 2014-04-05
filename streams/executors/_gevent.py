# -*- coding: utf-8 -*-
"""
This module provides implementation of :py:class:`GreenletFuture` (thin
wrapper around :py:class:`concurrent.futures.Future`) and implementation of
:py:class:`GeventExecutor`.

Basically you can use :py:class:`concurrent.futures.ThreadPoolExecutor`, it is
ok and will work but to utilize the power of greenlets more carefully it makes
sense to use custom one.
"""


###############################################################################


from warnings import warn

from concurrent.futures import Future, Executor

try:
    from gevent import Timeout
    from gevent.pool import Pool
except ImportError:
    warn("No gevent is available. Please do not use GeventExecutor, it won't "
         "work")

from .mixins import PoolOfPoolsMixin


###############################################################################


class GreenletFuture(Future):
    """
    Just a thin wrapper around a :py:class:`concurrent.futures.Future` to
    support greenlets.
    """

    def __init__(self, greenlet):
        super(GreenletFuture, self).__init__()
        self._greenlet = greenlet

    def execute(self, timeout=None):
        try:
            processed_result = self._greenlet.get(True, timeout)
        except Timeout as exc:
            self.set_exception(exc)
        else:
            if self._greenlet.exception:
                self.set_exception(self._greenlet.exception)
            else:
                self.set_result(processed_result)

    def result(self, timeout=None):
        self.execute(timeout)
        return super(GreenletFuture, self).result(timeout)

    def exception(self, timeout=None):
        self.execute(timeout)
        return super(GreenletFuture, self).exception(timeout)


class GeventExecutor(PoolOfPoolsMixin, Executor):
    """
    Implementation of Gevent executor fully compatible with
    :py:class:`concurrent.futures.Executor`.
    """

    # noinspection PyUnusedLocal
    def __init__(self, *args, **kwargs):
        super(GeventExecutor, self).__init__()
        self._max_workers = 100
        self.worker_pool = Pool(self._max_workers)

    def submit(self, fn, *args, **kwargs):
        future = self.worker_pool.apply_async(fn, args, kwargs)
        return GreenletFuture(future)
