# -*- coding: utf-8 -*-


###############################################################################


from concurrent.futures import Future, Executor

from gevent import Timeout
from gevent.pool import Pool

from .mixins import PoolOfPoolsMixin


###############################################################################


class GreenletFuture(Future):

    def __init__(self, greenlet):
        super(GreenletFuture, self).__init__()
        self.greenlet = greenlet

    def execute(self, timeout=None):
        try:
            processed_result = self.greenlet.get(True, timeout)
        except Timeout as exc:
            self.set_exception(exc)
        else:
            if self.greenlet.exception:
                self.set_exception(self.greenlet.exception)
            else:
                self.set_result(processed_result)

    def result(self, timeout=None):
        self.execute(timeout)
        return super(GreenletFuture, self).result(timeout)

    def exception(self, timeout=None):
        self.execute(timeout)
        return super(GreenletFuture, self).exception(timeout)

    def cancel(self):
        self.greenlet.kill()
        return super(GreenletFuture, self).cancel()


class GeventExecutor(PoolOfPoolsMixin, Executor):

    # noinspection PyUnusedLocal
    def __init__(self, *args, **kwargs):
        super(GeventExecutor, self).__init__()
        self._max_workers = 100
        self.worker_pool = Pool(self._max_workers)

    def submit(self, fn, *args, **kwargs):
        greenlet = self.worker_pool.apply_async(fn, args, kwargs)
        return GreenletFuture(greenlet)
